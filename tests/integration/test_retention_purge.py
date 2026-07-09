"""Tier-2 tests for the PDPA retention-purge job (DEVIATIONS §F2, shard 1d).

Exercises :func:`sequor.db.retention.run_retention_purge_once` against a real
PostgreSQL (pgvector) instance — NO mocking (Tier-2 contract). The job must:

1. Enforce the per-plan retention cutoff (free 7d / starter 90d / professional
   365d / enterprise 730d) on each tenant independently — an old row for one
   plan may be a fresh row for another.
2. Purge ALL three time-bounded tables (Message / AuditEntry / Escalation) in a
   single sweep, leaving within-retention rows untouched.
3. Write one summary ``AuditEntry(action="retention.purge")`` per tenant whose
   purge actually deleted something — the accountability trail data-model.md
   § "Data Retention Schedule" requires ("logging each deletion to the audit
   entry").

Cascade note: ``Escalation.message_id`` is ``ondelete=CASCADE``. To test the
Escalation purge path INDEPENDENTLY of the Message-cascade, the Escalations
reference a fresh anchor Message (within retention, survives purge) while the
Escalations' own ``assigned_at`` is old/new. That isolates "the escalation-row
purge deleted this escalation" from "the message-row purge cascaded it."
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import (
    Account,
    AccountChannel,
    AuditEntry,
    BackupContact,
    ChannelPreference,
    Contact,
    ContactTier,
    Escalation,
    EscalationPriority,
    EscalationStatus,
    Message,
    MessageChannel,
    MessageDirection,
    OwnershipType,
    Tenant,
    TenantPlan,
)
from sequor.db.database import get_engine
from sequor.db.retention import purge_expired_records, run_retention_purge_once
from sequor.db.tenant_context import reset_key_manager, set_tenant_context

# Per-plan retention in days (mirrors RETENTION_DAYS in retention.py).
_RETENTION_DAYS = {
    TenantPlan.free.value: 7,
    TenantPlan.starter.value: 90,
    TenantPlan.professional.value: 365,
    TenantPlan.enterprise.value: 730,
}


async def _seed_tenant(session: AsyncSession, plan: TenantPlan) -> Tenant:
    """Create a Tenant of *plan* + provision its encryption key. Caller commits."""
    reset_key_manager()
    tenant = Tenant(
        name=f"T-{plan.value}",
        email_domain=f"{plan.value}.example.com",
        plan=plan,
        settings={},
    )
    session.add(tenant)
    await session.flush()
    # Provision the tenant AES key BEFORE seeding any encrypted-column row
    # (Contact.name, Account.owner_email, BackupContact.email).
    await set_tenant_context(session, tenant.id, provision=True)
    return tenant


async def _seed_message(
    session: AsyncSession, tenant_id, contact_id, *, days: float, now: datetime
) -> Message:
    """Insert a Message with received_at = now - days. Encrypted body columns are
    left null (the purge filters on received_at + tenant_id, not content)."""
    msg = Message(
        tenant_id=tenant_id,
        contact_id=contact_id,
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        received_at=now - timedelta(days=days),
    )
    session.add(msg)
    await session.flush()
    return msg


async def _seed_audit(
    session: AsyncSession, tenant_id, *, days: float, now: datetime, suffix: str
) -> AuditEntry:
    """Insert an AuditEntry with occurred_at = now - days."""
    import uuid as _uuid

    entry = AuditEntry(
        tenant_id=tenant_id,
        doer_type="system",
        doer_id=_uuid.uuid4(),
        action_type=f"test.{suffix}",
        recipient_type="system",
        recipient_id=_uuid.uuid4(),
        occurred_at=now - timedelta(days=days),
    )
    session.add(entry)
    await session.flush()
    return entry


async def _seed_escalation_chain(
    session: AsyncSession, tenant_id, *, now: datetime
) -> tuple[Message, list[Escalation]]:
    """Seed the FK chain an Escalation needs (Account + BackupContact) plus a
    fresh anchor Message, and return the anchor + an [old, new] Escalation pair
    referencing it (so the Escalation purge path is exercised, not the cascade)."""
    account = Account(
        tenant_id=tenant_id,
        name="A retention",
        ownership_type=OwnershipType.individual,
        channels=[AccountChannel.email.value],
        owner_email="retention@example.com",
        email_address="retention@example.com",
        routing_rules={},
    )
    session.add(account)
    await session.flush()
    backup = BackupContact(
        tenant_id=tenant_id,
        account_id=account.id,
        name="BC retention",
        email="bc@example.com",
        tier=ContactTier.primary,
    )
    session.add(backup)
    await session.flush()
    # Anchor message: within retention (1d old) so it SURVIVES the purge — the
    # escalations reference it so their deletion is the escalation-purge path,
    # not a cascade from the message-purge path.
    contact = Contact(
        tenant_id=tenant_id,
        name="C anchor",
        channel_preference=ChannelPreference.email,
    )
    session.add(contact)
    await session.flush()
    anchor = await _seed_message(session, tenant_id, contact.id, days=1, now=now)
    escalations = [
        Escalation(
            tenant_id=tenant_id,
            message_id=anchor.id,
            backup_contact_id=backup.id,
            tier=1,
            status=EscalationStatus.pending,
            priority=EscalationPriority.medium,
            assigned_at=now - timedelta(days=days),
        )
        for days in (8, 6)  # (old: past 7d, new: within 7d)
    ]
    for esc in escalations:
        session.add(esc)
    await session.flush()
    return anchor, escalations


# ---------------------------------------------------------------------------
# Test 1 — per-plan retention enforced, independently per tenant.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_per_plan_retention_enforced_on_messages():
    """Four tenants (one per plan) each have one message just past their plan's
    cutoff and one well within it. After the sweep, each tenant's old message is
    purged and each within-retention message survives — proving both the
    plan→cutoff mapping AND that one tenant's purge does not leak into another
    (a free-tier 8-day-old message dies; an enterprise 700-day-old message lives)."""
    now = datetime.now(timezone.utc)
    seeded: dict[str, dict] = {}

    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        for plan in (
            TenantPlan.free,
            TenantPlan.starter,
            TenantPlan.professional,
            TenantPlan.enterprise,
        ):
            tenant = await _seed_tenant(session, plan)
            contact = Contact(
                tenant_id=tenant.id,
                name=f"C-{plan.value}",
                channel_preference=ChannelPreference.email,
            )
            session.add(contact)
            await session.flush()
            retention = _RETENTION_DAYS[plan.value]
            old_days = retention + 1  # one day past the cutoff
            new_days = max(1, retention - 10)  # comfortably within
            m_old = await _seed_message(session, tenant.id, contact.id, days=old_days, now=now)
            m_new = await _seed_message(session, tenant.id, contact.id, days=new_days, now=now)
            seeded[plan.value] = {
                "tenant_id": tenant.id,
                "old_id": m_old.id,
                "new_id": m_new.id,
            }
        await session.commit()

    await run_retention_purge_once(now=now)

    async with AsyncSession(get_engine()) as session:
        for plan_value, ids in seeded.items():
            await set_tenant_context(session, ids["tenant_id"])
            ids_present = {row[0] for row in (await session.execute(select(Message.id))).all()}
            assert (
                ids["old_id"] not in ids_present
            ), f"{plan_value}: message {ids['old_id']} (past retention) must be purged"
            assert (
                ids["new_id"] in ids_present
            ), f"{plan_value}: message {ids['new_id']} (within retention) must survive"


# ---------------------------------------------------------------------------
# Test 2 — all three time-bounded tables purged + audit entry written.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_all_three_tables_purged_with_audit_entry():
    """A free-tier tenant has old + new rows across Message, AuditEntry, and
    Escalation. The sweep purges exactly the old rows of each type, leaves the
    new rows, and writes ONE ``retention.purge`` audit entry whose metadata
    records the per-table counts."""
    now = datetime.now(timezone.utc)

    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant = await _seed_tenant(session, TenantPlan.free)
        tid = tenant.id
        contact = Contact(
            tenant_id=tid,
            name="C free",
            channel_preference=ChannelPreference.email,
        )
        session.add(contact)
        await session.flush()
        m_old = await _seed_message(session, tid, contact.id, days=8, now=now)
        m_new = await _seed_message(session, tid, contact.id, days=1, now=now)
        a_old = await _seed_audit(session, tid, days=8, now=now, suffix="old")
        a_new = await _seed_audit(session, tid, days=1, now=now, suffix="new")
        anchor, escalations = await _seed_escalation_chain(session, tid, now=now)
        e_old, e_new = escalations[0], escalations[1]
        await session.commit()

    summaries = await run_retention_purge_once(now=now)

    # Exactly one summary touched our free tenant with non-zero counts.
    free_summary = next(s for s in summaries if s["plan"] == TenantPlan.free.value)
    assert free_summary["purged"] == {
        "messages": 1,
        "audit_entries": 1,
        "escalations": 1,
    }, free_summary

    async with AsyncSession(get_engine()) as session:
        await set_tenant_context(session, tid)
        msg_ids = {row[0] for row in (await session.execute(select(Message.id))).all()}
        esc_ids = {row[0] for row in (await session.execute(select(Escalation.id))).all()}
        audit_actions = [
            row[0] for row in (await session.execute(select(AuditEntry.action_type))).all()
        ]

        # Old rows purged, new rows + anchor survive.
        assert m_old.id not in msg_ids
        assert m_new.id in msg_ids
        assert anchor.id in msg_ids, "anchor message (within retention) must survive"
        assert e_old.id not in esc_ids
        assert e_new.id in esc_ids
        assert a_old.action_type not in audit_actions, "old audit entry must be purged"
        assert a_new.action_type in audit_actions

        # One retention.purge audit row was written for this tenant.
        purge_entries = [
            row[0]
            for row in (
                await session.execute(
                    select(AuditEntry.metadata_).where(AuditEntry.action_type == "retention.purge")
                )
            ).all()
        ]
        assert len(purge_entries) == 1, "exactly one retention.purge audit row expected"
        meta = purge_entries[0]
        assert meta["plan"] == TenantPlan.free.value
        assert meta["purged"] == {
            "messages": 1,
            "audit_entries": 1,
            "escalations": 1,
        }


# ---------------------------------------------------------------------------
# Test 3 — bind_tenant is load-bearing: the sweep binds each tenant (the GUC
# scopes the DELETE under a non-owner role). Proved indirectly: the sweep's
# per-tenant summary shows the bind worked (old rows were found + deleted),
# which requires the tenant_isolation RLS policy to have been satisfied via
# the GUC the sweep sets inside run_retention_purge_once. The fail-closed
# behavior itself is covered by test_rls_tenant_isolation.py (Property 2).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_sweep_purges_only_seeded_old_rows_not_other_tenants():
    """Two free tenants, each with one old (8d) message. The sweep purges both
    tenants' old messages and nothing else — the per-tenant summary list has an
    entry per tenant and the total purged matches the seeded count (no over- or
    under-deletion from a missing or leaked bind)."""
    now = datetime.now(timezone.utc)
    tenant_ids: list = []

    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        for label in ("alpha", "beta"):
            tenant = await _seed_tenant(session, TenantPlan.free)
            tenant_ids.append(tenant.id)
            contact = Contact(
                tenant_id=tenant.id,
                name=f"C-{label}",
                channel_preference=ChannelPreference.email,
            )
            session.add(contact)
            await session.flush()
            await _seed_message(session, tenant.id, contact.id, days=8, now=now)
        await session.commit()

    summaries = await run_retention_purge_once(now=now)

    purged_summary = [s for s in summaries if s["purged"].get("messages", 0) > 0]
    assert len(purged_summary) == 2, "each tenant's old message must be purged independently"
    total = sum(s["purged"]["messages"] for s in purged_summary)
    assert total == 2, f"exactly 2 messages purged (one per tenant), got {total}"


# ---------------------------------------------------------------------------
# Test 4 — regression: leaf-first purge order counts an old escalation on an
# old message, instead of letting the message purge cascade-delete it first
# (which would make purged.escalations undercount the audit trail).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_old_escalation_on_old_message_is_counted_not_cascaded():
    """Escalation.message_id is ondelete=CASCADE. With the leaf-first purge
    order (escalations before messages) an old escalation referencing an old
    message is counted in ``purged.escalations``. A messages-first order would
    cascade-delete the escalation before the explicit delete ran and report 0."""
    now = datetime.now(timezone.utc)
    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant = await _seed_tenant(session, TenantPlan.free)
        tid = tenant.id
        account = Account(
            tenant_id=tid,
            name="A cascade",
            ownership_type=OwnershipType.individual,
            channels=[AccountChannel.email.value],
            owner_email="casc@example.com",
            email_address="casc@example.com",
            routing_rules={},
        )
        session.add(account)
        await session.flush()
        backup = BackupContact(
            tenant_id=tid,
            account_id=account.id,
            name="BC cascade",
            email="bcc@example.com",
            tier=ContactTier.primary,
        )
        session.add(backup)
        await session.flush()
        contact = Contact(
            tenant_id=tid,
            name="C cascade",
            channel_preference=ChannelPreference.email,
        )
        session.add(contact)
        await session.flush()
        old_msg = await _seed_message(session, tid, contact.id, days=8, now=now)
        old_esc = Escalation(
            tenant_id=tid,
            message_id=old_msg.id,
            backup_contact_id=backup.id,
            tier=1,
            status=EscalationStatus.pending,
            priority=EscalationPriority.medium,
            assigned_at=now - timedelta(days=8),
        )
        session.add(old_esc)
        await session.commit()

    summaries = await run_retention_purge_once(now=now)
    free_summary = next(s for s in summaries if s["plan"] == TenantPlan.free.value)
    assert free_summary["purged"]["escalations"] == 1, (
        "old escalation must be counted (leaf-first order); a messages-first order "
        "would cascade-delete it silently and report 0 — undercounting the audit trail"
    )
    assert free_summary["purged"]["messages"] == 1


# ---------------------------------------------------------------------------
# Test 5 — unknown plan: fail-safe toward under-purge (purge nothing).
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unknown_plan_string_purges_nothing():
    """``purge_expired_records`` with a plan absent from RETENTION_DAYS purges
    nothing — the fail-safe direction for a plan the map doesn't know. The
    DB-level TenantPlan enum constraint prevents an unknown plan reaching here
    in production; this pins the guard as defense-in-depth (a future "purge
    everything" default would fail this test)."""
    now = datetime.now(timezone.utc)
    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant = await _seed_tenant(session, TenantPlan.free)
        tid = tenant.id
        contact = Contact(
            tenant_id=tid,
            name="C unknown-plan",
            channel_preference=ChannelPreference.email,
        )
        session.add(contact)
        await session.flush()
        ancient = await _seed_message(session, tid, contact.id, days=999, now=now)
        await session.commit()

    async with AsyncSession(get_engine()) as session:
        await set_tenant_context(session, tid)
        summary = await purge_expired_records(session, tid, "internal_beta", now=now)
        await session.commit()
    assert summary["purged"] == {}, "unknown plan must purge nothing"

    async with AsyncSession(get_engine()) as session:
        await set_tenant_context(session, tid)
        survivor_ids = {row[0] for row in (await session.execute(select(Message.id))).all()}
    assert ancient.id in survivor_ids, "unknown-plan tenant's rows must survive"
