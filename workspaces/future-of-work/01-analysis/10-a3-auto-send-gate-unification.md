# 10 — A3: Auto-Send Gate Unification (analysis)

Wave 2 anchor. Source of truth: `specs/DEVIATIONS.md` §A3 (ratified 2026-07-05, user "approved
all") + `specs/response-accuracy.md`. This analysis is **verification-grounded** — three
parallel agents independently re-derived every code-state claim against the source (per
`agents.md` MUST: ≥3-issue brief → parallel deep-dive verification). One brief claim was
refuted by verification (urgency guard — see §3).

## 1. The contradiction

Two surfaces disagree about when the AI may auto-send a reply without a human:

- **`response-accuracy.md` Option C prose**: "For confidence > 90%: auto-send with badge."
- **`response-accuracy.md` Badge table**: >95% "High" auto-send **AND** 80–95% "Moderate"
  auto-send → effective auto-send floor is **>80%**, not >90%.

So the spec contradicts _itself_ (Option C >90% vs table >80%). The ratified canonical
resolution: **the badge table wins; the gate and the badge MUST read the SAME confidence
quantity.** Rationale: gate-on-classifier + badge-on-synthesis is a genuine bug, and a more
conservative (unified) auto-send quantity is the safer default for a compliance-sensitive
comms product.

## 2. Verified as-is (code) — three parallel agents, file:symbol evidence

| Claim                                                                                             | Verdict                      | Evidence                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        |
| ------------------------------------------------------------------------------------------------- | ---------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Gate reads **classifier** confidence; badge reads **synthesis** confidence (different quantities) | **TRUE**                     | `response.py::ResponseGenerator.generate`: gate `confidence = classification.confidence` (l.107) → `was_auto_sent = confidence >= 0.9 and ...` (l.118); badge `confidence_badge=synthesis.confidence_badge, confidence_score=synthesis.confidence` (ll.137–138). Classifier conf is the `MessageClassifier` LLM output; synthesis conf = `retrieval_result.synthesis_confidence * (1.0 if hallucination_passed else 0.5)` (`rag_pipeline.py::_synthesize` l.289–291). **A message can auto-send at classifier 0.95 while the badge shows 0.3.** |
| Thresholds 0.9/0.85/0.8, scattered + inconsistent                                                 | **TRUE**                     | 6 sites, 3+ shapes: `response.py:118` `conf>=0.9 ∧ is_routine ∧ has_good_synthesis ∧ ¬is_complex`; `response.py:214` `conf>=0.85 ∧ category∈[ROUTINE,SEMI_ROUTINE]` (learned path); `response.py:268` `classifier.conf>=0.9 ∧ synthesis.badge∈[high,moderate]`; route-to-backup `conf>=0.6` (l.122); `email/auto_reply.py:72` + `whatsapp/auto_reply.py:74` `CONFIDENCE_THRESHOLD_AUTO_REPLY=0.90`.                                                                                                                                             |
| No unified predicate; `should_auto_respond` is an orphan                                          | **TRUE**                     | `classifier.py::MessageClassifier.should_auto_respond` (l.290, `confidence_threshold=0.90` default) defines a canonical predicate but has **zero production callers** (test-only). The decision is inlined at the 6 sites above.                                                                                                                                                                                                                                                                                                                |
| `Account.confidence_threshold` exists, never read                                                 | **TRUE**                     | `models.py:275` `confidence_threshold: Mapped[float] = mapped_column(Float, nullable=False, default=0.90)`; written once at signup (`onboarding/service.py:200`); **zero reads**. The auto-reply modules bind their own `CONFIDENCE_THRESHOLD_AUTO_REPLY` constant instead of the per-account field.                                                                                                                                                                                                                                            |
| WhatsApp send-gate ignores `was_auto_sent`; email honors it                                       | **TRUE (at the gate)**       | `email/auto_reply.py:168` `elif response_result.was_auto_sent and classification.confidence >= threshold:` (two-clause); `whatsapp/auto_reply.py:166` `elif classification.confidence >= threshold:` (single-clause, no `was_auto_sent`). Recording is symmetric; the divergence is exactly at the safety gate.                                                                                                                                                                                                                                 |
| WhatsApp footer omits confidence % + "Reply STOP"                                                 | **TRUE** (DEVIATIONS §NEW-8) | `whatsapp/auto_reply.py::DEFAULT_WHATSAPP_FOOTER` (l.26–29) has neither. Pairs with A3 — the badge renders in this footer.                                                                                                                                                                                                                                                                                                                                                                                                                      |

## 3. Brief claim REFUTED by verification (scope correction)

The deviation's A3-code-unification note says: _"restore the urgency guard on the learned-answer
path."_ Verification shows this guard **already exists** — at the dispatcher, not the learned
path:

- `response.py::generate` (l.86–91): `HIGH_STAKES` → `_handle_high_stakes` (`was_auto_sent=False`);
  `urgency ∈ [HIGH, CRITICAL]` → `_handle_urgent` (`was_auto_sent=False`). Both short-circuit
  **before** the learned branch (`_generate_from_learned`, l.92–95) is reached.
- `learning.py::search_learned_answers` is a pure vector search with no auto-send decision —
  correctly no urgency check there.

**Conclusion: A3 does NOT add an urgency guard.** It already fires at the dispatcher. (The
learned path's own `conf>=0.85` gate at l.214 doesn't redundantly re-check urgency, which is
fine — defense-in-depth at the dispatcher, not a missing guard.) This is logged as a DISCOVERY
so the `/todos` plan doesn't carry a stale task.

## 4. The unified fix (the A3 shard)

1. **One confidence quantity.** Define a single `ResponseConfidence` computed once per response
   from the components the spec already names — classifier confidence × retrieval/synthesis ×
   hallucination × staleness. Both the **gate** and the **badge** read THIS quantity (closing
   the classifier-vs-synthesis split). High-stakes still short-circuits to backup at the
   dispatcher (unchanged).
2. **One predicate.** Revive `should_auto_respond` as the **sole** auto-send decision, returning
   the unified `ResponseConfidence` verdict against `Account.confidence_threshold`. Delete the 6
   inlined gates; both channels + all three response paths (RAG / learned / fallback) route
   through it.
3. **Threshold = badge table, per-account configurable.** Auto-send at Moderate-and-above (the
   badge-table floor); `Account.confidence_threshold` (default per table) feeds the predicate;
   <70% requires the existing user acknowledgement; high-stakes always routes to backup.
4. **Channel parity.** WhatsApp's send-gate calls the same predicate as email (so `was_auto_sent`
   is honored on both). As part of the same badge unification, the WhatsApp footer renders the
   confidence figure (closes §NEW-8's confidence half — the "Reply STOP" opt-out is a separate
   compliance decision, tracked there).
