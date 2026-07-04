# C4 — Test Coverage Audit (Round 1)

**Agent:** testing-specialist · **Mode:** `rules/testing.md` Audit Mode (re-derived from scratch; `.test-results` NOT consulted)
**Scope:** shipped comms-wedge implementation `src/sequor/**` only. Platform specs/todos (M0–M10) target-state → out of scope.
**Runner:** `.venv/bin/python -m pytest` · kailash 2.45.3 · CPython 3.12 · conftest auto-loads `.env`
**Date:** 2026-07-04

---

## 1. Collect-only re-derivation

Command: `.venv/bin/python -m pytest --collect-only -q tests/`

**Result: 497 tests collected, 3 errors during collection (collection interrupted).**

### Collection errors (verbatim symbol mismatch)

All three are the same root cause: three integration tests import symbols that **do not exist** in the shipped `sequor.digest.service`.

```
ERROR tests/integration/test_digest_integration.py
  test_digest_integration.py:28:
    from sequor.digest.service import gather_digest_data, send_digest
  E ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'

ERROR tests/integration/test_e2e_escalation_chain.py
  test_e2e_escalation_chain.py:24:
    from sequor.digest.service import gather_digest_data
  E ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'
  (also imports format_digest_email at line 208)

ERROR tests/integration/test_e2e_happy_path.py
  test_e2e_happy_path.py:30:
    from sequor.digest.service import gather_digest_data, format_digest_email
  E ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'
```

**Expected-vs-actual symbol table** — `sequor.digest.service` module surface:

| Symbol tests import    | Exists? | Actual shipped equivalent                                  |
| ---------------------- | ------- | ---------------------------------------------------------- |
| `gather_digest_data`   | NO      | `DigestService._gather_stats` (private async method)       |
| `format_digest_email`  | NO      | `build_digest_email` (module-level func)                   |
| `send_digest` (module) | NO      | `DigestService.send_digest` (async **method**, not a func) |

Actual public exports: `DigestService`, `build_digest_email`, `build_digest_subject`, `DigestEmailData`, plus module helpers `_after_cutoff`, `_ensure_aware`.

**Finding F-C4-01 (HIGH):** The digest module was refactored from free functions (`gather_digest_data` / `format_digest_email` / `send_digest`) into a `DigestService` class + `build_digest_email` module func. Three integration tests — including the two primary **E2E** suites (`test_e2e_happy_path`, `test_e2e_escalation_chain`) — were never updated and **fail at import time**, so the full end-to-end escalation + digest flow has **zero executing E2E coverage**. These are stale tests, not shipped-code bugs. Do not "fix" by re-adding the old symbols; update the tests to the `DigestService` API. Note the unit tests already use the correct API (`test_digest_service.py` imports `DigestService`; `test_digest.py` imports `_after_cutoff`), confirming the symbols moved rather than being deleted.

---

## 2. Module → importing-test coverage matrix

Every row is a live `re.escape`-anchored grep (`(?:from|import)\s+<module>(?![A-Za-z0-9_])`) across all `tests/**/*.py`. "ZERO" = no test file imports the module directly.

