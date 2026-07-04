# /redteam Round 1 — Aggregate Summary & Dispositions

Date: 2026-07-04 · Posture: L5_DELEGATED · Scope: SHIPPED comms-wedge (`src/sequor` + `api/`) vs the 7 comms-wedge specs. Platform specs (7) + M0–M10 todos are target-state vision — out of scope.

Agents: c0 orchestrator sweep · c1 routing/channels · c2 rag/response · c3 data/onboarding/billing · c4 test-coverage · c5 security. Reports: `c{0..5}-*.md` in this dir.

## Aggregate tally (deduplicated)

| Severity | Count | Notes                                                             |
| -------- | ----- | ----------------------------------------------------------------- |
| CRITICAL | 1     | JWT auth-bypass (fixed)                                           |
| HIGH     | ~15   | 6 fixed this pass; rest are feature-gaps / test-infra (see below) |
| MEDIUM   | ~12   | deferred (security MEDs + spec gaps)                              |
| LOW      | ~11   | deferred                                                          |

## FIXED this pass — branch `fix/redteam-r1-security-correctness` (defects under any convergence option)

| ID              | Sev      | Fix                                                                                                                                                                     | File                     |
| --------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------ |
| c5-CRIT / c0-H1 | CRITICAL | JWT fail-closed: no constant-secret fallback outside `app_env=development`; ≥32-byte warn                                                                               | `auth.py`                |
| c5 / c3-F6      | HIGH     | Encryption fail-CLOSED via `settings.app_env` (was raw `os.environ["APP_ENV"]` defaulting to plaintext)                                                                 | `db/encrypted_column.py` |
| c2-F1           | HIGH     | `vector_store.search` wrap raw SQL in `text()` (RAG retrieval was dead on SQLAlchemy 2.0)                                                                               | `ai/vector_store.py`     |
| c3-F1           | HIGH     | `ConfidenceBadge` enum add `uncertain` (persisting uncertain response raised ValueError)                                                                                | `db/models.py`           |
| c5              | HIGH     | Login/signup/upload 500 handlers no longer leak traceback/`str(e)` to caller                                                                                            | `onboarding/app.py`      |
| c5 / c3-F3      | HIGH     | PDPA erasure: scrub message content; remove broken `DocumentChunk.message_id` chunk step; remove all-tenant over-deletion (was wiping tenant KB on no-message contacts) | `compliance.py`          |

Regression tests: `tests/unit/test_auth.py` (new, 6 cases) · `test_encrypted_column.py` (fail-closed via settings) · `test_compliance_erasure.py` (message-scrub + over-deletion guard). Suite: **461 passed**, 26 new; my changes add zero new failures.

## DEFERRED — needs the ②-scope decision (build-to-spec vs reconcile-spec)

These are "spec claims a feature ships; code partial" — large builds and/or PDPA-claim reconciliation. User-gated per `value-prioritization.md` MUST-4.

- **Message-body encryption** (c5 HIGH): `Message.body_text/subject/body_raw`, `Response.content`, `DocumentChunk.chunk_text`, `LearnedAnswer` text stored plaintext vs spec "all PII encrypted". Build encryption OR amend spec claim.
- **Schema-per-tenant isolation** (c5 / c3-F2 HIGH): live paths use `tenant_id`-column filter, not the schema-per-tenant the spec says PDPA requires (`session_for_tenant` unused). Build OR amend spec + PDPA sign-off.
- **Digest API drift** (c1-H1 HIGH): 3 integration tests import `gather_digest_data`/`format_digest_email`/`send_digest` (function API over `AsyncSession`) but the code ships class `DigestService` over a different DB abstraction. Reconcile which API is canonical, then implement/rewrite. (Collection error left visible — stubbing would violate zero-tolerance.)
- **RoutingOutcome instrumentation** (c1-H2), **HUMAN-override persistence** (c1-H3), **multi-channel dedup / thread-key** (c1-H5), **unified Escalation record fields + contradiction wiring** (c1-H6), **digest/recap scheduling** (c1-H7): specced-but-unwired feature-moats.
- **Confidence-badge rendering** (c2-F3), **staleness warning** (c2-F4), **answerability<0.3 exclusion** (c2-F2), **badge threshold drift** (c2-F5/F6): response-accuracy gaps.
- **WhatsApp zero tests** (c1-H4 / c4): 7 whatsapp modules + `auth`, `ai.ingestion`, `onboarding.api` have zero importing tests. Build test suite.
- **Security MEDIUMs** (c5): admin backfill endpoint unguarded (also has a latent `settings` NameError, app.py:679), unauthenticated DNS lookups, onboarding upload no size limit, serverless-ineffective rate limiter, prompt-injection on auto-send path, SendGrid webhook replay/verification.
- **F11 spec-internal contradiction** (c2): response-accuracy badge thresholds — 95/80/60 (table) vs 90/60 (Option C). Spec-author decision before F5/F6 fixes.
- **Test-infra F-C4-05** (c4 HIGH, pre-existing): 8 unit failures = `test_onboarding_api` validation tests need live Postgres (tier violation) + `test_config`/`test_contains_form` isolation. Move to integration OR add pre-DB validation.

## Orchestrator-Pyright latent bugs (not in agent scope, recorded)

- `onboarding/app.py:679` `settings` not defined · `:1401` `select` not defined — runtime NameErrors on those endpoints. Cheap import fixes; batch with the admin-endpoint MED fix.

## Convergence status

NOT converged. Round 1 finding pass complete. The ①-defect fixes are in-flight (PR pending). Reaching the convergence criteria (0 CRIT/0 HIGH × 2 clean rounds) requires the ②-scope decision to close the deferred feature-gaps. Receipt for the fixes: commit SHAs on `fix/redteam-r1-security-correctness`.
