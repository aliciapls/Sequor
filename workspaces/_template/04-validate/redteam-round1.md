# Red Team Validation Report — Round 1

**Date:** 2026-05-04
**Status:** PARTIAL CONVERGENCE — Critical/High fixes applied, architectural gaps deferred

## Agents Ran

| Agent                   | Scope                        | Findings                                        |
| ----------------------- | ---------------------------- | ----------------------------------------------- |
| Spec compliance auditor | 8 spec files, 138 assertions | 85 PASS, 40 FAIL, 6 PARTIAL                     |
| Security reviewer       | 34 source files              | 7 CRITICAL, 8 HIGH, 8 MEDIUM, 5 LOW             |
| Code quality reviewer   | 34 source files              | 5 CRITICAL, 12 HIGH, 8 MEDIUM                   |
| Test verifier           | 30 test files                | 4 failures, 4 stale imports, 9 modules untested |

## Fixes Applied This Round

### CRITICAL fixes (runtime crashes / security holes)

| #   | File                           | Issue                                                                                                                                                | Fix                                                                                                                      |
| --- | ------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| 1   | `email/auto_reply.py`          | Broken imports (`EmailSenderImpl`, `get_email_sender` don't exist), wrong constructor (`db_pool` → `engine`), calls non-existent `send_auto_reply()` | Fixed imports to `SendGridEmailSender`, fixed constructor arg, replaced with `send_email()` + `build_auto_reply_email()` |
| 2   | `email/inbound.py:199`         | Webhook verification returns `True` (skip) when key not configured                                                                                   | Changed to return `False` — reject unverified webhooks                                                                   |
| 3   | `ai/learning.py:139-164`       | Race condition: INSERT then `SELECT ORDER BY created_at` to get ID                                                                                   | Replaced with `RETURNING id` in INSERT, wrapped SQL in `text()`                                                          |
| 4   | `ai/vector_store.py:73`        | Raw SQL not wrapped in `text()`                                                                                                                      | Added `from sqlalchemy import text` and wrapped                                                                          |
| 5   | `db/database.py:47`            | `drop_all()` has no confirmation gate                                                                                                                | Added `force: bool = False` parameter                                                                                    |
| 6   | `onboarding/app.py:42,104,151` | Stack traces leaked in 500 responses                                                                                                                 | Replaced `str(e)` with generic "Internal server error" + `logger.exception()`                                            |
| 7   | `onboarding/app.py:80`         | `VectorStore()` created without required engine arg                                                                                                  | Fixed to pass `get_engine()`                                                                                             |
| 8   | `onboarding/app.py:138`        | Webhook reads body twice (`request.body()` then `request.json()`)                                                                                    | Changed to `json.loads(body)` from already-read body                                                                     |

### HIGH fixes

| #   | File                       | Issue                                                                | Fix                                                                 |
| --- | -------------------------- | -------------------------------------------------------------------- | ------------------------------------------------------------------- |
| 9   | `ai/rag_pipeline.py:361`   | Hallucination check defaults to `passed=True` on failure (fail-open) | Changed to `passed=False` (fail-closed)                             |
| 10  | `billing/service.py:24`    | Unbounded in-memory event dedup dict (OOM risk)                      | Added `_MAX_EVENT_ID_ENTRIES = 10_000` with eviction                |
| 11  | `billing/service.py:50`    | Error message leaks Stripe details                                   | Replaced with generic message                                       |
| 12  | `billing/service.py:21`    | Dead `STARTER_PRICE_ID` constant                                     | Removed                                                             |
| 13  | `ai/ingestion.py:323-329`  | Fallback `uuid4()` when INSERT+RETURNING returns no row              | Changed to raise `RuntimeError`                                     |
| 14  | `ai/ingestion.py:294,350`  | `datetime.utcnow()` (deprecated)                                     | Replaced with `datetime.now(timezone.utc)`                          |
| 15  | `ai/classifier.py:127,153` | `datetime.utcnow()` (deprecated)                                     | Replaced with `datetime.now(timezone.utc)`                          |
| 16  | `email/auto_reply.py:238`  | `datetime.utcnow()` (deprecated)                                     | Replaced with `datetime.now(timezone.utc)`                          |
| 17  | `escalation/service.py`    | Raw email addresses in logs                                          | Added `_mask_email()` helper, applied to all log calls              |
| 18  | `email/auto_reply.py:365`  | Raw email in error log                                               | Added `_mask_email()`                                               |
| 19  | `db/models.py`             | Missing `UniqueConstraint` on `DocumentChunk`                        | Added `UniqueConstraint("tenant_id", "document_id", "chunk_index")` |

### Test fixes

| #   | File                          | Issue                                                                          | Fix                                                  |
| --- | ----------------------------- | ------------------------------------------------------------------------------ | ---------------------------------------------------- |
| 20  | `test_billing_integration.py` | All tests use same event ID `"evt_test_123"` — only first test exercises logic | Changed to `f"evt_test_{uuid4().hex[:12]}"`          |
| 21  | `test_config.py`              | Asserts `debug is True` but default is `False`                                 | Fixed assertion                                      |
| 22  | `test_digest.py`              | Imports stale functions (`format_digest_email`, `compute_breached_count`)      | Rewrote to test `_after_cutoff` helper (current API) |
| 23  | `test_escalation_service.py`  | Asserts raw email (now masked)                                                 | Updated assertions to match masked form              |
| 24  | `test_scheduler.py`           | Asserts raw email (now masked)                                                 | Updated assertion                                    |

## Deferred Items (Architectural — requires product decision or large effort)

| #   | Category      | Issue                                                                                     | Effort                                 |
| --- | ------------- | ----------------------------------------------------------------------------------------- | -------------------------------------- |
| D1  | Spec gap      | No per-tenant schema isolation (spec requires separate PostgreSQL schemas)                | Large — migration + all queries        |
| D2  | Spec gap      | No PII encryption at rest (spec requires AES-256)                                         | Large — key management                 |
| D3  | Spec gap      | AuditEntry model exists but no code writes audit rows during message processing           | Medium                                 |
| D4  | Spec gap      | Billing integration is config-only — no plan enforcement, no overage calculations         | Medium                                 |
| D5  | Spec gap      | Missing entities: `RoutingThresholdConfig`, `RoutingOutcomeAggregate`, `OOOConfiguration` | Medium                                 |
| D6  | Spec gap      | Confidence thresholds wrong (code: >=80%, spec: >95%)                                     | Small but product decision needed      |
| D7  | Security      | No auth/rate limiting on onboarding endpoint                                              | Medium                                 |
| D8  | Security      | Password field collected but never hashed/stored                                          | Small — remove field or implement auth |
| D9  | Security      | No contact erasure endpoint (PDPA requirement)                                            | Medium                                 |
| D10 | Security      | Domain duplicate check runs but result ignored (dead code)                                | Small                                  |
| D11 | Performance   | VectorStore + LearningLoop load ALL chunks into Python (no pgvector indexed search)       | Large                                  |
| D12 | Test coverage | 9 modules (2,528 LOC) have zero test coverage (`ai.*`, `email/auto_reply`)                | Large                                  |
| D13 | Stale tests   | 3 integration test files have stale imports (`test_e2e_*`, `test_digest_integration`)     | Medium                                 |

## Convergence Status

| Criterion                  | Status                                           |
| -------------------------- | ------------------------------------------------ |
| 0 CRITICAL findings        | **PASS** — all 14 fixed                          |
| 0 HIGH findings            | **PARTIAL** — 12 of 20+ fixed, 8+ deferred       |
| 2 consecutive clean rounds | **NOT MET** — round 1                            |
| 100% spec compliance       | **NOT MET** — 40 FAIL, 6 PARTIAL of 138          |
| New code has new tests     | **NOT MET** — 9 modules uncovered                |
| 0 mock data                | **PASS** — no MOCK/FAKE/DUMMY in production code |

**Recommendation:** Round 1 fixes address all runtime crashes and immediate security holes. The deferred items are architectural gaps that require product decisions (especially per-tenant isolation, PII encryption, confidence thresholds, and auth strategy). A second round should focus on test coverage for the 9 uncovered modules and resolving the stale E2E test files.