| module                             | importing test files                                                                                                        | verdict                                                                                                                   |
| ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| sequor.ai.chunker                  | unit/test_chunker                                                                                                           | ✅                                                                                                                        |
| sequor.ai.classifier               | unit/test_classifier, test_auto_reply, test_response                                                                        | ✅                                                                                                                        |
| sequor.ai.client                   | unit/test_llm_failover                                                                                                      | ✅                                                                                                                        |
| sequor.ai.document_parser          | unit/test_document_parser                                                                                                   | ✅                                                                                                                        |
| **sequor.ai.ingestion**            | **— ZERO —**                                                                                                                | **HIGH**                                                                                                                  |
| sequor.ai.learning                 | unit/test_learning                                                                                                          | ✅                                                                                                                        |
| sequor.ai.rag_pipeline             | unit/test_rag_pipeline, test_auto_reply, test_response                                                                      | ✅                                                                                                                        |
| sequor.ai.response                 | unit/test_response, test_auto_reply                                                                                         | ✅                                                                                                                        |
| sequor.ai.vector_store             | unit/test_vector_store                                                                                                      | ✅                                                                                                                        |
| **sequor.auth**                    | **— ZERO —**                                                                                                                | **HIGH (security-critical)**                                                                                              |
| sequor.billing.service             | integration/test_billing_integration, unit/test_billing_webhook_verification                                                | ✅                                                                                                                        |
| sequor.compliance                  | guardrails/test_compliance, unit/test_compliance_erasure                                                                    | ✅                                                                                                                        |
| sequor.config                      | unit/test_config, guardrails/test_no_secrets                                                                                | ✅                                                                                                                        |
| sequor.db.audit                    | unit/test_audit, test_escalation_audit                                                                                      | ✅                                                                                                                        |
| **sequor.db.base**                 | **— ZERO —**                                                                                                                | LOW (9-LOC DeclarativeBase; exercised transitively by every model test)                                                   |
| sequor.db.crud                     | unit/test_session_crud                                                                                                      | ✅                                                                                                                        |
| sequor.db.database                 | integration ×6                                                                                                              | ✅ (integration only)                                                                                                     |
| sequor.db.encrypted_column         | unit/test_encrypted_column                                                                                                  | ✅                                                                                                                        |
| sequor.db.encryption_keys          | unit/test_encryption_keys                                                                                                   | ✅                                                                                                                        |
| sequor.db.models                   | integration ×5 + unit ×7                                                                                                    | ✅                                                                                                                        |
| sequor.db.schema_manager           | unit/test_schema_manager                                                                                                    | ✅                                                                                                                        |
| sequor.digest.service              | unit/test_digest, test_digest_service + integration ×3 (ERRORing — §1)                                                      | ⚠️ unit-only (E2E broken)                                                                                                 |
| sequor.dns.service                 | unit/test_dns                                                                                                               | ✅                                                                                                                        |
| sequor.email.auto_reply            | unit/test_auto_reply                                                                                                        | ✅                                                                                                                        |
| sequor.email.inbound               | unit/test_email_parser, test_inbound_escalation_resolution, test_sendgrid_signature                                         | ✅                                                                                                                        |
| sequor.email.parser                | unit/test_email_parser                                                                                                      | ✅                                                                                                                        |
| sequor.email.rate_limiter          | unit/test_email_rate_limiter                                                                                                | ✅                                                                                                                        |
| sequor.email.sender                | unit/test_email_retry, integration/test_email_sender, guardrails/test_email_guardrails                                      | ✅                                                                                                                        |
| sequor.email.templates             | unit/test_email_templates, guardrails/test_email_guardrails                                                                 | ✅                                                                                                                        |
| **sequor.email.utils**             | **— ZERO —**                                                                                                                | LOW (15-LOC utility)                                                                                                      |
| sequor.escalation.scheduler        | unit/test_scheduler                                                                                                         | ✅                                                                                                                        |
| sequor.escalation.service          | unit/test_escalation_service, test_escalation_audit, test_scheduler                                                         | ✅                                                                                                                        |
| sequor.escalation.sla              | unit/test_sla                                                                                                               | ✅                                                                                                                        |
| sequor.escalation.thread_key       | unit/test_thread_key                                                                                                        | ✅                                                                                                                        |
| **sequor.onboarding.api**          | **— ZERO —**                                                                                                                | MEDIUM (wired via app.py `handle_signup`; exercised transitively by test_onboarding_api — which is currently FAILING, §3) |
| sequor.onboarding.app              | unit/test_onboarding_api, test_dns_api, test_document_upload_api                                                            | ✅ (but 7 tests failing, §3)                                                                                              |
| **sequor.onboarding.rate_limiter** | **— ZERO —**                                                                                                                | MEDIUM (wired via app.py; exercised transitively)                                                                         |
| sequor.onboarding.service          | integration/test_e2e_happy_path (ERRORing), test_onboarding_integration, unit/test_onboarding, test_onboarding_provisioning | ✅                                                                                                                        |
| sequor.protocols                   | unit/test_auto_reply, integration/test_email_sender, guardrails/test_email_guardrails                                       | ✅                                                                                                                        |
| sequor.schemas                     | guardrails/test_schemas + integration ×3 + unit ×2                                                                          | ✅                                                                                                                        |
| **sequor.whatsapp.auto_reply**     | **— ZERO —**                                                                                                                | **HIGH**                                                                                                                  |
| **sequor.whatsapp.inbound**        | **— ZERO —**                                                                                                                | **HIGH**                                                                                                                  |
| **sequor.whatsapp.parser**         | **— ZERO —**                                                                                                                | **HIGH**                                                                                                                  |
| **sequor.whatsapp.rate_limiter**   | **— ZERO —**                                                                                                                | MEDIUM                                                                                                                    |
| **sequor.whatsapp.sender**         | **— ZERO —**                                                                                                                | **HIGH**                                                                                                                  |
| **sequor.whatsapp.signature**      | **— ZERO —**                                                                                                                | **HIGH (security — HMAC verify)**                                                                                         |
| **sequor.whatsapp.utils**          | **— ZERO —**                                                                                                                | MEDIUM (17-LOC, `mask_phone` PII redaction)                                                                               |

