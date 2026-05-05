"""InboundEmailProcessor — receives parsed emails and creates Message records.

When a reply matches an active escalation, resolves the escalation automatically.
"""

from __future__ import annotations

import hashlib
import hmac
import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from sequor.config import settings
from sequor.db.models import EscalationStatus, MessageChannel, MessageDirection
from sequor.email.parser import InboundEmail, parse_sendgrid_payload

logger = structlog.get_logger()


class InboundEmailProcessor:
    """Processes inbound emails and creates Message records.

    Resolves the sender to a Contact (creates one if new), links to
    existing threads via In-Reply-To, and stores the message for
    downstream classification and routing.

    When the inbound email is a reply to an escalation notification,
    automatically resolves the escalation with the reply content.
    """

    def __init__(self, db_express: Any) -> None:
        self._db = db_express

    async def process_sendgrid_payload(
        self,
        payload: dict[str, Any],
        raw_body: str | None = None,
        signature: str | None = None,
    ) -> dict[str, Any]:
        """Process a SendGrid Inbound Parse webhook payload.

        Args:
            payload: The parsed form fields from SendGrid.
            raw_body: The raw request body (for signature verification).
            signature: The X-Twilio-Email-Event-Webhook-Signature header.

        Returns the created Message record.
        """
        if raw_body is not None and signature is not None:
            if not _verify_sendgrid_signature(raw_body, signature):
                logger.warning("inbound.signature_invalid")
                return {"status": "rejected", "reason": "invalid_signature"}

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

        # If this is a reply to an escalated message, resolve the escalation
        escalation_resolved = False
        if parent_message_id and inbound.is_reply:
            escalation_resolved = await self._try_resolve_escalation(
                parent_message_id=parent_message_id,
                reply_text=inbound.body_text,
                tenant_id=tenant_id,
            )

        return {
            "status": "created",
            "message_id": message["id"],
            "contact_id": str(contact["id"]),
            "tenant_id": str(tenant_id),
            "account_id": str(account_id),
            "is_reply": inbound.is_reply,
            "escalation_resolved": escalation_resolved,
        }

    async def _try_resolve_escalation(
        self,
        parent_message_id: str,
        reply_text: str,
        tenant_id: str,
    ) -> bool:
        """Check if the parent message has an active escalation and resolve it.

        Looks up pending/acknowledged escalations for the parent message
        and resolves the first one found with the reply text as the resolution summary.
        """
        try:
            escalations = await self._db.list("Escalation", {
                "message_id": parent_message_id,
                "tenant_id": tenant_id,
            })
            for esc in escalations:
                if esc.get("status") in (
                    EscalationStatus.pending.value,
                    EscalationStatus.acknowledged.value,
                ):
                    summary = (reply_text or "Resolved via email reply")[:500]
                    await self._db.update(
                        "Escalation",
                        esc["id"],
                        {
                            "status": EscalationStatus.resolved.value,
                            "resolved_at": datetime.now(timezone.utc),
                            "resolution_summary": summary,
                        },
                    )
                    logger.info(
                        "inbound.escalation_resolved",
                        escalation_id=esc["id"],
                        parent_message_id=parent_message_id,
                    )
                    return True
        except Exception:
            logger.exception(
                "inbound.escalation_resolve_failed",
                parent_message_id=parent_message_id,
            )
        return False

    async def _resolve_account(self, to_email: str) -> dict | None:
        lower = to_email.lower()
        by_email = await self._db.list("Account", {"email_address": lower})
        if by_email:
            return by_email[0]
        by_owner = await self._db.list("Account", {"owner_email": lower})
        if by_owner:
            return by_owner[0]
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


def _verify_sendgrid_signature(raw_body: str, signature: str) -> bool:
    """Verify SendGrid Inbound Parse webhook signature using HMAC-SHA256.

    The public key is configured via SENDGRID_WEBHOOK_VERIFICATION_KEY in .env.
    If the key is not configured, verification is skipped (logged as warning).
    """
    public_key = settings.sendgrid_webhook_verification_key
    if not public_key:
        logger.warning("inbound.webhook_key_not_configured")
        return False

    import base64
    try:
        key_bytes = base64.b64decode(public_key)
        expected = hmac.new(key_bytes, raw_body.encode("utf-8"), hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)
    except Exception:
        logger.exception("inbound.signature_verification_error")
        return False
