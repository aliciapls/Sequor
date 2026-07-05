"""Tier-2 round-trip tests for PII-at-rest encryption (DEVIATIONS §A1, shard 1b.2).

Exercises the now-wrapped EncryptedString columns against real PostgreSQL with a
real per-tenant key:

1. Ciphertext-at-rest: an ORM write of plaintext PII stores base64 ciphertext
   in the column (verified by reading the raw column OUTSIDE the ORM, so the
   TypeDecorator does not decrypt).
2. Plaintext-on-read: an ORM read of the same row returns the original plaintext.
3. Per-tenant key isolation: a SECOND tenant's key cannot decrypt the first
   tenant's ciphertext (different HKDF-derived key → InvalidTag).
4. Fail-closed: under APP_ENV=production with no tenant key set, an encrypted
   write raises RuntimeError (never silent plaintext).
"""

import uuid
from datetime import datetime, timezone

import cryptography.exceptions
import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.config import settings
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
    MessageChannel,
    MessageDirection,
    Response,
    SourceType,
    Tenant,
)
from sequor.db.tenant_context import reset_key_manager, set_tenant_context
from sequor.db.encrypted_column import set_tenant_key


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    # expire_on_commit=False so attribute reads (e.g. obj.id) after commit() do
    # not trigger a sync refresh that would raise MissingGreenlet under async.
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    await close_engine()


async def _provision_tenant(session: AsyncSession, domain: str):
    """Create a tenant + account + backup and provision its encryption key."""
    reset_key_manager()
    tenant = Tenant(name=domain, email_domain=domain, plan="starter", settings={})
    session.add(tenant)
    await session.flush()
    # Provision + bind BEFORE the Account/BackupContact writes so their encrypted
    # email/phone columns encrypt under this tenant's key (mirrors signup).
    await set_tenant_context(session, tenant.id, provision=True)
    account = Account(
        tenant_id=tenant.id,
        name="Round-Trip Account",
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
        name="Backup",
        email=f"backup@{domain}",
        tier="primary",
        active=True,
    )
    session.add(backup)
    await session.flush()
    account.backup_contact_ids = [backup.id]
    await session.commit()
    return tenant.id, account.id, backup.id


@pytest.mark.asyncio
async def test_orm_write_stores_ciphertext_orm_read_returns_plaintext(db_session):
    """Plaintext PII written via the ORM is stored as base64 ciphertext; reading
    the row back via the ORM returns the original plaintext."""
    tenant_id, _, _ = await _provision_tenant(db_session, "roundtrip.test")
    # Re-bind for the new transaction (GUC is transaction-local; key contextvar
    # persists, but re-binding is the contract every production path follows).
    await set_tenant_context(db_session, tenant_id)

    contact = Contact(tenant_id=tenant_id, email="client@roundtrip.test", name="Alice Wong")
    db_session.add(contact)
    await db_session.flush()
    contact_id = contact.id

    secret_subject = "Confidential: invoice dispute #9942"
    secret_body = "My balance looks wrong — please advise urgently."
    msg = Message(
        tenant_id=tenant_id,
        contact_id=contact_id,
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        subject=secret_subject,
        body_text=secret_body,
        body_raw="<p>body html</p>",
    )
    db_session.add(msg)
    await db_session.flush()
    message_id = msg.id
    await db_session.commit()

    # 1. Raw column read (bypasses the ORM TypeDecorator) → MUST be ciphertext,
    #    not the plaintext.
    raw = (
        await db_session.execute(
            text("SELECT subject, body_text FROM messages WHERE id = :id"),
            {"id": message_id},
        )
    ).first()
    assert raw is not None
    assert raw.subject != secret_subject, "subject stored as plaintext — encryption did not fire"
    assert raw.body_text != secret_body, "body_text stored as plaintext — encryption did not fire"
    # Ciphertext is base64 over an ASCII alphabet; the plaintext had spaces/specials.
    assert " " not in raw.subject and ":" not in raw.subject

    # 2. ORM read (with the tenant key bound) → MUST decrypt back to plaintext.
    # Raw text() reads do NOT route through the TypeDecorator, so use select().
    await set_tenant_context(db_session, tenant_id)
    from sqlalchemy import select

    orm_msg = (
        await db_session.execute(select(Message).where(Message.id == message_id))
    ).scalar_one()
    assert orm_msg.subject == secret_subject
    assert orm_msg.body_text == secret_body
    assert orm_msg.body_raw == "<p>body html</p>"


