# 0008 — RISK: the two hardest unknowns are M4 non-coder legibility and the untrusted-publisher trust model

- **Type:** RISK
- **Date:** 2026-07-03
- **Phase:** /todos → /codify (workspace: future-of-work)
- **Author:** jack-hong

## Risks identified during planning

1. **M4 (C5) non-coder legibility — the frontier.** The cascade _engine_ is the tractable part (a ~20% novel composition over shipped primitives). The frontier is whether a **non-coder can read the trace and drive the rewind** — answer "which version is current?" in seconds, without the history looking like a developer's git graph. If this falsifier fires, the platform risks degrading to "an agent does your work in one interface" (the surface Cowork owns). Mitigation in the todos: deliberately-reduced v1 (linear retrace, reuse-recorded default, no branching), the cost-preview as a hard acceptance gate, and proving legibility on the comms-wedge's small 4-step graph before it is the headline.

2. **M5 (C6) untrusted-publisher trust model — greenfield, design-first.** When org B runs org A's recipe, B runs A's instructions inside B's agent against B's systems, with B's authority. No shipping product solves this. It is a novel-architecture decision that _constrains the registry's shape_ — so M5-1 (the trust-model DESIGN) gates every cross-org build. Mitigation: within-org sharing ships first (needs no new trust model); default-deny intake fence + capability-scoped recipes + mechanical over-broad-scope detection.

## Secondary risks (tracked, mitigated in the todos)

- The C0→C1→C5 gating edges are now captured as real dependency edges (M0-5 gates M1; M0-9 gates M4/M7), not prose — red-team B-1/B-2.
- The reused governance (PACT) is facade-heavy → orphan risk; every wired manager carries a hot-path call site + Tier-2 wiring test (non-negotiable).
- Decision B's deferred-GTM creates a "lands nowhere" risk; the comms lighthouse (C7b) is the specific, concurrent falsifier.

Cross-refs: [[0003-GAP-unproven-bets-and-netnew-unknowns]], [[0006-DECISION-todos-capability-sharding]]. Source: `01-analysis/09-risks-failure-points.md`, `02-plans/02-capability-roadmap.md §8, §9, §14`.
