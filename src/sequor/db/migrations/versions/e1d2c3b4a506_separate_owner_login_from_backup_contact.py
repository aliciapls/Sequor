"""separate_owner_login_from_backup_contact (R7-01)

Revision ID: e1d2c3b4a506
Revises: b7d2a9e5f401
Create Date: 2026-07-06 20:00:00.000000

R7-01 (``DEVIATIONS.md``): ``backup_contacts`` conflated the owner-login identity
with the escalation backup contact — signup stored the OWNER's ``email`` +
``password_hash`` + ``email_blind_index`` on the BackupContact row, so the backup
person's email was discarded and every escalation routed to the account owner (not
the designated backup person). Shard 1e separates the two:

- **Account** owns the owner-login identity (``owner_email`` + ``password_hash`` +
  ``owner_email_blind_index``); login resolves the Account.
- **BackupContact** owns the backup person's contact details (their email/name/tier);
  escalations send to ``backup['email']`` (now the backup person's email).

This migration:
- ADDs ``accounts.password_hash`` (the owner-login credential, moved off BackupContact).
- DROPs ``backup_contacts.password_hash`` (dead once login re-points to Account).
- DROPs the legacy ``resolve_backup_contact_by_email_blind_index`` SECURITY DEFINER
  function (login now uses ``resolve_account_login_by_email_blind_index`` on accounts).
- CREATEs ``resolve_account_login_by_email_blind_index`` — the cross-tenant login
  lookup (returns the active account row by ``owner_email_blind_index``, RLS-bypassing
  via SECURITY DEFINER, mirroring the 1f inbound resolver shape).

The application test loop uses ``init_db()`` → ``Base.metadata.create_all`` (model-
driven, emits the new/removed columns on a fresh create) + ``apply_rls_and_policies``
(``db.rls``, which creates the new resolver and DROPs the legacy one); this migration
is the durable artifact for production deploys that track schema via Alembic.

CAVEAT — no data backfill. Schema-only, correct for a greenfield deploy where rows
are created by the post-1e signup (which sets ``Account.password_hash`` and the backup
person's email on BackupContact) and no pre-existing rows hold the legacy layout (this
repo's state: PR #7 is unmerged, the app is undeployed, no production data exists).
For a populated deploy, backfill ``accounts.password_hash`` from the legacy
``backup_contacts.password_hash`` (plain VARCHAR — no master key needed at migrate
time) in a dedicated data migration BEFORE applying this one, else existing operators
cannot log in (``Account.password_hash`` would be NULL).
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e1d2c3b4a506"
down_revision: str | Sequence[str] | None = "b7d2a9e5f401"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


# Resolver function DDL (literal SQL — constant identifiers, no dynamic input;
# mirrors the b7d2a9e5 enable_rls_tenant_isolation migration's op.execute style).
_NEW_LOGIN_FN = """
CREATE OR REPLACE FUNCTION resolve_account_login_by_email_blind_index(p_idx varchar)
RETURNS TABLE (id uuid, tenant_id uuid, password_hash varchar, name varchar)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT id, tenant_id, password_hash, name
    FROM accounts
    WHERE owner_email_blind_index = p_idx AND status = 'active'
    LIMIT 1;
$$;
"""

_LEGACY_LOGIN_FN = """
CREATE OR REPLACE FUNCTION resolve_backup_contact_by_email_blind_index(p_idx varchar)
RETURNS TABLE (
    id uuid, tenant_id uuid, account_id uuid,
    name varchar, password_hash varchar, tier text
)
LANGUAGE sql SECURITY DEFINER SET search_path = public AS $$
    SELECT id, tenant_id, account_id, name, password_hash, tier::text
    FROM backup_contacts
    WHERE email_blind_index = p_idx AND active = true
    LIMIT 1;
$$;
"""


def upgrade() -> None:
    """Move the owner-login identity from BackupContact to Account + swap resolvers."""
    # Owner-login credential now lives on Account (the owner-login identity).
    op.add_column(
        "accounts",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    # BackupContact is now purely the escalation recipient (backup person) —
    # password_hash is dead here once login resolves the Account.
    op.drop_column("backup_contacts", "password_hash")

    # Swap the cross-tenant login resolver from backup_contacts → accounts.
    op.execute("DROP FUNCTION IF EXISTS resolve_backup_contact_by_email_blind_index(varchar)")
    op.execute(_NEW_LOGIN_FN)


def downgrade() -> None:
    """Restore the legacy owner-login-on-BackupContact layout."""
    op.execute("DROP FUNCTION IF EXISTS resolve_account_login_by_email_blind_index(varchar)")
    op.execute(_LEGACY_LOGIN_FN)
    op.add_column(
        "backup_contacts",
        sa.Column("password_hash", sa.String(length=255), nullable=True),
    )
    op.drop_column("accounts", "password_hash")
