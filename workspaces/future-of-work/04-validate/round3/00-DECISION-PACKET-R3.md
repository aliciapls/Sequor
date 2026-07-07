# /redteam Round 3 — Decision Packet

Date 2026-07-05 · Branch `fix/redteam-r1-security-correctness` · Posture L5_DELEGATED.
Round 3 ran 4 independent reviewers (spec-parity, security, test-coverage, code-quality) over the 7 SHIPPED comms-wedge specs + the branch diff. This packet is your decision surface; everything in "Closed autonomously" needed no decision.

---

## Closed autonomously this session (defects — no decision needed)

Nine defects fixed + a probe-driven eval-harness added, all committed to this branch (commit `3c68654`), each with a regression probe:

- **Broken test suite unblocked** — the digest feature was missing two functions the tests import, which broke all integration-test collection. Added them; collection went from 3 errors to clean (516 tests).
- **File-upload memory crash (2nd door)** — the earlier fix bounded one upload door; a second door (the logged-in customer's upload) was still unbounded. Now bounded — a giant file is rejected instead of crashing the server.
- **Rate limiter could be switched off by flooding** — an attacker sending from many addresses could fill the limiter and then bypass it entirely. Now it stays on (evicts oldest instead of failing open).
- **Anonymous DNS-check abuse** — the domain-check endpoints had no timeout, no rate limit, and weak input checks. Added all three.
- **Unsigned inbound email slipped through** — in production, an empty-body webhook skipped signature checking. Now anything that can't be verified is rejected.
- **Silent DNS errors** — DNS failures were swallowed with no log. Now logged.
- **Hallucination check math** — the "too many unsupported claims" check divided by the wrong number. Fixed to match the spec (per-claim).
- **Weak-answer filter** — passages the AI can't actually answer from are now excluded from replies (was specified, never implemented).
- **A latent crash guard** in the answer-scoring path.

**Eval-harness**: a new probe suite (`tests/redteam-evals/`) that re-checks every one of these defects on each run so they can't silently come back. 23 probes, all green.

**Unit tests**: 431 pass. The 1 remaining failure (`test_contains_form`) is the signup form↔API mismatch (F8 below) — a real question for you, not a stale test.

All spec↔code gaps are now **logged** in `specs/DEVIATIONS.md`, so none is an un-tracked issue.

---

## GROUP A — Product-truth & compliance decisions (your call)

### A1 — Encrypt message content at rest (recommend BUILD; it's the one CRITICAL)

- **What:** Your spec promises "all personal data encrypted at rest (PDPA)." Today, customer message bodies, AI replies, and learned answers are stored as plain text — only email/phone are encrypted. A database backup leak would expose all customer conversations in clear.
- **Why it's not already fixed:** doing it safely is a multi-step build, not a one-line change. The encryption machinery fails _closed_ — if we just flip the columns on without first wiring the per-customer key into every save path, the entire auto-reply pipeline would stop working (worse than today). So this needs a proper, tested build wave, not a rushed toggle.
- **Recommendation:** BUILD it as its own wave (scoped in `DEVIATIONS.md` A1). **Con:** encrypted text can't be SQL-searched (your search already uses a separate path, so impact is small); needs a data migration.
- **→ RATIFY (schedule the build) / OVERRIDE (accept plaintext bodies with written PDPA sign-off): ______**

### A2 — "Separate database per customer" (needs a legal answer first)

- **What:** Your spec states, as a PDPA requirement, that each customer's data must live in a _separate schema_, not just be tagged with a customer ID. Today the code tags by customer ID on shared tables (the separate schemas are created but never used).
- **Recommendation:** get a PDPA determination. If a strong customer-ID tag is legally acceptable → we amend the spec (cheap). If the separate-schema rule stands → it's a large build. I won't guess a compliance fact.
- **→ RATIFY (build separate-schema) / OVERRIDE (amend spec, with legal sign-off) / DEFER (get counsel): ______**

### A3 — When does the AI reply on its own vs ask a human?

- **What:** Your spec contradicts itself on the confidence cutoff (">90%" in one place, ">95%/80–95%" in another), and the code uses three different numbers. This controls how often a machine reply goes out without a human checking it.
- **Recommendation:** use the more cautious rule (auto-send only above 95%; 80–95% goes out with a visible "moderate confidence" badge). Fewer machine replies without a human is the safer default for a compliance-sensitive product. The code unification is safety-critical and needs live-infrastructure testing, so it's scoped as its own shard.
- **Con:** more messages route to a human (slower replies, more human load) than the looser ">90%" rule.
- **→ RATIFY (95% cautious) / OVERRIDE (90% looser): ______**

### A4 — The specced-but-unbuilt features (recommend sequencing behind F5, not cramming)

Confidence badges on replies, staleness warnings on old documents, and the WhatsApp test suite are all specced but unbuilt. Per your own repivot brief, F5 (validate director-as-buyer) is the top priority and gates scaling the build. Recommend planning these as value-ranked waves _after_ the F5 decision, not cramming them for a green banner.

- **→ Sequence behind F5 (recommended) / build now: ______**

### Spec contradictions to ratify (I recommend canonical values in `specs/DEVIATIONS.md`)

Dedup window (48h vs 72h → **72h**), audit retention (flat 24-mo vs tiered → **tiered by plan** — a pricing/compliance call), template count (5/6/8 → **8**), embedding model (spec says OpenAI/1536, code ships local/768 → **amend to shipped**). These are mostly internal cleanups; the audit-retention one is a real product/compliance choice.

- **→ Ratify the recommended values / adjust: ______**

---

## GROUP B — PR #7 merge (production deploy) — unchanged gate

This branch now carries R1 + R2 + R3 fixes. **Merging = a Vercel production deploy.** Before merge, confirm these are set in the Vercel production environment (the fail-closed changes mean the app now _refuses to boot_ without them): `JWT_SECRET` (≥32 bytes), `ENCRYPTION_MASTER_KEY`, `APP_ENV=production`.

- **→ CONFIRM env is set + merge / hold: ______**

---

## Convergence status

- **Defect surface: CONVERGED** — 0 CRITICAL / 0 HIGH _defects_ remain open; all 9 R3 defects fixed + probe-guarded; 2 consecutive clean rounds on the defect surface (R2 holistic + R3 with fixes).
- **Spec-ahead surface: LOGGED, not closed** — 1 CRITICAL (A1 encryption) + the HIGH feature/compliance items are logged deviations recommended for build/counsel, per your F5-gated brief. Literal 0-HIGH requires the Group-A decisions + the scoped builds. That is a product/strategy gate (F5), not an autonomous one.

## Process follow-up

- Repo is in fresh-substrate-adopter state (no operator roster). Run `/whoami --enroll-genesis` before the next `/release`.
