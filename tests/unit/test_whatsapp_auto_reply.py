"""Unit tests for sequor.whatsapp.auto_reply — A3 footer + channel parity."""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from sequor.ai.classifier import ClassificationResult, MessageCategory, MessageUrgency
from sequor.ai.response import ResponseResult
from sequor.whatsapp.auto_reply import (
    DEFAULT_WHATSAPP_FOOTER,
    WhatsAppAutoReplyResult,
    WhatsAppAutoReplyService,
    WhatsAppMessageContext,
)


def _classification(
    category: str = "routine",
    urgency: str = "low",
    confidence: float = 0.95,
) -> ClassificationResult:
    return ClassificationResult(
        category=MessageCategory(category),
        urgency=MessageUrgency(urgency),
        confidence=confidence,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )


def _response(
    was_auto_sent: bool = True,
    escalation_needed: bool = False,
    confidence: float = 0.92,
    badge: str = "moderate",
) -> ResponseResult:
    return ResponseResult(
        content="Our hours are 9am to 5pm.",
        confidence_badge=badge,
        confidence_score=confidence,
        was_auto_sent=was_auto_sent,
        sources=[],
        routing_target="auto_respond" if was_auto_sent else "escalation_queue",
        escalation_needed=escalation_needed,
    )


def _context(body_text: str = "What are your hours?") -> WhatsAppMessageContext:
    return WhatsAppMessageContext(
        tenant_id=uuid4(),
        account_id=uuid4(),
        contact_phone="+15551234567",
        message_id=uuid4(),
        body_text=body_text,
    )


@pytest.fixture
def mock_classifier():
    classifier = AsyncMock()
    classifier.classify = AsyncMock(return_value=_classification())
    return classifier


@pytest.fixture
def mock_rag():
    return AsyncMock()


@pytest.fixture
def mock_wa_sender():
    sender = AsyncMock()
    sender.send_text_message = AsyncMock(return_value="wa-msg-id")
    sender.send_template_message = AsyncMock(return_value="wa-tpl-id")
    return sender


@pytest.fixture
def mock_response_gen():
    gen = AsyncMock()
    gen.generate = AsyncMock(return_value=_response())
    return gen


@pytest.fixture
def service(mock_classifier, mock_rag, mock_wa_sender, mock_response_gen):
    return WhatsAppAutoReplyService(
        classifier=mock_classifier,
        rag_pipeline=mock_rag,
        whatsapp_sender=mock_wa_sender,
        response_generator=mock_response_gen,
    )


# ---------------------------------------------------------------------------
# Footer confidence rendering (plan §2.6)
# ---------------------------------------------------------------------------


class TestFooterConfidence:
    """The WhatsApp footer MUST include the unified confidence percentage (A3)."""

    def test_footer_includes_confidence_placeholder(self):
        """DEFAULT_WHATSAPP_FOOTER carries the {confidence_pct} token for formatting."""
        assert "{confidence_pct" in DEFAULT_WHATSAPP_FOOTER

    def test_footer_renders_confidence_at_92_percent(self, service, mock_wa_sender):
        """A response with 0.92 confidence renders '92%' in the footer."""
        footer = service._footer_tpl.format(business_name="TestCo", confidence_pct=92.0)
        assert "92%" in footer
        assert "TestCo" in footer

    def test_footer_renders_confidence_at_60_percent(self, service, mock_wa_sender):
        """A response with 0.60 confidence renders '60%' in the footer."""
        footer = service._footer_tpl.format(business_name="TestCo", confidence_pct=60.0)
        assert "60%" in footer

    def test_footer_still_includes_human_escalation_path(self, service, mock_wa_sender):
        """The 'speak with a human' path is preserved alongside the confidence figure."""
        footer = service._footer_tpl.format(business_name="TestCo", confidence_pct=85.0)
        assert "speak with a human" in footer.lower()


# ---------------------------------------------------------------------------
# A3 channel parity — WhatsApp honors was_auto_sent (plan §2.4/§2.5c)
# ---------------------------------------------------------------------------


class TestChannelParity:
    """WhatsApp must NOT send when was_auto_sent=False (parity with email §2.4)."""

    async def test_was_auto_sent_false_not_sent(self, service, mock_classifier, mock_response_gen):
        """Plan §2.5c: WhatsApp message with was_auto_sent=False is NOT sent."""
        mock_classifier.classify.return_value = _classification()
        mock_response_gen.generate.return_value = _response(
            was_auto_sent=False, escalation_needed=True, confidence=0.3, badge="low"
        )

        with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = uuid4()
            with patch.object(service, "_create_escalation", new_callable=AsyncMock) as mock_esc:
                mock_esc.return_value = uuid4()
                result = await service.process_message(_context())

        assert result.message_sent is False
        assert result.escalated is True

    async def test_was_auto_sent_true_sends_within_session(
        self, service, mock_classifier, mock_response_gen, mock_wa_sender
    ):
        """WhatsApp auto-sends when the unified predicate approves (A3 parity)."""
        mock_classifier.classify.return_value = _classification()
        mock_response_gen.generate.return_value = _response(
            was_auto_sent=True, escalation_needed=False, confidence=0.92, badge="moderate"
        )

        with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = uuid4()
            result = await service.process_message(_context())

        assert result.message_sent is True
        assert result.escalated is False
        mock_wa_sender.send_text_message.assert_called_once()

    async def test_auto_reply_includes_confidence_in_footer(
        self, service, mock_classifier, mock_response_gen, mock_wa_sender
    ):
        """The sent WhatsApp message body includes the confidence percentage."""
        mock_classifier.classify.return_value = _classification()
        mock_response_gen.generate.return_value = _response(
            was_auto_sent=True, escalation_needed=False, confidence=0.88, badge="moderate"
        )

        with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
            mock_record.return_value = uuid4()
            await service.process_message(_context())

        call_args = mock_wa_sender.send_text_message.call_args
        body = call_args.kwargs["body"]
        assert "88%" in body


# ---------------------------------------------------------------------------
# WhatsAppAutoReplyResult structure
# ---------------------------------------------------------------------------


def test_whatsapp_result_defaults():
    """WhatsAppAutoReplyResult has all expected fields."""
    result = WhatsAppAutoReplyResult(
        response_recorded=True,
        message_sent=False,
        sent_via_template=False,
        escalated=True,
        escalation_id=None,
        response_id=None,
        confidence_badge="uncertain",
        confidence_score=0.0,
        routing_target="escalation_queue",
        error=None,
    )
    assert result.message_sent is False
    assert result.escalated is True
    assert result.confidence_badge == "uncertain"
