"""Tier-2 tests for DB-enforced tenant isolation via Row-Level Security
(DEVIATIONS §A2, shard 1c).

The ``tenant_isolation`` RLS policy moves cross-tenant protection INTO the
database: a session bound to tenant A cannot read tenant B's rows even with a
filter-less query, and cannot WRITE another tenant's tenant_id. These tests
genuinely exercise RLS by running the verification queries as a dedicated
non-superuser, non-BYPASSRLS role (``sequor_rls_test``).

Why the role dance: every other Tier-2 test connects as ``postgres`` (a
superuser), and superusers BYPASS RLS — so a test that ran as ``postgres`` would
see all rows regardless of the policy and prove nothing about enforcement. The
non-owner role is subject to the policy; ``SET ROLE`` drops the superuser
privilege for the duration of the query so the policy actually applies.

Pool-safety: the role-scoped engine uses ``NullPool`` so each ``SET ROLE``
connection is discarded (not returned to the shared pool) — a ``SET ROLE`` can
never leak into another test's pooled connection. ``RESET ROLE`` in ``finally``
is belt-and-suspenders.

The four properties under test:

1. Filter-less isolation — bound to A, a bare ``SELECT`` sees only A's rows.
2. Fail-closed — with NO tenant GUC bound, a tenant-scoped query sees nothing
   (the policy's ``current_setting(..., true)`` returns NULL → no row matches),
   and does not error.
3. WITH CHECK — a session bound to A cannot INSERT/UPDATE a row carrying
   tenant B's id (write-side defense).
4. SECURITY DEFINER bypass — the cross-tenant lookup functions
   (``resolve_account_by_email_blind_index`` etc.) return the matched row
   regardless of the caller's GUC; they are the controlled tenant-discovery
   escape hatch for inbound resolution + login, not a forgotten-WHERE leak.
"""

from __future__ import annotations

import uuid

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool

from sequor.config import settings
from sequor.db.database import get_engine, init_db
from sequor.db.encrypted_column import compute_email_blind_index
from sequor.db.models import (
    Account,
    AccountChannel,
    OwnershipType,
    Tenant,
    TenantPlan,
)
from sequor.db.tenant_context import reset_key_manager, set_tenant_context

_RLS_ROLE = "sequor_rls_test"

# Idempotent: create a non-login, non-BYPASSRLS role and grant it DML on every
# public table + sequence. The role is NOT the table owner (postgres owns the
# tables) so RLS applies to it. Re-running each test is safe (CREATE ROLE via a
# caught duplicate_object; GRANTs are idempotent).
_ROLE_DDL = f"""
DO $$ BEGIN
  CREATE ROLE {_RLS_ROLE} NOLOGIN NOBYPASSRLS;
EXCEPTION WHEN duplicate_object THEN NULL; END $$;
GRANT USAGE ON SCHEMA public TO {_RLS_ROLE};
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO {_RLS_ROLE};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO {_RLS_ROLE};
-- Revoke access to the one table this shard EXEMPTS from RLS (chicken-and-egg
-- with KeyManager): the test role must not normalize direct access to the
-- encrypted tenant-key blobs, even though it is NOLOGIN/test-only.
REVOKE SELECT, INSERT, UPDATE, DELETE ON tenant_encryption_keys FROM {_RLS_ROLE};
"""


@pytest.fixture
async def rls_engine():
    """init_db (creates RLS via db.rls) + the role grant + a NullPool engine for
    role-scoped queries that cannot leak SET ROLE into the shared pool."""
    await init_db()
    async with get_engine().begin() as conn:
        await conn.execute(text(_ROLE_DDL))

    url = settings.database_url.replace("postgresql://", "postgresql+psycopg://")
    engine = create_async_engine(url, poolclass=NullPool)
    try:
        yield engine
    finally:
        await engine.dispose()


# ---------------------------------------------------------------------------
# Seed helpers (run as the superuser/owner — bypasses RLS, so cross-tenant
# fixture rows can be planted).
# ---------------------------------------------------------------------------


