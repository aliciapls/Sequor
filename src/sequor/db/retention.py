"""PDPA retention-purge job (DEVIATIONS §F2, shard 1d).

A scheduled job that auto-deletes records older than the per-tier retention
period on the time-bounded tenant-scoped tables, writing one summary audit
entry per tenant per sweep. Closes the PDPA over-retention gap documented in
``data-model.md`` § "Data Retention Schedule": until this module shipped,
retention periods were policy-defined but nothing machine-enforced them —
customer PII was kept indefinitely past the stated retention floor.

Scope (this shard): the three uniformly-time-bounded tables — ``Message``,
``AuditEntry``, ``Escalation`` — purged by their creation timestamp at the
per-plan retention (7d / 90d / 365d / 730d). Free-tier ``Contact`` (7d) and
``Document`` (7d) are deferred to the 1d-tail follow-up: ``Contact`` has no
``created_at`` column (needs a schema decision; ``last_seen`` is last activity,
not creation, so it is the wrong key), and ``Document`` purge requires the RAG
chunk/embedding cascade. Tracked in journal/<NNNN> + the wave plan.

Per-tenant isolation: the sweep enumerates tenants and binds each in a FRESH
``AsyncSession`` (mirroring the startup admin-backfill pattern), so one tenant's
RLS GUC + encryption key can never leak into another's purge window.
``bind_tenant`` is load-bearing here for the same reason it is on every other
tenant-scoped path: it sets the ``app.current_tenant`` GUC so the
``tenant_isolation`` RLS policy scopes the DELETE. Without it, under a
non-owner app role the policy fail-closes and the DELETE silently purges zero
rows — the same trap shard 1c documented for portal/inbound reads. An explicit
``WHERE tenant_id = :tid`` filter is applied too (defense-in-depth alongside
RLS, and the primary scope when tests run as the superuser, which bypasses RLS).

The DELETE itself does not read encrypted columns (it filters on ``tenant_id``
+ a timestamp), so the tenant AES key is not strictly needed for the delete;
``bind_tenant`` is still called because RLS enforcement is independent of
encryption and applies in both prod (key + GUC) and dev (GUC only) branches.
"""

from __future__ import annotations

import asyncio
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, cast

import structlog
from sqlalchemy import delete, select
from sqlalchemy.engine import CursorResult
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession

from sequor.config import settings
from sequor.db.audit import audit
from sequor.db.models import AuditEntry, Escalation, Message, Tenant, TenantPlan
from sequor.db.tenant_context import bind_tenant

logger = structlog.get_logger()


# Per-plan retention in DAYS, keyed by ``TenantPlan`` value, per time-bounded
# table. A table absent from a plan's entry (or a 0/None value) means "until
# deleted" — no time-based purge for that table on that plan. Source of truth:
# ``specs/data-model.md`` § "Data Retention Schedule". 12mo→365d, 24mo→730d
# (the conservative day-count PDPA floors; a calendar "month" boundary is ±1d
# of these, which is well inside the enforcement granularity that matters).
RETENTION_DAYS: dict[str, dict[str, int]] = {
    TenantPlan.free.value: {
        "messages": 7,
        "audit_entries": 7,
        "escalations": 7,
    },
    TenantPlan.starter.value: {
        "messages": 90,
        "audit_entries": 90,
        "escalations": 90,
    },
    TenantPlan.professional.value: {
        "messages": 365,
        "audit_entries": 365,
        "escalations": 365,
    },
    TenantPlan.enterprise.value: {
        "messages": 730,
        "audit_entries": 730,
        "escalations": 730,
    },
}

# ``(table key, ORM model, creation-timestamp column)`` for each purged table.
# The timestamp column is the row's creation time used to compute its age. Keys
# match ``RETENTION_DAYS`` so a single lookup drives the cutoff per table.
#
# Order is LEAF-FIRST. ``Escalation.message_id`` is ``ondelete=CASCADE``: if
# Messages were purged first, Postgres would cascade-delete the old Escalations
# BEFORE the explicit ``delete(Escalation)`` ran, so that statement's rowcount
# would be 0 and the audit metadata would undercount escalations removed. Purging
# escalations first captures the true count; the later Message purge then cascades
# only the already-counted rows (plus uncounted children like Classification /
# Response, which are transient derived data, not retention-tracked).
# (``AuditEntry.message_id`` is ``ondelete=SET NULL``, so audit rows survive a
# Message purge uncounted-but-intact — order is irrelevant for them.)
_PURGE_TABLES: list[tuple[str, type, Any]] = [
    ("escalations", Escalation, Escalation.assigned_at),
    ("audit_entries", AuditEntry, AuditEntry.occurred_at),
    ("messages", Message, Message.received_at),
]


