"""Tier-2 inbound account-resolution tests (DEVIATIONS §A1, shard 1f).

Pre-1f, ``email/whatsapp inbound._resolve_account`` filtered on ``EncryptedString``
columns (``owner_email``/``email_address``) to resolve the tenant from an inbound
webhook's destination address. Two compounding failure modes, both fire in
production under a master key:

1. Equality on the ciphertext never matches (AES-GCM random nonce per write).
2. An ORM load would call ``EncryptedString.process_result_value`` on
   ``owner_email`` and fail-close before the tenant key is known (the tenant is
   not known yet — this lookup IS the tenant resolution).

Net: every inbound email/WhatsApp webhook 500'd in production. The dev/test
loop never saw it (without a master key, EncryptedString stores plaintext and
the dev-fallback ORM path works).

The 1f fix: signup populates two Account email blind indexes (HMAC under the
GLOBAL master-key-derived lookup key, mirroring BackupContact.email_blind_index)
and both resolvers look up by blind index / plain ``whatsapp_phone`` via a raw
projection of non-encrypted columns (mirrors onboarding.app.auth_login), so no
encrypted column is ever materialized before the tenant is bound.

These tests exercise the real ``signup()`` → resolver flow against real
PostgreSQL under a master key.
"""

import pytest
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.config import settings
from sequor.db.crud import SessionCrud
from sequor.db.database import close_engine, get_engine, init_db
from sequor.db.encrypted_column import compute_email_blind_index, set_tenant_key
from sequor.db.models import Account
from sequor.db.tenant_context import set_tenant_context
from sequor.email.inbound import InboundEmailProcessor
from sequor.onboarding.service import signup
from sequor.schemas import OnboardingRequest
from sequor.whatsapp.inbound import InboundWhatsAppProcessor


def _valid_request(**overrides):
    defaults = dict(
        org_name="1f Resolver Corp",
        owner_email="owner@1fresolve.com",
        owner_password="SecurePass1",
        account_name="1f Account",
        ownership_type="individual",
        backup_name="Backup Person",
        backup_email="backup@1fresolve.com",
        escalation_sla_hours=4,
        routing_rule="full_ai",
    )
    defaults.update(overrides)
    return OnboardingRequest(**defaults)


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine, expire_on_commit=False) as session:
        yield session
    await close_engine()


@pytest.mark.asyncio
async def test_signup_populates_account_blind_indexes(db_session):
    """signup stores BOTH email blind indexes on the Account row and stores
    owner_email as ciphertext — the preconditions the inbound resolver relies
    on. Verifies the 1f.2 signup edit end-to-end through the real signup()."""
    req = _valid_request(owner_email="owner@idx.com")
    result = await signup(db_session, req)
    account_id = result["account_id"]

    # Read the raw columns OUTSIDE the ORM so the TypeDecorator does not decrypt
    # (and so we observe the true at-rest bytes).
    raw = (
        (
            await db_session.execute(
                text(
                    "SELECT owner_email, owner_email_blind_index, email_address_blind_index "
                    "FROM accounts WHERE id = :id"
                ),
                {"id": account_id},
            )
        )
        .mappings()
        .first()
    )
    assert raw is not None
    # owner_email is ciphertext at rest (a tenant key was bound during signup).
    assert raw["owner_email"] != "owner@idx.com"
    expected = compute_email_blind_index("owner@idx.com")
    assert raw["owner_email_blind_index"] == expected
    assert raw["email_address_blind_index"] == expected


@pytest.mark.asyncio
async def test_email_resolver_finds_account_under_prod_without_tenant_key(db_session, monkeypatch):
    """The production scenario: an inbound email webhook lands on a fresh request
    where no tenant key is bound. Under APP_ENV=production an ORM load of the
    Account would fail-close on owner_email (the original 500). The resolver MUST
    find the account via the blind index + raw projection instead."""
    monkeypatch.setattr(settings, "app_env", "production")
    req = _valid_request(owner_email="owner@emailresolve.com")
    result = await signup(db_session, req)
    tenant_id, account_id = result["tenant_id"], result["account_id"]

    # Fresh request: no tenant key bound (conftest cleared it; assert explicitly).
    set_tenant_key(None)

    engine = get_engine()
    # Proof the trap is real: a naive ORM load under the same conditions
    # fail-closes. This is the exact 500 the resolver must sidestep.
    async with AsyncSession(engine) as session:
        with pytest.raises(RuntimeError, match="tenant key"):
            (await session.execute(select(Account).where(Account.id == account_id))).scalar_one()

    # The resolver returns the account anyway — raw projection, no ORM
    # materialization of encrypted columns.
    async with AsyncSession(engine) as session:
        account = await InboundEmailProcessor(SessionCrud(session))._resolve_account(
            "owner@emailresolve.com"
        )
    assert account is not None, "blind-index lookup failed — inbound would 500 in prod"
    assert str(account["tenant_id"]) == str(tenant_id)
    assert str(account["id"]) == str(account_id)


@pytest.mark.asyncio
async def test_email_resolver_returns_none_for_unknown_address(db_session, monkeypatch):
    """An address no account owns resolves to None (→ 'no_account'), never raises."""
    monkeypatch.setattr(settings, "app_env", "production")
    await signup(db_session, _valid_request(owner_email="owner@known.com"))
    set_tenant_key(None)

    engine = get_engine()
    async with AsyncSession(engine) as session:
        account = await InboundEmailProcessor(SessionCrud(session))._resolve_account(
            "nobody@nonexistent.com"
        )
    assert account is None


@pytest.mark.asyncio
async def test_whatsapp_resolver_finds_account_by_phone_under_prod(db_session, monkeypatch):
    """WhatsApp channel: ``whatsapp_phone`` is plain (equality works) but an ORM
    load would still materialize owner_email and fail-close. The resolver uses a
    raw projection, so it finds the account under production without a tenant key."""
    monkeypatch.setattr(settings, "app_env", "production")
    result = await signup(db_session, _valid_request(owner_email="owner@wa1f.com"))
    tenant_id, account_id = result["tenant_id"], result["account_id"]
    phone = "+15551234567"

    # signup does not set whatsapp_phone; bind the tenant and add one (mirrors a
    # portal update), then clear the key to simulate a fresh inbound request.
    await set_tenant_context(db_session, tenant_id)
    await db_session.execute(
        text("UPDATE accounts SET whatsapp_phone = :p WHERE id = :id"),
        {"p": phone, "id": account_id},
    )
    await db_session.commit()
    set_tenant_key(None)

    engine = get_engine()
    async with AsyncSession(engine) as session:
        account = await InboundWhatsAppProcessor(SessionCrud(session))._resolve_account(phone)
    assert account is not None
    assert str(account["tenant_id"]) == str(tenant_id)
    assert str(account["id"]) == str(account_id)
