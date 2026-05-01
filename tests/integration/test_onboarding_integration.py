"""Integration test for onboarding signup flow.

Tests that a real signup creates all three records (Tenant, Account,
BackupContact) in the database and that the records are linked correctly.
Requires a running PostgreSQL instance.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.database import close_engine, get_engine, init_db
from sequor.db.models import Account, BackupContact, Tenant
from sequor.onboarding.service import signup
from sequor.schemas import OnboardingRequest


def _valid_request(**overrides):
    defaults = dict(
        org_name="Integration Test Corp",
        owner_email="owner@integrationtest.com",
        owner_password="SecurePass1",
        account_name="Test Account",
        ownership_type="individual",
        backup_name="Backup Person",
        backup_email="backup@integrationtest.com",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    defaults.update(overrides)
    return OnboardingRequest(**defaults)


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
    await close_engine()


@pytest.mark.asyncio
async def test_signup_creates_tenant(db_session):
    req = _valid_request()
    result = await signup(db_session, req)

    # Verify tenant exists
    tenant = await db_session.get(Tenant, result["tenant_id"])
    assert tenant is not None
    assert tenant.name == "Integration Test Corp"
    assert tenant.email_domain == "integrationtest.com"
    assert tenant.plan.value == "starter"


@pytest.mark.asyncio
async def test_signup_creates_account(db_session):
    req = _valid_request()
    result = await signup(db_session, req)

    # Verify account exists and is linked to tenant
    account = await db_session.get(Account, result["account_id"])
    assert account is not None
    assert account.name == "Test Account"
    assert str(account.tenant_id) == result["tenant_id"]
    assert account.owner_email == "owner@integrationtest.com"
    assert account.ownership_type.value == "individual"
    assert account.escalation_sla_hours == 4
    assert account.routing_rules["auto_respond"] is True


@pytest.mark.asyncio
async def test_signup_creates_backup_contact(db_session):
    req = _valid_request()
    result = await signup(db_session, req)

    # Verify backup contact exists and is linked to account
    backup = await db_session.get(BackupContact, result["backup_contact_id"])
    assert backup is not None
    assert backup.name == "Backup Person"
    assert backup.email == "backup@integrationtest.com"
    assert backup.tier.value == "primary"
    assert backup.active is True
    assert str(backup.tenant_id) == result["tenant_id"]
    assert str(backup.account_id) == result["account_id"]


@pytest.mark.asyncio
async def test_signup_links_backup_to_account(db_session):
    req = _valid_request()
    result = await signup(db_session, req)

    # Verify account has backup_contact_ids set
    account = await db_session.get(Account, result["account_id"])
    assert account.backup_contact_ids is not None
    assert len(account.backup_contact_ids) == 1
    assert str(account.backup_contact_ids[0]) == result["backup_contact_id"]


@pytest.mark.asyncio
async def test_signup_with_department_type(db_session):
    req = _valid_request(ownership_type="department", account_name="HR Department")
    result = await signup(db_session, req)

    account = await db_session.get(Account, result["account_id"])
    assert account.ownership_type.value == "department"
    assert account.name == "HR Department"


@pytest.mark.asyncio
async def test_signup_with_all_to_backup_routing(db_session):
    req = _valid_request(routing_rule="all_to_backup")
    result = await signup(db_session, req)

    account = await db_session.get(Account, result["account_id"])
    assert account.routing_rules["auto_respond"] is False
