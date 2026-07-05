"""DigestService — queries 24h stats and sends daily digest emails."""

from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

import structlog
from sqlalchemy import select

from sequor.db.models import (
    Account,
    Escalation,
    EscalationStatus,
    LearnedAnswer,
    Response,
)
from sequor.email.templates import DigestEmailData, build_digest_email, build_digest_subject
from sequor.protocols import EmailSender

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession

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
        # Bind before any encrypted-column read (Account.owner_email/email_address
        # are EncryptedString; Escalation.resolution_summary / Response.content /
        # LearnedAnswer.*_text are encrypted under the tenant key). No-op without
        # ENCRYPTION_MASTER_KEY (dev fail-open).
        await self._db.bind_tenant(tenant_id)

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
                result = await self.send_digest(tenant_id, uuid.UUID(str(account["id"])))
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
                tenant_results = await self.send_all_accounts(uuid.UUID(str(tenant["id"])))
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

        recent_learned = [la for la in learned if _after_cutoff(la.get("created_at"), cutoff)]
        recent_learned_topics = [
            la["question_text"][:80] for la in recent_learned if la.get("question_text")
        ][:10]

        auto_responses = [
            r
            for r in responses
            if r.get("was_auto_sent") and _after_cutoff(r.get("sent_at"), cutoff)
        ]

        rag_responses = [r for r in auto_responses if r.get("rag_retrieval_id") is not None]

        recent_esc = [e for e in escalations if _after_cutoff(e.get("assigned_at"), cutoff)]

        pending_esc = [e for e in escalations if e.get("status") == EscalationStatus.pending.value]

        breached_esc = [
            e
            for e in escalations
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
            rag_resolved_count=len(rag_responses),
            learned_answers_count=len(recent_learned),
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


async def gather_digest_data(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    hours: int = 24,
) -> dict[str, Any]:
    """Assemble coverage-digest stats for one account over the past ``hours``.

    Session-based API (real ``AsyncSession``) used by the digest email path and
    the integration suite. Escalations and Responses are tenant-scoped (a
    Message carries no account FK); LearnedAnswers are tenant+account scoped.
    The SLA breach threshold is the account's ``escalation_sla_hours``.
    """
    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(hours=hours)

    # Bind the session to the tenant so Escalation.resolution_summary,
    # Response.content and LearnedAnswer.*_text (all EncryptedString) decrypt on
    # the reads below. No-op without ENCRYPTION_MASTER_KEY (dev fail-open).
    from sequor.db.tenant_context import bind_tenant

    await bind_tenant(session, tenant_id)

    # Select ONLY the non-encrypted columns we need. Loading the full Account
    # row would decrypt owner_email/email_address (EncryptedString) during
    # result processing, which fail-closes with RuntimeError in production when
    # no per-tenant key is set for this session (see encrypted_column.py).
    account_row = (
        await session.execute(
            select(Account.name, Account.escalation_sla_hours).where(Account.id == account_id)
        )
    ).first()
    account_name = account_row.name if account_row is not None else "your account"
    sla_hours = account_row.escalation_sla_hours if account_row is not None else 4

    escalations = (
        (await session.execute(select(Escalation).where(Escalation.tenant_id == tenant_id)))
        .scalars()
        .all()
    )

    pending = [e for e in escalations if e.status == EscalationStatus.pending]
    recent_esc = [e for e in escalations if _after_cutoff(e.assigned_at, cutoff)]
    sla_delta = timedelta(hours=sla_hours)
    breached = [
        e
        for e in pending
        if e.assigned_at is not None and (now - _ensure_aware(e.assigned_at)) > sla_delta
    ]

    oldest_unresolved_hours: float | None = None
    if pending:
        ages = [
            (now - _ensure_aware(e.assigned_at)).total_seconds() / 3600
            for e in pending
            if e.assigned_at is not None
        ]
        if ages:
            oldest_unresolved_hours = max(ages)

    responses = (
        (await session.execute(select(Response).where(Response.tenant_id == tenant_id)))
        .scalars()
        .all()
    )
    auto = [r for r in responses if r.was_auto_sent and _after_cutoff(r.sent_at, cutoff)]
    resolved_by_rag = [r for r in auto if r.rag_retrieval_id is not None]
    resolved_by_learned = [r for r in auto if r.rag_retrieval_id is None]

    learned = (
        (
            await session.execute(
                select(LearnedAnswer).where(
                    LearnedAnswer.tenant_id == tenant_id,
                    LearnedAnswer.account_id == account_id,
                )
            )
        )
        .scalars()
        .all()
    )
    recent_learned = [la for la in learned if _after_cutoff(la.created_at, cutoff)]
    learned_topics = [la.question_text[:80] for la in recent_learned if la.question_text][:10]

    return {
        "account_name": account_name,
        "pending": len(pending),
        "escalated": len(recent_esc),
        "breached_sla": len(breached),
        "oldest_unresolved_hours": oldest_unresolved_hours,
        "auto_resolved": len(auto),
        "resolved_by_rag": len(resolved_by_rag),
        "resolved_by_learned": len(resolved_by_learned),
        "learned_count": len(recent_learned),
        "learned_topics": learned_topics,
    }


async def send_digest(
    session: AsyncSession,
    email_sender: EmailSender,
    tenant_id: uuid.UUID,
    account_id: uuid.UUID,
    hours: int = 24,
) -> dict[str, Any] | None:
    """Gather digest stats for an account, render the email, send it to the
    account's active primary backup. Returns a summary dict, or ``None`` when
    the account has no primary backup to receive the digest.
    """
    from sequor.db.models import BackupContact, ContactTier

    data = await gather_digest_data(session, tenant_id, account_id, hours=hours)
    subject, body = format_digest_email(data)

    backups = (
        (
            await session.execute(
                select(BackupContact).where(
                    BackupContact.account_id == account_id,
                    BackupContact.tier == ContactTier.primary,
                    BackupContact.active.is_(True),
                )
            )
        )
        .scalars()
        .all()
    )
    if not backups:
        logger.warning("digest.no_backup", account_id=str(account_id))
        return None

    recipient = backups[0]
    await email_sender.send_email(
        to=recipient.email,
        subject=subject,
        body_html=body,
        body_text=body,
    )
    logger.info(
        "digest.sent",
        tenant_id=str(tenant_id),
        account_id=str(account_id),
        to=recipient.email,
    )
    return {"account_id": str(account_id), "sent_to": recipient.email}


def format_digest_email(data: dict[str, Any]) -> tuple[str, str]:
    """Render ``gather_digest_data`` output into a ``(subject, body)`` pair.

    Subject uses the account name (not the org name). When any escalation has
    breached its SLA the body carries a ``Breached SLA:`` call-to-action line.
    """
    account_name = data.get("account_name", "your account")
    subject = f"[COVERAGE DIGEST] {account_name}"

    lines = [
        f"Coverage digest for {account_name}",
        "",
        (
            f"AI auto-resolved: {data['auto_resolved']} "
            f"({data['resolved_by_rag']} via knowledge base, "
            f"{data['resolved_by_learned']} via learned answers)"
        ),
        f"New knowledge learned: {data['learned_count']}",
        f"Pending escalations: {data['pending']}",
        f"Escalated in period: {data['escalated']}",
    ]

    if data.get("breached_sla", 0) > 0:
        lines.append(f"Breached SLA: {data['breached_sla']} item(s) need attention")

    oldest = data.get("oldest_unresolved_hours")
    if oldest:
        lines.append(f"Oldest unresolved: {oldest:.1f}h")

    topics = data.get("learned_topics") or []
    if topics:
        lines.append("")
        lines.append("New topics learned:")
        lines.extend(f"  - {t}" for t in topics)

    return subject, "\n".join(lines)