### Zero-direct-test modules (13) — grouped by severity

**HIGH — security-critical, zero coverage:**

- **`sequor.auth`** (87 LOC) — `hash_password` / `verify_password` (paired) + `create_access_token` / `decode_token` / `create_access_token_for_operator`. This is the password-hashing + JWT primitive of the whole app. Wired (imported by `onboarding/app.py`) but app tests never exercise a login/auth path (no `login`/`session_token`/`require_` references in the api tests). **A regression in `verify_password` or `decode_token` would ship silently.**

**HIGH — the entire WhatsApp channel is shipped-but-untested (and not wired):**

- `whatsapp.auto_reply` (375), `whatsapp.inbound` (268 — `InboundWhatsAppProcessor`), `whatsapp.sender` (250 — `MetaWhatsAppSender`, Meta Cloud API), `whatsapp.parser` (132 — `parse_meta_webhook_payload`), `whatsapp.signature` (33 — `verify_meta_signature`, HMAC), `whatsapp.rate_limiter` (76), `whatsapp.utils` (17 — `mask_phone`). **~1,272 LOC, 7 modules, exported via `whatsapp/__init__.py`, but NOT wired into the onboarding app** (only `config.py` settings + a `models.py` channel-enum value reference WhatsApp; no handler imports the package). This is dormant/un-integrated code carrying a full inbound webhook + signature-verification + sender surface with zero tests. See F-C4-04.

**HIGH — large wired module, zero coverage:**

- **`sequor.ai.ingestion`** (380 LOC) — `DocumentIngester` / `IngestionResult`. Wired and live: imported by `onboarding/app.py` at two sites (document upload) and re-exported from `ai/__init__.py`. 380 LOC of document-ingestion pipeline with no direct test.

**LOW / transitively-covered (report, do not block):**

- `db.base` (9 LOC DeclarativeBase — every model test exercises it), `email.utils` (15 LOC).

---

## 3. Unit-suite run

Command: `.venv/bin/python -m pytest tests/unit -q`
**Result: 8 failed, 415 passed (308s).** Full non-integration run (`unit + guardrails + sdk`): **8 failed, 454 passed, 8 skipped** (the 8 skips are all `tests/sdk/test_sdk_patterns.py` — _"Standalone script — run directly, not via pytest"_, intentional/benign).

### Failure triage (8)

| #   | test                                                                                                                                                                                                                                           | assertion                              | root cause                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                  |
| --- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `test_config.py::test_settings_loads_defaults`                                                                                                                                                                                                 | `assert s.debug is False` → got `True` | **Env contamination.** conftest auto-loads `.env`, which sets `debug=True` + `database_url=postgresql://localhost/test`. The test asserts hard-coded defaults but is not hermetic (no `patch.dict(os.environ, clear=True)` / `_env_file=None`). Test-isolation bug, not a code bug.                                                                                                                                                                                                                                                                                                                         |
| 2   | `test_onboarding_api.py::TestSignupPage::test_contains_form`                                                                                                                                                                                   | `assert '<form' in res.text` → absent  | **Page-contract drift.** `GET /` serves `templates/signup.html`, which contains **zero `<form` tags** (the form lives in `register.html`, served by `GET /portal/...`). Test expects an inline signup form on `/`; shipped `/` is a marketing landing page. Either the test should target the register route or the page regressed.                                                                                                                                                                                                                                                                         |
| 3–8 | `test_onboarding_api.py::TestSignupEndpointValidation::{test_rejects_missing_fields, test_rejects_invalid_email, test_rejects_html_in_org_name, test_rejects_weak_password, test_rejects_invalid_routing_rule, test_rejects_sla_out_of_range}` | `assert 500 == 422`                    | **Two compounding causes.** (a) **3-tier violation:** these live in `tests/unit/` but drive the full FastAPI app via `TestClient(app)`, and the signup handler opens a real PostgreSQL connection → they require live infra. (b) **DB unreachable:** `database_url=postgresql://localhost/test` has no password → `psycopg.OperationalError: fe_sendauth: no password supplied`, so the handler 500s **before** returning the expected 422 validation error. This also hints validation is not enforced at the schema/pre-DB boundary (invalid input reaches a DB call instead of short-circuiting to 422). |

