# 0018 — BUILD: shard 1d PDPA retention-purge job (redteam-CONVERGED)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: implement → redteam (shard 1d).
Value-anchor: `specs/data-model.md` § "Data Retention Schedule" (PDPA over-retention —
customer PII kept indefinitely past the stated retention floor). User-ratified wave plan
2026-07-05. Closes `DEVIATIONS.md` §F2 (core).

## What shipped

`src/sequor/db/retention.py` — a per-tenant sweep that bulk-deletes the three uniformly
time-bounded tables past their per-plan retention:

- `RETENTION_DAYS` — `{free: 7d, starter: 90d, professional: 365d, enterprise: 730d}` ×
  `{messages, audit_entries, escalations}`. Source of truth: `data-model.md`.
- `purge_expired_records(session, tenant_id, plan, *, now, run_id)` — one parameterized
  ORM `DELETE` per table, scoped `WHERE tenant_id = :tid AND <ts_col> < cutoff`; writes
  ONE summary `AuditEntry(action="retention.purge")` per purged tenant (the purge log is
  itself an audit row, subject to the same retention — a self-cleaning trail).
- `run_retention_purge_once(engine, *, now)` — the sweep body. Fresh `AsyncSession` +
  `bind_tenant` per tenant (the GUC/key never crosses tenants); per-tenant commit boundary;
  per-tenant failure rolls back only that tenant. `run_id` correlation on every sweep log line.
- `RetentionPurgeScheduler` + `create_retention_scheduler` — periodic loop mirroring
  `SLAScheduler`; wired into `_app_lifespan` (onboarding/app.py). **Opt-in**
  (`retention_purge_enabled`, default OFF) — unit tests boot the app via TestClient and the
  destructive loop must not auto-run until the deploy role/env is configured (RLS is
  no-FORCE → app connects as a non-owner role).

`_PURGE_TABLES` is **leaf-first** (escalations → audit_entries → messages): `Escalation.message_id`
is `ondelete=CASCADE`, so a messages-first order would cascade-delete old escalations before the
explicit `delete(Escalation)` ran and undercount the audit metadata. (`AuditEntry.message_id` is
`ondelete=SET NULL`, so its order is irrelevant.) Pinned by a regression test.

`src/sequor/escalation/scheduler.py` — same-class fix: `SLAScheduler._run_loop` now catches
transient `Exception` per-tick + keeps ticking (re-raises `CancelledError`). The retention
scheduler got the identical fix; without it a DB blip during tenant enumeration would silently
kill the compliance loop.

## Tier-2 evidence (real sequor-test-pg pgvector, NO mocking)

`tests/integration/test_retention_purge.py` (5) + `tests/integration/test_retention_scheduler_wiring.py` (3):
per-plan cutoffs across all 4 plans; all-three-tables purge + audit-entry metadata;
cross-tenant isolation (each tenant purged independently); cascade-ordering regression
(old esc on old msg counted, not silently cascaded); unknown-plan fail-safe (purges nothing);
scheduler factory-gate + start/tick/stop + double-start.

Full suite: **unit 421/1-xfailed, Tier-2 63/1-xfailed** (combined 484/2-xfailed). The 1 xfail
is the known R7-01 login/backup separation tripwire = shard 1e.

## Redteam convergence (3 rounds → CONVERGED)

- **R1** (reviewer + security-reviewer, both `ran:true`): security CLEAN; reviewer BLOCKED
  on 2 HIGH + 2 MED — (1) cascade ordering undercounted escalations in the audit metadata
  [the test masked it with a within-retention anchor message]; (2) `_run_loop` silently died
  on a transient DB error (compliance job quietly stops); (3) no partial-failure WARN on the
  sweep tally [observability Rule 7]; (4) `RetentionPurgeScheduler` had no lifecycle test
  [orphan/facade-manager Rule 1]. Fixed in `949479d`: leaf-first reorder + regression test;
  `_run_loop` resilience (retention + same-class SLA); partial-failure WARN; scheduler-wiring
  test; + run_id correlation, `now` trust-boundary docstring, unknown-plan pin.
- **R2** (reviewer + security-reviewer, both `ran:true`): both CLEAN on all load-bearing axes
  (all 4 round-1 fixes CONFIRMED-FIXED against schema ground truth). 1 MINOR: the per-tenant
  success log `retention.purge.tenant` used the unbound module logger, missing the sweep's
  `run_id`. Fixed in `e96bf45` (threaded `run_id` into `purge_expired_records`).
- **Final sign-off** (reviewer, `ran:true`): CONFIRMED-FIXED, zero remaining findings,
  **"SHARD 1d REDTEAM-CONVERGED."**

## Receipts

- Build: `8d87244` (feat). Round-1 fixes: `949479d`. Round-2 polish: `e96bf45` (HEAD).
- Convergence receipt: commit `e96bf45` + Tier-2 `8 passed` (retention + wiring).
- Spec: `specs/DEVIATIONS.md` §F2 relabeled "PARTIAL (core shipped)"; `specs/data-model.md`
  retention-enforcement statement updated to describe what shipped (3 tables enforced;
  Contact/Document deferred → 0019).

## Deploy note

The purge is **opt-in** (`RETENTION_PURGE_ENABLED=true`) and runs as a daily in-process asyncio
scheduler (`retention_purge_interval_seconds`, default 86400). Enable only after the deploy
connects as a non-owner, non-`BYPASSRLS` role (RLS is no-FORCE — `data-model.md` § "Security
by Design"); under the owner role RLS is bypassed and the explicit `WHERE tenant_id` is the
sole scoping filter (still correct, but the defense-in-depth layer is inert).
