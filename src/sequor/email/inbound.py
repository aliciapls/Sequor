"""InboundEmailProcessor — receives parsed emails and creates Message records.

When a reply matches an active escalation, resolves the escalation automatically.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from sequor.config import settings
from sequor.db.models import EscalationStatus, MessageChannel, MessageDirection
from sequor.email.parser import InboundEmail, parse_sendgrid_payload
from sequor.email.utils import mask_email as _mask_email

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
        # Signature verification: skipped in development mode for local testing without SendGrid credentials.
        # In production (app_env != "development"), signature is mandatory.
        if settings.app_env != "development":
            if raw_body is not None and signature is not None:
                if not _verify_sendgrid_signature(raw_body, signature):
                    logger.warning("inbound.signature_invalid")
                    return {"status": "rejected", "reason": "invalid_signature"}
            else:
                # raw_body OR signature absent: the request cannot be verified.
                # In production an empty-body webhook previously fell through
                # UNVERIFIED — reject anything we cannot authenticate.
                logger.warning(
                    "inbound.unverifiable",
                    has_body=raw_body is not None,
                    has_signature=signature is not None,
                )
                return {"status": "rejected", "reason": "missing_signature"}
        else:
            if raw_body is not None and signature is None:
                logger.warning("inbound.no_signature_dev_mode")

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

        # Bind this session to the resolved tenant BEFORE any encrypted-column
        # write/read (Contact.name, Message.subject/body_text/body_raw,
        # Escalation.resolution_summary, LearnedAnswer.*). The session is shared
        # across the whole request, so one bind covers every downstream CRUD
        # call in this flow. No-op without ENCRYPTION_MASTER_KEY (dev fail-open).
        await self._db.bind_tenant(tenant_id)

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
                sender_email=inbound.from_email,
            )

        return {
            "status": "created",
            "message_id": message["id"],
            "contact_id": str(contact["id"]),
            "contact_email": contact.get("email", inbound.from_email),
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
        sender_email: str | None = None,
    ) -> bool:
        """Check if the parent message has an active escalation and resolve it.

        Only resolves if the sender matches the backup contact assigned to
        the escalation. After resolving: triggers learning loop and forwards
        the reply to the original customer.
        """
        try:
            escalations = await self._db.list(
                "Escalation",
                {
                    "message_id": parent_message_id,
                    "tenant_id": tenant_id,
                },
            )
            for esc in escalations:
                if esc.get("status") not in (
                    EscalationStatus.pending.value,
                    EscalationStatus.acknowledged.value,
                ):
                    continue

                # Require backup_contact_id — skip if unassigned
                if not esc.get("backup_contact_id"):
                    logger.warning(
                        "inbound.escalation_no_backup",
                        escalation_id=esc["id"],
                    )
                    continue

                # Require sender_email for authorization
                if not sender_email:
                    logger.warning(
                        "inbound.escalation_no_sender",
                        escalation_id=esc["id"],
                    )
                    continue

                # Verify the sender is the assigned backup contact
                backup = await self._db.read("BackupContact", str(esc["backup_contact_id"]))
                if backup and backup.get("email", "").lower() != sender_email.lower():
                    logger.warning(
                        "inbound.escalation_unauthorized_sender",
                        escalation_id=esc["id"],
                        sender=_mask_email(sender_email),
                    )
                    continue

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

                # Trigger learning loop — capture human answer for future AI improvement
                await self._capture_learning(
                    tenant_id=tenant_id,
                    account_id=str(esc.get("account_id", "")),
                    escalation_id=esc["id"],
                    parent_message_id=parent_message_id,
                    human_reply=reply_text,
                )

                # Forward the human reply to the original customer
                await self._forward_reply_to_customer(
                    parent_message_id=parent_message_id,
                    reply_text=reply_text,
                    tenant_id=tenant_id,
                )

                return True
        except Exception:
            logger.exception(
                "inbound.escalation_resolve_failed",
                parent_message_id=parent_message_id,
            )
        return False

    async def _capture_learning(
        self,
        tenant_id: str,
        account_id: str,
        escalation_id: str,
        parent_message_id: str,
        human_reply: str,
    ) -> None:
        """Feed the human's resolution back into the learning loop."""
        try:
            parent = await self._db.read("Message", parent_message_id)
            if not parent or not parent.get("body_text"):
                return

            from sequor.ai.learning import LearningLoop
            from sequor.db.database import get_engine

            loop = LearningLoop(engine=get_engine())
            await loop.capture_human_answer(
                tenant_id=uuid.UUID(str(tenant_id)),
                account_id=uuid.UUID(str(account_id)),
                escalation_id=uuid.UUID(str(escalation_id)),
                original_query=parent["body_text"],
                human_reply=human_reply or "",
            )
            logger.info(
                "inbound.learning_captured",
                escalation_id=escalation_id,
                tenant_id=tenant_id,
            )
        except Exception:
            logger.exception("inbound.learning_capture_failed", escalation_id=escalation_id)

    async def _forward_reply_to_customer(
        self,
        parent_message_id: str,
        reply_text: str,
        tenant_id: str,
    ) -> None:
        """Forward the backup contact's reply to the original customer."""
        try:
            parent = await self._db.read("Message", parent_message_id)
            if not parent:
                return

            contact = await self._db.read("Contact", str(parent.get("contact_id", "")))
            if not contact or not contact.get("email"):
                return

            from sequor.email.sender import SendGridEmailSender

            sender = SendGridEmailSender()
            await sender.send_reply_to_customer(
                to=contact["email"],
                original_subject=parent.get("subject", "Re: your inquiry"),
                reply_text=reply_text,
                in_reply_to=parent.get("external_message_id"),
            )
            logger.info(
                "inbound.reply_forwarded",
                parent_message_id=parent_message_id,
                to=_mask_email(contact["email"]),
            )
        except Exception:
            logger.exception(
                "inbound.reply_forward_failed",
                parent_message_id=parent_message_id,
            )

    async def _resolve_account(self, to_email: str) -> dict | None:
        """Resolve the destination mailbox to an Account.

        Production (ENCRYPTION_MASTER_KEY set): ``owner_email``/``email_address``
        are ``EncryptedString`` (random AES-GCM nonce per write), so an equality
        filter on the ciphertext never matches and an ORM load would call
        ``process_result_value`` and fail-close before the tenant key is known.
        Look up by the global email blind index via a raw projection of
        non-encrypted columns — mirrors ``onboarding.app.auth_login``.

        Dev (no master key): ``EncryptedString`` stores plaintext and no blind
        index exists, so fall back to plaintext equality on the ORM path. This
        mirrors ``bind_tenant``'s no-op-in-dev split.
        """
        from sequor.config import settings

        if not settings.encryption_master_key:
            lower = to_email.lower()
            by_email = await self._db.list("Account", {"email_address": lower})
            if by_email:
                return by_email[0]
            by_owner = await self._db.list("Account", {"owner_email": lower})
            if by_owner:
                return by_owner[0]
            return None

        from sequor.db.encrypted_column import compute_email_blind_index

        idx = compute_email_blind_index(to_email)
        rows = await self._db.raw_execute(
            "SELECT id, tenant_id, name, status "
            "FROM accounts "
            "WHERE owner_email_blind_index = :idx "
            "OR email_address_blind_index = :idx "
            "LIMIT 1",
            {"idx": idx},
        )
        return rows[0] if rows else None

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

        contact = await self._db.create(
            "Contact",
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "email": email,
                "name": name or email.split("@")[0],
            },
        )
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


def _verify_sendgrid_signature(raw_body: str, signature: str) -> bool:
    """Verify SendGrid Inbound Parse webhook signature using ECDSA.

    SendGrid signs webhooks with ECDSA (Elliptic Curve), not HMAC.
    The public key is configured via SENDGRID_WEBHOOK_VERIFICATION_KEY in .env.
    """
    public_key = settings.sendgrid_webhook_verification_key
    if not public_key:
        logger.warning("inbound.webhook_key_not_configured")
        return False

    import base64

    try:
        from cryptography.hazmat.primitives.asymmetric import ec, utils
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.exceptions import InvalidSignature

        key_bytes = base64.b64decode(public_key)
        sig_bytes = base64.b64decode(signature)

        public_ec_key = serialization.load_der_public_key(key_bytes)
        public_ec_key.verify(
            sig_bytes,
            raw_body.encode("utf-8"),
            ec.ECDSA(hashes.SHA256()),
        )
        return True
    except InvalidSignature:
        logger.warning("inbound.signature_verification_failed")
        return False
    except Exception:
        logger.exception("inbound.signature_verification_error")
        return False