@pytest.mark.asyncio
async def test_contact_name_and_resolution_summary_round_trip(db_session):
    """Cover the two columns the migration widens (Contact.name VARCHAR→TEXT,
    Escalation.resolution_summary) plus LearnedAnswer + Response content."""
    tenant_id, account_id, backup_id = await _provision_tenant(db_session, "cols.test")
    await set_tenant_context(db_session, tenant_id)

    contact = Contact(tenant_id=tenant_id, email="c@cols.test", name="Boba Fett")
    db_session.add(contact)
    await db_session.flush()

    msg = Message(
        tenant_id=tenant_id,
        contact_id=contact.id,
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        body_text="question",
    )
    db_session.add(msg)
    await db_session.flush()

    resp = Response(
        tenant_id=tenant_id,
        message_id=msg.id,
        content="Here is the auto-generated answer.",
        confidence_badge="high",
        confidence_score=0.93,
        was_auto_sent=True,
    )
    db_session.add(resp)
    await db_session.flush()

    esc = Escalation(
        tenant_id=tenant_id,
        message_id=msg.id,
        backup_contact_id=backup_id,
        tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.medium,
    )
    db_session.add(esc)
    await db_session.flush()
    esc.resolution_summary = "Resolved: refunded the invoice."
    db_session.add(esc)

    learned = LearnedAnswer(
        tenant_id=tenant_id,
        account_id=account_id,
        question_text="How do I reset my password?",
        answer_text="Click 'Forgot password' on the login page.",
        source_type=SourceType.human_answer,
    )
    db_session.add(learned)
    await db_session.commit()

    # Raw columns are ciphertext.
    raw_name = (
        await db_session.execute(
            text("SELECT name FROM contacts WHERE id = :id"), {"id": contact.id}
        )
    ).scalar()
    assert raw_name != "Boba Fett"
    raw_summary = (
        await db_session.execute(
            text("SELECT resolution_summary FROM escalations WHERE id = :id"), {"id": esc.id}
        )
    ).scalar()
    assert raw_summary != "Resolved: refunded the invoice."
    raw_q = (
        await db_session.execute(
            text("SELECT question_text FROM learned_answers WHERE id = :id"), {"id": learned.id}
        )
    ).scalar()
    assert raw_q != "How do I reset my password?"

    # ORM reads decrypt.
    await set_tenant_context(db_session, tenant_id)
    from sqlalchemy import select

    c2 = (await db_session.execute(select(Contact).where(Contact.id == contact.id))).scalar_one()
    e2 = (await db_session.execute(select(Escalation).where(Escalation.id == esc.id))).scalar_one()
    l2 = (
        await db_session.execute(select(LearnedAnswer).where(LearnedAnswer.id == learned.id))
    ).scalar_one()
    r2 = (await db_session.execute(select(Response).where(Response.id == resp.id))).scalar_one()
    assert c2.name == "Boba Fett"
    assert e2.resolution_summary == "Resolved: refunded the invoice."
    assert l2.question_text == "How do I reset my password?"
    assert l2.answer_text == "Click 'Forgot password' on the login page."
    assert r2.content == "Here is the auto-generated answer."


