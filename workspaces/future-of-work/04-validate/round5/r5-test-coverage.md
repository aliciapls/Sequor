# R5 — Test-Coverage Audit (comms-wedge, SHIPPED)

Audit mode per `rules/testing.md` § Audit Mode. Coverage re-derived from scratch via
`pytest --collect-only`/live runs — `.test-results` NOT consulted. Behavioral over source-grep.
Branch: `fix/redteam-r1-security-correctness`. Date: 2026-07-05.

## 1. Collection — re-derived, verbatim tail

`python -m pytest --collect-only -q`:

```
549 tests collected in 0.89s
```

**0 collection errors.** Count matches the expected ~549. The suite is not broken.

## 2. Suite runs — REAL pass/fail (re-derived)

Unit — `python -m pytest tests/unit/ -q -p no:cacheprovider`:

```
432 passed, 1 xfailed, 1 warning in 301.80s (0:05:01)
```

Eval harness — `python -m pytest tests/redteam-evals/ -q`:

```
32 passed, 1 warning in 1.19s
```

The lone warning is the upstream `StarletteDeprecationWarning` (httpx/testclient) — third-party,
not a suite defect.

### Skip / xfail inventory — COMPLETE (grep of every skip form across `tests/`)

```
tests/unit/test_onboarding_api.py:44:    @pytest.mark.xfail(   # test_contains_form (F8)
tests/redteam-evals/test_spec_compliance_probes.py:105:@pytest.mark.skip(  # TestOnlineDigestExecution
```

No `skipif`, no `pytest.skip()`, no `importorskip`. Only two markers exist:

- **1 xfail** — `test_contains_form` (the `x` in the unit run) — F8 signup-form↔API mismatch.
  Confirmed present and firing as XFAIL with the F8 reason. **NOT a silent skip.**
- **1 skip marker** on class `TestOnlineDigestExecution` — but the class has **zero `test_`
  methods** (docstring-only placeholder; collect-only of redteam-evals returns 32 with no
  `OnlineDigest` entry). It contributes **0 skipped tests** — a deliberately-visible gap
  marker for the Postgres-dependent digest round-trip, `reason="probe-unavailable: requires
postgres"`. Compliant with `probe-driven-verification.md` MUST-3 (structural skip, no regex
  fallback). **No hidden broken behavior.**

Net: **0 unexpected skips, 1 expected xfail.** Suite health is GREEN.

## 3. Per-module coverage — comms-wedge modules

### WhatsApp channel — all 7 modules, grep for importing tests

```
$ for m in auto_reply inbound parser rate_limiter sender signature utils; do
    grep -rl "whatsapp.$m|from sequor.whatsapp.$m" tests/ | wc -l ; done
whatsapp.auto_reply  -> 0
whatsapp.inbound     -> 0
whatsapp.parser      -> 0
whatsapp.rate_limiter-> 0
whatsapp.sender      -> 0
whatsapp.signature   -> 0
whatsapp.utils       -> 0
```

Broad sweep confirms it: the ONLY `whatsapp` token anywhere in `tests/` is a string literal
channel arg in `test_classifier.py:326` (`channel="whatsapp"`) — not an import of any module.

```
$ grep -rn "whatsapp" tests/   # 2 hits, both the string literal in test_classifier.py
$ grep -rn "verify_meta_signature" tests/   # exit 1 — ZERO hits
```

**DEVIATIONS' claim is CONFIRMED true and its log is ACCURATE:** all 7 `src/sequor/whatsapp/`
modules have 0 importing tests, including `signature.py::verify_meta_signature` (Meta Cloud API
webhook HMAC — a working but 0%-tested security control) and `rate_limiter.py` (0 tests). Logged
in `specs/DEVIATIONS.md` → "WhatsApp test suite (HIGH, coverage) — recommend BUILD".

## 4. Eval-harness accretion (Step 4b) — probe → defect map

Every probe class in `tests/redteam-evals/` and its prior-wave defect:

| Probe class / function                               | Prior-wave defect                                 | Mapped |
| ---------------------------------------------------- | ------------------------------------------------- | ------ |
| `TestR1AuthBypass` (valid/tampered/alg=none)         | R1 CRITICAL JWT auth-bypass + alg:none forgery    | ✓      |
| `TestR2FailClosedDefault::test_app_env_defaults…`    | R1/R2 fail-closed `app_env` default (auth+crypto) | ✓      |
| `TestR3N3RateLimiterFailClosed`                      | R3 N3 rate-limiter fail-closed at capacity        | ✓      |
| `TestR3N2DnsDomainValidation`                        | R3 N2 DNS hostname validation                     | ✓      |
| `TestR3N1UploadBound`                                | R3 N1 upload size bound                           | ✓      |
| `TestR3DnsResolverHardening` (timeout, no-propagate) | R3 DNS resolver hardening                         | ✓      |
| `TestR3AnswerabilityUnboundGuard` (NameError guard)  | R3 answerability `response` free-name NameError   | ✓      |
| `TestR4WebhookBodyGuard`                             | R4 webhook body-size DoS guard                    | ✓      |
| `TestR3N4InboundUnverifiableRejected`                | R3 N4 inbound unverifiable-in-prod rejection      | ✓      |
| `TestR3New5HallucinationPerClaim` (3 probes)         | R3 NEW-5 per-claim hallucination denominator      | ✓      |
| `TestNew3AnswerabilityFloor`                         | R3 NEW-3 answerability<0.3 exclusion              | ✓      |
| `TestD1DigestFormat`                                 | D1 digest subject/breach-line format              | ✓      |

