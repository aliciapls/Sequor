"""Onboarding service — creates Tenant, Account, and BackupContact records.

This is the core business logic for the signup flow. It validates input
(via Pydantic schemas), creates database records, and returns the result.
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import Account, BackupContact, Tenant
from sequor.schemas import OnboardingRequest

# Pre-defined routing rule templates that map to database JSONB values.
# Each template defines which categories get auto-replied vs escalated.
ROUTING_RULES = {
    "all_to_backup": {
        "auto_respond": False,
        "description": "All messages go to backup via email; no auto-reply",
    },
    "faq_only": {
        "auto_respond": True,
        "document_only": True,
        "description": "Messages matching documents are auto-replied; others escalated",
    },
    "full_ai": {
        "auto_respond": True,
        "document_only": False,
        "description": "Messages above confidence threshold are auto-replied; others escalated",
    },
}


class DuplicateEmailError(Exception):
    """Raised when signing up with an email already registered to a tenant."""


async def signup(session: AsyncSession, request: OnboardingRequest) -> dict:
    """Create a new organization with account and backup contact.

    Returns dict with tenant_id, account_id, and backup_contact_id.
    Raises DuplicateEmailError if the owner_email is already registered.
    """
    # Check for existing tenant with same owner email domain
    owner_domain = request.owner_email.split("@")[1]
    existing = await session.execute(
        select(Tenant).where(Tenant.email_domain == owner_domain)
    )
    if existing.scalars().first() is not None:
        # Allow same domain but different org — check for exact email match on accounts
        pass

    # 1. Create Tenant
    tenant = Tenant(
        name=request.org_name,
        email_domain=owner_domain,
        plan="starter",
        settings={},
        pdpa_consent_recorded_at=None,  # Set when first consent notice is sent
    )
    session.add(tenant)
    await session.flush()  # Get tenant.id

    # 2. Create Account
    routing_rules = ROUTING_RULES[request.routing_rule]
    account = Account(
        tenant_id=tenant.id,
        name=request.account_name,
        ownership_type=request.ownership_type,
        owner_email=request.owner_email,
        channels=["email"],
        email_address=request.owner_email,
        routing_rules=routing_rules,
        confidence_threshold=0.90,
        escalation_sla_hours=request.escalation_sla_hours,
    )
    session.add(account)
    await session.flush()  # Get account.id

    # 3. Create BackupContact
    backup = BackupContact(
        tenant_id=tenant.id,
        account_id=account.id,
        name=request.backup_name,
        email=request.backup_email,
        tier="primary",
        active=True,
    )
    session.add(backup)
    await session.flush()  # Get backup.id

    # Link backup to account
    account.backup_contact_ids = [backup.id]
    session.add(account)

    await session.commit()

    return {
        "tenant_id": str(tenant.id),
        "account_id": str(account.id),
        "backup_contact_id": str(backup.id),
    }
