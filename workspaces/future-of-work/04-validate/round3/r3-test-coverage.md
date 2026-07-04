# Round 3 — Test-Coverage Audit (INDEPENDENT re-derivation)

Auditor: testing-specialist. Method: `pytest --collect-only` + grep of `tests/` for
importing tests (testing.md Audit Mode). `.test-results` NOT read. All counts
re-derived from live command output quoted inline.

Repo: `/Users/esperie/repos/projects/Sequor` · venv `.venv/` · date 2026-07-05.

---

## 1. Collection status — HIGH (3 modules, DB-independent break)

```
$ .venv/bin/python -m pytest --collect-only -q tests/ 2>&1 | tail
tests/integration/test_digest_integration.py:28: in <module>
    from sequor.digest.service import gather_digest_data, send_digest
E   ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'
tests/integration/test_e2e_escalation_chain.py:24: in <module>
    from sequor.digest.service import gather_digest_data
E   ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'
tests/integration/test_e2e_happy_path.py:30: in <module>
    from sequor.digest.service import gather_digest_data, format_digest_email
E   ImportError: cannot import name 'gather_digest_data' from 'sequor.digest.service'
...
ERROR tests/integration/test_digest_integration.py
ERROR tests/integration/test_e2e_escalation_chain.py
ERROR tests/integration/test_e2e_happy_path.py
!!! Interrupted: 3 errors during collection !!!
506 tests collected, 3 errors in 0.78s
```

**Confirmed modules** (exactly the 3 the brief predicted):

- `tests/integration/test_digest_integration.py` — imports `gather_digest_data`, `send_digest`
- `tests/integration/test_e2e_escalation_chain.py` — imports `gather_digest_data`
- `tests/integration/test_e2e_happy_path.py` — imports `gather_digest_data`, `format_digest_email`

**Root cause (evidence-first, quoted from source):**

```
$ grep -n 'def ' src/sequor/digest/service.py
18:class DigestService:
35:    async def send_digest(          # ← a METHOD on DigestService, not a module fn
109:    async def send_all_tenants
127:    async def _gather_stats         # ← the real gathering logic, private method
227:def _after_cutoff
233:def _ensure_aware
```

`gather_digest_data` and `format_digest_email` **do not exist anywhere** in
`service.py`; `send_digest` exists only as a `DigestService` method, not the
module-level symbol the tests import. This is a genuine API/test contract drift,
NOT a missing DB. **Classification: HIGH.** It is a broken suite — zero-tolerance
Rule 1: collection errors are fixed, not skipped as "pre-existing". Disposition is
audit-only here; fix owner must either (a) restore module-level
`gather_digest_data`/`format_digest_email`/`send_digest` wrappers, or (b) rewrite
the 3 integration tests to drive `DigestService` — with the caveat that these tests
encode the intended digest API and MUST NOT be silently gutted to fit the class.

---

## 2. Unit suite — 1 failed / 431 passed

```
$ .venv/bin/python -m pytest tests/unit/ -q 2>&1 | tail
FAILED tests/unit/test_onboarding_api.py::TestSignupPage::test_contains_form
1 failed, 431 passed, 1 warning in 301.65s (0:05:01)
```

Confirmed identical on a second independent run (`1 failed, 431 passed ... in 302.42s`).

**The one failure — `test_contains_form` (frontend↔API contract gap, NOT a stale test):**

```
    def test_contains_form(self, client):
        res = client.get("/")
>       assert "<form" in res.text
E       assert '<form' in '<!DOCTYPE html>...built for professional services
        teams in Singapore and SEA.</div></div></footer></body></html>'
```

`GET /` now serves a **marketing landing page** with no `<form>` element; the test
expects the signup form to live at `/`. This is a real surface/route contract
mismatch (the signup form moved or was never rendered at `/`), not an outdated
assertion. Per brief instruction: **do NOT recommend silently rewriting the test.**
Fix owner must decide the intended contract (form at `/` vs. landing at `/` +
form at another route) and reconcile route + test together.

