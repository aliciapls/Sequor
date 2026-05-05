"""Per-tenant PostgreSQL schema management.

Each tenant gets a dedicated PostgreSQL schema (e.g., 'tenant_550e8400...')
containing private copies of all tenant-scoped tables. The public schema
holds only the tenant registry and cross-tenant indexes.
"""

import re
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

logger = structlog.get_logger()

_IDENTIFIER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]{0,62}$")
_MAX_IDENTIFIER_LENGTH = 63

# Tables that get cloned into each tenant schema.
# Must match the __tablename__ values in models.py.
TENANT_TABLES: list[str] = [
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


class IdentifierError(ValueError):
    """Raised when a SQL identifier fails validation."""


def validate_identifier(name: str) -> None:
    """Validate a SQL identifier to prevent injection.

    Raises IdentifierError if the identifier contains disallowed characters
    or exceeds PostgreSQL's maximum identifier length. Error messages use a
    fingerprint instead of echoing raw input to prevent log injection.
    """
    if not isinstance(name, str):
        raise IdentifierError("Identifier must be a string")
    if len(name) > _MAX_IDENTIFIER_LENGTH:
        raise IdentifierError(
            f"Identifier exceeds {_MAX_IDENTIFIER_LENGTH}-char limit "
            f"(len={len(name)})"
        )
    if not _IDENTIFIER_RE.match(name):
        raise IdentifierError(
            "Identifier failed validation "
            f"(fingerprint={hash(name) & 0xFFFF:04x})"
        )


def tenant_id_to_schema(tenant_id) -> str:
    """Convert a UUID tenant_id to a safe PostgreSQL schema name.

    Format: tenant_{hex_no_dashes}
    e.g. 550e8400-e29b-41d4-a716-446655440000 -> tenant_550e8400e29b41d4a716446655440000

    Deterministic: same UUID always produces the same schema name.
    """
    hex_str = str(tenant_id).replace("-", "")
    schema = f"tenant_{hex_str}"
    validate_identifier(schema)
    return schema


async def create_tenant_schema(
    conn: AsyncConnection,
    schema_name: str,
) -> None:
    """Create a new tenant schema with all tenant-scoped tables.

    Uses CREATE TABLE ... (LIKE public.tablename INCLUDING DEFAULTS
    INCLUDING CONSTRAINTS) to copy structure from the public schema.
    The public schema tables must already exist (created by init_db()).

    Args:
        conn: Async database connection (will be committed).
        schema_name: Validated schema name (use tenant_id_to_schema()).
    """
    validate_identifier(schema_name)
    await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))

    for table_name in TENANT_TABLES:
        validate_identifier(table_name)
        await conn.execute(
            text(
                f'CREATE TABLE IF NOT EXISTS "{schema_name}"."{table_name}" '
                f'(LIKE public."{table_name}" INCLUDING DEFAULTS INCLUDING CONSTRAINTS)'
            )
        )

    logger.info(
        "schema.created",
        schema_name=schema_name,
        tables=len(TENANT_TABLES),
    )


async def drop_tenant_schema(
    conn: AsyncConnection,
    schema_name: str,
    *,
    force: bool = False,
) -> None:
    """Drop a tenant schema and all its data. Requires force=True.

    Args:
        conn: Async database connection (will be committed).
        schema_name: Validated schema name.
        force: Must be True to acknowledge irreversible data loss.
    """
    if not force:
        raise RuntimeError(
            "drop_tenant_schema refused — pass force=True to acknowledge "
            "irreversible data loss"
        )
    validate_identifier(schema_name)
    await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
    await conn.commit()
    logger.info("schema.dropped", schema_name=schema_name)
