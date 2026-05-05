"""Audit trail helper — writes AuditEntry rows for key operations.

Usage:
    from sequor.db.audit import audit
    await audit(session, tenant_id=..., action="message.classified",
                doer_type="ai_agent", doer_id=agent_id,
                recipient_type="contact", recipient_id=contact_id,
                message_id=msg_id, metadata={"category": "routine"})
"""

import uuid
from datetime import datetime, timezone
from typing import Any

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import AuditEntry, DoerType, RecipientType

logger = structlog.get_logger()


async def audit(
    session: AsyncSession,
    *,
    tenant_id: uuid.UUID,
    action: str,
    doer_type: str,
    doer_id: uuid.UUID,
    recipient_type: str,
    recipient_id: uuid.UUID,
    message_id: uuid.UUID | None = None,
    metadata: dict[str, Any] | None = None,
) -> AuditEntry:
    """Write an audit entry and return it.

    All parameters except message_id and metadata are required so that
    every audit row has full traceability.
    """
    entry = AuditEntry(
        id=uuid.uuid4(),
        tenant_id=tenant_id,
        doer_type=doer_type,
        doer_id=doer_id,
        action_type=action,
        recipient_type=recipient_type,
        recipient_id=recipient_id,
        message_id=message_id,
        metadata_=metadata,
        occurred_at=datetime.now(timezone.utc),
    )
    session.add(entry)
    await session.flush()

    logger.debug(
        "audit.written",
        action=action,
        tenant_id=str(tenant_id),
        doer_type=doer_type,
    )
    return entry
