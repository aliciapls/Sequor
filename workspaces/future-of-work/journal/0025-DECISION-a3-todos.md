# 0025 — DECISION: A3 /todos — shard sizing + branch strategy + scope

Date 2026-07-08 · Branch `feat/a3-auto-send-gate` (stacked on `feat/data-layer-security`) ·
Phase: /todos (Wave 2).

Three planning decisions worth a durable record (the next session + the Wave-2 PR reviewer need
the rationale).

## D1 — A3 is ONE shard, with a stated split condition (not pre-split)

A3 fits the per-session capacity budget as a single shard: ≈2 invariants (auto-send predicate
correctness + gate/badge quantity agreement), ≤3–4 call-graph hops, <500 LOC load-bearing, with a
live feedback loop (eval-harness + `should_auto_respond` unit cases + Tier-2 PG) so the
feedback-loop multiplier applies. Pre-splitting into 2a/2b would be ceremony.

**Split condition (declared, not deferred):** IF the `ResponseConfidence` extraction in
`rag_pipeline.py` proves load-bearing mid-`/implement` (the synthesis-confidence derivation
l.289–291 is entangled with the hallucination cross-check), split into 2a (quantity) + 2b
(predicate + parity) at the invariant boundary. This is the wave-loop MUST-1 invariant-axis
split, decided at `/todos` time — NOT a mid-`/implement` abandonment.

## D2 — Branch `feat/a3-auto-send-gate` STACKS on `feat/data-layer-security` (PR #8), not `main`

A3 overlaps Wave-1's files: Wave-1 added `bind_tenant` to `email/auto_reply.py` +
`whatsapp/auto_reply.py`; A3 changes those same files' send-gates. Branching A3 from `main`
(pre-Wave-1) would conflict on both files at merge. Stacking on `feat/data-layer-security` gives
A3 Wave-1's `bind_tenant` baseline so the send-gate edits land cleanly. The Wave-2 PR opens with
base `feat/data-layer-security` (stacked), retargeted to `main` after PR #8 merges.

**Alternative rejected:** wait for PR #8 to merge, then branch A3 from `main`. PR #8 is held for
the prod non-owner-DB-role gate (could be a while); stacking lets Wave 2 proceed now.

## D3 — Scope: urgency guard OUT (verified); NEW-8 "Reply STOP" OUT (separate compliance decision)

- **Urgency guard on the learned-answer path: OUT.** Verification (journal 0024) showed it already
  fires at the dispatcher (`response.py::generate` l.86–91). The deviation note's "restore" task
  is a stale claim — dropped, not carried into todos.
- **WhatsApp "Reply STOP" opt-out keyword: OUT of A3.** §NEW-8 splits into two halves — the
  confidence figure (IN scope for A3, todo 2.6, since the badge renders in the footer) and the
  Meta-compliant "Reply STOP" opt-out keyword (a separate compliance decision, stays under §NEW-8).
  Conflating them would couple a safety unification with a compliance/product decision.

## Value-rank (forest-vs-trees, per `value-prioritization.md` MUST-1)

Remaining forest top-3: (1) **A3** — safety-critical machine-reply gate, single shard, ratified
[PRIMARY anchor: DEVIATIONS §A3 + response-accuracy.md core principle]; (2) **Wave 3 A4 moats +
R5-01** — multi-shard, user-ratified [DEVIATIONS A4/NEW-8]; (3) **F7 Wave-1 tail** — low, internal
hardening [journal 0017/0019/0021/0022]. A3 is #1 by value AND shard-fittable → the correct pick.
No fittability-streetlight trade-off (the highest-value item is also the fittable one).
