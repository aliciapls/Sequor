"""DigestService — queries 24h stats and sends daily digest emails."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any

import structlog

from sequor.db.models import EscalationStatus
from sequor.email.templates import DigestEmailData, build_digest_email, build_digest_subject
from sequor.protocols import EmailSender

logger = structlog.get_logger()


class DigestService:
    """Builds and sends daily digest emails for each account.

    Queries the DB for the past 24h of activity, assembles the
    DigestEmailData, and sends via the injected EmailSender.
    """

    def __init__(
        self,
        db_express: Any,
        email_sender: EmailSender,
        hours: int = 24,
    ) -> None:
        self._db = db_express
        self._email = email_sender
        self._hours = hours

    async def send_digest(
        self,
        tenant_id: uuid.UUID,
        account_id: uuid.UUID,
    ) -> dict[str, Any] | None:
        """Build and send a digest for a single account.

        Returns a summary dict or None if the account has no activity.
        """
        account = await self._db.read("Account", str(account_id))
        if account is None:
            logger.warning("digest.account_not_found", account_id=str(account_id))
            return None

        tenant = await self._db.read("Tenant", str(tenant_id))
        org_name = tenant["name"] if tenant else account.get("name", "your team")

        cutoff = datetime.now(timezone.utc) - timedelta(hours=self._hours)
        now = datetime.now(timezone.utc)

        data = await self._gather_stats(
            tenant_id=str(tenant_id),
            account_id=str(account_id),
            account_name=account["name"],
            org_name=org_name,
            cutoff=cutoff,
            now=now,
        )

        html, text = build_digest_email(data)
        subject = build_digest_subject(data)

        backup = await self._get_primary_backup(account_id)
        if backup is None:
            logger.warning("digest.no_backup", account_id=str(account_id))
            return None

        await self._email.send_email(
            to=backup["email"],
            subject=subject,
            body_html=html,
            body_text=text,
        )

        logger.info(
            "digest.sent",
            tenant_id=str(tenant_id),
            account_id=str(account_id),
            to=backup["email"],
        )
        return {"account_id": str(account_id), "sent_to": backup["email"]}

    async def send_all_accounts(
        self,
        tenant_id: uuid.UUID,
    ) -> list[dict[str, Any]]:
        """Send digest emails for every active account under a tenant."""
        accounts = await self._db.list(
            "Account",
            {"tenant_id": str(tenant_id)},
        )
        results = []
        for account in accounts:
            try:
                result = await self.send_digest(tenant_id, uuid.UUID(account["id"]))
                if result:
                    results.append(result)
            except Exception:
                logger.exception(
                    "digest.account_error",
                    account_id=account.get("id"),
                )
        return results

    async def send_all_tenants(self) -> list[dict[str, Any]]:
        """Send digest emails for every tenant. Entry point for scheduler."""
        tenants = await self._db.list("Tenant", {})
        results = []
        for tenant in tenants:
            try:
                tenant_results = await self.send_all_accounts(
                    uuid.UUID(tenant["id"])
                )
                results.extend(tenant_results)
            except Exception:
                logger.exception(
                    "digest.tenant_error",
                    tenant_id=tenant.get("id"),
                )
        logger.info("digest.complete", tenant_count=len(tenants), digests_sent=len(results))
        return results

    async def _gather_stats(
        self,
        tenant_id: str,
        account_id: str,
        account_name: str,
        org_name: str,
        cutoff: datetime,
        now: datetime,
    ) -> DigestEmailData:
        escalations = await self._db.list(
            "Escalation",
            {"tenant_id": tenant_id},
        )

        responses = await self._db.list(
            "Response",
            {"tenant_id": tenant_id},
        )

        learned = await self._db.list(
            "LearnedAnswer",
            {"tenant_id": tenant_id, "account_id": account_id},
        )

        recent_learned = [
            la for la in learned
            if _after_cutoff(la.get("created_at"), cutoff)
        ]
        recent_learned_topics = [
            la["question_text"][:80]
            for la in recent_learned
            if la.get("question_text")
        ][:10]

        auto_responses = [
            r for r in responses
            if r.get("was_auto_sent") and _after_cutoff(r.get("sent_at"), cutoff)
        ]

        recent_esc = [
            e for e in escalations
            if _after_cutoff(e.get("assigned_at"), cutoff)
        ]

        pending_esc = [
            e for e in escalations
            if e.get("status") == EscalationStatus.pending.value
        ]

        breached_esc = [
            e for e in escalations
            if e.get("status") == EscalationStatus.expired.value
            and _after_cutoff(e.get("resolved_at"), cutoff)
        ]

        oldest_hours: float | None = None
        if pending_esc:
            ages = [
                (now - _ensure_aware(e["assigned_at"])).total_seconds() / 3600
                for e in pending_esc
                if e.get("assigned_at")
            ]
            if ages:
                oldest_hours = max(ages)

        return DigestEmailData(
            account_name=account_name,
            date=now.strftime("%Y-%m-%d"),
            ai_handled_count=len(auto_responses),
            rag_resolved_count=len(auto_responses),
            learned_answers_count=len(auto_responses),
            pending_count=len(pending_esc),
            oldest_unresolved_hours=oldest_hours,
            escalated_count=len(recent_esc),
            breached_count=len(breached_esc),
            new_knowledge_count=len(recent_learned),
            new_knowledge_topics=recent_learned_topics,
            org_name=org_name,
        )

    async def _get_primary_backup(self, account_id: uuid.UUID) -> dict | None:
        from sequor.db.models import ContactTier
        backups = await self._db.list(
            "BackupContact",
            {
                "account_id": str(account_id),
                "tier": ContactTier.primary.value,
                "active": True,
            },
        )
        return backups[0] if backups else None


def _after_cutoff(dt: datetime | None, cutoff: datetime) -> bool:
    if dt is None:
        return False
    return _ensure_aware(dt) >= cutoff


def _ensure_aware(dt: datetime) -> datetime:
    if isinstance(dt, str):
        dt = datetime.fromisoformat(dt)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt
