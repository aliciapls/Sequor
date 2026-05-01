"""Billing service — Stripe integration for subscription management.

Handles checkout session creation, webhook processing, and plan upgrades.
Tenant.plan is the source of truth for subscription status, updated by
webhook events from Stripe.
"""

import structlog
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from sequor.db.models import Tenant, TenantPlan
from sequor.schemas import StripeWebhookEvent

logger = structlog.get_logger()

STARTER_PRICE_ID = "price_starter_monthly"
STARTER_PRICE_SGD = 20


async def create_checkout_session(
    tenant_id: UUID,
    owner_email: str,
    success_url: str,
    cancel_url: str,
) -> str:
    """Create a Stripe Checkout session for the Starter plan.

    Returns the checkout session URL for the user to complete payment.
    """
    from sequor.config import settings

    if not settings.stripe_api_key:
        logger.warning("billing.checkout.skip", reason="no stripe_api_key")
        return ""

    import stripe
    stripe.api_key = settings.stripe_api_key

    session = stripe.checkout.Session.create(
        mode="subscription",
        payment_method_types=["card"],
        customer_email=owner_email,
        line_items=[{
            "price": settings.stripe_starter_price_id,
            "quantity": 1,
        }],
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"tenant_id": str(tenant_id)},
    )
    logger.info("billing.checkout.created", tenant_id=str(tenant_id), session_id=session.id)
    return session.url


async def handle_webhook(session: AsyncSession, event: StripeWebhookEvent) -> None:
    """Process a Stripe webhook event and update tenant plan.

    Handles: checkout.session.completed, customer.subscription.updated,
    customer.subscription.deleted, invoice.payment_failed.
    """
    event_type = event.type
    logger.info("billing.webhook.received", type=event_type, event_id=event.id)

    if event_type == "checkout.session.completed":
        await _handle_checkout_completed(session, event)
    elif event_type == "customer.subscription.updated":
        await _handle_subscription_updated(session, event)
    elif event_type == "customer.subscription.deleted":
        await _handle_subscription_deleted(session, event)
    elif event_type == "invoice.payment_failed":
        await _handle_payment_failed(session, event)
    else:
        logger.info("billing.webhook.ignored", type=event_type)


async def _get_tenant_from_metadata(session: AsyncSession, event: StripeWebhookEvent) -> Tenant | None:
    """Extract tenant_id from event metadata and load the tenant."""
    data = event.data
    # Try object-level metadata first
    obj = data.get("object", data)
    metadata = obj.get("metadata", {})
    tenant_id_str = metadata.get("tenant_id")

    if not tenant_id_str:
        logger.warning("billing.webhook.no_tenant_id", event_id=event.id)
        return None

    try:
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        logger.warning("billing.webhook.invalid_tenant_id", tenant_id=tenant_id_str)
        return None

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        logger.warning("billing.webhook.tenant_not_found", tenant_id=tenant_id_str)
    return tenant


async def _handle_checkout_completed(session: AsyncSession, event: StripeWebhookEvent) -> None:
    tenant = await _get_tenant_from_metadata(session, event)
    if not tenant:
        return

    tenant.plan = TenantPlan.starter
    tid = str(tenant.id)
    session.add(tenant)
    await session.commit()
    logger.info("billing.plan.upgraded", tenant_id=tid, plan="starter")


async def _handle_subscription_updated(session: AsyncSession, event: StripeWebhookEvent) -> None:
    data = event.data
    obj = data.get("object", data)
    status = obj.get("status", "")
    metadata = obj.get("metadata", {})

    tenant_id_str = metadata.get("tenant_id")
    if not tenant_id_str:
        return

    try:
        tenant_id = UUID(tenant_id_str)
    except ValueError:
        return

    tenant = await session.get(Tenant, tenant_id)
    if not tenant:
        return

    if status == "active":
        tenant.plan = TenantPlan.starter
    elif status == "past_due":
        logger.warning("billing.subscription.past_due", tenant_id=str(tenant.id))
    elif status == "canceled":
        tenant.plan = TenantPlan.free

    session.add(tenant)
    await session.commit()


async def _handle_subscription_deleted(session: AsyncSession, event: StripeWebhookEvent) -> None:
    tenant = await _get_tenant_from_metadata(session, event)
    if not tenant:
        return

    tenant.plan = TenantPlan.free
    tid = str(tenant.id)
    session.add(tenant)
    await session.commit()
    logger.info("billing.plan.downgraded", tenant_id=tid, plan="free")


async def _handle_payment_failed(session: AsyncSession, event: StripeWebhookEvent) -> None:
    """Payment failed — log but don't immediately downgrade (7-day grace period)."""
    data = event.data
    obj = data.get("object", data)
    lines = obj.get("lines", {}).get("data", [])

    # Attempt to find tenant_id from subscription metadata
    tenant = await _get_tenant_from_metadata(session, event)
    if not tenant:
        return

    logger.warning(
        "billing.payment_failed",
        tenant_id=str(tenant.id),
        plan=tenant.plan.value,
        note="Grace period: plan unchanged for 7 days",
    )
