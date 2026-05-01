"""E2E integration test — escalation chain (TODO-23).

Tests escalation timing, multi-tier routing, SLA breach detection,
and breach appearance in daily digest.
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
    Message,
    Tenant,
)
from sequor.digest.service import gather_digest_data


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
    await close_engine()


async def _setup_escalation_test(session: AsyncSession, sla_hours: int = 1):
    """Create tenant, account, contacts for escalation testing."""
    import uuid
    domain = f"esc-{uuid.uuid4().hex[:8]}.test"

    tenant = Tenant(name="Esc Test", email_domain=domain, plan="starter", settings={})
    session.add(tenant)
    await session.flush()
    tenant_id = tenant.id

    account = Account(
        tenant_id=tenant_id,
        name="Front Desk",
        ownership_type="individual",
        owner_email=f"owner@{domain}",
        channels=["email"],
        email_address=f"owner@{domain}",
        routing_rules={},
        escalation_sla_hours=sla_hours,
    )
    session.add(account)
    await session.flush()
    account_id = account.id

    primary = BackupContact(
        tenant_id=tenant_id, account_id=account_id,
        name="Primary Backup", email=f"primary@{domain}", tier="primary", active=True,
    )
    secondary = BackupContact(
        tenant_id=tenant_id, account_id=account_id,
        name="Secondary Backup", email=f"secondary@{domain}", tier="second_tier", active=True,
    )
    session.add_all([primary, secondary])
    await session.flush()

    contact = Contact(tenant_id=tenant_id, email="client@external.com", name="Client")
    session.add(contact)
    await session.flush()

    account.backup_contact_ids = [primary.id, secondary.id]
    session.add(account)

    tid = tenant_id
    aid = account_id
    pid = primary.id
    sid = secondary.id
    cid = contact.id
    await session.commit()

    return tid, aid, pid, sid, cid


@pytest.mark.asyncio
async def test_escalation_to_primary_backup(db_session):
    """Low-confidence query triggers escalation to primary backup."""
    tenant_id, account_id, primary_id, _, contact_id = await _setup_escalation_test(db_session)

    msg = Message(
        tenant_id=tenant_id, contact_id=contact_id,
        direction="inbound", channel="email",
        body_text="Complex legal question about contract terms",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(msg)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant_id, message_id=msg.id,
        backup_contact_id=primary_id, tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=datetime.now(timezone.utc),
    )
    db_session.add(esc)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant_id, account_id, hours=24)
    assert data["pending"] >= 1
    assert data["escalated"] >= 1


@pytest.mark.asyncio
async def test_sla_breach_detection(db_session):
    """Escalation past SLA deadline is flagged as breached."""
    tenant_id, account_id, primary_id, _, contact_id = await _setup_escalation_test(db_session, sla_hours=1)

    msg = Message(
        tenant_id=tenant_id, contact_id=contact_id,
        direction="inbound", channel="email",
        received_at=datetime.now(timezone.utc) - timedelta(hours=3),
    )
    db_session.add(msg)
    await db_session.flush()

    # Assigned 3 hours ago, 1-hour SLA = breached
    esc = Escalation(
        tenant_id=tenant_id, message_id=msg.id,
        backup_contact_id=primary_id, tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=3),
    )
    db_session.add(esc)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant_id, account_id, hours=24)
    assert data["breached_sla"] >= 1


@pytest.mark.asyncio
async def test_second_tier_escalation(db_session):
    """When primary doesn't respond, escalation goes to secondary."""
    tenant_id, account_id, primary_id, secondary_id, contact_id = await _setup_escalation_test(db_session)

    msg = Message(
        tenant_id=tenant_id, contact_id=contact_id,
        direction="inbound", channel="email",
        body_text="Urgent matter requiring attention",
        received_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )
    db_session.add(msg)
    await db_session.flush()

    # Tier 1 escalation (primary)
    esc1 = Escalation(
        tenant_id=tenant_id, message_id=msg.id,
        backup_contact_id=primary_id, tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.critical,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=5),
    )
    db_session.add(esc1)

    # Tier 2 escalation (secondary) after SLA expired
    esc2 = Escalation(
        tenant_id=tenant_id, message_id=msg.id,
        backup_contact_id=secondary_id, tier=2,
        status=EscalationStatus.pending,
        priority=EscalationPriority.critical,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=1),
    )
    db_session.add(esc2)
    await db_session.commit()

    data = await gather_digest_data(db_session, tenant_id, account_id, hours=24)
    assert data["escalated"] >= 2
    assert data["breached_sla"] >= 1  # Tier 1 past SLA


@pytest.mark.asyncio
async def test_breached_items_appear_in_digest(db_session):
    """Breached escalations are visible in the formatted digest."""
    tenant_id, account_id, primary_id, _, contact_id = await _setup_escalation_test(db_session, sla_hours=1)

    msg = Message(
        tenant_id=tenant_id, contact_id=contact_id,
        direction="inbound", channel="email",
        received_at=datetime.now(timezone.utc) - timedelta(hours=4),
    )
    db_session.add(msg)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant_id, message_id=msg.id,
        backup_contact_id=primary_id, tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=4),
    )
    db_session.add(esc)
    await db_session.commit()

    from sequor.digest.service import format_digest_email
    data = await gather_digest_data(db_session, tenant_id, account_id, hours=24)
    _, body = format_digest_email(data)

    assert data["breached_sla"] >= 1
    assert "Breached SLA:" in body
    assert "need attention" in body
