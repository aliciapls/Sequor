"""PDPA compliance constants and helpers.

Single source of truth for consent notice text, HUMAN keyword detection,
and erasure verification. All compliance-facing code imports from here.
"""

import uuid
from typing import Any

import structlog
from sqlalchemy import delete, select, update
from sqlalchemy.ext.asyncio import AsyncSession

logger = structlog.get_logger()

# The consent notice included in every first auto-reply to a contact.
# Must be a complete sentence explaining AI processing and the opt-out mechanism.
CONSENT_NOTICE = (
    "This inbox is managed by {org_name}'s AI assistant. "
    "Your message is processed to route and respond to your inquiry. "
    "Reply HUMAN to speak with a person."
)

# Keywords that trigger immediate opt-out (case-insensitive, exact or starts-with)
OPT_OUT_KEYWORDS = {"HUMAN", "STOP"}


def is_opt_out(message_body: str) -> bool:
    """Check if a message body contains an opt-out keyword.

    Matches HUMAN or STOP as the entire message, or as the first word.
    Case-insensitive.
    """
    stripped = message_body.strip().upper()
    if not stripped:
        return False
    first_word = stripped.split()[0]
    return first_word in OPT_OUT_KEYWORDS


def build_consent_notice(org_name: str) -> str:
    """Format the consent notice with the organization's name."""
    return CONSENT_NOTICE.format(org_name=org_name)


# Fields on the Contact model that constitute PII and must be erased.
PII_FIELDS = {"email", "phone", "name", "company"}

# Fields to scrub (set to None) on erasure.
ERASURE_NULL_FIELDS = {
    "email": None,
    "phone": None,
    "name": "[erased]",
    "company": None,
    "tags": None,
}


async def erase_contact_pii(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    contact_id: uuid.UUID,
) -> dict[str, Any]:
    """Erase a contact's PII per PDPA data subject request.

    Overwrites PII fields with [erased]/null, deletes vector embeddings,
    and writes an audit entry. The contact row itself is kept (with name
    set to [erased]) so that audit trails and message references remain
    intact.

    Returns a summary of what was erased.
    """
    from sequor.db.models import (
        Contact,
        DocumentChunk,
        LearnedAnswer,
        Message,
    )

    # 1. Verify contact exists and belongs to tenant
    result = await session.execute(
        select(Contact).where(
            Contact.id == contact_id,
            Contact.tenant_id == tenant_id,
        )
    )
    contact = result.scalar_one_or_none()
    if contact is None:
        raise ValueError(f"Contact {contact_id} not found in tenant {tenant_id}")

    erased = {"contact_id": str(contact_id), "tables_affected": []}

    # 2. Load tenant encryption key so encrypted columns can be updated
    try:
        from sequor.config import settings
        from sequor.db.encryption_keys import KeyManager
        from sequor.db.encrypted_column import set_tenant_key

        if settings.encryption_master_key:
            km = KeyManager(settings.encryption_master_key)
            key = await km.get_tenant_key(session, tenant_id)
            set_tenant_key(key)
    except Exception:
        logger.exception("compliance.erasure_key_failed", tenant_id=str(tenant_id))
        raise RuntimeError("Cannot load tenant encryption key for erasure")

    # 3. Overwrite contact PII fields
    await session.execute(
        update(Contact)
        .where(Contact.id == contact_id)
        .values(**ERASURE_NULL_FIELDS)
    )
    erased["tables_affected"].append("contacts")

    # 4. Delete vector embeddings from document chunks for this contact's messages
    from sequor.db.models import Message

    msg_result = await session.execute(
        select(Message.id).where(
            Message.tenant_id == tenant_id,
            Message.contact_id == contact_id,
        )
    )
    message_ids = [row[0] for row in msg_result.all()]

    chunk_result = await session.execute(
        select(DocumentChunk.id).where(
            DocumentChunk.tenant_id == tenant_id,
            DocumentChunk.message_id.in_(message_ids) if message_ids else False,
        )
    ) if message_ids else await session.execute(
        select(DocumentChunk.id).where(DocumentChunk.tenant_id == tenant_id)
    )
    chunk_ids = [row[0] for row in chunk_result.all()]
    if chunk_ids:
        await session.execute(
            update(DocumentChunk)
            .where(DocumentChunk.id.in_(chunk_ids))
            .values(embedding=None)
        )
        erased["tables_affected"].append("document_chunks")
        erased["embeddings_removed"] = len(chunk_ids)

    # 5. Delete vector embeddings from learned answers for this contact's escalations
    from sequor.db.models import Escalation

    esc_result = await session.execute(
        select(Escalation.id).where(
            Escalation.tenant_id == tenant_id,
            Escalation.message_id.in_(message_ids) if message_ids else False,
        )
    ) if message_ids else await session.execute(
        select(Escalation.id).where(Escalation.tenant_id == tenant_id)
    )
    escalation_ids = [row[0] for row in esc_result.all()]

    learned_result = await session.execute(
        select(LearnedAnswer.id).where(
            LearnedAnswer.tenant_id == tenant_id,
            LearnedAnswer.source_escalation_id.in_(escalation_ids) if escalation_ids else False,
        )
    ) if escalation_ids else await session.execute(
        select(LearnedAnswer.id).where(LearnedAnswer.tenant_id == tenant_id)
    )
    learned_ids = [row[0] for row in learned_result.all()]
    if learned_ids:
        await session.execute(
            update(LearnedAnswer)
            .where(LearnedAnswer.id.in_(learned_ids))
            .values(embedding=None)
        )
        erased["tables_affected"].append("learned_answers")

    # 6. Write audit entry
    try:
        from sequor.db.audit import audit

        await audit(
            session,
            tenant_id=tenant_id,
            action="contact.pii_erased",
            doer_type="system",
            doer_id=tenant_id,
            recipient_type="contact",
            recipient_id=contact_id,
            metadata={"erased_fields": list(ERASURE_NULL_FIELDS.keys())},
        )
    except Exception:
        logger.exception("compliance.erasure_audit_failed", contact_id=str(contact_id))

    await session.flush()

    logger.info(
        "compliance.pii_erased",
        contact_id=str(contact_id),
        tenant_id=str(tenant_id),
        tables=erased["tables_affected"],
    )

    return erased
