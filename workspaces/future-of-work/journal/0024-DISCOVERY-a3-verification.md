# 0024 — DISCOVERY: A3 verification refuted one brief claim + named the root cause

Date 2026-07-08 · Branch `feat/data-layer-security` · Phase: /analyze (Wave 2, A3).
Value-anchor: `agents.md` MUST — a brief covering ≥3 distinct issues MUST be verified by
parallel deep-dive agents; single-agent analysis inherits the brief's framing. This entry
records what verification found that the brief got wrong + the non-obvious root cause.

## The brief was wrong about the urgency guard (scope correction)

The `DEVIATIONS.md` §A3 code-unification note lists "restore the urgency guard on the
learned-answer path" as part of the shard. Parallel verification (`should_auto_respond` +
config cluster agent) REFUTED this: the guard already fires at the **dispatcher**, not the
learned path — `response.py::generate` l.86–91 routes `HIGH_STAKES` → `_handle_high_stakes`
and `urgency ∈ [HIGH, CRITICAL]` → `_handle_urgent` (both `was_auto_sent=False`) BEFORE the
learned branch (`_generate_from_learned`, l.92–95) is ever reached. `learning.py::
search_learned_answers` is a pure vector search with no auto-send decision, so correctly has
no urgency check.

**Consequence:** the Wave-2 `/todos` plan MUST NOT carry a "restore urgency guard" task — it
would re-add a guard that exists. Analysis `01-analysis/10-...` §3 + plan `02-plans/06-...`
"Out of scope" record this. (Exactly the failure mode the parallel-verification mandate exists
to prevent: a stale brief claim propagating into the plan → todos → a no-op or duplicate
implementation.)

## The root cause is a quantity split, not just threshold drift

The A3 deviation reads as a threshold contradiction (Option C >90% vs badge table >80%). The
deeper root cause verification surfaced: the auto-send **gate** and the user-visible **badge**
read **different confidence quantities from different pipeline stages**.

- Gate (`response.py:107/118`): `classification.confidence` — the `MessageClassifier` LLM.
- Badge (`response.py:137–138`): `synthesis.confidence` — `retrieval × hallucination`
  (`rag_pipeline.py:289–291`).

So a message can auto-send at classifier 0.95 while the badge shows 0.3. The fix is not "pick
one threshold number" — it is **unify the quantity** so gate + badge read the same
`ResponseConfidence`, THEN apply the badge-table threshold. This reframes A3 from a threshold
reconciliation into a confidence-quantity unification + single-predicate extraction (6 inlined
gates → one revived `should_auto_respond`). Captured in analysis §4.

## Confirmed-true claims (the actionable surface)

- `should_auto_respond` (`classifier.py:290`) is an orphan (zero prod callers) → revive as the
  sole predicate.
- `Account.confidence_threshold` (`models.py:275`, default 0.90) is written at signup, never
  read → wire into the predicate (the per-account threshold the spec already promises).
- WhatsApp send-gate ignores `was_auto_sent`; email honors it (asymmetry at the safety gate,
  `whatsapp/auto_reply.py:166` vs `email/auto_reply.py:168`) → parity.
- WhatsApp footer omits the confidence figure + "Reply STOP" (`DEFAULT_WHATSAPP_FOOTER`) →
  §NEW-8 pairs with A3 (badge renders in this footer).

## Verdict

A3 premise holds; one scope correction (urgency guard) + the root-cause reframe (quantity
unification, not threshold-picking). Proceed to `/todos` with the corrected scope.
