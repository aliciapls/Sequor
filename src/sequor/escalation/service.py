"""EscalationService — core escalation business logic."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import structlog

from sequor.config import settings
from sequor.email.utils import mask_email as _mask_email
from sequor.db.models import (
    ContactTier,
    EscalationPriority,
    EscalationStatus,
)
from sequor.email.templates import (
    EscalationEmailData,
    _sanitize_header,
    build_escalation_email,
    build_escalation_subject,
)
from sequor.escalation.sla import calculate_deadline, is_breached
from sequor.protocols import EmailSender

if TYPE_CHECKING:
    pass

logger = structlog.get_logger()


class EscalationError(Exception):
    """Base exception for escalation failures."""


class BackupNotFoundError(EscalationError):
    """No backup contact found for the account."""


class EscalationNotFoundError(EscalationError):
    """The escalation record was not found."""


class EscalationService:
    """Handles escalation creation, notification, and resolution.

    Uses DataFlow's express CRUD for all database operations and
    delegates email sending to the injected EmailSender.
    """

    def __init__(
        self,
        db_express: Any,
        email_sender: EmailSender,
        config_sla_hours: int | None = None,
    ) -> None:
        """Initialize the escalation service.

        Args:
            db_express: A DataFlow express instance (e.g., db.express from kailash-dataflow).
                        Must implement: list(model, filter), create(model, data),
                        update(model, id, data), read(model, id).
            email_sender: An EmailSender-compatible async email client.
            config_sla_hours: Override for default_escalation_sla_hours (for testing).
        """
        self._db = db_express
        self._email_sender = email_sender
        self._default_sla = config_sla_hours or settings.default_escalation_sla_hours

    async def bind_tenant(self, tenant_id) -> None:
        """Bind this service's session to *tenant_id* for encrypted-column access.

        EscalationService reads ``BackupContact.email`` / ``Account.owner_email``
        / ``Message.*`` / ``Contact.name`` and writes ``Escalation.resolution_summary``
        — all ``EncryptedString``. The caller MUST bind the tenant before invoking
        any method that touches those columns. The request-bound callers
        (``auto_reply._create_escalation``) bind at session open; background
        callers (``SLAScheduler``) MUST call this per-tenant in their loop.
        """
        await self._db.bind_tenant(tenant_id)

    async def create_escalation(
        self,
        message_id: uuid.UUID,
        tenant_id: uuid.UUID,
        account_id: uuid.UUID,
        priority: EscalationPriority,
        ai_summary: str,
        routing_reason: str,
        suggested_response: str | None = None,
        confidence_score: float = 0.0,
    ) -> dict[str, Any]:
        """Create a tier-1 escalation and notify the primary backup contact.

        1. Look up the account to get SLA hours and org name.
        2. Look up the primary backup contact for the account.
        3. Fetch the original message for context.
        4. Create the Escalation record.
        5. Build and send the escalation email.
        6. Return the escalation record.

        Raises:
            BackupNotFoundError: if no active primary backup is configured.
        """
        account = await self._db.read("Account", str(account_id))
        if account is None:
            raise EscalationError(f"Account {account_id} not found")

        sla_hours = account.get("escalation_sla_hours", self._default_sla)
        org_name = account.get("name", "your team")

        backup = await self._get_primary_backup(account_id)
        if backup is None:
            raise BackupNotFoundError(
                f"No active primary backup contact found for account {account_id}"
            )

        message = await self._db.read("Message", str(message_id))
        if message is None:
            raise EscalationError(f"Message {message_id} not found")

        contact = await self._db.read("Contact", str(message["contact_id"]))

        now = datetime.now(timezone.utc)
        deadline = calculate_deadline(now, sla_hours)
        escalation_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": str(tenant_id),
            "message_id": str(message_id),
            "account_id": str(account_id),
            "backup_contact_id": str(backup["id"]),
            "tier": 1,
            "status": EscalationStatus.pending.value,
            "priority": priority.value,
        }
        escalation_record = await self._db.create("Escalation", escalation_data)

        logger.info(
            "escalation.created",
            escalation_id=escalation_record["id"],
            tier=1,
            priority=priority.value,
            backup_name=backup["name"],
            deadline=deadline.isoformat(),
        )

        # Write audit trail
        await self._write_audit(
            tenant_id=tenant_id,
            action="escalation.created",
            doer_type="system",
            doer_id=tenant_id,
            recipient_type="backup_contact",
            recipient_id=backup["id"],
            message_id=message_id,
            metadata={"tier": 1, "priority": priority.value},
        )

        body_html, body_text = self._build_email(
            escalation_record,
            contact,
            message,
            backup,
            deadline,
            ai_summary,
            routing_reason,
            suggested_response,
            org_name,
        )

        subject = build_escalation_subject(
            EscalationEmailData(
                escalation_id=escalation_record["id"],
                contact_name=contact["name"] if contact else "Unknown",
                contact_channel=message.get("channel", "unknown"),
                received_at=_format_datetime(message.get("received_at", now)),
                ai_attempted=routing_reason,
                confidence_score=confidence_score,
                confidence_category="escalated",
                original_message_body=message.get("body_text", ""),
                escalation_deadline=_format_datetime(deadline),
                backup_name=backup["name"],
                suggested_response=suggested_response,
                org_name=org_name,
                one_line_summary=ai_summary,
            )
        )

        try:
            await self._email_sender.send_escalation_email(
                to=backup["email"],
                escalation_id=escalation_record["id"],
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
            logger.info(
                "escalation.email_sent",
                escalation_id=escalation_record["id"],
                to=_mask_email(backup["email"]),
            )
        except Exception as e:
            logger.warning(
                "escalation.email_failed_notification_pending",
                escalation_id=escalation_record["id"],
                to=_mask_email(backup["email"]),
                error=str(e),
            )
            await self._db.update(
                "Escalation",
                escalation_record["id"],
                {"status": EscalationStatus.notification_pending.value},
            )
            escalation_record["status"] = EscalationStatus.notification_pending.value

        return escalation_record

    async def escalate_to_second_tier(
        self,
        escalation_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Create a tier-2 escalation and notify the second-tier backup.

        Looks up the original escalation's account (via BackupContact), finds
        the second-tier backup, creates a new escalation record, and sends
        the escalation email.

        Returns the new tier-2 escalation record.

        Raises:
            EscalationNotFoundError: if the original escalation is not found.
            BackupNotFoundError: if no active second-tier backup is configured.
        """
        original = await self._db.read("Escalation", str(escalation_id))
        if original is None:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")

        # Only escalate escalations that are expired (breached) or pending
        allowed = {EscalationStatus.pending.value, EscalationStatus.expired.value}
        if original.get("status") not in allowed:
            raise EscalationError(
                f"Cannot escalate from status '{original.get('status')}' "
                f"(expected pending or expired)"
            )

        backup = await self._db.read("BackupContact", str(original["backup_contact_id"]))
        account_id = backup["account_id"] if backup else None

        account = await self._db.read("Account", str(account_id)) if account_id else None
        if account is None:
            raise EscalationError("Account not found for escalation")

        sla_hours = account.get("escalation_sla_hours", self._default_sla)
        org_name = account.get("name", "your team")

        second_tier_backup = await self._get_second_tier_backup(account_id)
        if second_tier_backup is None:
            raise BackupNotFoundError(
                f"No active second-tier backup contact found for account {account_id}"
            )

        now = datetime.now(timezone.utc)
        deadline = calculate_deadline(now, sla_hours)
        escalation_data = {
            "id": str(uuid.uuid4()),
            "tenant_id": original["tenant_id"],
            "message_id": original["message_id"],
            "account_id": str(account_id),
            "backup_contact_id": str(second_tier_backup["id"]),
            "tier": 2,
            "status": EscalationStatus.pending.value,
            "priority": original["priority"],
        }
        new_escalation = await self._db.create("Escalation", escalation_data)

        logger.info(
            "escalation.second_tier",
            escalation_id=new_escalation["id"],
            original_escalation_id=str(escalation_id),
            tier=2,
            backup_name=second_tier_backup["name"],
        )

        message = await self._db.read("Message", str(original["message_id"]))
        contact = await self._db.read("Contact", str(message["contact_id"])) if message else None

        body_html, body_text = self._build_email(
            new_escalation,
            contact,
            message,
            second_tier_backup,
            deadline,
            original.get("ai_summary", "Escalated"),
            f"[ESCALATED from tier-1] {original.get('routing_reason', '')}",
            None,
            org_name,
        )

        _escalation_email_data = EscalationEmailData(
            escalation_id=new_escalation["id"],
            contact_name=contact["name"] if contact else "Unknown",
            contact_channel=message.get("channel", "unknown") if message else "unknown",
            received_at=_format_datetime(message.get("received_at", now)) if message else str(now),
            ai_attempted=original.get("routing_reason", ""),
            confidence_score=0.0,
            confidence_category="escalated",
            original_message_body=message.get("body_text", "") if message else "",
            escalation_deadline=_format_datetime(deadline),
            backup_name=second_tier_backup["name"],
            suggested_response=None,
            org_name=org_name,
            one_line_summary=original.get("ai_summary", "Escalated"),
        )
        subject = _sanitize_header(
            f"[ESCALATED] {build_escalation_subject(_escalation_email_data)}"
        )

        try:
            await self._email_sender.send_escalation_email(
                to=second_tier_backup["email"],
                escalation_id=new_escalation["id"],
                subject=subject,
                body_html=body_html,
                body_text=body_text,
            )
        except Exception as e:
            logger.warning(
                "escalation.second_tier_email_failed_notification_pending",
                escalation_id=new_escalation["id"],
                to=_mask_email(second_tier_backup["email"]),
                error=str(e),
            )
            await self._db.update(
                "Escalation",
                new_escalation["id"],
                {"status": EscalationStatus.notification_pending.value},
            )
            new_escalation["status"] = EscalationStatus.notification_pending.value

        return new_escalation

    async def resolve_escalation(
        self,
        escalation_id: uuid.UUID,
        resolution_summary: str,
    ) -> dict[str, Any]:
        """Mark an escalation as resolved.

        Sets status=resolved and resolved_at=now.
        """
        existing = await self._db.read("Escalation", str(escalation_id))
        if existing is None:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")
        now = datetime.now(timezone.utc)
        updated = await self._db.update(
            "Escalation",
            str(escalation_id),
            {
                "status": EscalationStatus.resolved.value,
                "resolved_at": now,
                "resolution_summary": resolution_summary,
            },
        )

        # Write audit trail
        await self._write_audit(
            tenant_id=uuid.UUID(existing["tenant_id"]),
            action="escalation.resolved",
            doer_type="backup_contact",
            doer_id=uuid.UUID(existing["backup_contact_id"]),
            recipient_type="contact",
            recipient_id=uuid.UUID(existing.get("message_id", str(escalation_id))),
            message_id=uuid.UUID(existing["message_id"]) if existing.get("message_id") else None,
            metadata={"resolution_summary": resolution_summary[:200]},
        )

        logger.info(
            "escalation.resolved",
            escalation_id=str(escalation_id),
            resolution_summary=resolution_summary,
        )
        return updated

    async def acknowledge_escalation(
        self,
        escalation_id: uuid.UUID,
    ) -> dict[str, Any]:
        """Mark an escalation as acknowledged (backup opened/viewed it).

        Sets status=acknowledged and acknowledged_at=now.

        Raises:
            EscalationNotFoundError: if the escalation does not exist.
        """
        existing = await self._db.read("Escalation", str(escalation_id))
        if existing is None:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")
        now = datetime.now(timezone.utc)
        updated = await self._db.update(
            "Escalation",
            str(escalation_id),
            {
                "status": EscalationStatus.acknowledged.value,
                "acknowledged_at": now,
            },
        )
        logger.info("escalation.acknowledged", escalation_id=str(escalation_id))
        return updated

    async def find_breached_escalations(
        self,
        tenant_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Find all pending escalations past their SLA deadline.

        Fetches BackupContacts and Accounts in bulk to avoid N+2 queries.
        Returns the list of breached escalations.

        Used by the scheduler to trigger reminders and second-tier escalation.
        """
        pending = await self._db.list(
            "Escalation",
            {"tenant_id": str(tenant_id), "status": EscalationStatus.pending.value},
        )

        if not pending:
            return []

        backup_ids = list({esc["backup_contact_id"] for esc in pending})
        backup_map: dict[str, dict] = {}
        for bid in backup_ids:
            b = await self._db.read("BackupContact", str(bid))
            if b:
                backup_map[str(bid)] = b

        account_ids = list({b["account_id"] for b in backup_map.values() if b.get("account_id")})
        account_map: dict[str, dict] = {}
        for aid in account_ids:
            a = await self._db.read("Account", str(aid))
            if a:
                account_map[str(aid)] = a

        breached = []
        now = datetime.now(timezone.utc)
        for esc in pending:
            backup = backup_map.get(str(esc["backup_contact_id"]))
            account_id = backup.get("account_id") if backup else None
            sla_hours = self._default_sla
            if account_id:
                account = account_map.get(str(account_id))
                if account:
                    sla_hours = account.get("escalation_sla_hours", self._default_sla)

            deadline = calculate_deadline(esc["assigned_at"], sla_hours)
            if is_breached(deadline, now):
                breached.append(esc)

        if breached:
            logger.warning(
                "escalation.breached_found",
                count=len(breached),
                tenant_id=str(tenant_id),
            )

        return breached

    async def process_breached_escalation(
        self,
        escalation: dict[str, Any],
    ) -> dict[str, Any]:
        """Process a single breached escalation.

        For tier-1: escalate to second tier, send reminder, mark expired.
        For tier-2: mark expired (end of chain).
        Skips if no longer pending (race condition guard).

        Status is set to expired BEFORE side effects (emails, tier-2
        escalation) to narrow the TOCTOU window — another worker or
        scheduler tick that reads the escalation after the update will
        see expired and skip it.
        """
        escalation_id = escalation["id"]
        tier = escalation.get("tier", 1)

        current = await self._db.read("Escalation", str(escalation_id))
        if current is None or current.get("status") != EscalationStatus.pending.value:
            logger.info(
                "escalation.breach_skipped",
                escalation_id=escalation_id,
                reason="not pending",
            )
            return {"escalation_id": escalation_id, "status": "skipped"}

        now = datetime.now(timezone.utc)
        summary = f"SLA breached at tier {tier}. " + (
            "Escalated to tier 2." if tier == 1 else "No further escalation available."
        )
        updated = await self._db.update(
            "Escalation",
            str(escalation_id),
            {
                "status": EscalationStatus.expired.value,
                "resolved_at": now,
                "resolution_summary": summary,
            },
        )

        # Guard against TOCTOU race: if another worker already changed the status,
        # the update may have overwritten it. Verify the update was legitimate.
        if updated is None:
            logger.info(
                "escalation.breach_skipped",
                escalation_id=escalation_id,
                reason="update returned None",
            )
            return {"escalation_id": escalation_id, "status": "skipped"}

        # Re-read to confirm no concurrent modification
        verify = await self._db.read("Escalation", str(escalation_id))
        if verify and verify.get("resolution_summary") != summary:
            logger.warning(
                "escalation.concurrent_modification",
                escalation_id=escalation_id,
            )
            return {"escalation_id": escalation_id, "status": "skipped"}

        result: dict[str, Any] = {
            "escalation_id": escalation_id,
            "new_status": EscalationStatus.expired.value,
            "tier_2_id": None,
        }

        if tier == 1:
            try:
                tier2 = await self.escalate_to_second_tier(uuid.UUID(escalation_id))
                result["tier_2_id"] = tier2["id"]
            except BackupNotFoundError:
                logger.warning(
                    "escalation.no_second_tier",
                    escalation_id=escalation_id,
                )

            try:
                backup = await self._db.read("BackupContact", str(escalation["backup_contact_id"]))
                if backup and backup.get("email"):
                    short_id = escalation_id[:8]
                    await self._email_sender.send_escalation_email(
                        to=backup["email"],
                        escalation_id=escalation_id,
                        subject=_sanitize_header(
                            f"[SLA BREACHED] Escalation {short_id} requires attention"
                        ),
                        body_html=(
                            "<p>The escalation for message "
                            f"{escalation.get('message_id', 'unknown')[:8]} "
                            "has not been acknowledged within the SLA window "
                            "and has been escalated.</p>"
                        ),
                        body_text=(
                            "The escalation for message "
                            f"{escalation.get('message_id', 'unknown')[:8]} "
                            "has not been acknowledged within the SLA window "
                            "and has been escalated."
                        ),
                    )
            except Exception:
                logger.exception(
                    "escalation.reminder_failed",
                    escalation_id=escalation_id,
                )

        logger.info(
            "escalation.processed_breach",
            escalation_id=escalation_id,
            tier=tier,
            new_status=EscalationStatus.expired.value,
        )
        return result

    async def check_contradiction(
        self,
        escalation_id: uuid.UUID,
        proposed_reply_summary: str,
    ) -> bool:
        """Return True if an AI auto-reply already addressed this escalation.

        Checks for any Response linked to this escalation's message that was
        auto-sent (was_auto_sent=True). If one exists, a human reply may
        contradict the AI's prior answer.
        """
        escalation = await self._db.read("Escalation", str(escalation_id))
        if escalation is None:
            raise EscalationNotFoundError(f"Escalation {escalation_id} not found")

        responses = await self._db.list(
            "Response",
            {"message_id": str(escalation["message_id"]), "was_auto_sent": True},
        )
        has_ai_reply = len(responses) > 0
        if has_ai_reply:
            logger.warning(
                "escalation.contradiction_detected",
                escalation_id=str(escalation_id),
                proposed_reply_summary=proposed_reply_summary,
                ai_response_count=len(responses),
            )
        return has_ai_reply

    # -------------------------------------------------------------------------
    # Internal helpers
    # -------------------------------------------------------------------------

    async def _get_primary_backup(
        self,
        account_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """Find the active primary backup contact for an account."""
        backups = await self._db.list(
            "BackupContact",
            {
                "account_id": str(account_id),
                "tier": ContactTier.primary.value,
                "active": True,
            },
        )
        return backups[0] if backups else None

    async def _get_second_tier_backup(
        self,
        account_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """Find the active second-tier backup contact for an account."""
        backups = await self._db.list(
            "BackupContact",
            {
                "account_id": str(account_id),
                "tier": ContactTier.second_tier.value,
                "active": True,
            },
        )
        return backups[0] if backups else None

    def _build_email(
        self,
        escalation: dict[str, Any],
        contact: dict[str, Any] | None,
        message: dict[str, Any] | None,
        backup: dict[str, Any],
        deadline: datetime,
        ai_summary: str,
        routing_reason: str,
        suggested_response: str | None,
        org_name: str,
    ) -> tuple[str, str]:
        """Build escalation email HTML and plain text bodies."""
        now = datetime.now(timezone.utc)
        data = EscalationEmailData(
            escalation_id=escalation["id"],
            contact_name=contact["name"] if contact else "Unknown",
            contact_channel=message.get("channel", "unknown") if message else "unknown",
            received_at=_format_datetime(message.get("received_at", now)) if message else str(now),
            ai_attempted=routing_reason,
            confidence_score=0.0,
            confidence_category="escalated",
            original_message_body=message.get("body_text", "") if message else "",
            escalation_deadline=_format_datetime(deadline),
            backup_name=backup["name"],
            suggested_response=suggested_response,
            org_name=org_name,
            one_line_summary=ai_summary,
        )
        return build_escalation_email(data)

    async def _write_audit(
        self,
        tenant_id: uuid.UUID,
        action: str,
        doer_type: str,
        doer_id: uuid.UUID,
        recipient_type: str,
        recipient_id: uuid.UUID,
        message_id: uuid.UUID | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Write an audit entry for this escalation's tenant."""
        session = getattr(self._db, "_session_inner", None) or getattr(self._db, "_session", None)
        if session is None:
            logger.error("escalation.audit_no_session", action=action)
            return

        from sequor.db.audit import audit as write_audit

        await write_audit(
            session,
            tenant_id=tenant_id,
            action=action,
            doer_type=doer_type,
            doer_id=doer_id,
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            message_id=message_id,
            metadata=metadata,
        )


def _format_datetime(dt: datetime) -> str:
    """Format a datetime for email display (ISO-8601, UTC)."""
    if dt is None:
        return "Unknown"
    if isinstance(dt, str):
        return dt
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.strftime("%Y-%m-%d %H:%M UTC")