@pytest.mark.asyncio
async def test_second_tenant_cannot_decrypt_first_tenant_ciphertext(db_session):
    """Per-tenant HKDF key: tenant B's key must fail to decrypt tenant A's
    ciphertext (InvalidTag), proving cross-tenant PII isolation at rest."""
    tenant_a, _, _ = await _provision_tenant(db_session, "tenant-a.test")
    await set_tenant_context(db_session, tenant_a)
    msg_a = Message(
        tenant_id=tenant_a,
        contact_id=(await _seed_contact(db_session, tenant_a, "ca@tenant-a.test")),
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        body_text="tenant A secret payload",
    )
    db_session.add(msg_a)
    await db_session.commit()
    msg_id = msg_a.id

    # Provision tenant B and bind ITS key (replaces A's key in the contextvar).
    tenant_b, _, _ = await _provision_tenant(db_session, "tenant-b.test")
    await set_tenant_context(db_session, tenant_b)

    from sqlalchemy import select

    # Reading tenant A's message under tenant B's key must raise — the GCM tag
    # check fails (cryptography.exceptions.InvalidTag, possibly SQLAlchemy-wrapped).
    # Walk the cause/context chain so an UNRELATED query error fails the test.
    with pytest.raises(Exception) as exc_info:
        (
            await db_session.execute(select(Message).where(Message.id == msg_id))
        ).scalar_one().body_text
    seen: list = []
    _e = exc_info.value
    while _e is not None and len(seen) < 6:
        seen.append(_e)
        _nxt = _e.__cause__ or _e.__context__
        if _nxt is None or _nxt is _e:
            break
        _e = _nxt
    assert any(isinstance(_e, cryptography.exceptions.InvalidTag) for _e in seen), (
        f"expected InvalidTag (GCM tag mismatch) in the exception chain, "
        f"got {[type(e).__name__ for e in seen]}"
    )


async def _seed_contact(session: AsyncSession, tenant_id, email: str) -> uuid.UUID:
    c = Contact(tenant_id=tenant_id, email=email, name=email.split("@")[0])
    session.add(c)
    await session.flush()
    return c.id


@pytest.mark.asyncio
async def test_fail_closed_under_production_without_tenant_key(db_session, monkeypatch):
    """APP_ENV=production + no tenant key → EncryptedString raises RuntimeError
    on write (never silent plaintext)."""
    # Ensure no tenant key is set in the contextvar.
    set_tenant_key(None)
    monkeypatch.setattr(settings, "app_env", "production")
    try:
        tenant = Tenant(
            name="fail-closed", email_domain="failclosed.test", plan="starter", settings={}
        )
        db_session.add(tenant)
        await db_session.flush()
        contact = Contact(tenant_id=tenant.id, email="x@failclosed.test", name="Should Not Leak")
        db_session.add(contact)
        # SQLAlchemy wraps the RuntimeError from process_bind_param in a
        # StatementError; match on the chained message text rather than the type.
        with pytest.raises(Exception, match="tenant key"):
            await db_session.flush()
    finally:
        # settings monkeypatch auto-restores; rollback the partial write.
        await db_session.rollback()


class _FakeLLM:
    """Stand-in for OllamaClient — returns a fixed 768-dim embedding for any text."""

    async def generate_embeddings(self, texts):
        return [[0.01] * 768 for _ in texts]


