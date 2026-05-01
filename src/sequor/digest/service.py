"""Daily digest service — generates and sends coverage summary emails.

Queries messages, responses, escalations, and learned answers from the
past 24 hours, formats a digest email per the spec template, and sends
it to the account owner.
"""

import structlog
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import (
    Account,
    Escalation,
    EscalationStatus,
    LearnedAnswer,
    Response,
    SourceType,
)

logger = structlog.get_logger()


def format_digest_email(data: dict) -> tuple[str, str]:
    """Format digest data into subject + body per the spec template.

    Returns (subject, body_text).
    """
    subject = f"[COVERAGE DIGEST] {data['date']} — {data['account_name']}"

    lines = [
        f"AI handled automatically: {data['auto_resolved']} messages",
        f" - Resolved by RAG: {data['resolved_by_rag']}",
        f" - Resolved by learned answers: {data['resolved_by_learned']}",
        "",
        f"Pending your response: {data['pending']} items",
    ]

    if data["oldest_unresolved_hours"] is not None:
        lines.append(f" - Oldest unresolved: {data['oldest_unresolved_hours']:.1f} hours ago")

    lines.extend([
        "",
        f"Escalated to backup: {data['escalated']} items",
        f" - Breached SLA: {data['breached_sla']} (need attention)",
        "",
        f"New knowledge learned: {data['learned_count']} answers added to knowledge base",
    ])

    for topic in data.get("learned_topics", []):
        lines.append(f'  - "{topic}"')

    return subject, "\n".join(lines)


def compute_breached_count(
    escalations: list[dict],
    sla_hours: int,
    now: datetime,
) -> int:
    """Count escalations past their SLA deadline that are not resolved."""
    breached = 0
    for esc in escalations:
        if esc["status"] == "resolved":
            continue
        deadline = esc["assigned_at"] + timedelta(hours=sla_hours)
        if now > deadline:
            breached += 1
    return breached


