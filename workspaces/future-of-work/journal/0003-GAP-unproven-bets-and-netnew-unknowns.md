# 0003 — GAP: three load-bearing claims are unproven/net-new and must be de-risked first

- **Type:** GAP
- **Date:** 2026-06-06
- **Phase:** /analyze → /codify (workspace: future-of-work)
- **Author:** jack-hong

## Gap

Three claims the vision rests on are NOT yet validated and concentrate the project's risk (`01-analysis/09-risks-failure-points.md`):

1. **The agent-comms hypothesis** (brief 3d: agent-mediated comms beats lossy human↔human) is unproven and contrarian — true for the _handoff_ layer, dangerous for the _relational/judgment_ layer. A research **BET** to validate cheaply via the comms lighthouse, never sold as fact.
2. **M1 versioned cascade re-execution** is the strongest moat AND the hardest build — LLM non-determinism makes "re-run from step N" semantically tricky; non-coder versioning UX is unsolved. v1 is deliberately reduced (linear retrace, reuse-recorded-output, no branching).
3. **The untrusted-publisher trust model** for cross-org M4 is genuinely net-new (loom's substrate is bounded-trust among enrolled operators) and must be **designed first** before opening cross-org sharing.

Also: non-coder _depth_ is where no-code historically dies at "the last 20%" — survivable only if M1 transparency makes depth legible.

## Disposition / follow-up

These become the first inputs to `/todos`: instrument the comms lighthouse for the agent-comms bet; spike runtime-ownership + M1-introspection (cheapest decisive falsifiers) before the heavy builds; design the untrusted-publisher trust model before opening cross-org M4. See [[0001-DISCOVERY-80pct-substrate-already-exists]] (the net-new 20%).

Source: `01-analysis/09-risks-failure-points.md`, `01-analysis/01-research/06-transparency-intervention-versioning.md`, `01-analysis/10-red-team/00-SUMMARY.md`.
