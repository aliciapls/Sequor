"""Onboarding service — creates Tenant, Account, and BackupContact records.

This is the core business logic for the signup flow. It validates input
(via Pydantic schemas), creates database records, provisions encryption
keys and tenant schema, sends a verification email, and returns the result.
"""

import structlog
from uuid import UUID

import bcrypt
from sequor.email.utils import mask_email as _mask_email

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import Account, BackupContact, Tenant
from sequor.schemas import OnboardingRequest

logger = structlog.get_logger()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode(), password_hash.encode())

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


VERIFICATION_EMAIL_SUBJECT = "Welcome to {org_name} — your coverage is active"
VERIFICATION_EMAIL_BODY = """Hello,

Your Sequor account for {org_name} is now active.

Account: {account_name}
Backup contact: {backup_name} ({backup_email})
Escalation deadline: {sla} hours
Routing: {routing_description}

Your coverage starts as soon as you connect your email inbox.
You'll receive separate instructions for that next step.

If you did not sign up for Sequor, please ignore this email.

— The Sequor Team
"""


async def send_verification_email(
    to: str,
    org_name: str,
    account_name: str,
    backup_name: str,
    backup_email: str,
    sla: int,
    routing_description: str,
) -> None:
    """Send a verification/welcome email after signup.

    Uses SendGrid if configured, otherwise logs the email content
    (for development/testing without email infrastructure).
    """
    from sequor.config import settings

    subject = VERIFICATION_EMAIL_SUBJECT.format(org_name=org_name)
    body = VERIFICATION_EMAIL_BODY.format(
        org_name=org_name,
        account_name=account_name,
        backup_name=backup_name,
        backup_email=backup_email,
        sla=sla,
        routing_description=routing_description,
    )

    if settings.sendgrid_api_key:
        import sendgrid
        from sendgrid.helpers.mail import Content, Email, Mail

        sg = sendgrid.SendGridAPIClient(api_key=settings.sendgrid_api_key)
        message = Mail(
            from_email=Email(f"noreply@{settings.email_from_domain}", "Sequor"),
            to_emails=to,
            subject=subject,
            plain_text_content=Content("text/plain", body),
        )
        try:
            sg.client.mail.send.post(request_body=message.get())
            logger.info("onboarding.verification_email.sent", to=_mask_email(to))
        except Exception as e:
            logger.warning("onboarding.verification_email.failed", to=_mask_email(to), error=str(e))
    else:
        logger.info(
            "onboarding.verification_email.skipped",
            to=_mask_email(to),
            reason="no sendgrid_api_key configured",
        )


async def signup(session: AsyncSession, request: OnboardingRequest) -> dict:
    """Create a new organization with account and backup contact.

    Returns dict with tenant_id, account_id, and backup_contact_id.
    Raises DuplicateEmailError if the owner_email is already registered.
    """
    # Check for existing account with same owner email
    owner_domain = request.owner_email.split("@")[1]
    existing = await session.execute(
        select(Account).where(Account.owner_email == request.owner_email)
    )
    if existing.scalars().first() is not None:
        raise DuplicateEmailError(
            f"An account with email {_mask_email(request.owner_email)} already exists"
        )

    # 1. Create Tenant
    tenant = Tenant(
        name=request.org_name,
        email_domain=owner_domain,
        plan="starter",
        settings={},
        pdpa_consent_recorded_at=None,
    )
    session.add(tenant)
    await session.flush()

    # 2. Provision encryption key BEFORE creating encrypted records
    try:
        from sequor.config import settings as app_settings
        from sequor.db.encryption_keys import KeyManager
        from sequor.db.encrypted_column import set_tenant_key

        if app_settings.encryption_master_key:
            km = KeyManager(app_settings.encryption_master_key)
            tenant_key = await km.provision_tenant_key(session, tenant.id)
            set_tenant_key(tenant_key)
            logger.info("onboarding.encryption_key_provisioned", tenant_id=str(tenant.id))
        else:
            raise RuntimeError(
                "ENCRYPTION_MASTER_KEY is not configured. "
                "Set it in .env before running signup."
            )
    except RuntimeError:
        raise
    except Exception:
        logger.exception("onboarding.encryption_key_failed", tenant_id=str(tenant.id))
        raise RuntimeError("Failed to provision tenant encryption key")

    # 3. Create Account (encrypted columns require tenant key set above)
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
    await session.flush()

    # 4. Create BackupContact (encrypted columns require tenant key set above)
    from sequor.db.encrypted_column import compute_email_blind_index

    backup = BackupContact(
        tenant_id=tenant.id,
        account_id=account.id,
        name=request.backup_name,
        email=request.backup_email,
        email_blind_index=compute_email_blind_index(request.backup_email),
        tier="primary",
        active=True,
        password_hash=hash_password(request.owner_password),
    )
    session.add(backup)
    await session.flush()

    # Link backup to account
    account.backup_contact_ids = [backup.id]
    session.add(account)

    # 5. Create tenant schema for isolation
    try:
        from sequor.db.schema_manager import create_tenant_schema, tenant_id_to_schema

        schema_name = tenant_id_to_schema(tenant.id)
        tenant.schema_name = schema_name
        session.add(tenant)

        conn = await session.connection()
        await create_tenant_schema(conn, schema_name)
        logger.info("onboarding.schema_created", schema_name=schema_name)
    except Exception:
        logger.exception("onboarding.schema_creation_failed", tenant_id=str(tenant.id))

    # Capture IDs before commit
    tenant_id = str(tenant.id)
    account_id = str(account.id)
    backup_id = str(backup.id)

    await session.commit()

    # 6. Send verification email
    await send_verification_email(
        to=request.owner_email,
        org_name=request.org_name,
        account_name=request.account_name,
        backup_name=request.backup_name,
        backup_email=request.backup_email,
        sla=request.escalation_sla_hours,
        routing_description=ROUTING_RULES[request.routing_rule]["description"],
    )

    return {
        "tenant_id": tenant_id,
        "account_id": account_id,
        "backup_contact_id": backup_id,
    }