**Probe-driven compliance (probe-driven-verification.md):** all probes are structural /
behavioral — they call the function and assert a raise/return, or mock the LLM judge and assert
on the STRUCTURED fields (`total_claims`/`uncited_claims` ratio in `TestR3New5…`,
`passed` flag from a JSON-schema-shaped judge output). **No regex-scoring-of-semantic-prose
found.** The mechanical sweep for `def (verify|score|…)_(recommend|refus|…)` over `tests/`
returns clean. Compliant.

### Accretion GAPS — two prior HIGH defects have NO behavioral regression probe

Not every prior-wave defect is covered. Two R1/R2 HIGH fixes are guarded by nothing that fails
on regression:

- **R2 `select` NameError** on the keyphrase/mappings endpoints. Fix closed in R2 packet via
  _"AST free-name sweep: 0 hits"_ — a **source sweep**, which `testing.md` § "Behavioral
  Regression Tests Over Source-Grep" BLOCKS as a sole assertion. The endpoints ship live
  (`src/sequor/onboarding/app.py:1411 GET`, `:1456 POST /api/v1/portal/keyphrase/mappings`)
  and have **zero endpoint tests** (`grep -rniE 'keyphrase|mappings' tests/` → empty).
- **R1 500-handler traceback/`str(e)` leak** on login/signup/upload. Fix returns generic
  `{"detail": "Internal server error"}` (app.py:261, 321, 426, 579, 713). **No test asserts the
  error body is generic / does NOT contain exception text.** A refactor re-introducing
  `detail=str(e)` ships an information-disclosure regression with a green suite.

## 5. Security/auth coverage floors (100% for auth/security-critical)

| Security control                                         | Behavioral coverage                                    | Floor status       |
| -------------------------------------------------------- | ------------------------------------------------------ | ------------------ |
| JWT sign/decode + alg:none (auth.py)                     | `TestR1AuthBypass`                                     | MET                |
| `EncryptedString` fail-closed                            | `test_encrypted_column.py` + `TestR2FailClosedDefault` | MET                |
| Stripe webhook signature                                 | `test_billing_webhook_verification.py`                 | MET                |
| SendGrid inbound signature                               | `test_sendgrid_signature.py`                           | MET                |
| **WhatsApp Meta webhook HMAC** (`verify_meta_signature`) | **0% — zero tests**                                    | **VIOLATED**       |
| WhatsApp rate limiter                                    | 0% — zero tests                                        | (HIGH, logged)     |
| 500-handler error-body non-leak                          | 0% — no assertion                                      | (accretion gap G3) |

The Meta webhook HMAC is a security-critical control (webhook authenticity) sitting at 0%
against a mandated 100% floor. It is the highest-priority item inside the logged WhatsApp gap.

## Findings ledger

| ID  | Sev  | Module / area                                                    | Evidence                                                                                                                                                                                  | NEW vs LOGGED                                                                                           |
| --- | ---- | ---------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| G1  | HIGH | `whatsapp/*` (7 modules); esp. `signature.py`, `rate_limiter.py` | `grep -rn verify_meta_signature tests/` → exit 1; all 7 → 0 importing tests                                                                                                               | **LOGGED** — DEVIATIONS "WhatsApp test suite (HIGH, coverage) — recommend BUILD"; log verified accurate |
| G2  | HIGH | `onboarding/app.py` keyphrase/mappings (R2 `select` NameError)   | endpoints at app.py:1411/1456 live; `grep -rniE 'keyphrase\|mappings' tests/` → empty; R2 closure was AST-sweep only (blocked as sole assertion)                                          | **NEW** (accretion gap)                                                                                 |
| G3  | HIGH | `onboarding/app.py` 500 handlers (R1 traceback-leak fix)         | generic body at app.py:261/321/426/579/713; no test asserts body lacks `str(e)`/traceback                                                                                                 | **NEW** (accretion gap; security info-disclosure)                                                       |
| G4  | LOW  | `test_onboarding_api.py::test_contains_form` xfail               | marker uses `strict=False`; `testing.md` xfail-strict MUST mandates `strict=True` for deferred conformance vectors → XPASS stays green-silent, weakening the "tripwire" the reason claims | **NEW** (test hygiene)                                                                                  |

## Convergence read (test-coverage axis)

- Suite is GREEN and honestly collected (549, 0 errors, 0 unexpected skips).
- **1 LOGGED HIGH** (G1 WhatsApp) — correctly parked behind the F5 BUILD gate; not an open finding.
- **2 NEW HIGH accretion gaps** (G2, G3) — prior HIGH defects whose closure rests on source-sweep
  / no assertion rather than a behavioral regression probe. Per `testing.md` Audit Mode + the
  Step-4 accretion rule these BLOCK a clean test-coverage convergence until each gets one
  behavioral test (G2: hit the keyphrase endpoint, assert 200/JSON not 500; G3: assert the 500
  body equals the generic string and excludes the exception text).
- **1 NEW LOW** (G4) — flip the F8 xfail to `strict=True`.
