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
    # New signups land on the Free entry tier (spec/onboarding.md: "Daily digest
    # (Starter+)" — Starter is a paid upgrade above Free). Matches
    # onboarding/service.py signup(plan="free") + Tenant model default.
    assert tenant.plan.value == "free"


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


# ---------------------------------------------------------------------------
# R7-01 (shard 1e): login resolves the ACCOUNT (the owner-login identity), not
# the backup contact. These exercise the new resolve_account_login_by_email_
# blind_index SECURITY DEFINER function + the Account.password_hash credential.
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_login_resolver_finds_account_by_owner_email(db_session):
    """After signup, the login resolver finds the ACCOUNT by owner_email blind
    index and returns its password_hash; verify_password succeeds for the owner's
    password. The backup person's email is NOT a login identity (resolves to
    nothing) — proving the owner-login / backup-contact separation."""
    from sqlalchemy import text

    from sequor.auth import verify_password
    from sequor.db.encrypted_column import compute_email_blind_index

    req = _valid_request()
    await signup(db_session, req)
    await db_session.commit()

    owner_idx = compute_email_blind_index(req.owner_email)
    row = (
        (
            await db_session.execute(
                text(
                    "SELECT id, tenant_id, password_hash, name "
                    "FROM resolve_account_login_by_email_blind_index(:idx)"
                ),
                {"idx": owner_idx},
            )
        )
        .mappings()
        .first()
    )
    assert row is not None, "login resolver must find the account by owner_email"
    assert row["password_hash"], "Account.password_hash must be populated at signup"
    assert verify_password(req.owner_password, row["password_hash"])

    # The backup person's email must NOT be a login identity (the R7-01 split).
    backup_idx = compute_email_blind_index(req.backup_email)
    backup_row = (
        (
            await db_session.execute(
                text("SELECT id FROM resolve_account_login_by_email_blind_index(:idx)"),
                {"idx": backup_idx},
            )
        )
        .mappings()
        .first()
    )
    assert backup_row is None, "the backup person's email must not resolve as a login"


@pytest.mark.asyncio
async def test_login_rejects_wrong_password(db_session):
    """verify_password fails for a wrong password and succeeds for the owner's."""
    from sqlalchemy import text

    from sequor.auth import verify_password
    from sequor.db.encrypted_column import compute_email_blind_index

    req = _valid_request()
    await signup(db_session, req)
    await db_session.commit()

    owner_idx = compute_email_blind_index(req.owner_email)
    row = (
        (
            await db_session.execute(
                text("SELECT password_hash FROM resolve_account_login_by_email_blind_index(:idx)"),
                {"idx": owner_idx},
            )
        )
        .mappings()
        .first()
    )
    assert row is not None
    assert not verify_password("wrong-password", row["password_hash"])
    assert verify_password(req.owner_password, row["password_hash"])


@pytest.mark.asyncio
async def test_login_resolver_unknown_email_finds_nothing(db_session):
    """An email no account owns resolves to nothing — login fails closed."""
    from sqlalchemy import text

    from sequor.db.encrypted_column import compute_email_blind_index

    # Signup one account so the table is non-empty.
    await signup(db_session, _valid_request())
    await db_session.commit()

    unknown_idx = compute_email_blind_index("nobody@nowhere.com")
    row = (
        (
            await db_session.execute(
                text("SELECT id FROM resolve_account_login_by_email_blind_index(:idx)"),
                {"idx": unknown_idx},
            )
        )
        .mappings()
        .first()
    )
    assert row is None, "unknown email must not resolve"


@pytest.mark.asyncio
async def test_portal_me_returns_owner_email_after_login(db_session):
    """R7-01 regression (user-flow walk): signup → /auth/login → /portal/me must
    return the OWNER's email. Post-1e ``operator_id`` is ``Account.id``; reading
    ``BackupContact`` by that id returns None, so /me used to come back blank.
    The fix reads the owner identity from Account. Walks the actual user-facing
    surface (the resolver-level tests cannot see this sibling call-site)."""
    import httpx

    from sequor.onboarding.app import app

    req = _valid_request()
    await signup(db_session, req)
    await db_session.commit()

    # ASGITransport runs the app in-process in the same event loop (no nested
    # loop); the AsyncClient persists the login cookie across the two requests.
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        login = await client.post(
            "/api/v1/auth/login",
            json={"email": req.owner_email, "password": req.owner_password},
        )
        assert login.status_code == 200, login.text

        me = await client.get("/api/v1/portal/me")
        assert me.status_code == 200, me.text
        body = me.json()
        assert body["email"] == req.owner_email, (
            "/portal/me must read the owner email from Account (was blank when it "
            "read BackupContact by the Account.id operator_id)"
        )
        assert body["role"] == "admin"
