# /redteam Round 8 — str(e) Error Message Leakage

Date 2026-07-11 · Branch `main` (HEAD `439e5d9`) · Posture **L5_DELEGATED**.

Round 8 closes the H1/H2 `str(e)` error message leakage class tracked in `DEVIATIONS.md`
since R7. 2 rounds, 2 parallel auditors per round, re-derived from scratch.

---

## Round summary

| Round | Date       | HEAD      | CRITICAL | HIGH | MED | Outcome            |
| ----- | ---------- | --------- | -------- | ---- | --- | ------------------ |
| R1    | 2026-07-11 | `a7019e4` | 0        | 0    | 0   | 9 sites fixed      |
| R2    | 2026-07-11 | `439e5d9` | 0        | 0    | 0   | Confirmation clean |

---

## Round 1 — 9 sites fixed across 2 commits

### Commit `a7019e4` — 6 JSONResponse `str(e)` sites in `onboarding/app.py`

| ID    | Endpoint                          | Was                  | Now                           |
| ----- | --------------------------------- | -------------------- | ----------------------------- |
| R8-01 | Signup ValueError                 | `{"detail": str(e)}` | `"Invalid signup request..."` |
| R8-02 | Upload request validation         | `{"detail": str(e)}` | `"Invalid upload request..."` |
| R8-03 | Upload processing ValueError      | `{"detail": str(e)}` | `"Invalid document..."`       |
| R8-04 | Stripe webhook signature          | `{"detail": str(e)}` | `"Invalid webhook request."`  |
| R8-05 | Stripe webhook payload ValueError | `{"detail": str(e)}` | `"Invalid webhook payload."`  |
| R8-06 | Portal upload ValueError          | `{"error": str(e)}`  | `"Invalid document..."`       |

Each site now logs the actual error via `_logger.warning(...)` with `error=str(e)` as a
structured field before returning the generic message. All exception handler hierarchies
preserved (ValueError caught before Exception).

### Commit `439e5d9` — 3 RuntimeError `str(e)` sites in `ai/client.py`

| ID    | Location                             | Was                                                | Now                                                 |
| ----- | ------------------------------------ | -------------------------------------------------- | --------------------------------------------------- |
| R8-07 | `OllamaClient.generate_embeddings`   | `RuntimeError(f"OpenAI embedding failed: {e}")`    | `RuntimeError("OpenAI embedding failed") from e`    |
| R8-08 | `DeepSeekClient.generate`            | `RuntimeError(f"DeepSeek generation failed: {e}")` | `RuntimeError("DeepSeek generation failed") from e` |
| R8-09 | `DeepSeekClient.generate_embeddings` | `RuntimeError(f"OpenAI embedding failed: {e}")`    | `RuntimeError("OpenAI embedding failed") from e`    |

Same-class companions found by R1 security-reviewer. The error is already logged via
`logger.warning/error` before each raise; `from e` preserves the exception chain.

---

## Round 2 — Confirmation (verification sweep)

Both reviewer + security-reviewer confirmed:

- **0 `content.*str(e)` in `onboarding/app.py`** ✅
- **0 `RuntimeError.*{e}` in `ai/client.py`** ✅
- **0 `str(e)` in any JSONResponse body across all source files** ✅
- **0 `str(e)` in any RuntimeError/ValueError message across all source files** ✅
- **Tests: 39 passed, 1 pre-existing integration error** ✅

Full `str(e)` audit (73 occurrences across the codebase): all are in structured logger
fields, internal data structures (LLMResult.error, ParsedDocument.metadata,
AutoReplyResult.error — all verified never reaching API clients), or server-side
keyword categorization (`error_msg = str(e).lower()` → generic message selection).

---

## Accepted as-is (operator-facing only, no customer exposure)

| ID  | Description                                                        | Rationale                                                                                          |
| --- | ------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------- |
| L1  | `classifier.py:150` `reasoning=f"Classification failed: {str(e)}"` | Flows to `ai_summary` in operator escalation emails only. Not in any customer-facing API response. |
| L2  | `document_parser.py` `metadata={"error": str(e)}` (6 sites)        | Consumers only read `parsed.text`; the error metadata is never returned to clients.                |
| L3  | `client.py` `LLMResult.error=str(e)` (2 sites)                     | `safe_generate` is an orphan (zero callers); `LLMResult.error` is never accessed.                  |

---

## Verified invariants (all holding)

- **No `str(e)` in any API response body**: confirmed by mechanical grep + auditor trace ✅
- **No `str(e)` in any exception message**: 0 `RuntimeError.*{e}` / `ValueError.*{e}` ✅
- **Logger calls use structured fields**: `error=str(e)` as kwarg, not f-string interpolation ✅
- **Exception chains preserved**: all wrapping raises use `from e` ✅
- **No stubs/TODOs introduced**: 0 in changed files ✅
- **Tests**: 39 passed, 1 pre-existing integration error, 589 collected ✅

---

## Convergence verdict — CONVERGED ✅

**2 rounds, 2 consecutive clean (R1, R2), 0 CRITICAL / 0 HIGH / 0 MED un-fixed.**
Convergence criteria met per `commands/redteam.md` § Convergence Criteria.

The `str(e)` error message leakage class (H1/H2 tracked since R7) is closed. All 9 sites
(6 JSONResponse + 3 RuntimeError) now return generic messages. The `safe_generate` orphan
and `LLMResult` dead code remain as pre-existing code quality items tracked in
`DEVIATIONS.md`.

Receipts:

- R1: reviewer `af1ec96ef71ebafaf`, security-reviewer `a8d9c9be68983848e`
- R2: reviewer `ab18ba97fd1724e65`, security-reviewer `aced64004646e15f1`
- R1 fixes: `a7019e4` (6 JSONResponse sites) · `439e5d9` (3 RuntimeError sites)
