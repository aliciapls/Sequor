# /redteam Round 6 — Confirmation Verification (2nd-consecutive-clean check)

Date 2026-07-05 · Branch `fix/redteam-r1-security-correctness` · R5 commit `42f8009` · Verifier: R6 confirmation lane.
Method: every R5 fix re-derived from source; every DEVIATIONS reality re-grepped; the spec softenings adversarially re-adjudicated against `spec-accuracy.md` Rule 2 vs `specs-authority.md` Rule 6. Trusted nothing in the R5 self-report.

## VERDICT: R6 IS CLEAN

**0 new CRITICAL / 0 new HIGH. All 5 R5 fixes present and correct. All R5 spec edits are accurate deviation-acknowledgments, not new CRIT/HIGH violations.** One LOW spec-hygiene residual (message-routing "When built…" future-tense list) — a net _improvement_ over the pre-R5 false claim, flagged for the record, not a regression. This is the 2nd consecutive clean round on the defect surface → **CONVERGED**.

Verbatim suite line (full `tests/unit/`):

```
437 passed, 1 xfailed, 1 warning in 2.57s
```

Eval harness: `32 passed`. Collect-only: `554 tests collected`, exit 0.

---

## R5 fix verification (each with inline evidence)

### 1. R5-02 — WhatsApp verify-token constant-time — CORRECT

`src/sequor/onboarding/app.py:189` `import hmac` present; `app.py:461`:

```python
if not hmac.compare_digest(token or "", expected_token):
    _logger.warning("whatsapp.verify.token_mismatch")
    return JSONResponse(status_code=403, content={"detail": "Token mismatch"})
```

No residual `token != expected_token`. Regression tests (`tests/unit/test_r5_regression_fixes.py`) genuinely assert behavior:

- `test_wrong_token_rejected` → asserts `status_code == 403` AND `"12345" not in resp.text` (reject-on-mismatch + no challenge echo).
- `test_correct_token_echoes_challenge` → `200` + `resp.text.strip() == "echo-me-42"`.
- `test_verify_uses_constant_time_compare` → asserts `compare_digest` in the source of the live function (constant-time guard).
  All 3 PASS.

### 2. G2 / G3 — behavioral, not source-grep — CORRECT

`python -m pytest tests/unit/test_r5_regression_fixes.py -v` → **5 passed in 0.76s**.

- **G2** (`test_keyphrase_mappings_get_resolves_names`): drives `GET /api/v1/portal/keyphrase/mappings` with a mocked async DB double, asserts `resp.status_code == 200` and `resp.json() == {"mappings": []}` — a NameError on unimported `select`/`desc` would 500. Behavioral. ✓
- **G3** (`test_500_body_excludes_exception_text`): injects `RuntimeError(_LEAK_MARKER)` into `DocumentIngester.ingest`, asserts `500` AND `_LEAK_MARKER not in resp.text` AND `"Internal server error" in resp.text`. Behavioral. ✓

### 3. G4 — F8 xfail strict=True, still XFAILs — CORRECT

`test_onboarding_api.py:51` diff shows `strict=False` → `strict=True`. Live run:
`tests/unit/test_onboarding_api.py::TestSignupPage::test_contains_form XFAIL`. The single suite-wide xfail IS this test — XFAIL, not XPASS (strict xfail did not trip → the form↔API mismatch is still unresolved, as intended). ✓

### 4. Backoff fix — patches the right symbol, suite is fast — CORRECT

`test_email_retry.py:243` autouse fixture: `with patch("sequor.email.sender.asyncio.sleep", new_callable=AsyncMock)`. Full `tests/unit/` completes in **2.57s** (R5 claimed 1.8s — machine variance, both well under the ~35-min hang the real backoff caused). ✓

### 5. Eval harness — green — CORRECT

`python -m pytest tests/redteam-evals/ -q` → **32 passed in 0.39s**. ✓

---

## New-issue hunt (the critical part)

### Item 6 — SPEC-ACCURACY of the three R5 softenings — ACCEPTABLE (Rule-6 side of the tension); 1 LOW residual

**Canonical audit grep is CLEAN on the R5-edited files.** `rg -i 'phase-?1.*phase-?2|target.state|promised.*current|scaffold.*later|TBD|backend.follow-?up|FE.follow-?up|pending.accessor|to.be.wired|accessor.pending' specs/` returns hits ONLY in the platform/vision specs (`_index.md`, `platform-overview.md`, etc.) via the `target.state` alternative — those are pre-existing whole-spec `> Status: TARGET-STATE` blockquotes (Rule-3 Exception-1 out-of-scope bounding, two-tier framing in `_index.md`), NOT touched by R5. **None of `rag-pipeline.md` / `data-model.md` / `message-routing.md` appears.** The R5 edits use `not yet implemented` — a token that is NOT on the spec-accuracy BLOCKED list.

**The Rule-2 vs Rule-6 adjudication (the crux):**

- **`specs-authority.md` Rule 6** governs the DUTY to (a) update the spec to new truth + (b) log the deviation. DEVIATIONS `§ R5 additions` F1/F2/F3 satisfy (b); the softened spec sentences satisfy (a) — the new truth being "not built, tracked at Fx."
- **`spec-accuracy.md` Rule 2** BLOCKS _split-state_ framings: `Promised/Current`, `Phase-1/Phase-2`, `Target/Fallback`, `Scaffold/Live`, `TBD`. The R5 edits contain **none** of these. They are _single-truth_ statements ("this is not built; tracked at F1/F2/F3"), materially different from the Rule-2 failure mode (a Promised-vs-Current column inviting implementation against the scaffold side). The lookaway-tombstone risk Rule 2 exists to prevent — a downstream dev building against a scaffold believing it ships — is **neutralized** by the explicit "not yet implemented / not yet modelled / no outcomes are written today" labels.

