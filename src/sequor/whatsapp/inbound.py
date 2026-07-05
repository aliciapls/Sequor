"""InboundWhatsAppProcessor — receives parsed WhatsApp messages and creates Message records.

Mirrors InboundEmailProcessor but handles WhatsApp-specific concerns:
- HUMAN override detection (stricter than email opt-out)
- 24-hour session window tracking
- First-contact consent recording
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog

from sequor.compliance import is_human_override
from sequor.db.models import (
    ConsentChannel,
    EscalationStatus,
    MessageChannel,
    MessageDirection,
    OptInMethod,
)
from sequor.whatsapp.parser import parse_meta_webhook_payload
from sequor.whatsapp.utils import mask_phone as _mask_phone

logger = structlog.get_logger()

SESSION_WINDOW_HOURS = 24


class InboundWhatsAppProcessor:
    """Processes inbound WhatsApp messages from Meta Cloud API webhooks.

    Resolves the sender to a Contact (creates one if new), tracks
    session windows, records consent, and stores the message for
    downstream classification and routing.
    """

    def __init__(self, db_express: Any) -> None:
        self._db = db_express

    async def process_meta_payload(self, payload: dict[str, Any]) -> list[dict[str, Any]]:
        """Process a Meta Cloud API webhook payload.

        A single payload may contain multiple messages. Returns a list
        of result dicts, one per message.
        """
        inbound_messages = parse_meta_webhook_payload(payload)

        if not inbound_messages:
            return [{"status": "no_messages"}]

        results = []
        for inbound in inbound_messages:
            result = await self._process_single(inbound)
            results.append(result)

        return results

    async def _process_single(self, inbound: Any) -> dict[str, Any]:
        """Process a single inbound WhatsApp message."""
        masked_from = _mask_phone(inbound.from_phone)
        logger.info(
            "whatsapp.inbound.received",
            from_phone=masked_from,
            message_type=inbound.message_type,
            message_id=inbound.message_id,
        )

        # 1. Resolve account by WhatsApp phone number
        account = await self._resolve_account(inbound.to_phone)
        if account is None:
            logger.warning("whatsapp.inbound.no_account", to=_mask_phone(inbound.to_phone))
            return {"status": "no_account", "from": inbound.from_phone}

        tenant_id = account["tenant_id"]
        account_id = account["id"]

        # Bind this session to the resolved tenant BEFORE any encrypted-column
        # write/read (Contact.name, Message.body_text). The session is shared
        # across the whole request, so one bind covers every downstream CRUD
        # call. No-op without ENCRYPTION_MASTER_KEY (dev fail-open).
        await self._db.bind_tenant(tenant_id)

        # 2. Resolve or create Contact by phone number
        contact = await self._resolve_or_create_contact(
            tenant_id=tenant_id,
            phone=inbound.from_phone,
            name=inbound.contact_name,
        )

        # 3. HUMAN override check — WhatsApp-specific stricter detection
        human_override = is_human_override(inbound.body_text)

        # 4. Check session window
        session_expired = await self._check_session_expired(
            tenant_id=tenant_id,
            contact_id=contact["id"],
        )

        # 5. Create Message record
        message_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": str(tenant_id),
            "contact_id": str(contact["id"]),
            "direction": MessageDirection.inbound.value,
            "channel": MessageChannel.whatsapp.value,
            "body_text": inbound.body_text,
            "external_message_id": inbound.message_id,
            "whatsapp_session_expired": session_expired,
            "received_at": datetime.now(timezone.utc),
        }

        if human_override:
            message_data["human_override"] = True

        message = await self._db.create("Message", message_data)

        logger.info(
            "whatsapp.inbound.message_created",
            message_id=message["id"],
            contact_id=str(contact["id"]),
            tenant_id=str(tenant_id),
            human_override=human_override,
            session_expired=session_expired,
        )

        # 6. First-contact consent recording
        await self._ensure_consent(
            tenant_id=tenant_id,
            contact_id=contact["id"],
            account_id=account_id,
        )

        # 7. If HUMAN override, force escalation
        if human_override:
            logger.info(
                "whatsapp.inbound.human_override",
                contact_id=str(contact["id"]),
                message_id=message["id"],
            )

        return {
            "status": "created",
            "message_id": message["id"],
            "contact_id": str(contact["id"]),
            "contact_phone": contact.get("phone", inbound.from_phone),
            "tenant_id": str(tenant_id),
            "account_id": str(account_id),
            "human_override": human_override,
            "session_expired": session_expired,
            "body_text": inbound.body_text,
            "external_message_id": inbound.message_id,
        }

    async def _resolve_account(self, to_phone: str) -> dict | None:
        """Look up an Account by its WhatsApp phone number.

        Production (ENCRYPTION_MASTER_KEY set): ``whatsapp_phone`` is a plain
        column (equality works), but an ORM load would also materialize
        ``owner_email`` (``EncryptedString``) and fail-close before the tenant
        key is known — use a raw projection of non-encrypted columns. Queries
        both the raw and digit-stripped forms in one shot via ``= ANY(:phones)``
        (row order is unspecified in the implausible case where two accounts
        hold the two forms).

        Dev (no master key): ``owner_email`` materializes as plaintext, so the
        ORM list path works; mirror ``bind_tenant``'s no-op-in-dev split.
        """
        from sequor.config import settings

        if not settings.encryption_master_key:
            accounts = await self._db.list("Account", {"whatsapp_phone": to_phone})
            if accounts:
                return accounts[0]
            cleaned = to_phone.replace("+", "").replace("-", "").replace(" ", "")
            if cleaned != to_phone:
                accounts = await self._db.list("Account", {"whatsapp_phone": cleaned})
                if accounts:
                    return accounts[0]
            return None

        cleaned = to_phone.replace("+", "").replace("-", "").replace(" ", "")
        candidates = [to_phone] if cleaned == to_phone else [to_phone, cleaned]
        # Route through the SECURITY DEFINER lookup function so the query bypasses
        # RLS — this lookup IS the tenant discovery (it must cross tenants to find
        # which tenant owns the phone). A direct SELECT on accounts under RLS
        # would see no rows (the inbound request has no tenant bound yet).
        rows = await self._db.raw_execute(
            "SELECT id, tenant_id, name, whatsapp_phone, status "
            "FROM resolve_account_by_phone(:phones)",
            {"phones": candidates},
        )
        return rows[0] if rows else None

    async def _resolve_or_create_contact(
        self,
        tenant_id: str,
        phone: str,
        name: str | None,
    ) -> dict:
        """Look up a Contact by phone within the tenant, or create one."""
        existing = await self._db.list(
            "Contact",
            {"tenant_id": tenant_id, "phone": phone},
        )
        if existing:
            return existing[0]

        contact = await self._db.create(
            "Contact",
            {
                "id": str(uuid.uuid4()),
                "tenant_id": tenant_id,
                "phone": phone,
                "name": name or phone,
            },
        )
        logger.info(
            "whatsapp.inbound.contact_created",
            contact_id=contact["id"],
            phone=_mask_phone(phone),
        )
        return contact

    async def _check_session_expired(self, tenant_id: str, contact_id: str) -> bool:
        """Check if the 24-hour WhatsApp session window has expired.

        Queries the most recent inbound Message from this contact on the
        WhatsApp channel. If none exists or it was >24h ago, the session
        is expired.
        """
        from datetime import timedelta

        try:
            recent = await self._db.list(
                "Message",
                {
                    "tenant_id": tenant_id,
                    "contact_id": contact_id,
                    "channel": MessageChannel.whatsapp.value,
                    "direction": MessageDirection.inbound.value,
                },
            )

            if not recent:
                return True

            latest = recent[0]
            received_at = latest.get("received_at")
            if not received_at:
                return True

            if isinstance(received_at, str):
                received_at = datetime.fromisoformat(received_at).replace(tzinfo=timezone.utc)

            cutoff = datetime.now(timezone.utc) - timedelta(hours=SESSION_WINDOW_HOURS)
            return received_at < cutoff

        except Exception:
            logger.exception(
                "whatsapp.inbound.session_check_failed",
                contact_id=contact_id,
            )
            return True

    async def _ensure_consent(
        self,
        tenant_id: str,
        contact_id: str,
        account_id: str,
    ) -> None:
        """Create a ChannelConsent record on first WhatsApp contact."""
        try:
            existing = await self._db.list(
                "ChannelConsent",
                {
                    "contact_id": contact_id,
                    "channel": ConsentChannel.whatsapp.value,
                },
            )
            if existing:
                return

            await self._db.create(
                "ChannelConsent",
                {
                    "id": str(uuid.uuid4()),
                    "tenant_id": tenant_id,
                    "contact_id": contact_id,
                    "account_id": account_id,
                    "channel": ConsentChannel.whatsapp.value,
                    "opt_in_method": OptInMethod.first_contact_notice.value,
                    "opt_in_at": datetime.now(timezone.utc),
                },
            )
            logger.info(
                "whatsapp.inbound.consent_created",
                contact_id=contact_id,
                tenant_id=tenant_id,
            )
        except Exception:
            logger.exception(
                "whatsapp.inbound.consent_failed",
                contact_id=contact_id,
            )
