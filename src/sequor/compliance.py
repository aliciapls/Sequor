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


def is_human_override(message_body: str) -> bool:
    """WhatsApp-specific HUMAN override detection.

    Per the WhatsApp spec, only exact "HUMAN" or starts-with "HUMAN "
    (with trailing space) triggers the override. This prevents false
    positives from phrases like "human resources" or "human form".

    The detection window is only within the active 24-hour session.
    """
    stripped = message_body.strip()
    if not stripped:
        return False
    upper = stripped.upper()
    return upper == "HUMAN" or upper.startswith("HUMAN ")


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
        LearnedAnswer,
        Message,
    )

    # 1. Bind the tenant BEFORE any encrypted-column read. Contact.name/email/phone
    # are all EncryptedString; without the key the ORM result construction
    # fail-closes in production. ``bind_tenant`` is the shard-1a boundary that sets
    # BOTH the per-tenant key (production) AND the RLS GUC (production AND dev). The
    # dev GUC fallback matters here: the explicit ``WHERE Contact.tenant_id``
    # clauses below hold isolation regardless, but RLS is the defense-in-depth layer
    # a future refactor (dropped WHERE) would rely on — it must be set in dev too.
    try:
        from sequor.db.tenant_context import bind_tenant

        await bind_tenant(session, tenant_id)
    except Exception:
        logger.exception("compliance.erasure_bind_failed", tenant_id=str(tenant_id))
        raise RuntimeError("Cannot bind tenant context for erasure")

    # 2. Verify contact exists and belongs to tenant
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

    # 3. Overwrite contact PII fields
    await session.execute(
        update(Contact).where(Contact.id == contact_id).values(**ERASURE_NULL_FIELDS)
    )
    erased["tables_affected"].append("contacts")

    # 4. Scrub message content for this contact. The messages ARE the contact's
    #    PII (data-model.md: "Message records: Hard delete"); prior code never
    #    touched body/subject at all.
    from sequor.db.models import Message

    msg_result = await session.execute(
        select(Message.id).where(
            Message.tenant_id == tenant_id,
            Message.contact_id == contact_id,
        )
    )
    message_ids = [row[0] for row in msg_result.all()]

    if message_ids:
        await session.execute(
            update(Message)
            .where(Message.id.in_(message_ids))
            .values(subject="[erased]", body_text="[erased]", body_raw="[erased]")
        )
        erased["tables_affected"].append("messages")
        erased["messages_scrubbed"] = len(message_ids)

    # NOTE: DocumentChunk has NO contact/message linkage (chunks belong to the
    # account's uploaded knowledge base via document_id, not to a contact's
    # messages). The previous code referenced DocumentChunk.message_id — a column
    # that does not exist (AttributeError on the has-messages path) — and, when a
    # contact had no messages, fell through to nulling embeddings for the ENTIRE
    # tenant's document store. Contact erasure MUST NOT touch the account KB, so
    # the chunk-erasure step is removed rather than "fixed".

    # 5. Scrub learned answers derived from THIS contact's escalations. Empty
    #    escalation/learned sets MUST affect zero rows — never fall through to an
    #    all-tenant wipe (the prior `if x else <all-tenant>` destroyed the whole
    #    tenant knowledge base when a contact had no escalations).
    from sequor.db.models import Escalation

    escalation_ids: list = []
    if message_ids:
        esc_result = await session.execute(
            select(Escalation.id).where(
                Escalation.tenant_id == tenant_id,
                Escalation.message_id.in_(message_ids),
            )
        )
        escalation_ids = [row[0] for row in esc_result.all()]

    learned_ids: list = []
    if escalation_ids:
        learned_result = await session.execute(
            select(LearnedAnswer.id).where(
                LearnedAnswer.tenant_id == tenant_id,
                LearnedAnswer.source_escalation_id.in_(escalation_ids),
            )
        )
        learned_ids = [row[0] for row in learned_result.all()]

    if learned_ids:
        await session.execute(
            update(LearnedAnswer)
            .where(LearnedAnswer.id.in_(learned_ids))
            .values(
                embedding=None,
                question_text="[erased]",
                answer_text="[erased]",
            )
        )
        erased["tables_affected"].append("learned_answers")
        erased["learned_answers_text_erased"] = len(learned_ids)

    # 7. Write audit entry
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
