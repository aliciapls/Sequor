# 0019 — GAP: shard 1d deferred hardening (4 items, non-blocking)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: redteam close-out (shard 1d).
Relates to: 0018 (1d convergence). All items are non-blocking for 1d; tracked for a
follow-up "1d-tail" sweep. Two are PDPA-scope extensions (Free-tier Contact/Document);
two are LOW hardening polish.

## The deferrals

1. **Free-tier `Contact` (7d) purge — NOT built** (PDPA scope gap).
   `data-model.md` § "Data Retention Schedule" lists Contact profiles at Free=7d. The
   shipped job does not purge Contact on any plan. `Contact` has NO `created_at` column
   (only `last_seen`, which is last activity — not creation; a contact messaged yesterday
   but created 30d ago has `last_seen=yesterday`, so `last_seen` would purge active contacts
   and keep inactive new ones — the wrong semantics). Fix needs a schema decision: add a
   `created_at` to `Contact` (migration) and purge by it, OR define Contact retention
   relative to its last message (`MAX(messages.received_at)`). Cascade note: `Message.contact_id`
   is `ondelete=CASCADE`, so a Contact purge cascades its messages + their escalations —
   consistent with Free-tier retention (all expire at 7d together) but a bigger semantic
   step than the time-bounded-tables purge. Recommend: add `Contact.created_at` (migration)
   - a Free-tier-only purge, with the cascade explicitly designed + tested.

2. **Free-tier `Document` (7d) purge — NOT built** (PDPA scope gap).
   `Document` is the tenant's uploaded RAG knowledge base. `Document.created_at` EXISTS
   (`models.py` ~line 576), so the timestamp is fine. The blocker is the cascade: purging a
   Document must also purge its `DocumentChunk` rows + their vector embeddings (the pgvector
   index) + any blob storage. The chunk/embedding purge path is not yet wired (the erasure
   flow in `compliance.py` notes the same gap — DocumentChunk has no contact linkage, and
   the RAG index purge is a separate surface). Fix: build the Document → chunks → embeddings
   cascade (mirrors erasure step 7 "RAG index: Document content purged from vector index and
   blob storage"), then add the Free-tier 7d Document purge on top.

3. **Unbounded tenant enumeration** (R2-security LOW — scalability, not correctness).
   `run_retention_purge_once` loads every `Tenant` row via `select(Tenant.id, Tenant.plan).all()`
   before iterating. For a SaaS with thousands of tenants this is a per-sweep memory spike.
   Matches the `SLAScheduler` + admin-backfill pattern (both also load-all). Fix: stream via
   `yield_per(500)` or `enum_session.stream(...)`. Non-blocking — nightly job, moderate
   tenant count. Defer until tenant count makes it matter.

4. **`stop()` 10s timeout may truncate a running bulk DELETE** (R1-reviewer LOW).
   `RetentionPurgeScheduler.stop()` cancels + `await asyncio.wait_for(self._task, timeout=10)`.
   Cancellation lands at the next await boundary, so this is usually fine, but a single huge
   bulk DELETE on a slow connection could hold across the 10s; if the timeout fires the task
   may still finalize in the background while `_task` is set to `None`. Not a correctness bug
   (process is shutting down), but worth documenting or making the timeout configurable.

## Non-deferrals (fixed in-session, recorded for the audit trail)

- Cascade ordering (R1 HIGH) → leaf-first `_PURGE_TABLES` + regression test (`949479d`).
- `_run_loop` silent death (R1 HIGH) → per-tick try/except + keep ticking, retention + SLA (`949479d`).
- Partial-failure WARN (R1 MED) → `retention.purge.sweep.partial_failure` (`949479d`).
- Scheduler lifecycle test (R1 MED) → `test_retention_scheduler_wiring.py` (`949479d`).
- Per-tenant `run_id` correlation (R2 MINOR) → threaded into `purge_expired_records` (`e96bf45`).
- `now` trust-boundary docstring; unknown-plan fail-safe pin (`949479d`).

## Why these are deferrable

Items 1–2 are PDPA-scope EXTENSIONS (Free-tier Contact/Document), not defects in what shipped
— the shipped job closes over-retention for the highest-sensitivity PII (message content) and
the accountability records (audit, escalation). Items 3–4 are LOW hardening polish with no
correctness or security impact. None block prod enablement of the shipped job.
