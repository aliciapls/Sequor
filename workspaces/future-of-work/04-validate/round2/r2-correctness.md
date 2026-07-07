# /redteam Round 2 — Correctness + Mechanical-Sweep Verification

Scope: `src/sequor/**`, `api/index.py`, `tests/**` on branch `fix/redteam-r1-security-correctness`.
Posture L5_DELEGATED. Read-only. Method: every row cites a literal command + actual output.
Round-1 inputs: `../round1/c1..c5-*.md`, `../round1/00-SUMMARY-and-dispositions.md`.

Environment note (evidence-first): bare `python3 -m pytest` reports 44 `ModuleNotFoundError: No module
named 'sequor'` collection errors — a venv artifact, NOT a code defect. Under the project venv
(`uv run pytest`) the count is 504 collected / 3 errors. All findings below use the venv result.

---

## Mechanical Sweep 1 — Latent NameError sweep (AST free-name analysis, all `async def` in `onboarding/app.py`)

A strict AST sweep (module-level names = direct-body imports/assigns/defs only; per-function binds =
args + local imports + stores + except-names) over every function in `app.py` returns EXACTLY 2
unresolved free names across the whole file — no others:

```
L679: fn 'backfill_blind_indexes' -> UNRESOLVED 'settings'
L1401: fn 'portal_api_keyphrase_create' -> UNRESOLVED 'select'
TOTAL distinct unresolved (name,line): 2
```

Both are the Round-1-recorded latents; the sweep found NO additional latent NameErrors.

## Mechanical Sweep 2 — pytest collection

`uv run pytest --collect-only -q tests/` → **504 collected, 3 errors**. All 3 errors are the digest
API drift (`cannot import name 'gather_digest_data' from 'sequor.digest.service'`): the shipped code
exposes class `DigestService`; the 3 integration tests import a module-level function API that does
not exist. Collection-blocking per `orphan-detection.md` Rule 5 / `zero-tolerance.md` Rule 1.

## Mechanical Sweep 3 — the three Round-1 correctness fixes

- **RAG `text()` wrap (`ai/vector_store.py`)** — VERIFIED CORRECT. Both `session.execute` sites
  (store L74, search L127) wrap raw SQL in `text()`. Sibling raw-SQL modules (`ai/learning.py`
  L141/187/233, `ai/ingestion.py` L317/368) also route through `text()`. No bare-string `execute`
  remains anywhere under `ai/`.
- **ConfidenceBadge `uncertain` (`db/models.py`)** — VERIFIED CORRECT. `ConfidenceBadge.uncertain =
  "uncertain"` (L143) matches migration `5ab03308b1f3` L257 enum `('high','moderate','low',
  'uncertain')`. The value is produced+persisted on multiple reachable paths (`ai/response.py` L164,
  `ai/rag_pipeline.py` L222, `email/auto_reply.py` L205), so the ValueError-on-persist class is closed.
- **Compliance erasure over-deletion guard (`compliance.py`)** — VERIFIED CORRECT. With empty
  `message_ids`: the Message scrub is guarded by `if message_ids` (L141); the Escalation query by
  `if message_ids` (L165); the LearnedAnswer query by `if escalation_ids` (L175); the LearnedAnswer
  scrub by `if learned_ids` (L184). Empty input therefore affects zero rows; an all-tenant wipe is
  structurally impossible. The broken `DocumentChunk.message_id` step is removed (not "fixed").

---

## Findings table

