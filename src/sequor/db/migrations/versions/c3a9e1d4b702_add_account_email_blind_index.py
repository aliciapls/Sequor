"""add_account_email_blind_index

Revision ID: c3a9e1d4b702
Revises: a1f4c82d6e90
Create Date: 2026-07-05 19:30:00.000000

Inbound account resolution (DEVIATIONS §A1, shard 1f). ``email/inbound`` and
``whatsapp/inbound`` resolve the tenant from the destination address of an
inbound webhook. ``Account.owner_email`` and ``Account.email_address`` are
``EncryptedString`` (random AES-GCM nonce per write), so (a) equality on the
ciphertext can never match and (b) an ORM load would call
``EncryptedString.process_result_value`` and fail-close before the tenant key
is known — every inbound webhook 500s in production under a master key.

The fix is a blind index mirroring ``BackupContact.email_blind_index``: an
HMAC of the email under the GLOBAL master-key-derived lookup key (see
``compute_email_blind_index``), so the resolver can match without decrypting.
This migration adds the two nullable VARCHAR(64) columns + their lookup
indexes and drops the dead ``ix_accounts_owner_email`` (it indexed
non-deterministic ciphertext and could never serve an equality lookup).

The application test loop uses ``init_db()`` → ``Base.metadata.create_all``
(model-driven), which emits both columns + the new indexes on a fresh create;
this migration is the durable artifact for production deploys that track
schema via Alembic.

CAVEAT — no data backfill. This migration is schema-only (DDL add). It is
correct for a greenfield deploy where Account rows are created by ``signup``
(which populates both blind indexes) and no pre-existing rows exist (this
repo's state: PR #7 is unmerged, the app is undeployed, no production data
exists). If this migration is ever applied against a database that already
holds Account rows, those rows' blind indexes stay NULL and inbound
resolution for them returns ``no_account`` (graceful, no 500) until a
backfill computes the index from each row's decrypted email. The backfill is
intentionally not embedded here: it requires the master key at migrate time
and belongs in a dedicated data migration, not a schema migration.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3a9e1d4b702"
down_revision: str | Sequence[str] | None = "a1f4c82d6e90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add Account email blind-index columns + indexes; drop the dead index."""
    op.add_column(
        "accounts",
        sa.Column("owner_email_blind_index", sa.String(length=64), nullable=True),
    )
    op.add_column(
        "accounts",
        sa.Column("email_address_blind_index", sa.String(length=64), nullable=True),
    )
    op.create_index(
        "ix_accounts_owner_email_blind_index",
        "accounts",
        ["owner_email_blind_index"],
        unique=True,
    )
    op.create_index(
        "ix_accounts_email_address_blind_index",
        "accounts",
        ["email_address_blind_index"],
        unique=True,
    )
    # Dead weight since Account encryption landed: indexes non-deterministic
    # AES-GCM ciphertext, so no equality lookup can ever use it.
    op.drop_index("ix_accounts_owner_email", table_name="accounts")


def downgrade() -> None:
    """Revert the blind-index columns and restore the (dead) legacy index."""
    op.create_index("ix_accounts_owner_email", "accounts", ["owner_email"])
    op.drop_index("ix_accounts_email_address_blind_index", table_name="accounts")
    op.drop_index("ix_accounts_owner_email_blind_index", table_name="accounts")
    op.drop_column("accounts", "email_address_blind_index")
    op.drop_column("accounts", "owner_email_blind_index")
