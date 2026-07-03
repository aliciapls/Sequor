# Todos — Index & Value Ranking

> **What this is.** The complete execution plan for the agentic-work-platform, decomposed from
> `02-plans/02-capability-roadmap.md` (the C0–C7 proof sequence) into **92 todos across 11 milestones**.
> Capability-first (Decision B): the order is a **dependency order**, and within it a **value order** —
> cheapest decisive falsifiers first, most-proven moat next, the headline moat after its cheap canary,
> the design-first trust model before the surface it constrains.
>
> **Discipline applied:** every component has separate BUILD / WIRE / TEST todos; the orphan-detection
> invariant (hot-path call site + Tier-2 wiring test) is mandatory for every governance manager; effort
> is in autonomous cycles, never human-days; load-bearing logic >~500 LOC or >5–10 invariants is
> pre-sharded at this phase (notably the C5 cascade engine → 4 invariant-focused shards).
>
> **Decision D applied** (`briefs/01-vision.md §4`): agent-mediated comms is a **settled founding
> thesis**, so the team substrate (**M6**) is built as **foundational**, not gated behind a validation
> spike; the old "agent-comms BET" is re-scoped to **non-gating** instrumentation.

## Milestones (dependency order)

| #       | Milestone                                      | Cap     | Todos | Value anchor                                                                                                                | Sizing posture                                        |
| ------- | ---------------------------------------------- | ------- | ----- | --------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------- |
| **M0**  | Foundational spikes                            | C0, C1  | 9     | Roadmap §10.2 — the two cheapest things that can kill the thesis; brief §3e (transparency/intervention is the signature)    | ~2–3 cycles; single-shard each                        |
| **M1**  | Governance foundation (M2 moat)                | C2      | 17    | brief §3e (posture beforehand); analysis 03 §3.4 (most-proven moat, ships first); produces the posture-stamped log C5 reads | glue + small net-new; shard per manager               |
| **M2**  | Non-coder self-service surface                 | C3      | 7     | brief §1b/§3a (non-coders; processes vary co-to-co); analysis 08 §1 (the 95%-pilot-failure escape)                          | multiple cycles (bulk net-new UX)                     |
| **M3**  | Cross-system reach                             | C4      | 6     | brief §1–§3 (the integration-layer inversion — the core thesis)                                                             | connector boilerplate ~5×; curation shards separately |
| **M4**  | Retrace/cascade engine (M1 moat)               | C5      | 9     | brief §3e (rewind any step); analysis 03 §2.4 (strongest moat)                                                              | **MUST shard** — 4 engine shards + UI + retention     |
| **M5**  | Cross-org artifact exchange (M4 moat)          | C6      | 8     | brief §3g (share artifacts across orgs); analysis 03 §5 (network-effects engine)                                            | trust model greenfield ~2–3×; registry after          |
| **M6**  | Multi-human+agent team substrate (M3 moat)     | M3 moat | 9     | brief §3d (team-oriented) + **Decision D** (settled → foundational)                                                         | substrate build; consumes M1 for HELD path            |
| **M7**  | The "capability proven" demo                   | §12     | 8     | brief §3e/§3f (the whole inversion, traced+interveneable+versioned)                                                         | integration; composes C0–C5 + C4                      |
| **M8**  | Testing infrastructure (cross-cutting)         | —       | 8     | rules/testing.md, rules/probe-driven-verification.md                                                                        | spans the build                                       |
| **M9**  | Deploy / infra / observability (cross-cutting) | —       | 7     | rules/observability.md; analysis 09 §4.4 (tenant isolation)                                                                 | spans the build                                       |
| **M10** | Documentation (cross-cutting)                  | —       | 5     | rules/specs-authority.md; brief §3a (non-coders)                                                                            | spans the build                                       |

**Files:** `M0-spikes.md` · `M1-governance.md` · `M2-surface.md` · `M3-connectors.md` · `M4-cascade-engine.md` · `M5-cross-org.md` · `M6-team-substrate.md` · `M7-capability-demo.md` · `M8-testing.md` · `M9-deploy-infra.md` · `M10-docs.md`

## Critical sequencing facts (from the roadmap)

- **M0 gates everything.** C0 (runtime-ownership) sets the architecture; C1 (single-step glass-box + replay) gates the C5 engine. A failed spike costs one session, not a program.
- **M1 ships before M4.** Governance is the most-proven moat AND produces the posture-stamped step log the cascade engine reads.
- **M2 ‖ M1 are parallel-eligible** (different layers). **M2 is paired with M4** — its "last 20% depth-death" falsifier is only neutralized by C5's transparency.
- **M5 is design-first.** The untrusted-publisher trust model is designed and gated **before** any cross-org build. Within-org sharing ships first (no new trust model needed).
- **M7 is the convergence** — the single end-to-end walk proving the capability whole; it deliberately omits branching, cross-org, and (for the demo) the team layer.
- **Explicit gate edges (the verdict-to-build dependencies captured in the todos).** **M0-5 (the C0 verdict — own-the-loop vs build-on-harness) gates the M1 governance builds** (the runtime direction must be settled before governance is wired native). **M0-9 (the C1 verdict — is one step replayable?) gates the M4 cascade engine and the M7 demo** (the cascade engine and the end-to-end walk both rest on the proven single-step record/replay substrate).
- **Foundational-first ordering (cross-cutting test harness before the first feature Tier-2 test).** The cross-cutting test harness + real-infra fixtures (**M8-1, M8-2**) MUST exist before the first Tier-2 test in each feature milestone runs — i.e. before **M1-4, M2-7, M3-6, M4-1, M5-2, M6-2**. This is an ordering rule held here once, rather than restated as a dependency in each feature file: a feature milestone's per-component Tier-2 test cannot run until the harness it stands on (M8-1) and the real-infra fixtures it consumes (M8-2) are in place.

## Forest check — the value-ranked top-3 workstreams to start (per `rules/value-prioritization.md` MUST-1)

1. **M0 — Foundational spikes (C0 + C1).** Value: **HIGHEST leverage to start.** Anchor: roadmap §10.2 + brief §3e. These convert the two thesis-killing uncertainties (must we own the agent's engine? is one step replayable?) into facts for ~2–3 cycles total. Shard-fit: two single-shard spikes. **Recommend START HERE.**
2. **M1 — Governance foundation (C2).** Value: **HIGH, ship-first moat.** Anchor: brief §3e + analysis 03 §3.4 (most-proven, regulation-backed; feeds C5). Decompose: per-manager build + wire-to-hot-path + Tier-2 wiring test. Parallel-eligible with **M2** once the spikes clear.
3. **M4 — Cascade engine (C5).** Value: **HIGHEST (the headline moat)** — but **gated by C1 and the hardest build.** Anchor: brief §3e + analysis 03 §2.4. **Named trade-off:** C5 is the highest-value capability, but the falsifier-first discipline says do _not_ start it first — start M0 (which de-risks C5 cheaply) and ship M1 (which produces the log C5 consumes). Decompose into the 4 engine shards + UI + retention before implementing.

**Recommendation:** begin with **M0** (both spikes), then **M1 ‖ M2** in parallel, gating the SHADOW→enforce flip and the runtime-ownership direction at their human gates. This is the capability-first order: prove-or-kill cheaply, then build the proven moat, then the headline.