@pytest.mark.asyncio
async def test_learning_raw_sql_encrypts_and_decrypts(db_session):
    """The learning loop's raw INSERT/SELECT bypass the TypeDecorator, so it must
    encrypt/decrypt with the SAME field_names the ORM declares. This is the C2
    gap from journal/0012: a plaintext raw INSERT would make the ORM digest read
    raise InvalidTag. Exercises _store_learned_answer (encrypt) AND
    search_learned_answers (decrypt) end-to-end against real PG + a real key."""
    tenant_id, account_id, _ = await _provision_tenant(db_session, "learning.test")

    from sequor.ai.learning import LearningLoop
    from sequor.db.database import get_engine
    from typing import Any, cast

    # _FakeLLM satisfies the OllamaClient embedding surface at runtime; cast for
    # the type checker (Protocol-satisfying deterministic adapter, not a mock).
    loop = LearningLoop(llm_client=cast(Any, _FakeLLM()), engine=get_engine())
    await loop.capture_human_answer(
        tenant_id=tenant_id,
        account_id=account_id,
        escalation_id=uuid.uuid4(),
        original_query="What is your return policy?",
        human_reply="Items can be returned within 30 days of purchase.",
    )

    # Raw column is ciphertext (the INSERT encrypted it).
    raw_q = (
        await db_session.execute(
            text("SELECT question_text FROM learned_answers WHERE tenant_id = :t"),
            {"t": tenant_id},
        )
    ).scalar()
    assert raw_q != "What is your return policy?"

    # search_learned_answers decrypts (same field_name → same HKDF key).
    results = await loop.search_learned_answers(
        tenant_id=tenant_id, query="return policy", account_id=account_id
    )
    assert results, "expected at least one learned answer matched"
    assert any("return" in r["question_text"].lower() for r in results)
    assert any("30 days" in r["answer_text"] for r in results)

    # And an ORM read (digest path) decrypts the same row consistently.
    from sqlalchemy import select

    await set_tenant_context(db_session, tenant_id)
    orm_la = (
        await db_session.execute(select(LearnedAnswer).where(LearnedAnswer.tenant_id == tenant_id))
    ).scalar_one()
    assert orm_la.question_text == "What is your return policy?"
    assert orm_la.answer_text == "Items can be returned within 30 days of purchase."


@pytest.mark.asyncio
async def test_erase_contact_pii_encrypts_erasure_markers(db_session):
    """The PDPA erasure path writes '[erased]' through EncryptedString under a
    real per-tenant key: raw columns store ciphertext (not the literal marker,
    not the original PII), email/phone are NULLed, and ORM reads with the key
    bound decrypt back to '[erased]'."""
    from sequor.compliance import erase_contact_pii

    tenant_id, _, _ = await _provision_tenant(db_session, "erasure.test")
    await set_tenant_context(db_session, tenant_id)

    contact = Contact(tenant_id=tenant_id, email="doomed@erasure.test", name="Real Name")
    db_session.add(contact)
    await db_session.flush()
    contact_id = contact.id
    msg = Message(
        tenant_id=tenant_id,
        contact_id=contact_id,
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        subject="Private subject",
        body_text="Private body",
    )
    db_session.add(msg)
    await db_session.commit()
    message_id = msg.id

    summary = await erase_contact_pii(db_session, tenant_id, contact_id)
    await db_session.commit()

    assert "contacts" in summary["tables_affected"]
    assert "messages" in summary["tables_affected"]

    # Raw columns: the '[erased]' markers were ENCRYPTED (ciphertext, not the
    # literal marker, not the original PII); email was NULLed.
    raw_c = (
        await db_session.execute(
            text("SELECT name, email FROM contacts WHERE id = :id"), {"id": contact_id}
        )
    ).one()
    assert raw_c.name != "[erased]"
    assert raw_c.name != "Real Name"
    assert raw_c.email is None
    raw_m = (
        await db_session.execute(
            text("SELECT subject, body_text FROM messages WHERE id = :id"), {"id": message_id}
        )
    ).one()
    assert raw_m.subject != "[erased]"
    assert raw_m.subject != "Private subject"
    assert raw_m.body_text != "Private body"

    # ORM reads (re-bind for the new transaction) decrypt to '[erased]'.
    from sqlalchemy import select

    await set_tenant_context(db_session, tenant_id)
    c2 = (await db_session.execute(select(Contact).where(Contact.id == contact_id))).scalar_one()
    m2 = (await db_session.execute(select(Message).where(Message.id == message_id))).scalar_one()
    assert c2.name == "[erased]"
    assert m2.subject == "[erased]"
    assert m2.body_text == "[erased]"


