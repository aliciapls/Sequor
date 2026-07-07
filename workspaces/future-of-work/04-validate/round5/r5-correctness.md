# R5 — Correctness + Code-Quality Audit (independent re-derivation)

Scope: `git diff main...HEAD` (src/sequor/**). Re-derived from source; prior R1–R4 self-reports NOT trusted.
Auditor: R5 correctness lane. Date: 2026-07-05.

## Verdict

**CLEAN — zero NEW correctness defects.** All prior-round fixes verified holding against source.
Two known-good items (`confidence_badge` no-op, digest over-count) are accurately LOGGED, not open.
Mechanical sweeps green: `pytest --collect-only -q` → 549 collected, exit 0; no TODO/FIXME/STUB/
NotImplementedError/placeholder in added src lines.

---

## Item-by-item findings

### 1. None-dereferences / latent AttributeError — CLEAN (guards hold; no new siblings)

Verified the two guards from commit `8321ba5` hold in current HEAD:

- `onboarding/app.py::auth_login` (line ~658-673): `operator = result.scalars().first()`; then
  `op_email = operator.email if operator else email` and the account lookup is guarded
  `if operator is not None:` before `operator.account_id`. HOLDS.
- `onboarding/app.py::portal_api_upload_document` (line ~1305-1308): `row = result.fetchone();
  if row is None: raise RuntimeError("document insert returned no id row")` before `row[0]`. HOLDS.

Swept EVERY other fetch site in app.py for the same class (fetch → unguarded attribute/subscript):
- L619 `contact = row.mappings().first()` → guarded `if not contact:` (401). OK
- L1062 `row = result.first()` → guarded `if not row:` (404); unpack `esc, msg, contact, backup = row`. OK
- L1199 `row = check.fetchone()` → guarded `if not row:`. OK
- L1487 `doc = doc_result.scalar_one_or_none()` → guarded `if not doc:` (404) before later `doc.name`. OK
- L1704 `tenant = ...first()` → `tenant.plan.value if tenant else "free"`. OK
- L1804/1807 `contact`/`account = ...first()` → `contact.name if contact else ...`, `account.name if account else ""`. OK
- `digest/service.py` `account_row = (...).first()` → `account_row.name if account_row is not None else ...`. OK
- `digest/service.py` `backups` → `if not backups: logger.warning(...); return None`. OK

`session.scalar(select(func.count(...)))` counts (L867-890, L1710-1726) always return an int (never
None) and are additionally `or 0`-guarded at use. No unguarded None-deref of this class remains. **NEW: none.**

MINOR (pre-existing, not branch-introduced): `portal_api_usage` (app.py ~L1707) fetches
`account = account_result.scalars().first()` that is never referenced afterward — a dead DB round-trip.
Diff shows this is a `-`/`+` reformat of an identical query already on main → PRE-EXISTING, LOW, no crash.

### 2. Hallucination-check math — CORRECT (re-derived against spec)

`rag_pipeline.py::_check_hallucination`:
```python
if total_claims > 0 and uncited / total_claims > 0.5:
    passed = False
elif total_claims == 0 and uncited > 0:   # malformed judge → fail CLOSED
    passed = False
```
Spec `rag-pipeline.md:102`: "If >50% of claims are un-cited: response is rejected". Denominator is
`total_claims` (per-claim), float division, `> 0.5` = strictly >50%. **Arithmetic matches the spec.**
The R4 malformed-judge branch (total==0, uncited>0 → fail closed) is a correct hardening, not a regression.

OBSERVATION (pre-existing spec-parity gap, NOT branch-introduced, informational): spec `:101` also
requires "if ANY un-cited claims found → flagged, confidence reduced, routed to backup review". The
code reduces confidence (×0.5 in `synthesize`) ONLY when `passed==False` (>50%); for 1–50% uncited,
`passed` stays True and confidence is not reduced. The pre-branch code was also binary
(`uncited > len(passages)*0.5`), so this partial gap predates the branch. `uncited_claims` IS surfaced
on `SynthesisResult` (L316) for downstream use. Recommend a DEVIATIONS row if not already covered; not
an R5 blocking finding.

### 3. `_ANSWERABILITY_FLOOR` weak-answer filter — WIRED (not a 3c no-op)

`rag_pipeline.py:119` inside the retrieval loop:
```python
if answerability < _ANSWERABILITY_FLOOR:   # 0.3
    continue
```
The `continue` genuinely excludes sub-floor passages from `passages` → they never reach synthesis.
Matches spec `:89` ("If answerability < 0.3, the passage is excluded even if vector similarity is high").
Empty-passages fallthrough is handled: `synthesize` returns the "I don't have information … forwarded
for review" uncertain result when `not retrieval_result.passages`. **Not a defined-but-unused constant.
No zero-tolerance 3c violation.**

### 4. R4 "3 self-introduced LOWs + N1 sibling" (commit 736b149) — ALL CLOSED, no regression

- DNS `$`→`\Z`: `app.py::_DNS_DOMAIN_RE` now ends `...\Z`; probes `"example.com\n"`,
  `"example.com\nevil.com"` added and assert non-match. CLOSED.
- Rate-limiter FIFO comment: `rate_limiter.py` evicts `self._windows.pop(next(iter(self._windows)))`
  = oldest-inserted (dict insertion order) = FIFO; comment now says "oldest-INSERTED (FIFO)". Behavior
  matches comment; fails closed; bounded (evict 1 + add 1 = net _MAX_TRACKED_KEYS). CLOSED.
- Malformed-judge fail-closed: verified in item 2. CLOSED.
- N1 sibling — webhook Content-Length guard: `_oversized_body(request)` (413 on oversize, 400 on
  non-int Content-Length, None when absent → proxy authoritative) is the first line of ALL THREE
  handlers: `stripe_webhook`, `email_inbound`, `whatsapp_inbound`. Probes added. CLOSED.

### 5. Silent fallbacks (zero-tolerance Rule 3) — CLEAN

Swept added lines. No bare `except:`, no `except: pass`, no empty `catch`, no
`except Exception: return None` without logging introduced.
- `dns/service.py`: the old `except (..., Exception): return False` catch-all was SPLIT — specific
  DNS-absence exceptions return False (expected not-configured case), and a separate `except Exception:`
  now `logger.warning(..., exc_info=True)`. IMPROVEMENT, not a swallow.
- `app.py::onboarding.signup` `except Exception:` → `_logger.exception("onboarding.signup.error")`
  then returns a generic 500 (no traceback leak). Logs. OK.
- `app.py` admin backfill `except Exception:` → `_logger.exception("admin.backfill.contact_failed", ...)`. OK.
- `rag_pipeline.py::_check_hallucination` `except (json.JSONDecodeError, Exception) as e:` →
  `logger.warning("rag.hallucination.check_failed", error=str(e)); return {"passed": False, ...}`.
  Logs + fails closed. OK.

MINOR (code-quality, non-blocking): that except tuple `(json.JSONDecodeError, Exception)` is redundant
(`Exception` supersets `JSONDecodeError`). Also its return `{"passed": False, "uncited_claims": 0}`
omits the `total_claims` key the happy path returns — verified SAFE: no consumer reads
`hallucination_result["total_claims"]` (consumers use only `["passed"]` and `["uncited_claims"]` at
L290/307/315/316), so no KeyError. Cosmetic only.

### 6. Documented-kwarg-unused — `build_auto_reply_email(confidence_badge)` — REAL 3c, ACCURATELY LOGGED

Confirmed: `email/templates.py:117` signature accepts `confidence_badge: str`, but the function body
(L121-140) never references it — genuine zero-tolerance 3c silent no-op (the only caller,
`email/auto_reply.py:317`, passes it and it is dropped). DEVIATIONS.md NEW-1 states exactly this:
"the kwarg has zero uses (silent no-op, zero-tolerance 3c)", classifies HIGH, recommends BUILD the
badge/footer rendering or remove the kwarg, sequenced behind the F5 validation gate. **The log is
accurate. LOGGED, not an open R5 finding.** (Dispatch is BUILD-vs-remove behind F5, per the logged row.)

### 7. Dual-shape hasattr guard (zero-tolerance 3d) — none

Only `hasattr` added in the diff: `app.py:~1525`
`contact["tier"].value if hasattr(contact["tier"], "value") else str(contact["tier"])`. This coerces a
raw-SQL row value (enum vs string, driver-dependent) — BOTH branches yield the tier string, deterministic,
no behavior silently skipped. Not the 3d anti-pattern (dual-shape RETURN consumed via existence guard that
silently flips). Acceptable; `isinstance(Enum)` would be marginally cleaner. Not a defect.

### 8. Mechanical sweeps — GREEN

- `python -m pytest --collect-only -q` → `549 tests collected`, exit 0, no collection errors.
- Diff grep of added src lines for `TODO|FIXME|STUB|XXX|NotImplementedError|placeholder` → none.

---

## Also verified

- Digest tenant-scoping over-count for multi-account tenants: DEVIATIONS.md logs it accurately as a
  data-model limitation ("Not introduced by R3"); correct for shipped one-account-per-tenant data model.
  LOGGED, not open.

## Summary table

| # | Area | Result | NEW/LOGGED |
|---|------|--------|-----------|
| 1 | None-derefs | guards hold; no new siblings | none NEW (1 pre-existing LOW dead query) |
| 2 | Hallucination math | matches spec >50% claims | none NEW (1 pre-existing spec-101 partial gap, informational) |
| 3 | Answerability floor | wired via `continue` | none |
| 4 | R4 LOWs + N1 sibling | all closed, no regression | none |
| 5 | Silent fallbacks | all log + fail closed | none NEW (1 cosmetic redundant-except) |
| 6 | confidence_badge no-op | real 3c | LOGGED (DEVIATIONS NEW-1, accurate) |
| 7 | hasattr dual-shape | not the anti-pattern | none |
| 8 | Mechanical sweeps | collect-only 549 exit 0; no stubs | none |
