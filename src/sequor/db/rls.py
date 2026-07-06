"""PostgreSQL Row-Level Security for tenant isolation (DEVIATIONS §A2, shard 1c).

Adopt PostgreSQL Row-Level Security on the shared schema as the DB-enforced
tenant-isolation boundary: ``ENABLE ROW LEVEL SECURITY`` + a ``tenant_isolation``
policy on every tenant-scoped table so the database refuses another tenant's
rows even when application code forgets the ``WHERE tenant_id`` filter. This is
the defense-in-depth the spec wants, at a layer an app bug cannot bypass.

Policy semantics: a row is visible/writeable iff its ``tenant_id`` equals the
transaction's bound tenant GUC (``app.current_tenant``, set transaction-local by
``tenant_context.set_tenant_context`` / ``bind_tenant``).
``current_setting('app.current_tenant', true)`` returns NULL when the GUC is
unset (``missing_ok=true``) → ``tenant_id = NULL`` is NULL, not TRUE → the row is
hidden. So an unbound session sees NO tenant-scoped rows (fail-closed, no error)
rather than leaking cross-tenant data.

Two deliberate exemptions / escape hatches:

- ``tenant_encryption_keys`` is EXEMPT from RLS. ``KeyManager.get_tenant_key``
  reads the key row *before* ``set_tenant_context`` sets the GUC (the GUC is set
  after the key load); a policy on that table would hide the key and break
  provisioning. The table is reached only by the trusted ``KeyManager``.
- Three cross-tenant lookup functions are ``SECURITY DEFINER`` (owned by the
  table owner) so they bypass RLS: inbound account resolution (email blind
  index, WhatsApp phone) and account login (owner_email blind index, R7-01).
  These are intentional tenant *discovery* lookups (the 1f blind-index design),
  not forgotten-WHERE bugs — they must cross tenants to find which tenant owns
  an address. (R7-01: login resolves the Account, not the backup contact — the
  legacy ``resolve_backup_contact_by_email_blind_index`` is dropped.)

This module is applied by ``database.init_db()`` (the create_all test loop) and
mirrored by the ``enable_rls_tenant_isolation`` Alembic migration (production
deploys). The table list is the single source of truth; the migration inlines it
for self-containedness and points back here.

Deploy note: RLS is enabled WITHOUT ``FORCE``, so the table OWNER bypasses the
policy (this is what lets the SECURITY DEFINER lookup functions, owned by the
migrator, bypass RLS). For RLS to actually constrain the application at runtime,
the app MUST connect as a non-owner, non-BYPASSRLS role (the table owner is the
migrator/deploy role). This is a deploy-time responsibility, like connection-pool
sizing — the schema declares the isolation contract; the deploy enforces the
role separation that makes it effective.
"""

from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

# Defense-in-depth (dataflow-identifier-safety Rule 5): the table names below are
# interpolated into DDL f-strings. They are a hardcoded literal (never config or
# user input), but validating them at apply time guards against a future refactor
# that reads the list from a less-trusted source.
_IDENTIFIER_RE = re.compile(r"^[a-z_][a-z0-9_]{0,62}$")


def _check_identifier(name: str) -> str:
    if not _IDENTIFIER_RE.match(name):
        raise ValueError(f"unsafe SQL identifier in TENANT_SCOPED_TABLES: {name!r}")
    return name


# Every table that carries a per-row tenant_id and is therefore subject to the
# tenant_isolation policy. Mirrors the __tablename__ values in models.py that have
# a tenant_id column. (key_phrase_mappings is registered on Base.metadata and
# created by create_all even though it is not in the retired schema_manager list.)
TENANT_SCOPED_TABLES: list[str] = [
    "accounts",
    "backup_contacts",
    "contacts",
    "channel_consents",
    "messages",
    "classifications",
    "rag_retrievals",
    "documents",
    "document_chunks",
    "learned_answers",
    "responses",
    "escalations",
    "audit_entries",
    "routing_outcomes",
    "key_phrase_mappings",
]

# A row is visible/writeable iff tenant_id matches the bound tenant GUC. NULL GUC
# → NULL comparison → row hidden (fail-closed). Unqualified tenant_id is
# unambiguous (one table per policy).
_POLICY_EXPR = "(tenant_id = current_setting('app.current_tenant', true)::uuid)"


async def apply_rls_and_policies(conn: AsyncConnection) -> None:
    """Idempotently enable RLS + (re)create the tenant_isolation policy on every
    tenant-scoped table, then (re)create the three SECURITY DEFINER lookup
    functions. Safe to run on every init_db() / create_all bootstrap.
    """
    for tbl in TENANT_SCOPED_TABLES:
        _check_identifier(tbl)  # defense-in-depth before DDL interpolation
        # ENABLE is a no-op if already enabled.
        await conn.execute(text(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY'))
        # CREATE POLICY has no IF NOT EXISTS in PG; drop-then-create is idempotent.
        await conn.execute(text(f'DROP POLICY IF EXISTS tenant_isolation ON "{tbl}"'))
        await conn.execute(
            text(
                f'CREATE POLICY tenant_isolation ON "{tbl}" '
                f"FOR ALL USING ({_POLICY_EXPR}) "
                f"WITH CHECK ({_POLICY_EXPR})"
            )
        )

    await _create_lookup_functions(conn)


async def _create_lookup_functions(conn: AsyncConnection) -> None:
    """(Re)create the three cross-tenant lookup functions.

    Each is SECURITY DEFINER + SET search_path=public so it runs as the table
    owner (bypassing RLS, since the owner is not FORCE'd) with a safe search_path
    (no pg_temp — defends against search_path hijack of a SECURITY DEFINER body).
    The body is a constant-SQL projection over a bound parameter — no user input
    reaches the SQL text, only the parameter value.
    """
    await conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION resolve_account_by_email_blind_index(p_idx varchar)
            RETURNS TABLE (id uuid, tenant_id uuid, name varchar, status text)
            LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
                SELECT id, tenant_id, name, status::text
                FROM accounts
                WHERE owner_email_blind_index = p_idx
                   OR email_address_blind_index = p_idx
                LIMIT 1;
            $$;
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION resolve_account_by_phone(p_phones text[])
            RETURNS TABLE (id uuid, tenant_id uuid, name varchar, whatsapp_phone varchar, status text)
            LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
                SELECT id, tenant_id, name, whatsapp_phone, status::text
                FROM accounts
                WHERE whatsapp_phone = ANY(p_phones)
                LIMIT 1;
            $$;
            """
        )
    )
    await conn.execute(
        text(
            """
            CREATE OR REPLACE FUNCTION resolve_account_login_by_email_blind_index(p_idx varchar)
            RETURNS TABLE (id uuid, tenant_id uuid, password_hash varchar, name varchar)
            LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
                SELECT id, tenant_id, password_hash, name
                FROM accounts
                WHERE owner_email_blind_index = p_idx AND status = 'active'
                LIMIT 1;
            $$;
            """
        )
    )
    # R7-01 (shard 1e): login now resolves the ACCOUNT by owner_email_blind_index,
    # not the backup contact. Drop the dead backup-contact login resolver so a
    # dev DB that created it under an earlier init_db does not keep a lingering
    # SECURITY DEFINER function that bypasses RLS on backup_contacts. Idempotent.
    await conn.execute(
        text("DROP FUNCTION IF EXISTS resolve_backup_contact_by_email_blind_index(varchar)")
    )
