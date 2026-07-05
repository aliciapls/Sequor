"""encrypt_pii_columns

Revision ID: a1f4c82d6e90
Revises: 5ab03308b1f3
Create Date: 2026-07-05 14:30:00.000000

PII-at-rest encryption (DEVIATIONS §A1, shard 1b.2). The Message.subject/
body_text/body_raw, Response.content, LearnedAnswer.question_text/answer_text,
Classification.reasoning, Escalation.resolution_summary and Contact.name columns
switch to ``EncryptedString`` (impl = TEXT, stores ``base64(nonce || ciphertext)``).

Most of those columns are already TEXT and need no DDL. The two bounded VARCHAR
columns — ``contacts.name`` (255) and ``messages.subject`` (500) — MUST widen to
TEXT: AES-256-GCM ciphertext is ``plaintext_len + 28`` bytes, then base64
(×4/3), so a 255-char name encrypts to ~378 chars and a 500-char subject to
~705 chars, both overflowing their legacy VARCHAR bound. TEXT is unbounded, so
the encryption can never silently truncate.

The application test loop uses ``init_db()`` → ``Base.metadata.create_all``
(model-driven), which emits TEXT for these columns on a fresh create; this
migration is the durable artifact for production deploys that track schema via
Alembic.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "a1f4c82d6e90"
down_revision: str | Sequence[str] | None = "5ab03308b1f3"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Widen the two bounded PII columns to TEXT so ciphertext never overflows."""
    op.alter_column(
        "contacts",
        "name",
        existing_type=sa.String(length=255),
        type_=sa.Text(),
        existing_nullable=False,
    )
    op.alter_column(
        "messages",
        "subject",
        existing_type=sa.String(length=500),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    """Revert to the legacy VARCHAR bounds.

    CAVEAT: rows whose ciphertext exceeds the VARCHAR length will be truncated
    by PostgreSQL on the cast back — this downgrade is lossy for any tenant that
    stored encrypted PII. Run only against a database you intend to reset.
    """
    op.alter_column(
        "messages",
        "subject",
        existing_type=sa.Text(),
        type_=sa.String(length=500),
        existing_nullable=True,
    )
    op.alter_column(
        "contacts",
        "name",
        existing_type=sa.Text(),
        type_=sa.String(length=255),
        existing_nullable=False,
    )