5. **Spec reconciliation.** Amend `response-accuracy.md` Option C's ">90%" to the badge table
   (>80% Moderate-and-above auto-send) and define the unified confidence quantity as the single
   source both surfaces read. Sibling-spec re-derivation sweep (`message-routing.md`,
   `data-model.md`, `rag-pipeline.md`) per `specs-authority.md` Rule 5b.

## 5. Why this is safety-critical + needs Tier-2

This is the **machine-reply-without-human** gate. A wrong unification could either (a) over-send
— auto-replying with low real confidence, the product's biggest risk per the spec's core
principle ("sending wrong information is worse than sending none") — or (b) under-send — routing
routine queries to humans, collapsing the automation value prop. The current classifier-only gate
already ships risk (a). The fix MUST be verified against real infra (Tier-2): a message with
classifier 0.95 + synthesis 0.3 must NOT auto-send post-fix; a message with unified 0.9 must
auto-send with the correct badge. Touches `classifier.py` / `response.py` / `rag_pipeline.py` /
`email/auto_reply.py` / `whatsapp/auto_reply.py` — its own shard, not a drive-by.

## 6. Shard fit (per `autonomous-execution.md` § Per-Session Capacity Budget)

One unified-predicate change + one confidence-quantity extraction + two channel call-sites +
spec edit. ≈1–2 invariants (the auto-send predicate correctness + the badge/quantity
agreement), ≤3–4 call-graph hops, <500 LOC load-bearing. Fits **one shard**; if the
confidence-quantity extraction in `rag_pipeline.py` proves load-bearing, split into 2a
(quantity) + 2b (predicate + channel parity). Tier-2 feedback loop (the eval-harness +
the existing `tests/unit/test_classifier.py` should_auto_respond cases) is live, so the
feedback-loop multiplier applies.