**Disposition (zero-tolerance Rule 1):** all 8 are failures that block sign-off and must be resolved in the `/implement` round — but note the classification: **#1 is test env-isolation, #2 is test-vs-page contract drift, #3–8 are a tier-misplacement + DB-credential/validation-ordering interaction.** None is a straightforward shipped-logic bug; do not "fix the code to make the test green" without first deciding the correct contract (per Audit Mode: respect original design). The #3–8 cluster in particular should be split — either move to `tests/integration/` with a real DB (test-env Postgres is at `localhost:5433`, but the app config points at `localhost:5432` with no password → config/infra mismatch to reconcile), or add pre-DB schema validation so invalid input returns 422 without a DB round-trip.

---

## 4. Warning triage (zero-tolerance Rule 1)

Ran the full non-integration suite with `-W default::DeprecationWarning -W default::ResourceWarning` to force-surface suppressed warnings.

| warning                                                                                                    | count | source                                  | disposition                                                                                                                                                                                                                                                                                                                                   |
| ---------------------------------------------------------------------------------------------------------- | ----- | --------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated; install httpx2 instead` | 1     | `fastapi/testclient.py:1` (third-party) | **Third-party deprecation, test-path only.** Not in `sequor` code; emitted by FastAPI's `TestClient` import. Pinned-dependency track: acceptable to defer per Rule 1 Exceptions only if pinned + tracking-issue'd. Fix path: bump FastAPI/Starlette or migrate the test HTTP client. Recommend a tracking issue rather than silent dismissal. |

**No `DeprecationWarning`, `ResourceWarning`, or `RuntimeWarning` originate from `sequor` code.** Clean on the first-party warning front. (The `OperationalError` traces in the log are the §3 DB failures, not warnings.)

---

## 5. Paired-variant coverage (`rules/testing.md`)

| pair                                                                              | both tested?  | note                                                                                                                                                                                                                                                                                                                                                             |
| --------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `DigestService.send_digest` / `send_all_accounts` / `send_all_tenants`            | ✅ all three  | `test_digest_service.py` covers each variant directly                                                                                                                                                                                                                                                                                                            |
| `EncryptedString.process_bind_param` (encrypt) / `process_result_value` (decrypt) | ✅            | roundtrip + wrong-key-fails both tested                                                                                                                                                                                                                                                                                                                          |
| **`auth.hash_password` / `auth.verify_password`**                                 | ❌ NEITHER    | security pair, zero tests (→ F-C4-02)                                                                                                                                                                                                                                                                                                                            |
| **`auth.create_access_token` / `auth.decode_token`**                              | ❌ NEITHER    | JWT encode/decode pair, zero tests (→ F-C4-02)                                                                                                                                                                                                                                                                                                                   |
| **email channel / whatsapp channel** (structural mirror)                          | ❌ asymmetric | `email.sender`/`inbound`/`parser`/`rate_limiter`/**sendgrid signature** all tested; the mirror-image `whatsapp.sender`/`inbound`/`parser`/`rate_limiter`/**meta signature** all ZERO. The most striking gap: `test_sendgrid_signature.py` exists but there is **no `test_meta_signature` / whatsapp signature test** for the equivalent HMAC verify. (→ F-C4-04) |

---

## Findings summary (by severity)

- **F-C4-01 (HIGH):** Digest module refactored to `DigestService` API; 3 integration tests (incl. both primary E2E suites) still import removed free-functions `gather_digest_data`/`format_digest_email`/`send_digest` → **ImportError at collection**, zero executing E2E coverage of the escalation+digest flow. Stale tests — update to `DigestService`.
- **F-C4-02 (HIGH):** `sequor.auth` (password hashing + JWT, 87 LOC) has **zero tests**, direct or transitive; both security pairs (`hash`/`verify`, `create_token`/`decode_token`) uncovered.
- **F-C4-03 (HIGH):** `sequor.ai.ingestion` (380 LOC `DocumentIngester`, wired into the document-upload path) has zero tests.
- **F-C4-04 (HIGH):** Entire WhatsApp channel — 7 modules / ~1,272 LOC incl. `verify_meta_signature` (HMAC) and `MetaWhatsAppSender` — has zero tests **and** is not wired into the app (dormant); email channel counterpart is fully covered (paired-variant asymmetry).
- **F-C4-05 (HIGH):** 6 `test_onboarding_api` validation tests fail `500 == 422` — unit tests requiring live Postgres (tier violation) + DB-credential/validation-ordering issue; plus `test_contains_form` fails on page-contract drift and `test_config` fails on env contamination (8 failures total).

**Headline numbers:** 497 collected · 3 collection errors · **13 modules with zero direct tests** (`auth`, `ai.ingestion`, `email.utils`, `db.base`, `onboarding.api`, `onboarding.rate_limiter`, and all 7 `whatsapp.*`) · unit suite **8 failed / 415 passed** · 1 warning (third-party Starlette, deferrable-with-tracking).
