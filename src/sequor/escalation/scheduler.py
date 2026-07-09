"""SLAScheduler — periodic SLA breach checker running as an asyncio task."""

from __future__ import annotations

import asyncio
import uuid
from typing import Any

import structlog

from sequor.config import settings
from sequor.escalation.service import EscalationService

logger = structlog.get_logger()


class SLAScheduler:
    """Periodic SLA breach checker.

    Each tick enumerates tenants, finds breached escalations per tenant,
    and processes them via EscalationService.process_breached_escalation().
    """

    def __init__(
        self,
        escalation_service: EscalationService,
        db_express: Any,
        interval_seconds: int | None = None,
    ) -> None:
        self._service = escalation_service
        self._db = db_express
        self._interval = interval_seconds or settings.scheduler_interval_seconds
        self._task: asyncio.Task | None = None
        self._lock = asyncio.Lock()

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            logger.warning("scheduler.already_running")
            return
        self._task = asyncio.create_task(self._run_loop())
        logger.info("scheduler.started", interval_seconds=self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("scheduler.stop_timeout")
        self._task = None
        logger.info("scheduler.stopped")

    async def _run_loop(self) -> None:
        try:
            while True:
                try:
                    await self._tick()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # A transient failure (e.g. the tenant-enumeration read fails
                    # on a DB blip) MUST NOT kill the loop — silently-stopped
                    # background work is the worst failure mode for a scheduler.
                    # Log + keep ticking.
                    logger.exception("scheduler.tick_failed")
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            raise

    async def _tick(self) -> None:
        async with self._lock:
            tenants = await self._db.list("Tenant", {})
            logger.info("scheduler.tick.start", tenant_count=len(tenants))
            total_processed = 0
            for tenant in tenants:
                try:
                    # Bind the service's session to this tenant BEFORE any
                    # encrypted-column read/write (BackupContact.email,
                    # Account.owner_email, Message.*, Escalation.resolution_summary
                    # are all EncryptedString). Without this the master-key-set
                    # (production) tick fail-closes per tenant.
                    await self._service.bind_tenant(uuid.UUID(str(tenant["id"])))
                    breached = await self._service.find_breached_escalations(
                        tenant_id=uuid.UUID(str(tenant["id"]))
                    )
                    for esc in breached:
                        await self._service.process_breached_escalation(esc)
                        total_processed += 1
                    # Per-tenant commit boundary. The RLS GUC is set transaction-
                    # local (SET LOCAL via bind_tenant), so committing here:
                    #   (a) clears the GUC — the next tenant starts a fresh
                    #       transaction with no tenant bound, then rebinds;
                    #   (b) isolates a tenant's writes from the next tenant's
                    #       (a failure rolled back below cannot un-roll a tenant
                    #       that already committed).
                    # Without this boundary one session-spanning transaction would
                    # either hold the first tenant's GUC stale across the loop or,
                    # under autocommit, lose the GUC between statements.
                    await self._db.commit()
                except Exception:
                    # Roll back this tenant's partial work so the next tenant's
                    # bind_tenant starts from a clean transaction (the GUC and
                    # any unflushed writes do not leak forward).
                    try:
                        await self._db.rollback()
                    except Exception:
                        logger.exception(
                            "scheduler.tenant_rollback_failed", tenant_id=tenant.get("id")
                        )
                    logger.exception(
                        "scheduler.tenant_error",
                        tenant_id=tenant.get("id"),
                    )
            logger.info("scheduler.tick.complete", total_processed=total_processed)


async def create_scheduler(
    escalation_service: EscalationService,
    db_express: Any,
    interval_seconds: int | None = None,
) -> SLAScheduler | None:
    """Create and start the SLA scheduler if enabled in config.

    Returns the started scheduler (caller should store it and call
    ``await scheduler.stop()`` on shutdown), or None if disabled.

    Usage in FastAPI lifespan::

        from sequor.escalation.scheduler import create_scheduler

        @asynccontextmanager
        async def lifespan(app):
            scheduler = await create_scheduler(service, db.express)
            yield
            if scheduler:
                await scheduler.stop()
    """
    if not settings.scheduler_enabled:
        logger.info("scheduler.disabled")
        return None

    scheduler = SLAScheduler(escalation_service, db_express, interval_seconds)
    await scheduler.start()
    return scheduler