async def gather_digest_data(
    session: AsyncSession,
    tenant_id: UUID,
    account_id: UUID,
    hours: int = 24,
) -> dict:
    """Query database for digest data covering the past `hours`.

    Returns a dict with all fields needed by format_digest_email.
    """
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    # 1. Auto-resolved responses (AI sent automatically)
    auto_rag_q = (
        select(func.count())
        .select_from(Response)
        .where(
            Response.tenant_id == tenant_id,
            Response.was_auto_sent.is_(True),
            Response.sent_at >= cutoff,
            Response.rag_retrieval_id.isnot(None),
        )
    )
    resolved_by_rag = (await session.execute(auto_rag_q)).scalar() or 0

    auto_learned_q = (
        select(func.count())
        .select_from(Response)
        .where(
            Response.tenant_id == tenant_id,
            Response.was_auto_sent.is_(True),
            Response.sent_at >= cutoff,
            Response.rag_retrieval_id.is_(None),
        )
    )
    resolved_by_learned = (await session.execute(auto_learned_q)).scalar() or 0

    auto_resolved = resolved_by_rag + resolved_by_learned

    # 2. Pending escalations (not yet resolved)
    pending_q = (
        select(func.count())
        .select_from(Escalation)
        .where(
            Escalation.tenant_id == tenant_id,
            Escalation.status == EscalationStatus.pending,
            Escalation.assigned_at >= cutoff,
        )
    )
    pending = (await session.execute(pending_q)).scalar() or 0

    # Oldest pending escalation
    oldest_q = (
        select(func.min(Escalation.assigned_at))
        .where(
            Escalation.tenant_id == tenant_id,
            Escalation.status == EscalationStatus.pending,
        )
    )
    oldest_assigned = (await session.execute(oldest_q)).scalar()
    now = datetime.now(timezone.utc)
    oldest_hours = None
    if oldest_assigned is not None:
        delta = now - oldest_assigned
        oldest_hours = round(delta.total_seconds() / 3600, 1)

    # 3. All unresolved escalations (for SLA breach check)
    unresolved_q = (
        select(Escalation.assigned_at, Escalation.status)
        .where(
            Escalation.tenant_id == tenant_id,
            Escalation.assigned_at >= cutoff,
            Escalation.status.in_([
                EscalationStatus.pending,
                EscalationStatus.acknowledged,
                EscalationStatus.expired,
            ]),
        )
    )
    unresolved_rows = (await session.execute(unresolved_q)).all()
    escalated = len(unresolved_rows)

    # Get SLA hours from account
    account = await session.get(Account, account_id)
    sla_hours = account.escalation_sla_hours if account else 4

    unresolved_dicts = [
        {"assigned_at": row.assigned_at, "status": row.status.value}
        for row in unresolved_rows
    ]
    breached_sla = compute_breached_count(unresolved_dicts, sla_hours, now)

    # 4. New learned answers
    learned_q = (
        select(func.count())
        .select_from(LearnedAnswer)
        .where(
            LearnedAnswer.tenant_id == tenant_id,
            LearnedAnswer.source_type == SourceType.human_answer,
            LearnedAnswer.created_at >= cutoff,
        )
    )
    learned_count = (await session.execute(learned_q)).scalar() or 0

    # Get topic list (up to 10)
    topics_q = (
        select(LearnedAnswer.question_text)
        .where(
            LearnedAnswer.tenant_id == tenant_id,
            LearnedAnswer.source_type == SourceType.human_answer,
            LearnedAnswer.created_at >= cutoff,
        )
        .order_by(LearnedAnswer.created_at.desc())
        .limit(10)
    )
    learned_topics = [
        row.question_text for row in (await session.execute(topics_q)).all()
    ]

    return {
        "date": now.strftime("%-d %B %Y"),
        "account_name": account.name if account else "Unknown",
        "auto_resolved": auto_resolved,
        "resolved_by_rag": resolved_by_rag,
        "resolved_by_learned": resolved_by_learned,
        "pending": pending,
        "oldest_unresolved_hours": oldest_hours,
        "escalated": escalated,
        "breached_sla": breached_sla,
        "learned_count": learned_count,
        "learned_topics": learned_topics,
    }


async def send_digest(
    session: AsyncSession,
    tenant_id: UUID,
    account_id: UUID,
    hours: int = 24,
) -> None:
    """Generate and send the daily digest email to the account owner."""
    data = await gather_digest_data(session, tenant_id, account_id, hours)
    subject, body = format_digest_email(data)

    account = await session.get(Account, account_id)
    if not account:
        logger.warning("digest.skip", reason="account not found", account_id=str(account_id))
        return

    # Use SendGrid if configured, otherwise log
    from sequor.config import settings

    if settings.sendgrid_api_key:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        message = Mail(
            from_email=Email(f"noreply@{settings.email_from_domain}", "Sequor"),
            to_emails=account.owner_email,
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )
        try:
            sg.client.mail.send.post(request_body=message.get())
            logger.info("digest.sent", to=account.owner_email, tenant_id=str(tenant_id))
        except Exception as e:
            logger.warning("digest.send_failed", to=account.owner_email, error=str(e))
    else:
        logger.info(
            "digest.skipped",
            to=account.owner_email,
            reason="no sendgrid_api_key configured",
            subject=subject,
        )


async def send_all_digests(hours: int = 24) -> int:
    """Send digest emails for all active accounts.

    Returns the number of digests sent.
    """
    from sequor.db.database import get_engine

    engine = get_engine()
    count = 0

    async with AsyncSession(engine) as session:
        accounts_q = select(Account).where(Account.status == "active")
        accounts = (await session.execute(accounts_q)).scalars().all()

        for account in accounts:
            try:
                await send_digest(session, account.tenant_id, account.id, hours)
                count += 1
            except Exception as e:
                logger.warning(
                    "digest.account_failed",
                    account_id=str(account.id),
                    error=str(e),
                )

    return count
