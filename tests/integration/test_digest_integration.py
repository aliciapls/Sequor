"""Integration test for daily digest email generation.

Verifies that digest queries return correct counts from the database.
Requires a running PostgreSQL instance.
"""

import pytest
from datetime import datetime, timedelta, timezone
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.database import close_engine, get_engine, init_db
from sequor.db.models import (
    Account,
    BackupContact,
    Contact,
    Escalation,
    EscalationPriority,
    EscalationStatus,
    LearnedAnswer,
    Message,
    RAGRetrieval,
    Response,
    SourceType,
    Tenant,
)
from sequor.digest.service import gather_digest_data, send_digest


def _uuid():
    return uuid4()


def _now():
    return datetime.now(timezone.utc)


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
    await close_engine()


async def _seed_account(session: AsyncSession, domain: str = "digesttest.com"):
    """Create a tenant + account + backup contact for testing."""
    tenant = Tenant(
        name="Digest Test Corp",
        email_domain=domain,
        plan="starter",
        settings={},
    )
    session.add(tenant)
    await session.flush()

    account = Account(
        tenant_id=tenant.id,
        name="Test Account",
        ownership_type="individual",
        owner_email=f"owner@{domain}",
        channels=["email"],
        email_address=f"owner@{domain}",
        routing_rules={},
        escalation_sla_hours=4,
    )
    session.add(account)
    await session.flush()

    backup = BackupContact(
        tenant_id=tenant.id,
        account_id=account.id,
        name="Backup Person",
        email=f"backup@{domain}",
        tier="primary",
        active=True,
    )
    session.add(backup)
    await session.flush()

    account.backup_contact_ids = [backup.id]
    session.add(account)

    # Capture IDs before commit to avoid async lazy-load issues
    tenant_id = tenant.id
    account_id = account.id
    backup_id = backup.id

    await session.commit()

    # Return simple namespace to avoid detached instance access
    class Result:
        pass
    r = Result()
    r.tenant_id = tenant_id
    r.id = tenant_id  # for gather_digest_data compatibility
    r.account_id = account_id
    r.backup_id = backup_id
    return r, account_id, backup_id


async def _seed_contact(session: AsyncSession, tenant_id, email: str = "client@example.com"):
    """Create a Contact record for FK references in Message."""
    contact = Contact(
        tenant_id=tenant_id,
        email=email,
        name="Test Client",
    )
    session.add(contact)
    await session.flush()
    contact_id = contact.id
    await session.commit()
    return contact_id


@pytest.mark.asyncio
async def test_digest_counts_auto_resolved_rag(db_session):
    tenant, account_id, backup_id = await _seed_account(db_session, "ragtest.com")
    contact_id = await _seed_contact(db_session, tenant.id, "client@ragtest.com")

    msg = Message(
        tenant_id=tenant.id,
        contact_id=contact_id,
        direction="inbound",
        channel="email",
        received_at=_now() - timedelta(hours=1),
    )
    db_session.add(msg)
    await db_session.flush()

    # Create a real RAG retrieval row to satisfy FK
    rag = RAGRetrieval(
        tenant_id=tenant.id,
        message_id=msg.id,
        retrieval_confidence=0.90,
    )
    db_session.add(rag)
    await db_session.flush()

    resp = Response(
        tenant_id=tenant.id,
        message_id=msg.id,
        content="Here is the answer from our docs.",
        confidence_badge="high",
        confidence_score=0.92,
        was_auto_sent=True,
        sent_at=_now() - timedelta(minutes=30),
        rag_retrieval_id=rag.id,
    )
    db_session.add(resp)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant.id, account_id, hours=24)

    assert data["auto_resolved"] == 1
    assert data["resolved_by_rag"] == 1
    assert data["resolved_by_learned"] == 0


@pytest.mark.asyncio
async def test_digest_counts_learned_answers(db_session):
    tenant, account_id, _ = await _seed_account(db_session, "learnedtest.com")

    learned = LearnedAnswer(
        tenant_id=tenant.id,
        account_id=account_id,
        question_text="What are the shipping timelines?",
        answer_text="We ship within 2-3 business days.",
        source_type=SourceType.human_answer,
    )
    db_session.add(learned)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant.id, account_id, hours=24)

    assert data["learned_count"] == 1
    assert "shipping timelines" in data["learned_topics"][0].lower()


@pytest.mark.asyncio
async def test_digest_counts_pending_escalations(db_session):
    tenant, account_id, backup_id = await _seed_account(db_session, "esctest.com")
    contact_id = await _seed_contact(db_session, tenant.id, "client@esctest.com")

    msg = Message(
        tenant_id=tenant.id,
        contact_id=contact_id,
        direction="inbound",
        channel="email",
        received_at=_now() - timedelta(hours=5),
    )
    db_session.add(msg)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant.id,
        message_id=msg.id,
        backup_contact_id=backup_id,
        tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=_now() - timedelta(hours=5),
    )
    db_session.add(esc)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant.id, account_id, hours=24)

    assert data["pending"] >= 1
    assert data["escalated"] >= 1
    assert data["oldest_unresolved_hours"] is not None


@pytest.mark.asyncio
async def test_digest_counts_breached_sla(db_session):
    tenant, account_id, backup_id = await _seed_account(db_session, "slatest.com")
    contact_id = await _seed_contact(db_session, tenant.id, "client@slatest.com")

    msg = Message(
        tenant_id=tenant.id,
        contact_id=contact_id,
        direction="inbound",
        channel="email",
        received_at=_now() - timedelta(hours=10),
    )
    db_session.add(msg)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant.id,
        message_id=msg.id,
        backup_contact_id=backup_id,
        tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=_now() - timedelta(hours=8),
    )
    db_session.add(esc)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant.id, account_id, hours=24)

    assert data["breached_sla"] == 1


@pytest.mark.asyncio
async def test_digest_empty_database(db_session):
    tenant, account_id, _ = await _seed_account(db_session, "emptytest.com")

    data = await gather_digest_data(db_session, tenant.id, account_id, hours=24)

    assert data["auto_resolved"] == 0
    assert data["pending"] == 0
    assert data["escalated"] == 0
    assert data["breached_sla"] == 0
    assert data["learned_count"] == 0
    assert data["learned_topics"] == []