**Verdict per edited file:**

- **`rag-pipeline.md:28`** — CLEAN. Single bullet, now truthfully labels malware scan as unbuilt + points to F1. Deviation-acknowledgment, right side of Rule 2.
- **`data-model.md:425`** — CLEAN. The retention _table_ (policy) is real domain truth today; the added paragraph correctly separates policy (shipped) from enforcement (F2, not built). Right side of Rule 2.
- **`message-routing.md:312`** — ACCEPTABLE with a **LOW residual**. The "When built, the loop delivers: [3-bullet future behavior]" list is future-tense description of unbuilt behavior in a spec body. `spec-accuracy.md` MUST-NOT "Write a spec section for behavior not yet implemented" + the Migration protocol ("don't soften — delete") would prefer this list DELETED and carried wholly by DEVIATIONS F3. **BUT**: (i) it is now unmistakably gated as "When built" — the lookaway failure mode is neutralized; (ii) R5 did NOT introduce this content — the pre-R5 text ("This is not a future feature. It is architected from day 1" + present-tense "Every routing decision logs a `RoutingOutcome` record") was a _false-shipped phantom claim_ = the strictly HIGHER-severity Rule-1/Rule-5 violation. R5 **reduced** the severity (false-shipped → clearly-labeled-unbuilt). So it is a **net improvement, not a regression**, and not a new CRIT/HIGH.
  - _Optional future fix (LOW):_ move the 3-bullet "When built…" list out of `message-routing.md` into DEVIATIONS F3, leaving only the one-line pointer in the spec. Not required for convergence.

### Item 7 — Cross-spec consistency after R5 edits — CONSISTENT

- **Template count:** `message-routing.md:26` claims "6 named templates … matching the 6 template ids enumerated under Minimum required templates below." The enumeration at `message-routing.md:97` lists exactly 6: `oo_acknowledgement`, `oo_notice`, `escalation_notice`, `no_information`, `human_override`, `urgent_routing`. Internally consistent (6 named ⊆ 8 pre-approved). ✓
- **Free-tier retention row:** `data-model.md` now carries a `Free` column (7 days across all types). `business-model.md:15` Free tier states "Audit log: 7-day retention" — consistent with the data-model Audit-entries=7-days cell. _Minor note (LOW, not a contradiction):_ business-model only explicitly backs the _audit-log_ 7-day figure; the 7-day figures for message-content / contact-profiles / RAG-documents are a reasonable extrapolation not separately cited, but nothing contradicts them anywhere. No finding.
- **NEW-8:** `grep -n 'NEW-8' specs/DEVIATIONS.md` → `154:### NEW-8 — WhatsApp auto-reply footer missing confidence + "Reply STOP" opt-out (HIGH)` — a defined heading row, not just an inline ref. ✓

### Item 8 — DEVIATIONS § R5 additions rows have accurate code-reality — CONFIRMED

- **F1** (malware scan): `grep -rni 'malware|clamav|virus' src/sequor/` → **0**. Accurate.
- **F2** (retention-purge job): `grep -rni 'purge|nightly|retention.*job' src/sequor/` → **0**. Accurate.
- **F3** (routing flywheel): `RoutingOutcome` class EXISTS (`db/models.py:720`); `RoutingThresholdConfig` / `RoutingOutcomeAggregate` have **no class** (grep → absent); no aggregation job. Accurate.
- **R5-01** (unauth onboarding upload): `upload_document` (`onboarding/app.py:179`) takes `tenant_id: str = Form(...)`, validates only UUID-parse (`:209`), has **no** `_require_auth` call (the helper at `:842` is used by OTHER endpoints at `:726`/`:855`). Accurate.
- **rag-uncited-1** (no 1–50% graded path): `ai/rag_pipeline.py:373` rejects only at `uncited / total_claims > 0.5`; hallucination confidence is binary (`1.0 if passed else 0.5`, `:290`). No 1–50% "reduce confidence + route to backup" path. Accurate.

### Item 9 — Mechanical sweeps — GREEN

- `python -m pytest --collect-only -q` → **554 collected**, exit 0.
- R5 src diff (`git show 42f8009 -- src/` added lines) grep for `TODO|FIXME|HACK|STUB|XXX|NotImplementedError|placeholder` → **0 matches** (exit 1). No stubs introduced.

---

## Pre-existing advisory (NOT R5-introduced, NOT part of the delta)

Every FastAPI TestClient run emits one `StarletteDeprecationWarning: Using httpx with starlette.testclient is deprecated`. Third-party upstream deprecation (starlette testclient), pre-dates this branch, unresolvable at repo level — the `zero-tolerance.md` Rule-1 upstream-third-party exception class. Surfaced for completeness; not an R5 regression, not CRIT/HIGH.

## Convergence disposition

R5 delta is correct and complete for what it claimed. No new CRITICAL/HIGH introduced. The single LOW residual (message-routing future-tense list) is a strict improvement over the pre-R5 false-shipped claim. **2nd consecutive clean round → the comms-wedge defect surface is CONVERGED.** The remaining CRITICAL/HIGH items (A1 encryption, F2 PDPA purge, etc.) are all LOGGED, user-ratified, F5-gated builds — a product gate, not an autonomous blocker.