async def _seed_tenant_with_document(doc_name: str) -> str:
    """Insert a Tenant + one Document (ORM — no encrypted columns; ORM applies
    Python-side defaults like created_at that raw SQL would have to repeat) and
    return tenant_id. Runs as the superuser/owner so RLS is bypassed for seeding."""
    from sqlalchemy.ext.asyncio import AsyncSession

    from sequor.db.models import (
        Document,
        DocumentStatus,
        DocumentType,
        Tenant,
        TenantPlan,
    )

    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant = Tenant(
            name=f"T {doc_name}",
            email_domain=f"{doc_name}.com",
            plan=TenantPlan.free,
            settings={},
        )
        session.add(tenant)
        await session.flush()
        session.add(
            Document(
                tenant_id=tenant.id,
                name=doc_name,
                type=DocumentType.faq,
                status=DocumentStatus.pending,
                chunk_count=0,
            )
        )
        await session.commit()
        return str(tenant.id)


async def _seed_account_with_blind_index(session, email: str) -> tuple[str, str, str]:
    """Insert a Tenant + Account (ORM, encrypted owner_email) with both email
    blind indexes set; return (tenant_id, account_id, blind_index)."""
    reset_key_manager()
    idx = compute_email_blind_index(email)
    tenant = Tenant(
        name=f"T {email}",
        email_domain=email.split("@")[1],
        plan=TenantPlan.starter,
        settings={},
    )
    session.add(tenant)
    await session.flush()
    await set_tenant_context(session, tenant.id, provision=True)
    acct = Account(
        tenant_id=tenant.id,
        name=f"A {email}",
        ownership_type=OwnershipType.individual,
        channels=[AccountChannel.email.value],
        owner_email=email,
        email_address=email,
        owner_email_blind_index=idx,
        email_address_blind_index=idx,
        routing_rules={},
    )
    session.add(acct)
    await session.flush()
    await session.commit()
    return str(tenant.id), str(acct.id), idx


async def _role_query(engine, sql: str, params: dict | None = None):
    """Run *sql* (with optional params) as the non-superuser role, with NO tenant
    GUC bound. Caller sets the GUC where needed via separate statements."""
    async with engine.connect() as conn:
        await conn.execute(text(f"SET ROLE {_RLS_ROLE}"))
        try:
            result = await conn.execute(text(sql), params or {})
            return result
        finally:
            await conn.execute(text("RESET ROLE"))


# ---------------------------------------------------------------------------
# Property 1 — filter-less isolation: bound to A, only A's rows visible.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rls_filterless_select_isolates_tenants(rls_engine):
    """A bare SELECT (no WHERE tenant_id) under a tenant-A bind returns ONLY A's
    rows — the DB enforces isolation even when the app forgets the filter."""
    tenant_a = await _seed_tenant_with_document("DocA")
    tenant_b = await _seed_tenant_with_document("DocB")

    async with rls_engine.connect() as conn:
        await conn.execute(text(f"SET ROLE {_RLS_ROLE}"))
        try:
            await conn.execute(
                text("SELECT set_config('app.current_tenant', :tid, true)"),
                {"tid": tenant_a},
            )
            rows_a = (
                (await conn.execute(text("SELECT name FROM documents ORDER BY name")))
                .scalars()
                .all()
            )

            # Re-bind to tenant B in a fresh statement (still same txn/role).
            await conn.execute(
                text("SELECT set_config('app.current_tenant', :tid, true)"),
                {"tid": tenant_b},
            )
            rows_b = (
                (await conn.execute(text("SELECT name FROM documents ORDER BY name")))
                .scalars()
                .all()
            )
        finally:
            await conn.execute(text("RESET ROLE"))

    assert rows_a == ["DocA"]
    assert rows_b == ["DocB"]


# ---------------------------------------------------------------------------
# Property 2 — fail-closed: no GUC → no rows (NULL comparison), no error.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rls_fail_closed_without_tenant_guc(rls_engine):
    """With no app.current_tenant bound, the policy hides every tenant-scoped row
    (tenant_id = NULL is NULL, not TRUE). This is the fail-closed behavior that
    makes a forgotten bind safe rather than a leak."""
    await _seed_tenant_with_document("DocA")
    await _seed_tenant_with_document("DocB")

    result = await _role_query(rls_engine, "SELECT name FROM documents")
    rows = result.scalars().all()
    assert rows == [], "RLS must hide all rows when no tenant GUC is bound"


