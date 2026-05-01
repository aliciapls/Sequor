"""SendGrid-backed email sender implementing the EmailSender protocol."""

from __future__ import annotations

import asyncio
import structlog
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import CustomArg, Header, Mail, ReplyTo

from sequor.config import settings
from sequor.email.rate_limiter import EmailRateLimiter, RateLimitExceededError

logger = structlog.get_logger()

_EXECUTOR_MAX_WORKERS = 10


class SendGridAPIError(Exception):
    """SendGrid returned a non-202 response."""

    def __init__(self, status_code: int, body: str) -> None:
        self.status_code = status_code
        self.body = body
        super().__init__(f"SendGrid API error {status_code}: {body[:200]}")


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

        loop = asyncio.get_running_loop()
        try:
            response = await loop.run_in_executor(
                self._executor, self._post, mail
            )
        except Exception as exc:
            logger.exception("email.send.error", to=masked_to, error=str(exc))
            raise

        status = response.status_code
        if status != 202:
            body = response.body.decode() if isinstance(response.body, bytes) else str(response.body)
            logger.error("email.send.error", to=masked_to, status_code=status)
            raise SendGridAPIError(status, body)

        message_id = _extract_message_id(response.headers)
        logger.info("email.send.ok", to=masked_to, message_id=message_id)
        return message_id

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
        mail = Mail(
            from_email=from_email,
            to_emails=to,
            subject=subject,
            html_content=body_html,
            plain_text_content=body_text,
        )

        if reply_to:
            mail.reply_to = ReplyTo(reply_to)

        if in_reply_to:
            mail.add_header(Header("In-Reply-To", in_reply_to))
            mail.add_header(Header("References", in_reply_to))

        if escalation_id:
            mail.add_header(Header("X-Sequor-Escalation-Id", escalation_id))
            mail.add_custom_arg(CustomArg("escalation_id", escalation_id))

        return mail

    def _post(self, mail: Mail) -> Any:
        return self._client.client.mail.send.post(request_body=mail.get())


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
