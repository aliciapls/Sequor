"""enable_rls_tenant_isolation

Revision ID: b7d2a9e5f401
Revises: c3a9e1d4b702
Create Date: 2026-07-05 21:30:00.000000

DB-enforced tenant isolation via PostgreSQL Row-Level Security (DEVIATIONS §A2,
shard 1c). ``ENABLE ROW LEVEL SECURITY`` + a ``tenant_isolation`` policy on every
tenant-scoped table so the database refuses another tenant's rows even when the
application forgets the ``WHERE tenant_id`` filter — the defense-in-depth the
spec wants, at a layer an app bug cannot bypass.

Policy: a row is visible/writeable iff ``tenant_id = current_setting(
'app.current_tenant', true)::uuid``. ``missing_ok=true`` returns NULL when the
GUC is unset → the comparison is NULL (not TRUE) → the row is hidden, fail-closed
with no error. The GUC is set transaction-local by ``tenant_context.set_tenant_context``
/ ``bind_tenant`` at every connection checkout (shard 1a).

Two deliberate exemptions:

- ``tenant_encryption_keys`` is NOT in the list — ``KeyManager`` reads the key row
  before the GUC is set (chicken-and-egg); a policy would hide the key and break
  provisioning. The table is reached only by the trusted ``KeyManager``.
- Three cross-tenant lookup functions are ``SECURITY DEFINER`` (owned by the
  migrator = table owner) so they bypass RLS: inbound account resolution by
  email blind index / WhatsApp phone, and backup-contact login by email blind
  index. These are the intentional tenant-DISCOVERY lookups (the 1f blind-index
  design), not forgotten-WHERE bugs.

This migration is the durable production artifact. The application test loop uses
``init_db()`` → ``Base.metadata.create_all`` + ``db.rls.apply_rls_and_policies``
(model-driven + idempotent RLS), which emits the equivalent DDL on a fresh
create. The tenant-scoped table list is canonical in ``db.rls.TENANT_SCOPED_TABLES``;
it is inlined here for Alembic self-containedness and points back there.

Deploy note (RLS effectiveness): RLS is enabled WITHOUT ``FORCE``, so the table
OWNER bypasses the policy (this is what lets the SECURITY DEFINER lookup
functions, owned by the migrator, bypass RLS). For RLS to actually constrain the
application at runtime, the app MUST connect as a non-owner, non-BYPASSRLS role
(e.g. a dedicated ``sequor_app`` role granted SELECT/INSERT/UPDATE/DELETE, while
the tables are owned by the migrator/deploy role). This is a deploy-time
responsibility analogous to connection-pool sizing — the schema declares the
isolation contract; the deploy enforces the role separation that makes it
effective. Sequor is undeployed today (PR #7 unmerged), so there is no existing
connection role to reconcile.
"""

from collections.abc import Sequence

from alembic import op
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = "b7d2a9e5f401"
down_revision: str | Sequence[str] | None = "c3a9e1d4b702"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Mirror of db.rls.TENANT_SCOPED_TABLES — every table carrying a per-row
# tenant_id. tenant_encryption_keys is EXEMPT (chicken-and-egg; see docstring).
_TENANT_SCOPED_TABLES = [
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
]

_POLICY_EXPR = "(tenant_id = current_setting('app.current_tenant', true)::uuid)"

_LOOKUP_FUNCTIONS_SQL = [
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
    """,
    """
    CREATE OR REPLACE FUNCTION resolve_account_by_phone(p_phones text[])
    RETURNS TABLE (id uuid, tenant_id uuid, name varchar, whatsapp_phone varchar, status text)
    LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
        SELECT id, tenant_id, name, whatsapp_phone, status::text
        FROM accounts
        WHERE whatsapp_phone = ANY(p_phones)
        LIMIT 1;
    $$;
    """,
    """
    CREATE OR REPLACE FUNCTION resolve_backup_contact_by_email_blind_index(p_idx varchar)
    RETURNS TABLE (
        id uuid, tenant_id uuid, account_id uuid,
        name varchar, email varchar, tier text
    )
    LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
        -- R7-01: password_hash moved from backup_contacts to accounts;
        -- this function returns backup-contact metadata (no credential columns)
        SELECT id, tenant_id, account_id, name, email, tier::text
        FROM backup_contacts
        WHERE email_blind_index = p_idx AND active = true
        LIMIT 1;
    $$;
    """,
]

_LOOKUP_FUNCTION_NAMES = [
    "resolve_account_by_email_blind_index",
    "resolve_account_by_phone",
    "resolve_backup_contact_by_email_blind_index",
]


def upgrade() -> None:
    """Enable RLS + tenant_isolation policy on every tenant-scoped table; create
    the three SECURITY DEFINER cross-tenant lookup functions."""
    bind = op.get_bind()
    for tbl in _TENANT_SCOPED_TABLES:
        bind.execute(text(f'ALTER TABLE "{tbl}" ENABLE ROW LEVEL SECURITY'))
        bind.execute(text(f'DROP POLICY IF EXISTS tenant_isolation ON "{tbl}"'))
        bind.execute(
            text(
                f'CREATE POLICY tenant_isolation ON "{tbl}" '
                f"FOR ALL USING ({_POLICY_EXPR}) "
                f"WITH CHECK ({_POLICY_EXPR})"
            )
        )
    for fn_sql in _LOOKUP_FUNCTIONS_SQL:
        bind.execute(text(fn_sql))


def downgrade() -> None:
    """Revert RLS: drop the lookup functions, the tenant_isolation policy, and
    disable RLS on each tenant-scoped table. Non-destructive (no data loss)."""
    bind = op.get_bind()
    for fn in _LOOKUP_FUNCTION_NAMES:
        bind.execute(text(f"DROP FUNCTION IF EXISTS {fn}"))
    for tbl in _TENANT_SCOPED_TABLES:
        bind.execute(text(f'DROP POLICY IF EXISTS tenant_isolation ON "{tbl}"'))
        bind.execute(text(f'ALTER TABLE "{tbl}" DISABLE ROW LEVEL SECURITY'))
