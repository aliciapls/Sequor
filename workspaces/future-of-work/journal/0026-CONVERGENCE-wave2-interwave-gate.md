# Journal 0026 — Wave 2 Inter-Wave Gate CONVERGED

Date: 2026-07-09 · Branch: `main` · HEAD: `5d6f8a6`

## Gate summary

Inter-wave gate (G1–G5) fired after Wave 2 (A3 auto-send gate unification) per
`wave-loop.md` MUST-2. Wave 2 was the last planned wave; this gate closes the cycle.

| Step | Action                          | Status                                        |
| ---- | ------------------------------- | --------------------------------------------- |
| G1   | /redteam to convergence         | ✅ CONVERGED (2 consecutive clean rounds, R6) |
| G2   | Capture learning                | ✅ This journal + session notes refresh       |
| G3   | Update specs + remaining todos  | ✅ See below                                  |
| G4   | Re-value-rank                   | ✅ See forest below                           |
| G5   | Launch next wave / declare done | ✅ DECLARE DONE (no wave 3 planned)           |

## R6 findings and fixes

Round 6 (holistic post-multi-wave) found 4 MEDIUM defects — all fixed this session:

1. **DuplicateEmailError swallowed by `except Exception`** (`9020f3e`): The RLS UUID cast
   error guard caught `DuplicateEmailError` (subclass of `Exception`) preventing dup-email
   rejection from propagating. Split handler: `except DuplicateEmailError: raise` before
   `except Exception`.

2. **bcrypt truncation at 72 bytes** (`5d6f8a6`): `schemas.py` accepted passwords up to 128
   chars, but bcrypt silently truncates beyond 72 bytes. Capped `max_length` at 72.

3. **Email confidence_badge silent-no-op** (`5d6f8a6`): `build_auto_reply_email` accepted
   `confidence_badge: str` but never rendered it — zero-tolerance Rule 3c violation.
   Wired into the email footer.

4. **Dead `if TYPE_CHECKING: pass` block** (`5d6f8a6`): Inert code left after refactor in
   `escalation/service.py`. Removed block + unused import.

## Learning capture

**What the plan claimed vs what redteam found:**

- Plan claimed "A3 unification ≈2 invariants, ≤3–4 call-graph hops, <500 LOC load-bearing" —
  this was accurate. The A3 gate was correctly unified; all 3 response paths gate through
  `should_auto_respond`; both gate and badge read the unified quantity. Redteam confirmed.

- The `except Exception` pattern introduced by the prod hotfix (`a5ea4a8`) was the only real
  correctness regression found across both waves. Lesson: safety-guard error handlers that
  swallow exceptions MUST explicitly re-raise domain-specific errors.

- The email confidence badge (NEW-1 in DEVIATIONS.md) was partially addressed — the badge
  is now rendered in the email footer. WhatsApp already had it. Spec parity for this item
  is now PARTIAL (email: done; WhatsApp: partially, missing "Reply STOP").

## Forest — remaining items

All remaining items are tracked in `DEVIATIONS.md`:

| ID             | Item                                                                         | Status                                           |
| -------------- | ---------------------------------------------------------------------------- | ------------------------------------------------ |
| F11            | Demo the platform end-to-end                                                 | Queued (needs Ollama + SendGrid + WhatsApp keys) |
| F12            | Fix `sequor_runtime` RLS signup                                              | BLOCKED (ORM flush fails under non-owner role)   |
| F13            | Configure API keys (SendGrid, Stripe, WhatsApp, Ollama)                      | Queued                                           |
| F7             | Wave-1 tail hardening                                                        | Queued (low)                                     |
| F9             | Wave-1 advisory deferrals                                                    | Queued (low)                                     |
| NEW-1          | Confidence badge in email partially addressed; WhatsApp "Reply STOP" missing | Open                                             |
| NEW-4          | Staleness warning not implemented                                            | Open (build-gated)                               |
| rag-uncited-1  | 1–50% graded-confidence path                                                 | Open (reconcile)                                 |
| F3             | Routing flywheel not built                                                   | Open (build-gated)                               |
| F1             | Upload malware scan                                                          | Open (build-gated)                               |
| WhatsApp tests | 0 tests for whatsapp/ modules                                                | Open (build-gated)                               |

## Value re-rank (G4)

Top remaining value items, re-ranked:

1. **F11 — Demo** (HIGHEST): User literal "demonstrate the platform." Needs API keys.
2. **F13 — Configure API keys** (HIGH): Unblocks F11. SendGrid + WhatsApp + Ollama.
3. **F12 — RLS `sequor_runtime` fix** (MEDIUM): Security infra; blocked on root cause.
4. **Remaining DEVIATIONS items** (LOW): Build-gated, no user urgency signal.

## Session notes

Updated `workspaces/future-of-work/.session-notes` with current state + traps.
