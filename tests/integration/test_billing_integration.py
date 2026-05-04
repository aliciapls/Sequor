"""Tests for Stripe billing webhook handling.

Integration tests that verify webhook events update Tenant.plan correctly.
"""

import pytest
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession

from sequor.billing.service import handle_webhook
from sequor.db.database import close_engine, get_engine, init_db
from sequor.db.models import Tenant, TenantPlan
from sequor.schemas import StripeWebhookEvent


@pytest.fixture
async def db_session():
    engine = get_engine()
    await init_db()
    async with AsyncSession(engine) as session:
        yield session
    await close_engine()


def _webhook(event_type: str, tenant_id: str = None, **extra) -> StripeWebhookEvent:
    data = {"object": {"metadata": {}}}
    if tenant_id:
        data["object"]["metadata"]["tenant_id"] = tenant_id
    data["object"].update(extra)
    return StripeWebhookEvent(
        id=f"evt_test_{uuid4().hex[:12]}",
        type=event_type,
        data=data,
    )


class TestCheckoutCompleted:
    """checkout.session.completed upgrades tenant to starter."""

    @pytest.mark.asyncio
    async def test_upgrades_to_starter(self, db_session):
        from sequor.db.models import Tenant
        tenant = Tenant(
            name="Test", email_domain="test.com", plan="free", settings={},
        )
        db_session.add(tenant)
        await db_session.flush()
        tid = tenant.id
        await db_session.commit()

        event = _webhook("checkout.session.completed", tenant_id=str(tid))
        await handle_webhook(db_session, event)

        updated = await db_session.get(Tenant, tid)
        assert updated.plan == TenantPlan.starter

    @pytest.mark.asyncio
    async def test_ignores_missing_tenant(self, db_session):
        event = _webhook("checkout.session.completed", tenant_id=str(uuid4()))
        # Should not raise
        await handle_webhook(db_session, event)

    @pytest.mark.asyncio
    async def test_ignores_no_metadata(self, db_session):
        event = StripeWebhookEvent(id="evt_1", type="checkout.session.completed", data={})
        await handle_webhook(db_session, event)


class TestSubscriptionDeleted:
    """customer.subscription.deleted downgrades to free."""

    @pytest.mark.asyncio
    async def test_downgrades_to_free(self, db_session):
        from sequor.db.models import Tenant
        tenant = Tenant(
            name="Test", email_domain="test2.com", plan="starter", settings={},
        )
        db_session.add(tenant)
        await db_session.flush()
        tid = tenant.id
        await db_session.commit()

        event = _webhook("customer.subscription.deleted", tenant_id=str(tid))
        await handle_webhook(db_session, event)

        updated = await db_session.get(Tenant, tid)
        assert updated.plan == TenantPlan.free


class TestSubscriptionUpdated:
    """customer.subscription.updated reflects status in plan."""

    @pytest.mark.asyncio
    async def test_active_sets_starter(self, db_session):
        from sequor.db.models import Tenant
        tenant = Tenant(
            name="Test", email_domain="test3.com", plan="free", settings={},
        )
        db_session.add(tenant)
        await db_session.flush()
        tid = tenant.id
        await db_session.commit()

        event = _webhook(
            "customer.subscription.updated",
            tenant_id=str(tid),
            status="active",
        )
        await handle_webhook(db_session, event)

        updated = await db_session.get(Tenant, tid)
        assert updated.plan == TenantPlan.starter

    @pytest.mark.asyncio
    async def test_canceled_sets_free(self, db_session):
        from sequor.db.models import Tenant
        tenant = Tenant(
            name="Test", email_domain="test4.com", plan="starter", settings={},
        )
        db_session.add(tenant)
        await db_session.flush()
        tid = tenant.id
        await db_session.commit()

        event = _webhook(
            "customer.subscription.updated",
            tenant_id=str(tid),
            status="canceled",
        )
        await handle_webhook(db_session, event)

        updated = await db_session.get(Tenant, tid)
        assert updated.plan == TenantPlan.free


class TestPaymentFailed:
    """invoice.payment_failed logs but does not downgrade (grace period)."""

    @pytest.mark.asyncio
    async def test_plan_unchanged_on_payment_failure(self, db_session):
        from sequor.db.models import Tenant
        tenant = Tenant(
            name="Test", email_domain="test5.com", plan="starter", settings={},
        )
        db_session.add(tenant)
        await db_session.flush()
        tid = tenant.id
        await db_session.commit()

        event = _webhook("invoice.payment_failed", tenant_id=str(tid))
        await handle_webhook(db_session, event)

        updated = await db_session.get(Tenant, tid)
        # Grace period: plan stays starter
        assert updated.plan == TenantPlan.starter


class TestUnknownEvent:
    """Unknown webhook event types are ignored."""

    @pytest.mark.asyncio
    async def test_ignores_unknown_type(self, db_session):
        event = _webhook("customer.created", tenant_id=str(uuid4()))
        await handle_webhook(db_session, event)
        # No error raised = pass
