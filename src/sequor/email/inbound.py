"""InboundEmailProcessor — receives parsed emails and creates Message records."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from sequor.db.models import MessageChannel, MessageDirection
from sequor.email.parser import InboundEmail, parse_sendgrid_payload

logger = structlog.get_logger()


class InboundEmailProcessor:
    """Processes inbound emails and creates Message records.

    Resolves the sender to a Contact (creates one if new), links to
    existing threads via In-Reply-To, and stores the message for
    downstream classification and routing.
    """

    def __init__(self, db_express: Any) -> None:
        self._db = db_express

    async def process_sendgrid_payload(
        self,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a SendGrid Inbound Parse webhook payload.

        Returns the created Message record.
        """
        inbound = parse_sendgrid_payload(payload)

        masked_from = _mask_email(inbound.from_email)
        logger.info(
            "inbound.received",
            from_email=masked_from,
            subject=inbound.subject[:80],
            is_reply=inbound.is_reply,
            has_attachments=len(inbound.attachments) > 0,
        )

        account = await self._resolve_account(inbound.to_email)
        if account is None:
            logger.warning("inbound.no_account", to=inbound.to_email)
            return {"status": "no_account", "from": inbound.from_email}

        tenant_id = account["tenant_id"]
        account_id = account["id"]

        contact = await self._resolve_or_create_contact(
            tenant_id=tenant_id,
            email=inbound.from_email,
            name=inbound.from_name,
        )

        parent_message_id = await self._find_parent_message(inbound)

        message_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": str(tenant_id),
            "contact_id": str(contact["id"]),
            "direction": MessageDirection.inbound.value,
            "channel": MessageChannel.email.value,
            "subject": inbound.subject,
            "body_text": inbound.body_text,
            "body_raw": inbound.body_html,
            "external_message_id": inbound.message_id,
            "in_reply_to_id": str(parent_message_id) if parent_message_id else None,
            "received_at": datetime.now(timezone.utc),
        }

        if inbound.attachments:
            attachment_meta = [
                {"filename": a.filename, "content_type": a.content_type}
                for a in inbound.attachments
            ]
            message_data["attachments"] = attachment_meta

        message = await self._db.create("Message", message_data)

        logger.info(
            "inbound.message_created",
            message_id=message["id"],
            contact_id=str(contact["id"]),
            tenant_id=str(tenant_id),
            is_reply=inbound.is_reply,
        )

        return {
            "status": "created",
            "message_id": message["id"],
            "contact_id": str(contact["id"]),
            "tenant_id": str(tenant_id),
            "account_id": str(account_id),
            "is_reply": inbound.is_reply,
        }

    async def _resolve_account(self, to_email: str) -> dict | None:
        accounts = await self._db.list("Account", {})
        for account in accounts:
            if account.get("email_address", "").lower() == to_email.lower():
                return account
            owner = account.get("owner_email", "").lower()
            if owner == to_email.lower():
                return account
        return None

    async def _resolve_or_create_contact(
        self,
        tenant_id: str,
        email: str,
        name: str,
    ) -> dict:
        existing = await self._db.list(
            "Contact",
            {"tenant_id": tenant_id, "email": email},
        )
        if existing:
            return existing[0]

        contact = await self._db.create("Contact", {
            "id": str(uuid.uuid4()),
            "tenant_id": tenant_id,
            "email": email,
            "name": name or email.split("@")[0],
        })
        logger.info("inbound.contact_created", contact_id=contact["id"], email=_mask_email(email))
        return contact

    async def _find_parent_message(self, inbound: InboundEmail) -> str | None:
        if not inbound.message_id:
            return None
        reply_header = inbound.in_reply_to or inbound.references
        if not reply_header:
            return None

        raw_id = reply_header.strip()
        clean_id = raw_id.strip("<>")

        for candidate in [raw_id, clean_id]:
            messages = await self._db.list(
                "Message",
                {"external_message_id": candidate},
            )
            if messages:
                return messages[0]["id"]

        if inbound.references:
            for ref_id in inbound.references.split():
                raw = ref_id.strip()
                clean = raw.strip("<>")
                for candidate in [raw, clean]:
                    refs = await self._db.list(
                        "Message",
                        {"external_message_id": candidate},
                    )
                    if refs:
                        return refs[0]["id"]

        return None


def _mask_email(email: str) -> str:
    if "@" not in email:
        return "***"
    local, domain = email.split("@", 1)
    if len(local) <= 2:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"
