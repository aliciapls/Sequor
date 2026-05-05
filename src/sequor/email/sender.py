"""SendGrid-backed email sender implementing the EmailSender protocol."""

from __future__ import annotations

import asyncio
import hashlib
import re
import structlog
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import CustomArg, Header, Mail, ReplyTo

from sequor.config import settings
from sequor.email.rate_limiter import EmailRateLimiter, RateLimitExceededError
from sequor.email.templates import _sanitize_header

logger = structlog.get_logger()

_EXECUTOR_MAX_WORKERS = 10


class SendGridAPIError(Exception):
    """SendGrid returned a non-202 response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        body_fingerprint = hashlib.sha256(body.encode()).hexdigest()[:8]
        super().__init__(
            f"SendGrid API error {status_code} (body_fingerprint={body_fingerprint})"
        )


class SendGridEmailSender:
    """SendGrid-backed implementation of the EmailSender protocol.

    Reads api_key from settings (loaded from .env).
    Rate-limits outbound sends to email_rate_limit_per_minute.
    """

    def __init__(
        self,
        api_key: str | None = None,
        from_domain: str | None = None,
        rate_limit_per_minute: int | None = None,
    ) -> None:
        key = api_key if api_key is not None else settings.sendgrid_api_key
        if not key:
            raise ValueError(
                "SendGrid API key is required. Set SENDGRID_API_KEY in .env"
            )
        self._client = SendGridAPIClient(api_key=key)
        self._from_domain = from_domain or settings.email_from_domain
        self._rate_limiter = EmailRateLimiter(
            max_per_minute=rate_limit_per_minute or settings.email_rate_limit_per_minute
        )
        self._executor = ThreadPoolExecutor(max_workers=_EXECUTOR_MAX_WORKERS)
        logger.info(
            "email.sender.initialized",
            from_domain=self._from_domain,
            rate_limit=rate_limit_per_minute or settings.email_rate_limit_per_minute,
        )

    async def send_email(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None = None,
        in_reply_to: str | None = None,
    ) -> str:
        """Send an email via SendGrid. Returns the SendGrid message ID."""
        return await self._send(to, subject, body_html, body_text, reply_to, in_reply_to)

    async def send_escalation_email(
        self,
        to: str,
        escalation_id: str,
        subject: str,
        body_html: str,
        body_text: str,
    ) -> str:
        """Send an escalation notification with reply-to-resolve metadata."""
        return await self._send(
            to,
            subject,
            body_html,
            body_text,
            reply_to=f"coverage@{self._from_domain}",
            in_reply_to=None,
            escalation_id=escalation_id,
        )

    async def send_reply_to_customer(
        self,
        to: str,
        original_subject: str,
        reply_text: str,
        in_reply_to: str | None = None,
    ) -> str:
        """Forward a backup contact's reply to the original customer."""
        subject = original_subject if original_subject.startswith("Re: ") else f"Re: {original_subject}"
        body_text = reply_text or ""
        body_html = f"<p>{body_text}</p>"
        return await self._send(
            to, subject, body_html, body_text,
            in_reply_to=in_reply_to,
        )

    async def _send(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None = None,
        in_reply_to: str | None = None,
        escalation_id: str | None = None,
    ) -> str:
        await self._rate_limiter.acquire()

        mail = self._build_mail(
            to, subject, body_html, body_text, reply_to, in_reply_to, escalation_id
        )

        masked_to = _mask_email(to)
        logger.info("email.send.start", to=masked_to, subject=subject[:80])

        backoff_delays = _get_backoff_delays()
        max_attempts = min(len(backoff_delays), _get_max_retry_attempts())

        last_exception: Exception | None = None

        for attempt in range(max_attempts):
            try:
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    self._executor, self._post, mail
                )

                status = response.status_code
                if status != 202:
                    body = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
                    raise SendGridAPIError(status, body)

                message_id = _extract_message_id(response.headers)
                logger.info(
                    "email.send.ok",
                    to=masked_to,
                    message_id=message_id,
                    attempt=attempt + 1,
                )
                return message_id

            except Exception as exc:
                last_exception = exc
                delay = backoff_delays[attempt] if attempt < len(backoff_delays) else backoff_delays[-1]

                if attempt < max_attempts - 1:
                    logger.warning(
                        "email.send.retry",
                        to=masked_to,
                        attempt=attempt + 1,
                        max_attempts=max_attempts,
                        delay_seconds=delay,
                        error=str(exc),
                    )
                    if delay > 0:
                        await asyncio.sleep(delay)
                else:
                    logger.error(
                        "email.send.exhausted",
                        to=masked_to,
                        attempts=max_attempts,
                        error=str(exc),
                    )
                    raise last_exception from None

        raise last_exception from None  # type: ignore[misc]

    def _build_mail(
        self,
        to: str,
        subject: str,
        body_html: str,
        body_text: str,
        reply_to: str | None = None,
        in_reply_to: str | None = None,
        escalation_id: str | None = None,
    ) -> Mail:
        from_email = f"coverage@{self._from_domain}"
        safe_to = _validate_email(to)
        safe_subject = _sanitize_header(subject)
        mail = Mail(
            from_email=from_email,
            to_emails=safe_to,
            subject=safe_subject,
            html_content=body_html,
            plain_text_content=body_text,
        )

        if reply_to:
            safe_reply_to = _validate_email(reply_to)
            mail.reply_to = ReplyTo(safe_reply_to)

        if in_reply_to:
            safe_irt = _sanitize_header(in_reply_to)
            mail.add_header(Header("In-Reply-To", safe_irt))
            mail.add_header(Header("References", safe_irt))

        if escalation_id:
            safe_esc_id = _sanitize_header(escalation_id)
            mail.add_header(Header("X-Sequor-Escalation-Id", safe_esc_id))
            mail.add_custom_arg(CustomArg("escalation_id", safe_esc_id))

        return mail

    def _post(self, mail: Mail) -> Any:
        return self._client.client.mail.send.post(request_body=mail.get())


def _get_backoff_delays() -> list[float]:
    raw = settings.email_retry_backoff_seconds
    try:
        return [float(s.strip()) for s in raw.split(",")]
    except (ValueError, AttributeError):
        return [0.0, 300.0, 1800.0]


def _get_max_retry_attempts() -> int:
    return settings.email_retry_max_attempts


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"


def _extract_message_id(headers: dict | Any) -> str:
    if isinstance(headers, dict):
        return headers.get("X-Message-Id", "")
    return getattr(headers, "get", lambda k, d="": d)("X-Message-Id", "")


_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")


def _validate_email(email: str) -> str:
    """Sanitize and validate an email address for use in SMTP headers."""
    clean = _sanitize_header(email.strip())
    clean = clean.replace("\r", "").replace("\n", "")
    if not _EMAIL_RE.match(clean):
        raise ValueError(f"Invalid email address (fingerprint={hashlib.sha256(email.encode()).hexdigest()[:8]})")
    return clean