| SEV | Title | file:line | evidence | defect-vs-spec-ahead | fix |
| --- | ----- | --------- | -------- | -------------------- | --- |
| HIGH | `select` NameError crashes keyphrase-create (live route `POST /api/v1/portal/keyphrase/mappings`) | `onboarding/app.py:1401` | Local imports L1379-1382 bring `get_engine, AsyncSession`, models, `BaseModel` — NOT `select`. `select(Document)` at L1401 is OUTSIDE the L1391-1395 try/except → uncaught `NameError` → 500 on every authenticated create. | genuine DEFECT (hard crash) | add `select` to the L1380 `from sqlalchemy import` (mirror L662). |
| MEDIUM | `settings` NameError silently zeroes admin blind-index backfill (`POST /api/v1/admin/backfill-blind-indexes`) | `onboarding/app.py:679` | Imports `select, update` (L662) but NOT `settings`. `settings.encryption_master_key` at L679 is INSIDE the per-contact `try/except Exception as e` (L677-695) → NameError swallowed into `errors[]`, `updated` stays 0. Endpoint returns 200 reporting 0 rows backfilled — a silent no-op, not a 500. | genuine DEFECT (silent wrong-result) | add `from sequor.config import settings` to the function's local imports. |
| HIGH | Digest API drift — 3 collection errors block the integration suite | `tests/integration/test_digest_integration.py`, `test_e2e_happy_path.py`, `test_e2e_escalation_chain.py` | `uv run pytest --collect-only` → 3 × `cannot import name 'gather_digest_data' from 'sequor.digest.service'`. Code ships class `DigestService`; tests import `gather_digest_data`/`format_digest_email`/`send_digest`. `DigestService` has NO production invoker (`__init__` exports only the class; only internal self-calls) so the feature is ALSO unwired. | genuine DEFECT (broken collection gate) + underlying feature spec-ahead | reconcile the canonical API, then implement/rewrite; do NOT stub (zero-tolerance). |
| MEDIUM | `key_phrase_mappings` table has NO migration (schema drift) | `db/models.py:759` vs `db/migrations/versions/5ab03308b1f3_initial_schema.py` | Only one migration exists; its `create_table` set (L25-271) omits `key_phrase_mappings`. `init_db` (`db/database.py:49`) uses `Base.metadata.create_all` (whole-module import registers the model, so dev/test tables exist) AND an inline `ALTER TABLE` (L59-61). Under Alembic-only prod (`upgrade head`) the table is absent → keyphrase routes would fail even after the L1401 fix. create_all + Alembic = two schema sources (`schema-migration.md` Rule 1/1a). NEW — not in Round 1. | genuine DEFECT (schema gap, masked in dev by create_all) | add a numbered migration creating `key_phrase_mappings`; converge on one schema source. |
| HIGH | 8 pre-existing unit failures (`test_onboarding_api` needs live Postgres = tier violation; `test_config`/`test_contains_form` isolation) | `tests/unit/**` (Round-1 F-C4-05) | Recorded in Round-1 c4; `zero-tolerance.md` Rule 1 — pre-existing failures owned by this session. | genuine DEFECT (test-infra) | move DB-dependent cases to integration OR add pre-DB validation; fix env isolation. |
| HIGH | Message-body / Response / chunk / LearnedAnswer PII stored plaintext vs spec "all PII encrypted" | `db/models.py` (Round-1 c5) | No crash; feature (column encryption) simply not built. Spec CLAIM is false as written. | spec-ahead-of-code | build encryption OR amend the spec/PDPA claim (user-gated). |
| HIGH | Schema-per-tenant isolation unbuilt (`session_for_tenant` unused; live paths use `tenant_id` column filter) | Round-1 c5 / c3-F2 | `tenant_id` filtering IS functional isolation; the schema-per-tenant architecture the spec names is absent. No wrong data returned. | spec-ahead-of-code | build OR amend spec + PDPA sign-off. |
| HIGH | `RoutingOutcome` instrumentation unwired (table exists, zero write sites) | Round-1 c1-H2 | Migration creates `routing_outcomes` (L228); `grep` finds zero `.create("RoutingOutcome"...)`. Orphan by `orphan-detection.md` §1 — honestly-partial, no crash. | spec-ahead-of-code | wire the write path OR amend spec. |
| HIGH | HUMAN-override persistence; multi-channel dedup / `derive_thread_key`; unified Escalation fields + contradiction wiring; digest/recap scheduling | Round-1 c1-H3/H5/H6/H7 | Detection logic present but persistence/wiring absent (`derive_thread_key` exported, zero call sites); no crashes. | spec-ahead-of-code | build the wiring OR amend spec (per feature). |
| HIGH | Response-accuracy gaps: confidence-badge rendering, staleness warning, answerability<0.3 exclusion, badge-threshold drift | Round-1 c2-F2/F3/F4/F5/F6 | Partial/absent features; quality gaps, not crashes. F5/F6 depend on the F11 spec-internal contradiction. | spec-ahead-of-code | build OR amend; resolve F11 first. |
| HIGH | F11 spec-internal contradiction — badge thresholds 95/80/60 (table) vs 90/60 (Option C) | Round-1 c2 | Two conflicting numbers within one spec. | spec-ahead-of-code (spec-author decision) | spec-author picks one before F5/F6 implementation. |
| HIGH | Zero importing tests for 7 whatsapp modules + `auth`, `ai.ingestion`, `onboarding.api` | Round-1 c1-H4 / c4 | `testing.md` audit mode: new module with zero importing test = HIGH. Not a runtime defect. | test-coverage gap | add Tier-1/2 suites per module. |

---

## Disposition summary (build-vs-amend-spec input)

**Genuine DEFECTS — fix regardless of the ②-scope decision (`zero-tolerance.md` Rule 1):**
`select` NameError (L1401, 500) · `settings` NameError (L679, silent 0-backfill) · digest 3 collection
errors · `key_phrase_mappings` missing migration (NEW) · 8 pre-existing unit failures. The two
NameErrors are one-line local-import additions and SHOULD be fixed in this branch — Round 1 recorded
them as "batch with the admin-endpoint MED fix" but the sweep confirms both are still present on HEAD.

**Spec-ahead-of-code — honestly-partial features (user-gated build-OR-amend-spec):**
message-body encryption · schema-per-tenant isolation · RoutingOutcome instrumentation ·
HUMAN-override persistence · multi-channel dedup/thread-key · unified Escalation fields ·
digest/recap scheduling · response-accuracy badge/staleness/answerability · F11 threshold
contradiction. Plus the test-coverage gap (whatsapp + 3 modules).

The three Round-1 correctness fixes (RAG `text()`, ConfidenceBadge `uncertain`, compliance
over-deletion guard) are independently re-verified CORRECT and reachable.
