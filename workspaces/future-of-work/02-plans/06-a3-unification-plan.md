# 06 — A3 Unification Plan (Wave 2)

Implementation plan for `01-analysis/10-a3-auto-send-gate-unification.md`. Safety-critical
(machine-reply-without-human gate). Single shard unless the confidence-quantity extraction proves
load-bearing (then split 2a/2b per the analysis §6).

## Shard 2 — A3 auto-send gate unification

### 2.1 — Define the unified `ResponseConfidence` quantity (rag_pipeline.py / response.py)

- Compute ONE confidence per response: `classifier_confidence × synthesis_confidence ×
(1.0 if hallucination_passed else 0.5) × staleness_factor`, reusing the components the spec
  already names. No new signal — unify the existing ones.
- Both the gate and the badge read THIS quantity. Remove the split where the gate reads
  `classification.confidence` and the badge reads `synthesis.confidence`
  (`response.py:107/118` vs `137–138`).

### 2.2 — Revive `should_auto_respond` as the sole predicate (classifier.py / response.py)

- Make `MessageClassifier.should_auto_respond` (`classifier.py:290`, currently orphan) the
  ONLY auto-send decision, returning the unified-confidence verdict against
  `Account.confidence_threshold`.
- Delete the 6 inlined gates: `response.py:118 / 214 / 268`, the route-to-backup `0.6`
  heuristic (l.122), and the two channel final-gates. All three response paths (RAG / learned /
  fallback) route through the predicate.
- Wire `Account.confidence_threshold` (currently dead config, `models.py:275`) into the
  predicate — the per-account threshold the spec already promises (configurable; <70% requires
  the existing acknowledgement; high-stakes always routes to backup).

### 2.3 — Channel parity (email + whatsapp auto_reply)

- Both `email/auto_reply.py:168` and `whatsapp/auto_reply.py:166` call the unified predicate
  (so WhatsApp honors `was_auto_sent`, closing the asymmetry agent 3 confirmed).
- WhatsApp footer renders the confidence figure (closes §NEW-8 confidence half). The "Reply
  STOP" opt-out keyword stays a separate compliance decision under §NEW-8.

### 2.4 — Spec reconciliation (response-accuracy.md + sibling sweep)

- Amend Option C's ">90% auto-send" to the badge table (>80% Moderate-and-above auto-send);
  declare the badge table canonical and the unified confidence the single quantity both
  surfaces read.
- Sibling-spec re-derivation (`message-routing.md`, `data-model.md`, `rag-pipeline.md`) per
  `specs-authority.md` Rule 5b — grep each for the confidence thresholds / badge levels and
  align.

### 2.5 — Tier-2 verification (the safety gate MUST be exercised)

- **Behavioral regression tests** (the as-is bugs, asserted to flip):
  - classifier 0.95 + synthesis 0.3 → **NOT auto-sent** post-fix (the core bug).
  - unified 0.9 → auto-send with the correct High/Moderate badge.
  - WhatsApp: `was_auto_sent=False` → **not sent** (parity with email).
  - `Account.confidence_threshold=0.95` → only ≥0.95 auto-sends (the dead-config wire-up).
- Re-use the existing `tests/unit/test_classifier.py` `should_auto_respond` cases (routine-high
  passes; high-stakes/critical-urgency/below-threshold blocked) — they already encode the
  predicate contract; promote them to exercise the unified quantity.
- Eval-harness: add an adversarial probe for the "confident classifier + uncertain synthesis"
  auto-send case (the exact failure mode) per `probe-driven-verification.md`.

### Out of scope (verified — do NOT add)

- The "urgency guard on the learned-answer path" from the deviation note — **already enforced**
  at `response.py::generate` l.86–91 (HIGH_STAKES / HIGH-CRITICAL urgency → backup before the
  learned branch). Analysis §3. No task here.
- The "Reply STOP" WhatsApp opt-out keyword — §NEW-8 (compliance decision, separate shard).

## Risks

- **Over-send regression**: if the unified quantity is calibrated too generously, more
  low-real-confidence messages auto-send. Mitigation: the Tier-2 "classifier-high + synthesis-low"
  test + the conservative badge-table floor.
- **Under-send regression**: if too conservative, routine queries route to humans, collapsing
  automation value. Mitigation: the `Account.confidence_threshold` default stays at the table
  floor; existing routine-high tests must still pass.
- **`should_auto_respond` signature drift**: it currently takes `ClassificationResult`; the
  unified quantity needs the synthesis/staleness components too. Amend the signature to take the
  unified `ResponseConfidence` (or the full response context) — update its 4 existing test
  call sites same-shard.
