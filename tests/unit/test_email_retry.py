"""Unit tests for email retry with exponential backoff."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from sequor.email.sender import SendGridEmailSender, SendGridAPIError


@pytest.fixture(autouse=True)
def _no_wall_clock_sleep():
    """Retry backoff delays are read from settings at SEND time (outside the
    per-test settings patch in `_make_sender`), so the exhaustion path would
    sleep on the REAL default backoff (0,300,1800s → tens of minutes) and hang
    the suite. These tests assert retry LOGIC (call counts / raise), not timing,
    so the wall-clock sleep is patched out here (testing.md: no time-dependent
    assertions in Tier-1)."""
    with patch("sequor.email.sender.asyncio.sleep", new_callable=AsyncMock):
        yield


def _make_sender():
    with patch("sequor.email.sender.SendGridAPIClient"):
        with patch("sequor.email.sender.settings") as mock_settings:
            mock_settings.sendgrid_api_key = "test-key"
            mock_settings.email_from_domain = "test.com"
            mock_settings.email_rate_limit_per_minute = 100
            mock_settings.email_retry_max_attempts = 3
            mock_settings.email_retry_backoff_seconds = "0,0,0"
            sender = SendGridEmailSender()
            sender._rate_limiter = AsyncMock()
            sender._rate_limiter.acquire = AsyncMock()
            return sender


class TestEmailRetryBackoff:
    @pytest.mark.asyncio
    async def test_succeeds_on_first_attempt(self):
        sender = _make_sender()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg-123"}
        sender._post = MagicMock(return_value=mock_response)

        result = await sender._send(
            to="test@example.com",
            subject="Test",
            body_html="<p>hi</p>",
            body_text="hi",
        )
        assert result == "msg-123"
        assert sender._post.call_count == 1

    @pytest.mark.asyncio
    async def test_retries_on_failure_then_succeeds(self):
        sender = _make_sender()
        mock_response = MagicMock()
        mock_response.status_code = 202
        mock_response.headers = {"X-Message-Id": "msg-456"}
        sender._post = MagicMock(side_effect=[Exception("network error"), mock_response])

        result = await sender._send(
            to="test@example.com",
            subject="Test",
            body_html="<p>hi</p>",
            body_text="hi",
        )
        assert result == "msg-456"
        assert sender._post.call_count == 2

    @pytest.mark.asyncio
    async def test_raises_after_all_retries_exhausted(self):
        sender = _make_sender()
        sender._post = MagicMock(side_effect=Exception("persistent error"))

        with pytest.raises(Exception, match="persistent error"):
            await sender._send(
                to="test@example.com",
                subject="Test",
                body_html="<p>hi</p>",
                body_text="hi",
            )
        assert sender._post.call_count == 3

    @pytest.mark.asyncio
    async def test_retries_on_sendgrid_api_error(self):
        sender = _make_sender()
        mock_ok = MagicMock()
        mock_ok.status_code = 202
        mock_ok.headers = {"X-Message-Id": "msg-789"}

        mock_err = MagicMock()
        mock_err.status_code = 500
        mock_err.body = b"Internal Server Error"

        sender._post = MagicMock(side_effect=[mock_err, mock_ok])

        result = await sender._send(
            to="test@example.com",
            subject="Test",
            body_html="<p>hi</p>",
            body_text="hi",
        )
        assert result == "msg-789"
        assert sender._post.call_count == 2


class TestBackoffParsing:
    def test_parses_comma_separated_string(self):
        with patch("sequor.email.sender.SendGridAPIClient"):
            with patch("sequor.email.sender.settings") as mock_settings:
                mock_settings.sendgrid_api_key = "test-key"
                mock_settings.email_from_domain = "test.com"
                mock_settings.email_rate_limit_per_minute = 100
                mock_settings.email_retry_backoff_seconds = "0,60,300"
                sender = SendGridEmailSender()
        from sequor.email.sender import _get_backoff_delays

        with patch("sequor.email.sender.settings") as mock_settings:
            mock_settings.email_retry_backoff_seconds = "0,60,300"
            delays = _get_backoff_delays()
        assert delays == [0.0, 60.0, 300.0]

    def test_fallback_on_invalid_string(self):
        from sequor.email.sender import _get_backoff_delays

        with patch("sequor.email.sender.settings") as mock_settings:
            mock_settings.email_retry_backoff_seconds = "not,valid"
            delays = _get_backoff_delays()
        assert delays == [0.0, 300.0, 1800.0]
