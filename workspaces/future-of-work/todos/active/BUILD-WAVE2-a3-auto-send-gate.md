# Build Wave 2 — A3 Auto-Send Gate Unification

Value-ranked, user-ratified 2026-07-05 ("approved all"). Source of truth: `specs/DEVIATIONS.md`
§A3 + `workspaces/future-of-work/02-plans/06-a3-unification-plan.md` + `01-analysis/10-a3-auto-send-gate-unification.md`.
Branch: `feat/a3-auto-send-gate` (**stacked on `feat/data-layer-security` = PR #8**, because A3
overlaps Wave-1's `email/whatsapp auto_reply.py` — branching from `main` would conflict).

**Safety-critical**: this is the machine-reply-without-human gate. Tier-2 verification is
mandatory (not optional). The unified change MUST be exercised end-to-end against real infra.

## Wave declaration (per `wave-loop.md` MUST-1)

- **Wave 2 — A3 auto-send gate unification (THIS FILE).** HIGHEST remaining value: safety-critical
  (the gate that decides whether the AI replies without a human). Anchor: `DEVIATIONS.md` §A3
  (ratified); `response-accuracy.md` core principle ("sending wrong information is worse than
  sending none"). Single convergence surface (one predicate + one confidence quantity) → ONE wave.
- **Wave 3 — A4 moats + R5-01 (provisional, in `BUILD-WAVE-data-layer-security.md`).** NEW-1/NEW-8
  confidence badge/footer render, NEW-4 staleness warning, WhatsApp test suite, F3 routing
  flywheel, R5-01 onboarding-upload token gate. Re-validated at the Wave-2 inter-wave gate.

Inter-wave gate (G1–G5) fires after Wave 2. Wave 2's own `/redteam` runs to convergence before
the gate.

## Shard fit (per `autonomous-execution.md` § Per-Session Capacity Budget)

One shard: ≈2 invariants (auto-send predicate correctness + gate/badge quantity agreement),
≤3–4 call-graph hops (`should_auto_respond` ← `response.py` ← `auto_reply.py`), <500 LOC
load-bearing. Live feedback loop (eval-harness + `tests/unit/test_classifier.py` should_auto_respond
cases + Tier-2 PG) → feedback-loop multiplier applies. If the `ResponseConfidence` extraction in
`rag_pipeline.py` proves load-bearing mid-`/implement`, split into 2a (quantity) + 2b (predicate +
parity) at the invariant boundary — NOT mid-shard.

## Todos (value-ranked within the shard; dependency order)

### 2.1 — Define the unified `ResponseConfidence` quantity

**Implements:** `specs/response-accuracy.md` §Confidence Badge Specification (single unified
confidence), `01-analysis/10-...` §4.1.

- Compute ONE confidence per response in `rag_pipeline.py`/`response.py`: `classifier_confidence ×
synthesis_confidence × (1.0 if hallucination_passed else 0.5) × staleness_factor`. Reuse the
  components the spec already names — no new signal.
- Both the gate (`response.py:107/118`) and the badge (`response.py:137–138`) read THIS quantity,
  closing the classifier-vs-synthesis split.
- **Acceptance:** a single `ResponseConfidence` value is computed once per response and consumed by
  BOTH the auto-send decision and the badge render. No path reads `classification.confidence` for
  the gate while reading `synthesis.confidence` for the badge.

### 2.2 — Revive `should_auto_respond` as the sole auto-send predicate

**Implements:** `specs/response-accuracy.md` §Response Options (auto-send decision),
`01-analysis/10-...` §4.2.

- Make `MessageClassifier.should_auto_respond` (`classifier.py:290`, currently orphan) the ONLY
  auto-send decision. Amend its signature to take the unified `ResponseConfidence` (+ category for
  the high-stakes short-circuit) instead of `ClassificationResult`; update its 4 existing test call
  sites (`tests/unit/test_classifier.py:239–292`) same-shard.
- Delete the 6 inlined gates: `response.py:118 / 214 / 268`, the route-to-backup `0.6` heuristic
  (l.122), and the two channel final-gates. All three response paths (RAG / learned / fallback)
  route through the predicate.
- **Acceptance:** `grep -rn 'was_auto_sent\s*=' src/` shows the assignment in exactly ONE place (the
  predicate); the 6 inlined sites are gone. `should_auto_respond` has ≥1 production caller.

### 2.3 — WIRE `Account.confidence_threshold` into the predicate (currently dead config)

**Implements:** `specs/response-accuracy.md` §Confidence Threshold Configuration (per-account,
configurable), `01-analysis/10-...` §4.3. This is the build/wire split: the field is built
(`models.py:275`, written at signup) but never WIRED to the gate.

- Feed `Account.confidence_threshold` (default 0.90) into `should_auto_respond`. The auto-reply
  modules currently bind their own `CONFIDENCE_THRESHOLD_AUTO_REPLY` constant (`email:72`,
  `whatsapp:74`) — replace with the per-account value passed through the call chain.
- `<70%` keeps the existing user-acknowledgement prompt (already specified); high-stakes always
  routes to backup (dispatcher, unchanged).
- **Acceptance:** `grep -rn 'confidence_threshold' src/` shows the Account field READ at the
  predicate; an account with `confidence_threshold=0.95` only auto-sends ≥0.95 (Tier-2 test 2.5d).

### 2.4 — Channel parity: WhatsApp honors `was_auto_sent` (matches email)

**Implements:** `01-analysis/10-...` §4.4, agent-3 verification.

- Both `email/auto_reply.py:168` and `whatsapp/auto_reply.py:166` call the unified predicate (so
  WhatsApp's send-gate becomes `was_auto_sent ∧ …`, matching email — closing the asymmetry).
- **Acceptance:** a WhatsApp message with `was_auto_sent=False` is NOT sent (parity with email);
  Tier-2 test 2.5c.

### 2.5 — Tier-2 behavioral regression tests (the safety gate MUST be exercised)

**Implements:** `testing.md` §Regression + §Tier-2, `probe-driven-verification.md`.

- (a) classifier 0.95 + synthesis 0.3 → **NOT auto-sent** post-fix (the core bug; must flip).
- (b) unified 0.9 → auto-send with the correct High/Moderate badge.
- (c) WhatsApp `was_auto_sent=False` → not sent (parity).
- (d) `Account.confidence_threshold=0.95` → only ≥0.95 auto-sends.
- Re-use the existing `should_auto_respond` unit cases (routine-high passes; high-stakes /
  critical-urgency / below-threshold blocked) — promote to exercise the unified quantity.
- **Acceptance:** all four flip-tests green against real PG (Tier-2); the eval-harness probe (2.7)
  passes.

### 2.6 — WhatsApp footer renders the confidence figure (NEW-8 confidence half)

**Implements:** `specs/response-accuracy.md` §Badge Display (WhatsApp footer), `DEVIATIONS.md` §NEW-8
(confidence half). Pairs with the badge unification — the badge renders in this footer.

- `DEFAULT_WHATSAPP_FOOTER` (`whatsapp/auto_reply.py:26–29`) gains the `[Auto-generated; N%
confidence …]` token driven by the unified quantity.
- The "Reply STOP" Meta opt-out keyword stays a SEPARATE compliance decision under §NEW-8 (NOT this
  shard).
- **Acceptance:** the shipped WhatsApp auto-reply footer includes the confidence figure; the
  "Reply STOP" keyword is explicitly out-of-scope (tracked under NEW-8).

### 2.7 — Eval-harness adversarial probe

**Implements:** `probe-driven-verification.md`, `04-validate/` eval harness.

- Add a probe for the exact failure mode: "confident classifier + uncertain synthesis must not
  auto-send." Schema + scoring rule (NOT regex-on-prose).
- **Acceptance:** probe green post-fix; would have failed pre-fix (the regression-detection property).

### 2.8 — Spec reconciliation (CODE-FIRST, same PR as the implementation)

**Implements:** `specs-authority.md` Rule 5 (first-instance), `spec-accuracy.md` Rule 5 (code-first).

- Amend `response-accuracy.md` Option C's ">90% auto-send" to the badge table (>80%
  Moderate-and-above); declare the badge table canonical + the unified confidence the single
  quantity both surfaces read. Lands in the SAME PR as the code (the code makes it true).
- Sibling-spec re-derivation sweep (`message-routing.md`, `data-model.md`, `rag-pipeline.md`) per
  `specs-authority.md` Rule 5b.
- Close `DEVIATIONS.md` §A3.

## Out of scope (verified — do NOT add)

- **"Restore the urgency guard on the learned-answer path"** (deviation note) — ALREADY enforced at
  `response.py::generate` l.86–91 (HIGH_STAKES / HIGH-CRITICAL urgency → backup before the learned
  branch). Verification refuted this claim; journal 0024. No task.
- **WhatsApp "Reply STOP" opt-out keyword** — §NEW-8 compliance decision (separate shard).
- **Wave 3 (A4 moats, R5-01)** — provisional, re-validated at the Wave-2 inter-wave gate.

## Risks (RISK journal-worthy if materialized)

- **Over-send regression** (unified quantity too generous → low-real-confidence auto-sends).
  Mitigation: the 2.5a flip-test + the conservative badge-table floor.
- **Under-send regression** (too conservative → routine queries routed to humans, collapsing
  automation value). Mitigation: default threshold at the table floor; existing routine-high tests
  must still pass.
- **`should_auto_respond` signature change** breaks the 4 test call sites → update same-shard (2.2).