def _retention_for(plan: TenantPlan | str) -> dict[str, int]:
    """Return the ``{table: days}`` retention map for *plan* (empty = unknown plan → purge nothing)."""
    plan_value = plan.value if isinstance(plan, TenantPlan) else str(plan)
    return RETENTION_DAYS.get(plan_value, {})


async def purge_expired_records(
    session: AsyncSession,
    tenant_id: uuid.UUID,
    plan: TenantPlan | str,
    *,
    now: datetime | None = None,
) -> dict[str, Any]:
    """Delete this tenant's expired rows per the plan's retention schedule.

    Runs one parameterized bulk ``DELETE`` per time-bounded table, scoped to
    ``tenant_id`` and rows whose creation timestamp precedes the plan's cutoff.
    Writes ONE summary ``AuditEntry`` if any rows were purged (the purge log is
    itself an audit row, subject to the same retention — a self-cleaning
    trail). Caller MUST have already bound *session* to *tenant_id* via
    ``bind_tenant`` (encryption key + RLS GUC).

    ``now`` defaults to the real current time; tests pass an explicit value so
    seeded "old" rows are deterministic relative to the cutoff. **Trust boundary:**
    *now* is the caller's reference time — a far-future value over-purges, so only
    trusted code (the scheduler tick / a test harness) supplies it; the production
    default is ``datetime.now(timezone.utc)``.

    Returns ``{"tenant_id", "plan", "purged": {table: count}, "cutoffs": {table: iso}}``.
    """
    now = now or datetime.now(timezone.utc)
    retention = _retention_for(plan)
    plan_value = plan.value if isinstance(plan, TenantPlan) else str(plan)

    purged: dict[str, int] = {}
    cutoffs: dict[str, str] = {}
    for table_key, model, ts_col in _PURGE_TABLES:
        days = retention.get(table_key)
        if not days:  # absent or 0 → "until deleted" → skip this table
            continue
        cutoff = now - timedelta(days=days)
        cutoffs[table_key] = cutoff.isoformat()
        stmt = (
            delete(model)
            .where(model.tenant_id == tenant_id, ts_col < cutoff)
            .execution_options(synchronize_session=False)
        )
        result = cast(CursorResult, await session.execute(stmt))
        # rowcount is reliable for bulk DELETE on psycopg3 (the async driver in
        # use); guard the ``or 0`` for any driver that reports -1 (unknown).
        purged[table_key] = max(0, result.rowcount or 0)

    if any(count for count in purged.values()):
        await audit(
            session,
            tenant_id=tenant_id,
            action="retention.purge",
            doer_type="system",
            doer_id=tenant_id,
            recipient_type="system",
            recipient_id=tenant_id,
            metadata={"plan": plan_value, "purged": purged, "cutoffs": cutoffs},
        )
    await session.flush()
    logger.info(
        "retention.purge.tenant",
        tenant_id=str(tenant_id),
        plan=plan_value,
        purged=purged,
    )
    return {
        "tenant_id": str(tenant_id),
        "plan": plan_value,
        "purged": purged,
        "cutoffs": cutoffs,
    }


