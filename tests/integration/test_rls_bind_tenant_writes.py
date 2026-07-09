"""Tier-2 regression for the Wave-1 bind_tenant sweep completion.

The shard-1c "application-tier bind_tenant sweep" (commit ``64fc842``) was scoped
to ``onboarding/app.py`` only and missed four pre-existing tenant-scoped writers.
Wave-1's RLS-enablement makes them FAIL under the production non-owner role the
wave itself mandates:

- ``ai/vector_store.py`` — ``store_chunks`` (INSERT) + ``search`` (SELECT) on
  ``document_chunks``.
- ``ai/ingestion.py`` — ``_create_document_record`` (INSERT) +
  ``_update_document_status`` (UPDATE) on ``documents``.
- ``ai/learning.py`` — ``delete_learned_answer`` (DELETE) on ``learned_answers``.

Without ``bind_tenant`` the RLS GUC (``app.current_tenant``) is unset on the
method's own session: INSERTs violate ``WITH CHECK``; SELECT/UPDATE/DELETE see 0
rows (silent fail-closed, not a leak).

Each test runs the REAL method on an engine whose every connection ``SET``s
``ROLE`` to the non-superuser, non-BYPASSRLS ``sequor_rls_test`` role — so the
method's OWN ``AsyncSession`` is subject to the policy (not bypassed as
superuser, as the rest of the Tier-2 suite is). The ``bind_tenant`` call inside
each method is what makes the operation succeed; remove it and every assertion
here fails (0 rows / WITH CHECK violation).
"""

from __future__ import annotations

import uuid
from typing import Any, cast

import pytest
from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from sequor.config import settings
from sequor.db.database import get_engine, init_db
from sequor.db.tenant_context import reset_key_manager

# Distinct from test_rls_tenant_isolation's ``sequor_rls_test`` (which REVOKEs
# tenant_encryption_keys to prove the role can't normalize direct key access).
# THIS role mirrors the PRODUCTION non-owner app role Wave-1 mandates: non-
# superuser, non-BYPASSRLS (so RLS applies to the tenant-scoped tables) BUT with
# DML on tenant_encryption_keys too — the app legitimately reads per-tenant keys
# via KeyManager (bind_tenant), and RLS EXEMPTS that table for exactly this
# reason. Revoking it here would break the legitimate read and mis-test the bug.
_RLS_ROLE = "sequor_app_rls_test"

_ROLE_DDL = f"""
DO $$ BEGIN
  CREATE ROLE {_RLS_ROLE} NOLOGIN NOBYPASSRLS;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT USAGE ON SCHEMA public TO {_RLS_ROLE};
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {_RLS_ROLE};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {_RLS_ROLE};
"""


class _FakeLLM:
    """Stand-in for OllamaClient — fixed 768-dim embedding (mirrors
    test_encryption_round_trip). A Protocol-satisfying deterministic adapter,
    NOT a mock."""

    async def generate_embeddings(self, texts):
        return [[0.01] * 768 for _ in texts]


@pytest.fixture
async def role_engine():
    """init_db + role grant + a NullPool engine that SETs ROLE to the non-owner
    on every new connection. NullPool so the SET ROLE can never leak into a
    sibling connection; the role-scoped connection is discarded after use."""
    await init_db()
    async with get_engine().begin() as conn:
        await conn.execute(text(_ROLE_DDL))

    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
    engine = create_async_engine(url, poolclass=NullPool)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_role_on_connect(dbapi_conn, _):  # noqa: ANN001
        cur = dbapi_conn.cursor()
        cur.execute(f"SET ROLE {_RLS_ROLE}")
        cur.close()

    try:
        yield engine
    finally:
        await engine.dispose()


