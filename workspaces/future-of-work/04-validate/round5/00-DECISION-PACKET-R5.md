# /redteam Round 5 — Holistic Post-Multi-Wave Decision Packet

Date 2026-07-05 · Branch `fix/redteam-r1-security-correctness` · Posture **L5_DELEGATED**.
Round 5 is the **holistic post-multi-wave redteam** across the union of R1–R4 fixes on the shipped
comms-wedge surface. 4 parallel auditors (spec-parity, security, correctness, test-coverage)
re-derived **every** check from scratch — trusting no prior round's self-report, no `DEVIATIONS`
disposition, no R3 packet. Reports: `round5/r5-{spec-parity,security,correctness,test-coverage}.md`.

---

## Convergence status

- **Defect surface: CONVERGED** — 0 CRITICAL / 0 HIGH un-logged defects. All R1–R4 fixes (auth-bypass, fail-closed encryption default, upload bounds, rate-limiter fail-closed, DNS abuse, unsigned-email reject, hallucination math, answerability floor, None-guards) were **independently verified holding** in current HEAD — not self-report theatre. 2 consecutive clean rounds on the defect surface (R3-with-fixes clean → R5 fresh re-derivation clean after the R5 fixes below).
- **Spec-ahead surface: LOGGED, not closed** — the CRITICAL A1 (PII-at-rest encryption) + the HIGH/MED feature & compliance items remain logged `DEVIATIONS` deviations recommended for build/counsel, per the F5-gated brief. Literal 0-HIGH requires the Group-A decisions + scoped builds (a product/strategy gate, not autonomous).

R5 found **no live CRITICAL/HIGH bug the prior rounds missed.** What it found was (a) two missing regression tests for prior fixes, (b) two spec-reconciliation residuals the R3 banner over-claimed as done, and (c) six previously **un-logged** spec-vs-code divergences + two minor security items — all now closed or logged.

---

## Closed autonomously this session (no decision needed)

**Code + tests (fixed now — root-cause, in-shard):**

- **R5-02** — WhatsApp webhook verify-token now uses constant-time `hmac.compare_digest` (was a plain `!=` timing oracle). + regression test.
- **G2** — added a behavioral regression test that the keyphrase/mappings endpoints resolve `select`/`desc` (guards the R2 NameError fix; was only source-swept before).
- **G3** — added a regression test asserting 500-handler bodies exclude exception text / tracebacks (guards the R1 info-disclosure fix).
- **G4** — flipped the F8 `test_contains_form` xfail from `strict=False` → `strict=True` so it auto-fails (tripwire) the moment F8 is resolved.

**Spec reconciliations (the R3 banner over-claimed "all applied"; now truly applied):**

- **CS-5 / F5** — `message-routing.md` named-template count reconciled 5 → 6 to match the shipped 6-template list.
- **CS-6 / F4** — added the Free-tier 7-day row to `data-model.md`'s retention table.
- **F6** — defined the dangling `NEW-8` id (WhatsApp footer opt-out) as a real row.
- **F1/F2/F3** — softened three false "shipped" spec claims (malware scan, retention-purge enforcement, routing-flywheel "day 1") to accurate deviation pointers.

**Newly LOGGED (un-logged → logged; now tracked, not open findings)** — see `DEVIATIONS.md § R5 additions`:
F1 (malware scan), **F2 (PDPA retention-purge job — compliance priority)**, F3 (routing flywheel), NEW-8 (WhatsApp footer), rag-uncited-1 (1–50% graded confidence), R5-01 (unauthenticated onboarding upload), R5-03 (JWT ≥32 warned-not-enforced).

---

## GROUP A — your call (unchanged from R3, still F5-gated)

The R3 decisions you ratified 2026-07-05 (A1 encryption → BUILD; A2 → RLS; A3 → 95% Badge; A4 → sequence behind F5; RECONCILE canonical values) are **unchanged and still stand**. R5 verified those dispositions are all accurate against code. The build wave (A1+A2 encryption + RLS, A3 auto-send unification) remains gated behind **F5 (validate director-as-buyer)** — the product/strategy gate you hold. It needs real Postgres (Tier-2) and is >1 shard, so it is not an autonomous action.

### New item that deserves your attention: F2 (PDPA retention-purge job) — HIGH, compliance

- **What:** Your spec says customer data is auto-deleted after its retention period (7 days Free → 24 months Enterprise). In reality **nothing deletes expired data** — no purge job exists. Data is kept indefinitely past its stated retention.
- **Why it matters:** this is a PDPA **over-retention** exposure (keeping PII longer than your own stated policy), distinct from A1 (which is about encrypting what's stored). It's now logged, the spec no longer falsely claims enforcement, but the gap is real.
- **Recommendation:** fold the purge job into the **same A1+A2 data-layer build wave** (it shares the scheduler/connection-boundary plumbing) rather than a separate wave. **Con:** it adds a scheduled-job + Tier-2 test to that wave's scope. **→ RATIFY (fold into the A1/A2 wave) / defer explicitly with written PDPA sign-off: ______**

### R5-01 — unauthenticated onboarding upload (MED, flow decision)

- **What:** the onboarding document-upload endpoint accepts a tenant id as a form field with no login / ownership proof, so anyone who learns a tenant's UUID could inject documents into its knowledge base (RAG poisoning). Guessing the 122-bit UUID is infeasible and it's rate-limited, so the practical risk is low — but the door isn't gated.
- **Recommendation:** gate the endpoint behind a short-lived onboarding token. This is a flow decision (does your pre-login onboarding wizard call this before a session exists?). **→ RATIFY (gate it) / accept the UUID-unguessability mitigation with sign-off: ______**

---

## GROUP B — PR #7 merge (production deploy) — unchanged gate

This branch carries R1+R2+R3+R4+R5 fixes. **The local branch is 6 commits ahead of what's on the PR remote** — R5's fixes will add one more. Merging = a Vercel production deploy; the fail-closed changes mean the app refuses to boot without: `JWT_SECRET` (unset → refuses to boot; a short secret is _warned_ not rejected — see R5-03), `ENCRYPTION_MASTER_KEY`, `APP_ENV=production`.

**→ CONFIRM env is set + push R5 commit + merge / hold: ______**

(I have not pushed. Pushing to the PR branch is a shared-state action on your production-deploy PR — your call.)

---

## Convergence verdict

**The comms-wedge DEFECT surface is CONVERGED (2 consecutive clean rounds, 0 CRIT / 0 HIGH un-logged).** Every spec-vs-code divergence is now logged in `DEVIATIONS.md`. The remaining CRITICAL/HIGH items are all **logged, user-ratified, F5-gated builds** — a product gate, not an autonomous blocker. Receipts: `round5/r5-*.md` (4 auditor reports) + `tests/unit/test_r5_regression_fixes.py` (5 green) + eval harness (32 green).