async def run_retention_purge_once(
    engine: AsyncEngine | None = None,
    *,
    now: datetime | None = None,
) -> list[dict[str, Any]]:
    """Sweep every tenant and purge its expired records (the nightly job body).

    One fresh ``AsyncSession`` per tenant (the startup admin-backfill pattern):
    each tenant is bound, purged, and committed in isolation, so a failure on
    one tenant rolls back only that tenant and the GUC/encryption key never
    crosses tenants. Returns the per-tenant summaries.

    This is the direct Tier-2 entry point AND the body the periodic
    ``RetentionPurgeScheduler`` calls each tick.
    """
    from sequor.db.database import get_engine

    engine = engine or get_engine()
    now = now or datetime.now(timezone.utc)
    summaries: list[dict[str, Any]] = []

    # A short run_id ties one sweep's start/per-tenant/complete log lines together
    # in the aggregator (a background scheduler has no HTTP request_id to borrow).
    run_logger = logger.bind(run_id=uuid.uuid4().hex[:8])

    # Enumerate tenants in a throwaway session. ``Tenant`` is the root entity
    # (not RLS-scoped — it IS the tenant), so an unbound read returns every
    # tenant, matching the SLA scheduler + admin-backfill enumeration.
    async with AsyncSession(engine) as enum_session:
        tenant_rows = (await enum_session.execute(select(Tenant.id, Tenant.plan))).all()

    run_logger.info("retention.purge.sweep.start", tenant_count=len(tenant_rows))
    for tenant_id, plan in tenant_rows:
        try:
            async with AsyncSession(engine) as session:
                await bind_tenant(session, tenant_id)
                summary = await purge_expired_records(session, tenant_id, plan, now=now)
                await session.commit()
                summaries.append(summary)
        except Exception:
            # Per-tenant isolation: a failure here rolls back only this tenant
            # (the AsyncSession context manager discards the uncommitted txn).
            run_logger.exception("retention.purge.tenant_failed", tenant_id=str(tenant_id))
    totals = {
        t: sum(s["purged"].get(t, 0) for s in summaries)
        for t in ("messages", "audit_entries", "escalations")
    }
    failed = len(tenant_rows) - len(summaries)
    if failed > 0:
        # Bulk-op partial-failure summary (observability Rule 7): without this a
        # per-tenant failure is visible only in the exception lines, not in the
        # sweep-complete tally an operator scans for.
        run_logger.warning(
            "retention.purge.sweep.partial_failure",
            attempted=len(tenant_rows),
            failed=failed,
            tenants_processed=len(summaries),
        )
    run_logger.info(
        "retention.purge.sweep.complete",
        tenants_processed=len(summaries),
        tenants_failed=failed,
        total_purged=totals,
    )
    return summaries


class RetentionPurgeScheduler:
    """Periodic PDPA retention-purge job (mirrors ``SLAScheduler``'s lifecycle).

    Each tick runs :func:`run_retention_purge_once` — a full sweep over every
    tenant. Defaults to daily (``settings.retention_purge_interval_seconds``)
    per the spec's "nightly batch job". The lifecycle (start / stop / _run_loop)
    intentionally mirrors ``SLAScheduler`` so the app lifespan can own and
    cleanly shut down both background jobs the same way.
    """

    def __init__(
        self,
        engine: AsyncEngine | None = None,
        interval_seconds: int | None = None,
    ) -> None:
        from sequor.db.database import get_engine

        self._engine = engine or get_engine()
        self._interval = interval_seconds or settings.retention_purge_interval_seconds
        self._task: asyncio.Task[None] | None = None

    async def start(self) -> None:
        if self._task is not None and not self._task.done():
            logger.warning("retention.scheduler.already_running")
            return
        self._task = asyncio.create_task(self._run_loop())
        logger.info("retention.scheduler.started", interval_seconds=self._interval)

    async def stop(self) -> None:
        if self._task is None:
            return
        self._task.cancel()
        try:
            await asyncio.wait_for(self._task, timeout=10)
        except asyncio.CancelledError:
            pass
        except asyncio.TimeoutError:
            logger.warning("retention.scheduler.stop_timeout")
        self._task = None
        logger.info("retention.scheduler.stopped")

    async def _run_loop(self) -> None:
        try:
            while True:
                try:
                    await self._tick()
                except asyncio.CancelledError:
                    raise
                except Exception:
                    # A transient failure here (e.g. the tenant-enumeration read
                    # fails on a DB blip, or get_engine() raises) MUST NOT kill
                    # the loop — for a destructive PDPA job, silent cessation is
                    # the worst failure mode: compliance believes the purge runs
                    # while expired PII accumulates. Log + keep ticking.
                    logger.exception("retention.scheduler.tick_failed")
                await asyncio.sleep(self._interval)
        except asyncio.CancelledError:
            raise

    async def _tick(self) -> None:
        await run_retention_purge_once(self._engine)


async def create_retention_scheduler(
    engine: AsyncEngine | None = None,
    interval_seconds: int | None = None,
) -> RetentionPurgeScheduler | None:
    """Create and start the retention-purge scheduler if enabled in config.

    Returns the started scheduler (caller stores it and calls
    ``await scheduler.stop()`` on shutdown), or ``None`` if disabled. Mirrors
    ``escalation.scheduler.create_scheduler``.
    """
    if not settings.retention_purge_enabled:
        logger.info("retention.scheduler.disabled")
        return None

    scheduler = RetentionPurgeScheduler(engine, interval_seconds)
    await scheduler.start()
    return scheduler