Also surfaced (zero-tolerance Rule 1, warnings = errors):

```
StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is
deprecated; install `httpx2` instead.
```

One deprecation warning present across the suite — should be resolved, not carried.

---

## 3. Modules with ZERO importing tests (HIGH)

Method: `grep -rl "from sequor.<pkg>.<mod>" tests/` per module.

### 3a. WhatsApp — ALL 7 modules, ZERO tests (HIGH)

```
$ for m in auto_reply inbound parser rate_limiter sender signature utils; do
    grep -rl "sequor.whatsapp.$m" tests/ | wc -l ; done
whatsapp/auto_reply.py   -> 0
whatsapp/inbound.py      -> 0
whatsapp/parser.py       -> 0
whatsapp/rate_limiter.py -> 0
whatsapp/sender.py       -> 0
whatsapp/signature.py    -> 0
whatsapp/utils.py        -> 0
$ grep -rln "sequor.whatsapp" tests/   → (no output — no test imports the package)
$ grep -rlni "whatsapp" tests/         → tests/unit/test_classifier.py   (channel STRING only, not an import)
```

Every one of the 7 shipped WhatsApp modules (`message-routing.md`: "SHIPPED:
Company WhatsApp Business API") has **zero test coverage**. Most severe:

- `whatsapp/signature.py::verify_meta_signature` — the **webhook HMAC-SHA256
  signature verification** (`hmac.compare_digest` of `X-Hub-Signature-256`). A
  security boundary that decides whether inbound webhooks are authentic — untested.
  No test asserts it rejects a forged/missing/malformed signature.
- `whatsapp/rate_limiter.py` — WhatsApp-required rate limiting
  (`message-routing.md §Rate Limits (WhatsApp-Required)`) — untested.
- `whatsapp/inbound.py`, `sender.py`, `auto_reply.py`, `parser.py` — inbound/outbound
  message path — untested.
  **Classification: HIGH** (shipped security-relevant channel, zero tests).

### 3b. onboarding/api.py — no DIRECT test; indirect validation-path only (MEDIUM)

```
$ grep -rln "sequor.onboarding.api" tests/   → NONE
$ grep -n handle_signup src/sequor/onboarding/app.py
19:from sequor.onboarding.api import handle_signup
138:    result = await handle_signup(body)      # wired into POST /api/v1/onboarding
```

`api.py::handle_signup` (creates Tenant + Account + BackupContact) is reached
INDIRECTLY via `client.post("/api/v1/onboarding")` in `test_onboarding_api.py` —
but the POST tests exercise **only rejection paths** (`test_rejects_missing_fields`,
`_invalid_email`, `_html_in_org_name`, `_weak_password`, `_invalid_routing_rule`,
`_sla_out_of_range`). No unit test drives a **successful** signup (the DB-record-
creation happy path). That success path is only in the integration E2E tests —
which currently FAIL collection (§1). Net: the onboarding success path has NO
runnable coverage at any tier right now. **Classification: MEDIUM→HIGH** (elevated
because the only happy-path coverage is in the 3 collection-broken modules).

### 3c. AI modules — all covered (OK)

```
ai/chunker.py->1  classifier.py->3  client.py->2  document_parser.py->1
ai/ingestion.py->1 (tests/unit/test_document_upload_api.py)  learning.py->1
ai/rag_pipeline.py->3  response.py->4  vector_store.py->2
```

Every `ai/` module (incl. `ai/ingestion`, changed on this branch) has ≥1 importing
test. No zero-coverage finding here.

### 3d. Branch-changed modules (git diff main...HEAD)

Changed: `ai/vector_store, auth, compliance, config, db/encrypted_column, db/models,
onboarding/api, onboarding/app`. NOTE: the branch does **not** touch `whatsapp/` or
`ai/ingestion` — those are pre-existing shipped code; their coverage gaps are
pre-existing but in-scope per zero-tolerance ("if you found it, you own it").
Changed modules with tests present: `auth`(test_auth.py), `compliance`
(test_compliance_erasure.py), `config`(test_config.py), `encrypted_column`
(test_encrypted_column.py), `onboarding/app`(4), `vector_store`(2). Only
`onboarding/api` lacks a direct test (§3b).

---

## 4. Spec success-criterion / security-threat → test mapping

The 7 comms-wedge specs use requirement/criteria prose rather than literal
"Security Threats" headers (only `data-model.md §Security by Design` is a named
security section). Mapping the security-relevant criteria to tests:

| Spec criterion / threat                                                         | Test present? | Evidence                                                                                       |
| ------------------------------------------------------------------------------- | ------------- | ---------------------------------------------------------------------------------------------- |
| WhatsApp webhook signature auth (message-routing)                               | **NO — HIGH** | `grep verify_meta_signature\|X-Hub-Signature tests/` → NONE                                    |
| WhatsApp rate limits (message-routing §Rate Limits)                             | **NO — HIGH** | `grep whatsapp.*rate tests/` → NONE                                                            |
| Multi-channel dedup / 48h window (message-routing, channel-coordination)        | yes           | `tests/unit/test_thread_key.py`                                                                |
| Tenant isolation / cross-tenant (data-model, rag-pipeline "impossible by arch") | partial       | `tests/unit/test_r2_security_fixes.py` (verify depth separately)                               |
| Hallucination / uncited-claim detection (rag-pipeline §Hallucination)           | yes           | `tests/unit/test_rag_pipeline.py`, `test_response.py`                                          |
| Confidence badge thresholds (response-accuracy §Badge Spec)                     | yes           | `test_response.py`, `test_rag_pipeline.py`, `test_auto_reply.py`, `test_escalation_service.py` |
| PDPA erasure / retention (data-model §Retention, §Breach)                       | yes           | `test_compliance_erasure.py`, `tests/guardrails/test_compliance.py`, `test_schemas.py`         |

**Documented-threat-with-no-test (HIGH):** WhatsApp webhook signature verification
and WhatsApp rate limiting — both shipped security controls, zero tests (§3a).

---

## 5. Eval-harness gap — convergence criterion #7 (HIGH)

```
$ ls -la tests/redteam-evals/           → No such file or directory
$ find tests/ -iname '*eval*' -o -iname '*probe*'   → (no output)
```

**`tests/redteam-evals/` does NOT exist.** There is no probe-driven adversarial
eval harness. Convergence criterion #7 is UNMET: every spec success-criterion +
brief intent needs ≥1 adversarial probe, and every prior-wave defect needs a
regression probe — none exist. Per `probe-driven-verification.md`, when this
harness is built, semantic assertions (refusal classification, confidence-badge
correctness, hallucination/uncited-claim judgment, response quality) MUST be
probe-driven (prompt template + expected-answer schema + scoring rule), NOT
regex/keyword/substring on assistant prose. Structural checks (signature reject,
route status, record creation) may stay assertion-based. **Classification: HIGH.**

---

## Summary of HIGH findings

1. **Collection break (HIGH)** — 3 integration modules fail on
   `gather_digest_data`/`format_digest_email`/`send_digest` ImportError;
   symbols absent from `digest/service.py` (only `DigestService` class exists).
   DB-independent, broken suite.
2. **WhatsApp 0-test (HIGH)** — all 7 shipped modules untested;
   `verify_meta_signature` (webhook HMAC auth) + rate limiter are untested
   security controls.
3. **Documented threats no test (HIGH)** — WhatsApp webhook signature auth &
   WhatsApp rate limiting have no corresponding test.
4. **Eval-harness gap (HIGH)** — `tests/redteam-evals/` absent; convergence
   criterion #7 unmet; must be probe-driven when built.
5. **Onboarding success path (MEDIUM→HIGH)** — `onboarding/api.py::handle_signup`
   happy path only covered by the 3 collection-broken integration tests; no
   runnable coverage of successful signup at any tier.

Non-HIGH: `test_contains_form` unit failure is a real frontend↔API route contract
gap (do NOT silently rewrite); 1 Starlette deprecation warning to resolve.
