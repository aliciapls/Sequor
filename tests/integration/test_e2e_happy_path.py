"""E2E integration test — happy path (TODO-22).

Tests the complete flow from signup through daily digest.
Steps that depend on Branch 1 (email) or Branch 2 (AI/RAG) are stubbed
with clear TODO markers for post-merge completion.
"""

import pytest
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
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
    Response,
    RAGRetrieval,
    SourceType,
    Tenant,
    TenantPlan,
)
from sequor.digest.service import gather_digest_data, format_digest_email
from sequor.onboarding.service import signup
from sequor.schemas import OnboardingRequest


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
    await close_engine()


def _unique_domain() -> str:
    import uuid

    return f"e2e-{uuid.uuid4().hex[:8]}.example.com"


@pytest.mark.asyncio
async def test_e2e_happy_path_signup_through_digest(db_session):
    """Full happy path: signup → create records → send message → digest."""
    domain = _unique_domain()

    # Step 1: Organization signs up via onboarding (TODO-17)
    req = OnboardingRequest(
        org_name="E2E Test Corp",
        owner_email=f"owner@{domain}",
        owner_password="SecurePass1",
        account_name="Front Desk",
        ownership_type="individual",
        backup_name="Backup Person",
        backup_email=f"backup@{domain}",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    result = await signup(db_session, req)

    from uuid import UUID

    tenant_id = UUID(result["tenant_id"])
    account_id = UUID(result["account_id"])

    # Verify tenant created
    tenant = await db_session.get(Tenant, tenant_id)
    assert tenant is not None
    assert tenant.plan.value == "free"  # new signups land on the Free entry tier
    assert tenant.email_domain == domain

    # Verify account created
    account = await db_session.get(Account, account_id)
    assert account is not None
    assert account.owner_email == f"owner@{domain}"
    assert account.routing_rules["auto_respond"] is True

    # Verify backup contact created
    backup = await db_session.get(BackupContact, result["backup_contact_id"])
    assert backup is not None
    backup_id = backup.id

    # Step 2: Upload a test document (TODO-18 — Branch 2)
    # TODO: Document upload will be tested post-merge with Branch 2

    # Step 3: Simulate an inbound message (TODO-04 — Branch 1)
    # Create contact + message to simulate incoming email
    contact = Contact(
        tenant_id=tenant_id,
        email="client@external.com",
        name="Test Client",
    )
    db_session.add(contact)
    await db_session.flush()

    msg_inbound = Message(
        tenant_id=tenant_id,
        contact_id=contact.id,
        direction="inbound",
        channel="email",
        body_text="What are your shipping timelines?",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(msg_inbound)
    await db_session.flush()
    contact_id = contact.id
    msg_id = msg_inbound.id
    await db_session.commit()

    # Step 4-5: AI classifies and auto-replies (TODO-07, TODO-09, TODO-16 — Branch 1+2)
    # Simulate: high-confidence RAG auto-reply
    rag = RAGRetrieval(
        tenant_id=tenant_id,
        message_id=msg_id,
        retrieval_confidence=0.92,
    )
    db_session.add(rag)
    await db_session.flush()

    auto_reply = Response(
        tenant_id=tenant_id,
        message_id=msg_id,
        rag_retrieval_id=rag.id,
        content="We ship within 2-3 business days.",
        confidence_badge="high",
        confidence_score=0.92,
        was_auto_sent=True,
        sent_at=datetime.now(timezone.utc),
    )
    db_session.add(auto_reply)
    await db_session.commit()

    # Step 6-8: Low-confidence query escalation and human reply (Branch 1+2)
    # Simulate: low-confidence message → escalation → human reply → learned answer
    msg_low = Message(
        tenant_id=tenant_id,
        contact_id=contact_id,
        direction="inbound",
        channel="email",
        body_text="Can you explain the refund policy for bulk orders?",
        received_at=datetime.now(timezone.utc),
    )
    db_session.add(msg_low)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant_id,
        message_id=msg_low.id,
        backup_contact_id=backup_id,
        tier=1,
        status=EscalationStatus.resolved,
        priority=EscalationPriority.medium,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=1),
        resolved_at=datetime.now(timezone.utc),
        resolution_summary="Provided bulk refund policy",
    )
    db_session.add(esc)
    await db_session.flush()

    # Step 8: Learned answer from human reply (TODO-13 — Branch 2)
    learned = LearnedAnswer(
        tenant_id=tenant_id,
        account_id=account_id,
        question_text="What is the refund policy for bulk orders?",
        answer_text="Bulk orders (>10 units) can be refunded within 30 days with a 10% restocking fee.",
        source_type=SourceType.human_answer,
    )
    db_session.add(learned)
    await db_session.commit()

    # Step 9: Daily digest sent next morning (TODO-15)
    data = await gather_digest_data(db_session, tenant_id, account_id, hours=24)
    subject, body = format_digest_email(data)

    # Verify digest reflects our activity
    assert data["auto_resolved"] >= 1
    assert data["resolved_by_rag"] >= 1
    assert data["learned_count"] >= 1
    assert "refund policy" in data["learned_topics"][0].lower()
    assert "[COVERAGE DIGEST]" in subject
    assert "E2E Test Corp" not in subject  # subject uses account name, not org