# ---------------------------------------------------------------------------
# Property 3 — WITH CHECK: a bound session cannot write another tenant's id.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_rls_with_check_blocks_cross_tenant_write(rls_engine):
    """A session bound to tenant A cannot INSERT a row carrying tenant B's id —
    the policy's WITH CHECK clause rejects it. Write-side defense, in the DB.

    The INSERT aborts the transaction on the RLS violation; NullPool discards the
    connection on close (SET ROLE + aborted txn die with it — no RESET ROLE
    needed, and one would fail anyway inside an aborted txn)."""
    tenant_a = await _seed_tenant_with_document("DocA")
    tenant_b = await _seed_tenant_with_document("DocB")

    async with rls_engine.connect() as conn:
        await conn.execute(text(f"SET ROLE {_RLS_ROLE}"))
        await conn.execute(
            text("SELECT set_config('app.current_tenant', :tid, true)"),
            {"tid": tenant_a},
        )
        with pytest.raises(SQLAlchemyError, match="row-level security"):
            await conn.execute(
                text(
                    "INSERT INTO documents "
                    "(id, tenant_id, name, type, status, chunk_count) "
                    "VALUES (:id, :tid, 'evil', 'faq', 'pending', 0)"
                ),
                {"id": str(uuid.uuid4()), "tid": tenant_b},
            )


# ---------------------------------------------------------------------------
# Property 4 — SECURITY DEFINER bypass: the lookup function crosses tenants.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lookup_function_bypasses_rls_for_tenant_discovery(rls_engine):
    """The cross-tenant lookup function returns the matched Account regardless of
    the caller's tenant GUC — it is the controlled escape hatch for inbound
    resolution + login. A direct SELECT on accounts under the same (no-bind)
    conditions returns nothing, proving the bypass is scoped to the function."""
    reset_key_manager()

    # Seed two accounts with distinct blind indexes (encrypted owner_email).
    from sqlalchemy.ext.asyncio import AsyncSession

    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        _, _, idx_a = await _seed_account_with_blind_index(session, "a@rlslookup.com")
    reset_key_manager()
    async with AsyncSession(get_engine(), expire_on_commit=False) as session:
        tenant_b, acct_b_id, idx_b = await _seed_account_with_blind_index(
            session, "b@rlslookup.com"
        )

    # As the non-superuser role with NO tenant bound:
    async with rls_engine.connect() as conn:
        await conn.execute(text(f"SET ROLE {_RLS_ROLE}"))
        try:
            # Direct SELECT on accounts → 0 rows (RLS fail-closed).
            direct = (await conn.execute(text("SELECT id FROM accounts"))).all()
            assert direct == [], "direct accounts SELECT must be RLS-filtered to empty"

            # Lookup function → returns account B even with no tenant bound.
            looked_up = (
                await conn.execute(
                    text("SELECT tenant_id FROM " "resolve_account_by_email_blind_index(:idx)"),
                    {"idx": idx_b},
                )
            ).scalar_one()
            assert str(looked_up) == tenant_b

            # auth_login regression (R1 security HIGH): the lookup returns the
            # tenant; the caller MUST then bind the tenant before the ORM reload.
            # Pre-fix the reload ran with no GUC → fail-closed → operator=None.
            # Prove the bind→reload sequence now works: bind tenant B's GUC, then
            # a direct SELECT for account B's id returns the row.
            reload_pre = (
                await conn.execute(
                    text("SELECT id FROM accounts WHERE id = :id"), {"id": acct_b_id}
                )
            ).first()
            assert reload_pre is None, "pre-bind reload must be RLS-hidden (the HIGH bug scenario)"
            await conn.execute(
                text("SELECT set_config('app.current_tenant', :tid, true)"),
                {"tid": tenant_b},
            )
            reload_post = (
                await conn.execute(
                    text("SELECT id FROM accounts WHERE id = :id"), {"id": acct_b_id}
                )
            ).first()
            assert reload_post is not None, "post-bind reload must see the row (the fix)"

            # And account A by its index.
            looked_a = (
                await conn.execute(
                    text("SELECT tenant_id FROM " "resolve_account_by_email_blind_index(:idx)"),
                    {"idx": idx_a},
                )
            ).scalar_one()
            assert looked_a is not None

            # An unknown index → no row (function returns the empty set).
            unknown = (
                await conn.execute(
                    text("SELECT tenant_id FROM " "resolve_account_by_email_blind_index(:idx)"),
                    {"idx": compute_email_blind_index("nobody@nowhere.com")},
                )
            ).first()
            assert unknown is None
        finally:
            await conn.execute(text("RESET ROLE"))
