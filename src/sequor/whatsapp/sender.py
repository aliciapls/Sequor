"""Meta Cloud API-backed WhatsApp sender implementing the WhatsAppSender protocol."""

from __future__ import annotations

import hashlib
from typing import Any

import httpx
import structlog

from sequor.config import settings
from sequor.whatsapp.rate_limiter import WhatsAppRateLimiter
from sequor.whatsapp.utils import mask_phone as _mask_phone

logger = structlog.get_logger()

_META_API_BASE = "https://graph.facebook.com"


class WhatsAppAPIError(Exception):
    """Meta Cloud API returned a non-200 response."""

    def __init__(self, status_code: int, error_data: dict | str) -> None:
        self.status_code = status_code
        self.error_data = error_data
        error_str = str(error_data)
        error_fingerprint = hashlib.sha256(error_str.encode()).hexdigest()[:8]
        super().__init__(
            f"WhatsApp API error {status_code} (error_fingerprint={error_fingerprint})"
        )


class MetaWhatsAppSender:
    """Meta Cloud API implementation of the WhatsAppSender protocol.

    Reads configuration from settings (loaded from .env).
    Rate-limits outbound sends to whatsapp_rate_limit_per_minute.
    """

    def __init__(
        self,
        access_token: str | None = None,
        phone_number_id: str | None = None,
        api_version: str | None = None,
        rate_limit_per_minute: int | None = None,
    ) -> None:
        token = access_token if access_token is not None else settings.whatsapp_access_token
        if not token:
            raise ValueError(
                "WhatsApp access token is required. Set WHATSAPP_ACCESS_TOKEN in .env"
            )
        self._token = token
        self._phone_number_id = phone_number_id or settings.whatsapp_phone_number_id
        if not self._phone_number_id:
            raise ValueError(
                "WhatsApp phone number ID is required. Set WHATSAPP_PHONE_NUMBER_ID in .env"
            )
        self._api_version = api_version or settings.whatsapp_api_version
        self._rate_limiter = WhatsAppRateLimiter(
            max_per_minute=rate_limit_per_minute or settings.whatsapp_rate_limit_per_minute
        )
        self._client: httpx.AsyncClient | None = None
        logger.info(
            "whatsapp.sender.initialized",
            phone_number_id=self._phone_number_id,
            api_version=self._api_version,
            rate_limit=rate_limit_per_minute or settings.whatsapp_rate_limit_per_minute,
        )

    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=_META_API_BASE,
                timeout=httpx.Timeout(30.0, connect=10.0),
            )
        return self._client

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    async def send_text_message(self, to: str, body: str) -> str:
        """Send a free-form text message.

        Only valid within the 24-hour session window after the customer
        has messaged the business.

        Args:
            to: Recipient phone number (with country code, e.g. +6512345678)
            body: Message text (max 4096 characters)

        Returns:
            Meta message ID
        """
        await self._rate_limiter.acquire()

        masked_to = _mask_phone(to)
        logger.info("whatsapp.send_text.start", to=masked_to, body_length=len(body))

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {
                "preview_url": False,
                "body": body,
            },
        }

        try:
            message_id = await self._post(payload)
            logger.info(
                "whatsapp.send_text.ok",
                to=masked_to,
                message_id=message_id,
            )
            return message_id
        except WhatsAppAPIError:
            raise
        except Exception as exc:
            logger.error(
                "whatsapp.send_text.error",
                to=masked_to,
                error=str(exc),
            )
            raise

    async def send_template_message(
        self,
        to: str,
        template_name: str,
        language_code: str = "en",
        components: list | None = None,
    ) -> str:
        """Send a pre-approved template message.

        Valid outside the 24-hour session window.

        Args:
            to: Recipient phone number (with country code)
            template_name: Name of the pre-approved template
            language_code: Template language code (default: en)
            components: List of component objects for template variables

        Returns:
            Meta message ID
        """
        await self._rate_limiter.acquire()

        masked_to = _mask_phone(to)
        logger.info(
            "whatsapp.send_template.start",
            to=masked_to,
            template_name=template_name,
            language_code=language_code,
        )

        payload: dict[str, Any] = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "template",
            "template": {
                "name": template_name,
                "language": {
                    "code": language_code,
                },
            },
        }

        if components:
            payload["template"]["components"] = components

        try:
            message_id = await self._post(payload)
            logger.info(
                "whatsapp.send_template.ok",
                to=masked_to,
                template_name=template_name,
                message_id=message_id,
            )
            return message_id
        except WhatsAppAPIError:
            raise
        except Exception as exc:
            logger.error(
                "whatsapp.send_template.error",
                to=masked_to,
                template_name=template_name,
                error=str(exc),
            )
            raise

    async def _post(self, payload: dict[str, Any]) -> str:
        """POST to the Meta WhatsApp messages endpoint."""
        client = await self._get_client()
        url = f"/{self._api_version}/{self._phone_number_id}/messages"

        headers = {
            "Authorization": f"Bearer {self._token}",
            "Content-Type": "application/json",
        }

        response = await client.post(url, json=payload, headers=headers)

        if response.status_code != 200:
            error_data: dict[str, Any] = {}
            try:
                error_data = response.json()
            except Exception:
                error_data = {"raw": response.text}
            raise WhatsAppAPIError(response.status_code, error_data)

        data = response.json()

        # Meta returns the message ID in the messages array
        messages = data.get("messages", [])
        if not messages:
            # When sending to a session window, Meta may return no messages array
            # but returns a contacts array. Use the to field as fallback.
            return data.get("messages", [{}])[0].get("id", "")

        return messages[0].get("id", "")


# Global client instance
_meta_whatsapp_sender: MetaWhatsAppSender | None = None


def get_whatsapp_sender() -> MetaWhatsAppSender:
    """Get or create the global WhatsApp sender."""
    global _meta_whatsapp_sender
    if _meta_whatsapp_sender is None:
        _meta_whatsapp_sender = MetaWhatsAppSender()
    return _meta_whatsapp_sender