class _FakeEscalationSender:
    """EmailSender stand-in for the scheduler/escalation flow (no real sends).
    Records escalation emails so a test can assert the reminder dispatched."""

    def __init__(self):
        self.escalation_emails_sent = 0

    async def send_email(self, **kwargs):
        return "fake-msg-id"

    async def send_escalation_email(self, **kwargs):
        self.escalation_emails_sent += 1
        return "fake-esc-id"


@pytest.mark.asyncio
async def test_scheduler_binds_tenant_before_processing_breach(db_session):
    """Regression for redteam C2: SLAScheduler._tick MUST bind each tenant before
    reading/writing encrypted columns. Without the bind, the master-key-set
    (production) tick fail-closes per tenant inside the `except Exception` and the
    SLA system silently stops processing breaches."""
    from datetime import timedelta
    from sqlalchemy import select

    from sequor.db.crud import SessionCrud
    from sequor.db.models import EscalationPriority, EscalationStatus
    from sequor.escalation.scheduler import SLAScheduler
    from sequor.escalation.service import EscalationService

    tenant_id, account_id, backup_id = await _provision_tenant(db_session, "sched.test")
    await set_tenant_context(db_session, tenant_id)

    contact = Contact(tenant_id=tenant_id, email="c@sched.test", name="Client")
    db_session.add(contact)
    await db_session.flush()
    msg = Message(
        tenant_id=tenant_id,
        contact_id=contact.id,
        direction=MessageDirection.inbound,
        channel=MessageChannel.email,
        body_text="urgent",
    )
    db_session.add(msg)
    await db_session.flush()
    # Pending escalation assigned 6h ago; account SLA is 4h → breached.
    esc = Escalation(
        tenant_id=tenant_id,
        message_id=msg.id,
        backup_contact_id=backup_id,
        tier=1,
        status=EscalationStatus.pending,
        priority=EscalationPriority.high,
        assigned_at=datetime.now(timezone.utc) - timedelta(hours=6),
    )
    db_session.add(esc)
    await db_session.commit()
    esc_id = esc.id

    # Build the scheduler stack on the SAME session as the seed. bind_tenant on
    # the service binds this session, so its encrypted reads/writes decrypt/encrypt.
    sender = _FakeEscalationSender()
    crud = SessionCrud(db_session)
    service = EscalationService(db_express=crud, email_sender=sender)  # type: ignore[arg-type]
    scheduler = SLAScheduler(service, crud, interval_seconds=999)
    # Clear the key to prove _tick re-binds (it must not rely on the seed's bind).
    set_tenant_key(None)
    await scheduler._tick()
    await db_session.commit()

    # The breach was processed END-TO-END: status moved to expired, the
    # resolution_summary was written through EncryptedString (raw column =
    # ciphertext, not plaintext), AND the SLA-breach reminder email dispatched.
    # Asserting the reminder catches a silent per-tenant `except Exception` that
    # would otherwise let the test pass while process_breached_escalation aborts
    # mid-function (the round-2 H1/H2 uuid.UUID-on-UUID-object class).
    raw_summary = (
        await db_session.execute(
            text("SELECT status, resolution_summary FROM escalations WHERE id = :id"),
            {"id": esc_id},
        )
    ).one()
    assert raw_summary.status == EscalationStatus.expired.value
    assert raw_summary.resolution_summary is not None
    assert "SLA breached" not in raw_summary.resolution_summary  # it's ciphertext
    assert sender.escalation_emails_sent >= 1, (
        "SLA-breach reminder did not dispatch — process_breached_escalation "
        "likely aborted before the reminder (silent tenant_error)"
    )

    # And an ORM read with the key bound decrypts it.
    await set_tenant_context(db_session, tenant_id)
    orm_esc = (
        await db_session.execute(select(Escalation).where(Escalation.id == esc_id))
    ).scalar_one()
    assert "SLA breached" in (orm_esc.resolution_summary or "")