async def _seed_tenant_and_document():
    """Seed (as superuser) a Tenant + a pending Document; return (tenant_id,
    document_id). The superuser import (module scope) bypasses RLS for seeding;
    the seeded rows are the FK targets + RLS visibility anchors for the writes
    exercised under the role."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from sequor.db.models import Document, DocumentStatus, DocumentType, Tenant, TenantPlan

    reset_key_manager()
    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant = Tenant(
            name="RLS write tenant",
            email_domain="rlswrite.test",
            plan=TenantPlan.starter,
            settings={},
        )
        session.add(tenant)
        await session.flush()
        # Provision the per-tenant encryption key the way signup does. Every
        # tenant has one in production; without it bind_tenant → KeyManager
        # raises "No encryption key found" on the methods under test (they call
        # bind_tenant, which eagerly loads the key regardless of whether the
        # touched table has encrypted columns).
        from sequor.db.tenant_context import set_tenant_context

        await set_tenant_context(session, tenant.id, provision=True)
        doc = Document(
            tenant_id=tenant.id,
            name="seeded.pdf",
            type=DocumentType.faq,
            status=DocumentStatus.pending,
            chunk_count=0,
        )
        session.add(doc)
        # Account is the non-nullable FK target for learned_answers.account_id.
        from sequor.db.encrypted_column import compute_email_blind_index
        from sequor.db.models import Account, AccountChannel, OwnershipType

        acct = Account(
            tenant_id=tenant.id,
            name="RLS write acct",
            ownership_type=OwnershipType.individual,
            channels=[AccountChannel.email.value],
            owner_email="acct@rlswrite.test",
            email_address="acct@rlswrite.test",
            owner_email_blind_index=compute_email_blind_index("acct@rlswrite.test"),
            email_address_blind_index=compute_email_blind_index("acct@rlswrite.test"),
            routing_rules={},
        )
        session.add(acct)
        await session.commit()
        return tenant.id, doc.id, acct.id


@pytest.mark.asyncio
async def test_vector_store_write_path_under_non_owner_role(role_engine):
    """VectorStore.store_chunks (INSERT) + search (SELECT) on document_chunks
    succeed under the non-owner role because the methods call bind_tenant
    (setting the RLS GUC on their own session)."""
    tenant_id, document_id, _ = await _seed_tenant_and_document()

    from sequor.ai.vector_store import VectorStore

    vs = VectorStore(role_engine)
    stored = await vs.store_chunks(
        tenant_id=tenant_id,
        document_id=document_id,
        chunks=[(0, "return policy: 30 days", [0.01] * 768)],
    )
    assert stored == 1, "store_chunks must insert the chunk under RLS (bind set the GUC)"

    # Read-back as superuser confirms the row actually landed (not silently 0).
    async with get_engine().connect() as conn:
        cnt = (
            await conn.execute(
                text("SELECT count(*) FROM document_chunks WHERE tenant_id = :t"),
                {"t": tenant_id},
            )
        ).scalar()
    assert cnt == 1

    # search under the role returns the chunk — NOT the 0-row failure the missing
    # bind produced before the fix.
    results = await vs.search(
        tenant_id=tenant_id,
        query_embedding=[0.01] * 768,
        query_text="return policy",
        top_k=5,
        min_score=0.0,
    )
    assert results, "search must return the chunk under RLS (bind set the GUC)"


@pytest.mark.asyncio
async def test_ingestion_record_path_under_non_owner_role(role_engine, monkeypatch):
    """DocumentIngester._create_document_record (INSERT) + _update_document_status
    (UPDATE) on documents succeed under the non-owner role. These methods hardcode
    ``get_engine()``; patch the SOURCE (``sequor.db.database.get_engine``) so their
    call-time ``from ... import get_engine`` resolves to the role-engine. The
    module-level ``get_engine`` import in THIS file still binds the original
    (superuser) function object, so seed + read-back stay privileged."""
    tenant_id, _, _ = await _seed_tenant_and_document()

    from sequor.ai.ingestion import DocumentIngester
    from sequor.ai.vector_store import VectorStore
    from sequor.db.models import DocumentStatus

    monkeypatch.setattr("sequor.db.database.get_engine", lambda: role_engine)

    ingester = DocumentIngester(
        vector_store=VectorStore(role_engine),
        llm_client=cast(Any, _FakeLLM()),
    )

    doc_id = await ingester._create_document_record(
        tenant_id=tenant_id,
        account_id=uuid.uuid4(),
        filename="policy.pdf",
        file_hash="deadbeef",
        document_type="policy",
        chunk_count=0,
        pages_total=0,
        pages_failed=0,
        status=DocumentStatus.pending,
    )
    assert doc_id, "documents INSERT must succeed under RLS (bind set the GUC)"

    # _update_document_status must not silently affect 0 rows under RLS — the
    # pre-fix UPDATE hit 0 rows (USING hid the row) and returned without error.
    await ingester._update_document_status(
        tenant_id=tenant_id,
        document_id=doc_id,
        status=DocumentStatus.indexing,
    )
    async with get_engine().connect() as conn:
        st = (
            await conn.execute(text("SELECT status FROM documents WHERE id = :d"), {"d": doc_id})
        ).scalar()
    assert st == "indexing", "UPDATE must land under RLS (bind set the GUC)"


@pytest.mark.asyncio
async def test_learning_delete_under_non_owner_role(role_engine):
    """LearningLoop.delete_learned_answer (DELETE) on learned_answers affects the
    row under the non-owner role (returns True). Without bind_tenant the RLS USING
    hides the row → rowcount=0 → returns False (silent no-op)."""
    tenant_id, _, account_id = await _seed_tenant_and_document()

    # Seed a learned_answer as SUPERUSER (handles PII encryption), then delete
    # under the role-engine.
    from sequor.ai.learning import LearningLoop

    reset_key_manager()
    super_loop = LearningLoop(llm_client=cast(Any, _FakeLLM()), engine=get_engine())
    learned_id = await super_loop._store_learned_answer(
        tenant_id=tenant_id,
        account_id=account_id,
        question_text="opening hours?",
        answer_text="9am to 5pm",
        source_escalation_id=None,
        embedding=[0.01] * 768,
    )

    role_loop = LearningLoop(llm_client=cast(Any, _FakeLLM()), engine=role_engine)
    deleted = await role_loop.delete_learned_answer(
        tenant_id=tenant_id, learned_answer_id=learned_id
    )
    assert deleted, "DELETE must affect the row under RLS (bind set the GUC)"

    async with get_engine().connect() as conn:
        cnt = (
            await conn.execute(
                text("SELECT count(*) FROM learned_answers WHERE id = :i"),
                {"i": learned_id},
            )
        ).scalar()
    assert cnt == 0
