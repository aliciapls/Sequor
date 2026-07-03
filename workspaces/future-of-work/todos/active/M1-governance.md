# M1 — Governance Foundation (C2 / moat M2): posture enforced live in SHADOW on the comms product

> **What this milestone is, in plain language.** This is the platform's most-proven, lowest-risk moat,
> and the strategic spine says ship it first (capability-roadmap §5.1; trust-posture-and-governance §1).
> The goal: a user picks how much rein the agent gets for a job — **"Go ahead" / "Ask me once" / "Step
> through with me"** — _before_ the work runs, and the platform enforces that choice _live_, on the
> real, deployed comms product, in **SHADOW mode** (it observes and logs what it _would_ have held or
> blocked, but never actually blocks — so it cannot break the live product). Plus a spending budget per
> job, and the agent's fan-out plan shown on screen as an approvable card before anything executes.
>
> **The core discipline this milestone is built around.** ~80% of this machinery already ships (PACT +
> EATP); the work is ~15% integration glue + ~5% genuinely new (trust-posture-and-governance §9.1). The
> single most dangerous failure mode is the **orphan**: PACT is facade-heavy, so it is easy to wire a
> governance manager that _looks_ implemented but is never actually called on the hot path — a silent
> no-op security promise (the Phase-5.11 pattern; capability-roadmap §5.2, §5.4; `orphan-detection.md`,
> `facade-manager-detection.md`). **This is why every governance manager gets THREE separate todos: a
> BUILD todo, a WIRE todo (a real call site on the comms hot path), and a TEST todo (a Tier-2
> integration test proving the framework actually calls it, with an externally observable effect).**
> That separation is non-negotiable per C2 §5.2/§5.4.
>
> **The one LLM-first rewrite.** PACT decides "is this action consequential?" by matching keywords
> (`write`, `send`, `delete`). Sequor's own rules forbid keyword/regex routing in agent decision paths
> (`agent-reasoning.md`; CLAUDE.md Directive 6). We keep PACT's verdict machinery (pause/block/auto-
> approve) but replace its decision path with an LLM-judged one (trust-posture-and-governance §9.2;
> capability-roadmap §5.3).
>
> **Reading note.** Effort is in autonomous execution cycles, never human-days. Delegation is named
> neutrally per `cross-cli-artifact-hygiene.md`. Per-manager WIRE + TEST todos are the
> orphan-detection invariant per `orphan-detection.md` / `facade-manager-detection.md`. The
> SHADOW→enforce flip is a structural human gate; SHADOW observation runs autonomously.

---

## Milestone dependency shape

```
  M1-1  DESIGN: posture-enum→3-button mapping + naming reconciliation (pin the contract)
     │
     ├──> M1-2  BUILD: per-objective keying (re-key agent_id → objective_id)
     │       └──> M1-3  WIRE per-objective posture onto comms hot path
     │              └──> M1-4  TEST (Tier-2) per-objective posture wiring
     │
     ├──> M1-5  BUILD: LLM-first consequentiality classifier (replaces keyword path)
     │       └──> M1-6  WIRE classifier into the verdict machinery on the hot path
     │              └──> M1-7  TEST (Tier-2) classifier wiring + LLM-first invariant
     │
     ├──> M1-8  BUILD: plan_proposed Decision subtype + USER pause trigger
     │       └──> M1-9  WIRE plan_proposed gate onto the comms fan-out path
     │              └──> M1-10 TEST (Tier-2) plan_proposed gate wiring
     │
     ├──> M1-11 BUILD: per-objective BudgetTracker wiring + progress widget
     │       └──> M1-12 WIRE budget ceiling onto the comms hot path (HELD on breach)
     │              └──> M1-13 TEST (Tier-2) budget-ceiling wiring
     │
     └──> M1-14 DESIGN: 3-button posture UX + plain-language verdict→prose renderer
              └──> M1-15 WIRE the 3-button surface + renderer to the live SHADOW stream
                     └──> M1-16 TEST (Tier-2) the surface + a user-facing walk with receipts
                            │
                            └──> M1-17 SHADOW→ENFORCE readiness verdict (structural human gate)
```

The four governance managers (per-objective posture, LLM-first classifier, plan_proposed gate, budget
tracker) shard independently and are parallel-eligible — each carries its own BUILD + WIRE + TEST trio
(the orphan-detection invariant set per manager; capability-roadmap §5.5). The UX track (M1-14..M1-16)
runs in parallel with the governance tracks (different layer). All converge on the SHADOW→enforce
readiness verdict.

---

### M1-1 — DESIGN: pin the posture-enum → three-button mapping + the naming reconciliation

- **Type:** DESIGN
- **Implements:** specs/trust-posture-and-governance.md §1.1 (numbering reconciliation), §1.2 (three plain buttons) (+ plan: 02-plans/04 §1; capability-roadmap §5.3)
- **What:** Pin, as a spec-anchored contract, the mapping from the canonical EATP five-rung enum to the three end-user buttons: "Go ahead" → `AUTONOMOUS` (5), "Ask me once" → `DELEGATING` (4), "Step through with me" → `SUPERVISED` (3). Document why the brief's L3/L4/L5 labels MUST NOT ship as the enum (they collide head-on with the engine's meaning — trust-posture-and-governance §1.1). Record the v1 narrowing (no `TOOL` rung in the UI) as a known limitation.
- **Reuses → Builds:** the canonical EATP `TrustPosture` enum (shipped) → a pinned, grep-able mapping contract (a lookup table, not code).
- **Invariants:** the canonical enum is the internal source of truth; the three buttons are presentation only; the collision is contained at the presentation boundary, not in the codebase (trust-posture-and-governance §1.1). Plain-language framing per `communication.md`.
- **Sizing:** <1 cycle (the mapping is a lookup table; the cost is writing it down once and pinning it).
- **Depends on:** none (but conceptually downstream of the M0-5 runtime verdict — the governed-core runtime is where posture enforcement is native).
- **Acceptance (confirm / falsify):** CONFIRM — a pinned mapping contract exists in-spec, grep-able, with the three buttons → enum levels and the "do not ship brief labels as enum" note; reviewer confirms no brief-label leakage into enum names. FALSIFY — the mapping ships the brief's labels as the enum (BLOCKED — confuses every reader of the existing system; trust-posture-and-governance §1.1).

### M1-2 — BUILD: per-objective keying (re-key the posture state machine from agent_id to objective_id)

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §8 (per-objective AND per-step posture), §9 Gap A (keying) (+ plan: 02-plans/04 §8, §9.3 shard 1; capability-roadmap §5.3)
- **What:** Re-key the EATP `PostureStateMachine` + `SQLitePostureStore` from "one posture per agent/repo" to "one posture per objective." Add the per-objective default posture record the per-action enforcer reads, set when the user picks a button at objective start. Enforce the inherit-only tightening rule on the step path: a sub-task inherits ≤ the objective's posture, never above. Delegate to dataflow-specialist (the posture store is a DataFlow-backed record) and pact-specialist (the enforcement polarity).
- **Reuses → Builds:** EATP `PostureStateMachine` + `SQLitePostureStore` + the constraint-tightening delegation rule (all shipped) → the per-objective keying glue + the per-objective default record (small).
- **Invariants:** posture inherit-only tightening (a step inherits ≤ objective posture); operative posture = `min(user-chosen, system-floor)`; per-objective default record; `tenant_id` on every posture record (trust-posture-and-governance §3.2, §8, §10; `tenant-isolation.md`). ≤500 LOC load-bearing, ≤5 invariants — single shard.
- **Sizing:** ~1 cycle (live feedback loop — testable against fixtures).
- **Depends on:** M1-1; M0-5 (C0 runtime-ownership verdict — sets whether posture enforcement is native to an owned runtime vs wrapped over a harness surface)
- **Acceptance (confirm / falsify):** CONFIRM — the posture state machine accepts an `objective_id` key, returns a per-objective default, and rejects a sub-task posture above the objective's. FALSIFY — the re-key requires re-architecting the state machine (it was supposed to be already-keyed-by-ID glue per trust-posture-and-governance §9 Gap A; if it is not, the "small glue" estimate is wrong and the scope must be re-sized). Requires the WIRE (M1-3) + TEST (M1-4) before "done" — building the manager is not the same as the framework calling it.

### M1-3 — WIRE: per-objective posture onto the comms product's hot path

- **Type:** WIRE
- **Implements:** specs/trust-posture-and-governance.md §15 (how M2 plugs into the comms wedge), §4.1 (verification gradient) (+ plan: 02-plans/04 §11; capability-roadmap §5.2, §5.4)
- **What:** Add a real call site on the comms hot path (`Message → Classification → RAG-retrieval → Response → auto-send|Escalation`) where the per-objective posture is read and applied via `engine.verify_action()` — so "auto-send vs escalate" becomes a posture decision. Roll in under `EnforcementMode.SHADOW` (observe + log what would be held/blocked, never block). This is the call site that makes the manager non-orphaned. Delegate to nexus-specialist (the comms product surface) + pact-specialist (the `verify_action` integration).
- **Reuses → Builds:** the comms product's shipped 4-step flow + PACT `verify_action` + `EnforcementMode.SHADOW` (all shipped) → the hot-path call site that invokes the per-objective posture manager.
- **Invariants:** no-orphan (a real call site in the comms hot path, not in tests or downstream — `orphan-detection.md` MUST Rule 1); SHADOW never blocks the live product (trust-posture-and-governance §9.2); `tenant_id` on the call path; posture-safety-floor applied (`min(user-chosen, system-floor)`).
- **Sizing:** ~1 cycle (one shard per wired manager per `autonomous-execution.md` § Shard When Any Threshold Is Exceeded; the orphan-detection invariant set travels with the call site).
- **Depends on:** M1-2
- **Acceptance (confirm / falsify):** CONFIRM — grep of the comms-product source (NOT tests, NOT downstream) shows a call site invoking the per-objective posture manager on the hot path, running in SHADOW. FALSIFY — the manager is exposed as a facade attribute with no hot-path call site (the orphan pattern — BLOCKED; capability-roadmap §5.2). Requires M1-4 (Tier-2 test) to confirm the framework actually calls it in production-shaped execution.

### M1-4 — TEST (Tier-2): per-objective posture wiring proves the framework calls the manager

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §13.4 unknown #7 (facade-orphan discipline) (+ plan: 02-plans/04 §9.3; capability-roadmap §5.2, §5.4; `facade-manager-detection.md`)
- **What:** Write a Tier-2 integration test (real infrastructure, NO mocking) that runs a comms objective end-to-end under a chosen posture in SHADOW and asserts an **externally observable effect**: a SHADOW audit row recording "this action WOULD have been held under Step-through." The test imports through the framework facade, not the manager class directly. Name it `test_per_objective_posture_wiring.py` so its absence is grep-able (`facade-manager-detection.md` MUST Rule 2). Delegate to testing-specialist.
- **Reuses → Builds:** real PACT/EATP infra + the comms 4-step fixture → the Tier-2 wiring test (proves the framework calls the manager, not that the manager works in isolation).
- **Invariants:** no-orphan (Tier-2 proves the hot path invokes the manager — `orphan-detection.md` MUST Rule 2, Tier-1 unit tests are NOT sufficient); real infra, no mocking (`testing.md` Tier 2); externally observable effect asserted (an audit row).
- **Sizing:** ~1 cycle (real-infra test against the comms fixture).
- **Depends on:** M1-3
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes, asserting a SHADOW audit row whose existence is only possible if the framework called the per-objective posture manager on the hot path; a user-facing walk with receipts (per `user-flow-validation.md`) shows a posture chosen → the corresponding would-hold logged. FALSIFY — the only coverage is a Tier-1 unit test against the manager in isolation (BLOCKED — proves the manager works, not that the framework calls it; capability-roadmap §5.4).

### M1-5 — BUILD: LLM-first consequentiality classifier (replaces PACT's keyword decision path)

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §9.2 (replace keyword classifier with AI-judged), specs/transparency-and-provenance.md §5.2 (reuse caution) (+ plan: 02-plans/04 §9.1; capability-roadmap §5.3)
- **What:** Replace PACT's keyword-matching "is this action consequential?" classifier (`write`/`send`/`delete` keywords) with an LLM-judged assessment — the model judges whether an action is consequential. Keep PACT's verdict machinery (pause/block/auto-approve) unchanged; replace only the decision path. Include the caching mitigation (judge once per step-type, cache the verdict shape, tenant-scoped) as a flagged-unproven design point. Delegate to kaizen-specialist (the LLM-first agent reasoning) + pact-specialist (the verdict-machinery seam).
- **Reuses → Builds:** PACT's verdict machinery (pause/block/auto-approve, shipped) → the LLM-judged classifier replacing the keyword decision path (a small, well-scoped rewrite, not a re-architecture — trust-posture-and-governance §9.2).
- **Invariants:** LLM-first — NO keyword/regex routing remains in the consequentiality decision path (`agent-reasoning.md`; CLAUDE.md Directive 6); the verdict shape is unchanged; the classifier cache key is per-step-type AND tenant-scoped (`tenant-isolation.md`). This is the load-bearing decision-path rewrite — single shard (the verdict machinery is reused unchanged; only the classifier is rewritten — capability-roadmap §5.5).
- **Sizing:** ~1 cycle (live feedback loop against fixture actions; the rewrite is well-scoped).
- **Depends on:** M1-1; M0-5 (C0 runtime-ownership verdict — sets whether posture enforcement is native to an owned runtime vs wrapped over a harness surface)
- **Acceptance (confirm / falsify):** CONFIRM — the classifier returns a consequentiality judgment from an LLM call (not a keyword match) and the verdict machinery consumes it unchanged; grep confirms no keyword-list routing remains in the decision path. FALSIFY — a keyword/regex fallback survives in the decision path (BLOCKED per `agent-reasoning.md`). Carries a real cost/latency tradeoff (an LLM call on every action vs an instant keyword match — trust-posture-and-governance §13.4 unknown #2); the caching mitigation is itself unproven at scale and must be flagged, not silently assumed. Requires M1-6 (WIRE) + M1-7 (TEST).

### M1-6 — WIRE: the LLM-first classifier into the verdict machinery on the hot path

- **Type:** WIRE
- **Implements:** specs/trust-posture-and-governance.md §4.1 (verification gradient), §9.2 (decision-path replacement) (+ plan: 02-plans/04 §9.1; capability-roadmap §5.2)
- **What:** Add the real call site where the comms hot path invokes the LLM-first classifier to decide whether an action is consequential (and therefore whether the posture's gate applies). Confirm the keyword path is fully removed from the live decision, not just shadowed. Delegate to nexus-specialist + pact-specialist.
- **Reuses → Builds:** the comms hot path + PACT verdict machinery → the call site invoking the LLM-first classifier in the live consequentiality decision.
- **Invariants:** no-orphan (a real comms-hot-path call site, not tests/downstream); LLM-first (the live decision path calls the LLM classifier, not the keyword list); `tenant_id` on the call path; SHADOW never blocks.
- **Sizing:** ~1 cycle (one shard per wired manager).
- **Depends on:** M1-5
- **Acceptance (confirm / falsify):** CONFIRM — grep of the comms source shows the hot path calling the LLM-first classifier; the keyword classifier is no longer reachable on the live decision path. FALSIFY — the classifier is built but the hot path still calls the keyword path (orphaned new classifier + live old path — BLOCKED). Requires M1-7.

### M1-7 — TEST (Tier-2): LLM-first classifier wiring + the no-keyword invariant

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §9.2 (+ plan: 02-plans/04 §9.1; capability-roadmap §5.4; `facade-manager-detection.md`, `probe-driven-verification.md`)
- **What:** Write a Tier-2 test that runs a comms action end-to-end and asserts the consequentiality verdict came from the LLM classifier (an externally observable effect — e.g. a logged classifier-invocation record / verdict-provenance field), AND a regression test asserting no keyword-routing path is reachable. The semantic assertion (was this judged consequential correctly?) MUST be probe-driven, not regex over the classifier output, per `probe-driven-verification.md`. Name `test_consequentiality_classifier_wiring.py`. Delegate to testing-specialist.
- **Reuses → Builds:** real PACT/EATP infra + a comms action fixture → the Tier-2 wiring test + the no-keyword regression test.
- **Invariants:** no-orphan (Tier-2 proves the framework calls the classifier); LLM-first (regression test proves no keyword path remains); probe-driven semantic verification (no regex/keyword scoring of the classifier's semantic verdict — `probe-driven-verification.md` MUST Rule 1); real infra, no mocking.
- **Sizing:** ~1 cycle.
- **Depends on:** M1-6
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes asserting an LLM-classifier-invocation record on the hot path, the regression test confirms no reachable keyword path, and the semantic-correctness probe (schema-validated) confirms the classifier judged a sample consequential action correctly. FALSIFY — coverage is Tier-1-only, OR the semantic assertion is a regex/keyword match (both BLOCKED).

### M1-18 — TEST (Tier-2): prove the classifier cache holds latency + cost within bounds

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §9.2 (caching mitigation), §13.4 unknown #2 (cost/latency tradeoff) (+ architecture §12 #6; capability-roadmap §5.4; `facade-manager-detection.md`)
- **What:** Write a Tier-2 performance/cost proof for the per-step-type, tenant-scoped classifier cache introduced as a flagged-unproven mitigation in M1-5. Run a comms objective with repeated step-types end-to-end against real infrastructure and assert the externally observable effects: (a) a repeated step-type hits the cache (the LLM classifier is NOT re-invoked — a cache-hit record / verdict-provenance field proves it), (b) the cache key is tenant-scoped (two tenants with the same step-type do NOT share a cached verdict — `tenant-isolation.md`), and (c) the per-action added latency and per-objective LLM-call cost stay within a stated budget (record the budget in-spec; the bare "an LLM call on every action" cost is the falsifier this proves against). Name `test_consequentiality_cache_proof.py`. Delegate to testing-specialist.
- **Reuses → Builds:** real PACT/EATP infra + a repeated-step-type comms fixture → the Tier-2 cache performance/cost proof (proves the M1-5 mitigation is real, not assumed).
- **Invariants:** the cache key is per-step-type AND tenant-scoped (no cross-tenant verdict reuse — `tenant-isolation.md`); LLM-first preserved (a cache MISS still routes to the LLM classifier, never to a keyword fallback — `agent-reasoning.md`); externally observable effect asserted (cache-hit record + measured latency/cost); real infra, no mocking.
- **Sizing:** ~1 cycle (real-infra performance proof against the comms fixture).
- **Depends on:** M1-7
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 proof passes: a repeated step-type is served from cache (LLM not re-invoked), two tenants do NOT share a cached verdict, and measured added latency + per-objective cost are within the stated budget. FALSIFY — the cache is unproven (no test exists), OR a cross-tenant cache hit occurs (tenant-isolation breach — BLOCKED), OR measured latency/cost exceed the stated budget (the M1-5 mitigation does not hold at scale — surface it here, not at the SHADOW→enforce flip). **Deferral option:** if the founder judges the cache proof deferrable, this todo MAY be replaced by an explicit founder-gated deferral recording the value-anchor — "the LLM-on-every-action cost/latency risk (trust-posture-and-governance §13.4 unknown #2) ships unproven into SHADOW; SHADOW observation surfaces real cost before any enforce flip" — so the un-proven mitigation is a recorded, founder-owned decision, not a silent assumption.

### M1-19 — BUILD + WIRE: the break-glass / EmergencyBypass primitive onto the comms hot path

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §13 (operator break-glass), §9.2 (verdict machinery seam) (+ capability-roadmap §5.2, §5.4; `orphan-detection.md`, `facade-manager-detection.md`)
- **What:** Wire the reused PACT `EmergencyBypass` primitive — referenced in operator docs but currently unbuilt — so an operator can break-glass past a governance hold in a genuine emergency. Add the real call site on the comms hot path where a break-glass invocation short-circuits the verdict machinery, and persist an audit record for EVERY bypass (who, when, which objective, which held action). The bypass MUST be the explicit orphan-detection trio in one wired unit: a BUILD of the bypass seam, a real comms-hot-path WIRE call site, and an audit-of-every-bypass effect. Roll in under `EnforcementMode.SHADOW` (in SHADOW, break-glass logs a would-bypass; it never actually blocks the live product, so there is nothing to bypass yet — the audit record still persists). Delegate to pact-specialist (the `EmergencyBypass` primitive + verdict seam) + nexus-specialist (the comms hot-path call site) + dataflow-specialist (the bypass audit record).
- **Reuses → Builds:** the reused PACT `EmergencyBypass` primitive (referenced in operator docs) + the comms hot path + the verdict machinery seam → the wired break-glass call site + the per-bypass audit record.
- **Invariants:** no-orphan (a real comms-hot-path call site, not docs/tests/downstream — `orphan-detection.md` MUST Rule 1); EVERY bypass writes an immutable audit record (no silent bypass — `zero-tolerance.md` Rule 3); `tenant_id` on the bypass call path and the audit record (`tenant-isolation.md`); SHADOW never blocks the live product. ≤500 LOC, ≤5 invariants — single shard.
- **Sizing:** ~1 cycle (one shard — the BUILD + the WIRE call site travel together with the orphan-detection invariant set).
- **Depends on:** M1-1; M0-5 (C0 runtime-ownership verdict — sets whether posture enforcement is native to an owned runtime vs wrapped over a harness surface)
- **Acceptance (confirm / falsify):** CONFIRM — grep of the comms source (NOT docs, NOT tests, NOT downstream) shows a break-glass call site invoking the reused `EmergencyBypass` on the verdict-machinery seam, and every bypass persists an audit record (who/when/objective/held-action). FALSIFY — `EmergencyBypass` is referenced in operator docs but has no hot-path call site (the doc-promised-but-unwired orphan pattern — BLOCKED; capability-roadmap §5.2), OR a bypass can occur without an audit record (silent break-glass — BLOCKED). Requires M1-20 (TEST).

### M1-20 — TEST (Tier-2): break-glass wiring proves the framework audits every bypass

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §13 (+ capability-roadmap §5.4; `facade-manager-detection.md`)
- **What:** Write a Tier-2 integration test (real infrastructure, NO mocking) that triggers a break-glass on a comms objective in SHADOW and asserts the externally observable effect: an immutable bypass audit record exists (who/when/objective/held-action) produced only if the framework called `EmergencyBypass` on the hot path. Verify the audit write with a read-back (`testing.md` state-persistence). Import through the framework facade, not the primitive class directly. Name `test_emergency_bypass_wiring.py` so its absence is grep-able (`facade-manager-detection.md` MUST Rule 2). Delegate to testing-specialist.
- **Reuses → Builds:** real PACT/EATP infra + the comms 4-step fixture → the Tier-2 break-glass wiring test (proves the framework calls + audits the bypass, not that the primitive works in isolation).
- **Invariants:** no-orphan (Tier-2 proves the hot path invokes the bypass + writes the audit — `orphan-detection.md` MUST Rule 2, Tier-1 unit tests are NOT sufficient); audit-of-every-bypass asserted via read-back; `tenant_id` on the audit record; real infra, no mocking.
- **Sizing:** ~1 cycle (real-infra test against the comms fixture).
- **Depends on:** M1-19
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes, asserting a bypass audit record (read-back-verified) whose existence is only possible if the framework called `EmergencyBypass` on the hot path. FALSIFY — the only coverage is a Tier-1 unit test against the primitive in isolation (BLOCKED — proves the primitive works, not that the framework calls + audits it), OR a bypass leaves no audit record (BLOCKED).

### M1-8 — BUILD: the plan_proposed Decision subtype + the USER pause trigger

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §4.3 (genuinely-new wiring), specs/transparency-and-provenance.md §5.1 (plan is an approvable Decision before execution) (+ plan: 02-plans/04 §4.2; capability-roadmap §5.3)
- **What:** Add a `plan_proposed` Decision subtype that surfaces the agent's fan-out plan (the sub-tasks, what each does, estimated cost) as an inspectable, approvable object BEFORE execution. Add a `USER` pause trigger to the existing `PlanSuspension` mechanism (which today suspends only on BUDGET/TEMPORAL/POSTURE/ENVELOPE) so a person can say "stop here" mid-flight. Delegate to pact-specialist (the Decision model + PlanSuspension) + dataflow-specialist (the `AgenticDecision` record).
- **Reuses → Builds:** PACT `AgenticDecision` model + `PlanSuspension` + `EventBridge.on_plan_event` (all shipped) → the `plan_proposed` decision subtype (~1 cycle of integration) + the `USER` trigger value + one route (small).
- **Invariants:** the plan is surfaced before any execution; the posture choice decides auto-approve ("Go ahead") / one-approval ("Ask me once") / pause-each-step ("Step through"); the USER pause halts the path; immutability (resolving the Decision creates a new linked record, never an edit — transparency-and-provenance §2.1); `tenant_id` on the Decision record. ≤500 LOC, ≤5 invariants — single shard.
- **Sizing:** ~1 cycle (live feedback loop; the integration is small).
- **Depends on:** M1-1; M0-5 (C0 runtime-ownership verdict — sets whether posture enforcement is native to an owned runtime vs wrapped over a harness surface)
- **Acceptance (confirm / falsify):** CONFIRM — a `plan_proposed` Decision is created and surfaced before execution carrying the fan-out + estimated cost, and a `USER` trigger can suspend a running plan; AND the `plan_proposed` Decision is persisted as an immutable provenance-ledger record (not only streamed to screen) BEFORE sub-task/fan-out execution — the persisted record uses the C1/M0 record model (M0-6/M0-9) and feeds the M4-1 provenance ledger (this covers the "recorded" half of brief §3e: "decisions surfaced on screen, recorded"). FALSIFY — the plan can only be surfaced AFTER execution begins (defeats the "approvable before it runs" contract — trust-posture-and-governance §4), OR the plan_proposed Decision is streamed to screen but never persisted as an immutable record (the "recorded" half of brief §3e is unmet — surfaced-but-not-recorded is BLOCKED). Requires M1-9 (WIRE) + M1-10 (TEST).

### M1-9 — WIRE: the plan_proposed gate onto the comms fan-out path

- **Type:** WIRE
- **Implements:** specs/transparency-and-provenance.md §5.2 (the live stream that carries it), specs/trust-posture-and-governance.md §4.2 (shipped surface-and-approve pipeline) (+ plan: 02-plans/04 §4; capability-roadmap §5.2)
- **What:** Add the real call site where a comms objective's fan-out forms a `plan_proposed` Decision, streamed to screen via `EventBridge.on_plan_event`, gated by the chosen posture (auto/once/each-step), running in SHADOW. The `gated_by` edge links each downstream step to the Decision it waited on. Delegate to nexus-specialist + pact-specialist.
- **Reuses → Builds:** PACT `EventBridge`/`EventBus` (WebSocket fan-out) + `SupervisorOrchestrator`/`ApprovalBridge` (block-until-approve) + the comms hot path → the call site that forms + surfaces the plan_proposed gate.
- **Invariants:** no-orphan (real comms-hot-path call site); plan surfaced before execution; posture gates the plan_proposed card; SHADOW never blocks; `tenant_id` on the call path.
- **Sizing:** ~1 cycle (one shard per wired manager).
- **Depends on:** M1-8
- **Acceptance (confirm / falsify):** CONFIRM — grep of the comms source shows the fan-out path forming a `plan_proposed` Decision streamed before execution, posture-gated, in SHADOW. FALSIFY — the `plan_proposed` subtype exists but no comms call site forms it (orphan — BLOCKED). Requires M1-10.

### M1-10 — TEST (Tier-2): plan_proposed gate wiring proves the framework surfaces the plan

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §4 (+ plan: 02-plans/04 §4; capability-roadmap §5.4; `facade-manager-detection.md`)
- **What:** Write a Tier-2 test that runs a comms objective whose agent fans out, and asserts the externally observable effect: a `plan_proposed` Decision row exists BEFORE any sub-task step executes, with the fan-out + estimated cost, and (under "Step through" in SHADOW) a would-hold log. Test the `USER` pause trigger end-to-end too. Name `test_plan_proposed_gate_wiring.py`. Delegate to testing-specialist.
- **Reuses → Builds:** real PACT infra + a comms fan-out fixture → the Tier-2 wiring test.
- **Invariants:** no-orphan (Tier-2 proves the framework forms + surfaces the plan); externally observable effect (the Decision row precedes step execution); real infra, no mocking; the `USER` pause path covered (one direct test per variant — `testing.md`).
- **Sizing:** ~1 cycle.
- **Depends on:** M1-9
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes asserting a `plan_proposed` row timestamped before the first sub-task step, plus a working USER pause; user-facing walk with receipts shows the fan-out card surfaced before execution. FALSIFY — Tier-1-only coverage, OR the plan_proposed row appears only after execution starts (both BLOCKED).

### M1-11 — BUILD: per-objective BudgetTracker wiring + the progress widget

- **Type:** BUILD
- **Implements:** specs/trust-posture-and-governance.md §5 (budget ceilings), §13.2 (budget exhaustion mid-objective) (+ plan: 02-plans/04 §5, §9.3 shard 4; capability-roadmap §5.2)
- **What:** Wire a per-objective `BudgetTracker(tracker_id="obj-<id>")` giving a spending ceiling per piece of work, with 80%/95%/exhausted alerts surfaced to the user, and expose the `budget_status` dict as a progress widget. Crossing `requires_approval_above_usd` flips the verdict to HELD → spawns an approval card (M1-8). Delegate to pact-specialist + dataflow-specialist (the `SQLiteBudgetStore`).
- **Reuses → Builds:** EATP `BudgetTracker` (integer microdollars, reserve-then-record fail-closed, 80/95/exhausted callbacks, crash-safe `SQLiteBudgetStore` — all shipped) → the per-objective tracker wiring + the progress widget (small).
- **Invariants:** fail-closed reserve (never denies a spend that should have been allowed — over-reporting is the only tolerated error); 80/95/exhausted callbacks fire once each; the renderer leaks no jargon (`communication.md`); `tenant_id` / `tracker_id` validated and tenant-scoped (`tenant-isolation.md`). ≤500 LOC, ≤5 invariants — single shard.
- **Sizing:** ~1 cycle (live feedback loop against fixtures).
- **Depends on:** M1-1; M0-5 (C0 runtime-ownership verdict — sets whether posture enforcement is native to an owned runtime vs wrapped over a harness surface)
- **Acceptance (confirm / falsify):** CONFIRM — a per-objective budget tracker reserves/records spend, fires 80/95/exhausted alerts once each, and the `budget_status` dict renders as a progress widget. FALSIFY — the tracker denies a spend it should have allowed (the fail-closed safe-direction invariant is violated — trust-posture-and-governance §5). Requires M1-12 (WIRE) + M1-13 (TEST).

### M1-12 — WIRE: the budget ceiling onto the comms hot path (HELD on breach)

- **Type:** WIRE
- **Implements:** specs/trust-posture-and-governance.md §5 (contract for the platform), §13.2 (+ plan: 02-plans/04 §5; capability-roadmap §5.2)
- **What:** Add the real call site where the comms hot path reserves/records against the per-objective budget tracker before/after each costed action, so that crossing the ask-first threshold flips the verdict to HELD (in SHADOW: logs a would-hold), and exhaustion surfaces a "raise the limit or stop?" card. Delegate to nexus-specialist + pact-specialist.
- **Reuses → Builds:** the comms hot path + EATP `BudgetTracker` reserve/record → the hot-path call site invoking the tracker.
- **Invariants:** no-orphan (real comms-hot-path call site); fail-closed reserve; budget breach → HELD verdict (raising the budget is a structural gate requiring a human even at "Go ahead" — trust-posture-and-governance §13.2); SHADOW never blocks; `tenant_id` on the call path.
- **Sizing:** ~1 cycle (one shard per wired manager).
- **Depends on:** M1-11
- **Acceptance (confirm / falsify):** CONFIRM — grep of the comms source shows reserve/record calls on the hot path; a breach logs a would-hold in SHADOW. FALSIFY — the tracker is built but no comms call site reserves against it (orphan — BLOCKED). Requires M1-13.

### M1-13 — TEST (Tier-2): budget-ceiling wiring proves the framework calls the tracker

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §5, §13.2 (+ plan: 02-plans/04 §5; capability-roadmap §5.4; `facade-manager-detection.md`)
- **What:** Write a Tier-2 test that runs a comms objective accruing cost against a per-objective tracker and asserts the externally observable effects: the 80/95 alerts fired, a breach produced a would-hold log in SHADOW, and exhaustion produced a "raise or stop" card. Verify every write with a read-back (`testing.md` state-persistence). Name `test_budget_ceiling_wiring.py`. Delegate to testing-specialist.
- **Reuses → Builds:** real EATP `SQLiteBudgetStore` infra + a costed comms fixture → the Tier-2 wiring test.
- **Invariants:** no-orphan (Tier-2 proves the framework calls the tracker); externally observable effect (alert records + would-hold log); real infra, no mocking; read-back verification of persisted budget state.
- **Sizing:** ~1 cycle.
- **Depends on:** M1-12
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes asserting alert records + a would-hold-on-breach log produced only by the framework calling the tracker on the hot path; user-facing walk with receipts shows the progress widget moving + the breach card. FALSIFY — Tier-1-only coverage, OR success asserted on a status code without a read-back of persisted budget state (both BLOCKED).

### M1-14 — DESIGN: the three-button posture UX + the plain-language verdict→prose renderer

- **Type:** DESIGN
- **Implements:** specs/trust-posture-and-governance.md §4.3 item 3 (verdict→prose renderer), §9 Gap B (non-coder presentation), §13.4 unknown #1 (non-coder rendering — dominant risk) (+ plan: 02-plans/04 §4.3, §7.2; capability-roadmap §5.1)
- **What:** Design the non-coder presentation layer: the three plain buttons ("Go ahead" / "Ask me once" / "Step through with me") at objective start, the Approve/Edit/Reject cards, and the verdict→prose renderer that turns engine holds (`constraint_dimension=financial, requires_approval_above_usd=200`) into _"This step would spend $240, above your $200 auto-approve limit — approve?"_. Design the unspoofable non-coder confirmation gesture for posture upgrade (the challenge-nonce re-skinned from "paste this code" to a UI gesture the agent cannot perform — trust-posture-and-governance §7.2). Use PACT's web objectives/approvals screens as scaffold. Delegate to uiux-designer + react-specialist for the surface design; this is the dominant M2 usability risk and is iterative discovery, not a one-shot.
- **Reuses → Builds:** PACT's web objectives/approvals screens (scaffold) → the non-coder three-button surface + verdict→prose renderer + the confirmation-gesture design (the bulk of the net-new UX — trust-posture-and-governance §9.1).
- **Invariants:** plain-language framing, no unexplained jargon, recommendation + implications surfaced (`communication.md`, `recommendation-quality.md`); the renderer leaks no engine jargon; the upgrade gesture is unspoofable (the agent cannot grant itself more rein — trust-posture-and-governance §7.2); traceability-not-accountability boundary stated in any user-facing trust copy (trust-posture-and-governance §7.5).
- **Sizing:** multiple cycles — size by usability-walk milestones (a non-coder picks a posture; a non-coder reads + acts on a hold card), not LOC; this is the open-ended part (trust-posture-and-governance §9.2, §13.4 #1).
- **Depends on:** M1-1
- **Acceptance (confirm / falsify):** CONFIRM — a design exists for the three buttons + Approve/Edit/Reject cards + verdict→prose renderer + the upgrade gesture, validated by a usability walk where a non-coder picks a posture and reads a hold card without confusion (receipts per `user-flow-validation.md`). FALSIFY — turning "Supervised / constraint_dimension=financial / envelope_version" into something a non-coder acts on proves intractable in the walk (the dominant M2 usability risk firing — trust-posture-and-governance §13.4 #1); surface it here, on the design, before it is the headline.

### M1-15 — WIRE: the three-button surface + renderer to the live SHADOW stream

- **Type:** WIRE
- **Implements:** specs/trust-posture-and-governance.md §4.2 (`EventBridge` live stream), specs/transparency-and-provenance.md §5.2 (+ plan: 02-plans/04 §4, §11; capability-roadmap §5.2)
- **What:** Wire the three-button surface and the verdict→prose renderer to the live decision stream (`EventBridge.on_plan_event` / `on_hold_event` / `on_cost_event`) on the comms product, so a posture picked in the UI sets the per-objective posture (M1-2) and a SHADOW would-hold renders as a plain-language card. Delegate to react-specialist + nexus-specialist.
- **Reuses → Builds:** PACT `EventBridge`/`EventBus` live stream + the M1-2 per-objective posture manager + the M1-14 design → the wired non-coder surface over the live SHADOW stream.
- **Invariants:** no-orphan (the surface actually drives the per-objective posture manager + renders the live stream, not a static mock — `zero-tolerance.md` Rule 2 forbids frontend mock data presented as real); `tenant_id` on the stream; SHADOW never blocks; the renderer leaks no jargon.
- **Sizing:** ~1–2 cycles (surface wiring over the live stream).
- **Depends on:** M1-14, M1-3 (the per-objective posture call site the buttons drive)
- **Acceptance (confirm / falsify):** CONFIRM — picking a button in the comms UI sets the per-objective posture and a SHADOW would-hold renders as a plain-language card from real stream data. FALSIFY — the surface renders fabricated/mock cards not driven by the live stream (frontend stub — BLOCKED per `zero-tolerance.md` Rule 2). Requires M1-16.

### M1-16 — TEST (Tier-2): the surface + a user-facing walk with receipts on the live SHADOW stream

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §9 Gap B, §13.4 #1 (+ plan: 02-plans/04 §9.2; capability-roadmap §5.2; `user-flow-validation.md`, `facade-manager-detection.md`)
- **What:** Write a Tier-2 test driving the comms product end-to-end with a posture picked through the UI surface, asserting the externally observable effect: the per-objective posture record was set from the UI AND a SHADOW would-hold rendered to the surface as plain-language prose. Perform the literal user-facing walk (pick "Step through" → run a comms objective → observe the would-hold card) and capture verbatim receipts per `user-flow-validation.md`. Delegate to testing-specialist + react-specialist.
- **Reuses → Builds:** real PACT infra + the comms product + the wired surface → the Tier-2 surface-wiring test + the user-facing walk receipts.
- **Invariants:** no-orphan (Tier-2 + the walk prove the surface drives the framework on the hot path); user-facing walk with receipts mandatory (`user-flow-validation.md` — tests passing is necessary but insufficient); receipts scrubbed of secrets/PII before embedding (`user-flow-validation.md` MUST-6); real infra, no mocking.
- **Sizing:** ~1 cycle.
- **Depends on:** M1-15
- **Acceptance (confirm / falsify):** CONFIRM — the Tier-2 test passes AND a scrubbed user-flow receipt (verbatim button-pick → verbatim would-hold card → user disposition) is embedded in the deliverable. FALSIFY — "tests pass" is claimed without the literal user walk + receipts (BLOCKED per `user-flow-validation.md` MUST-1).

### M1-17 — SHADOW→ENFORCE readiness verdict (structural human gate)

- **Type:** TEST
- **Implements:** specs/trust-posture-and-governance.md §9.2 item 2 (SHADOW→enforce), §15 (comms-wedge first proof) (+ plan: 02-plans/04 §11; capability-roadmap §5.2, §5.5)
- **What:** Synthesize the four governance tracks (posture, classifier, plan_proposed, budget) + the UX track into a readiness verdict: on the live comms product in SHADOW, does a posture chosen beforehand demonstrably change what WOULD happen (Step-through would-holds every consequential action; Ask-once would-gate once at plan→execute; Go-ahead would-auto-approve in-envelope and would-block out-of-envelope), with a budget would-halt at its limit, the fan-out surfaced before execution, and every manager proven non-orphaned by a passing Tier-2 wiring test? State whether the platform is ready to flip from SHADOW (observe) to ENFORCE (block) on the live product. Delegate to reviewer + security-reviewer in parallel; delegate to value-auditor for the buyer-perspective check.
- **Reuses → Builds:** all four track verdicts + the UX walk receipts → one decision-grade readiness verdict (no new production code).
- **Invariants:** no-orphan — every wired manager has a passing Tier-2 wiring test (the single most important C2 invariant, non-negotiable — capability-roadmap §5.4); SHADOW calibration evidence is real (not asserted); symmetric pros/cons of flipping to enforce per `recommendation-quality.md`; the falsifier checked — governance must NOT ship as a facade that never executes on the hot path (capability-roadmap §5.2).
- **Sizing:** ~1 cycle (synthesis + the parallel reviews).
- **Depends on:** M1-4, M1-7, M1-10, M1-13, M1-16
- **Acceptance (confirm / falsify):** CONFIRM — a readiness verdict exists showing all four managers non-orphaned (passing Tier-2 wiring tests), a posture choice demonstrably changing live SHADOW behavior, and a clean reviewer + security-reviewer sign-off; the founder can read it and decide the SHADOW→enforce flip. **STRUCTURAL HUMAN GATE:** flipping from observe to enforce on the live product changes real user behavior — the founder gates this; SHADOW observation runs autonomously up to here (capability-roadmap §5.5). FALSIFY (the moat-killer) — any governance manager ships as a facade with no hot-path call site / no passing Tier-2 wiring test (the Phase-5.11 orphan pattern — a no-op security promise is worse than no promise; capability-roadmap §5.2).

---

## M1 exit criteria (before the SHADOW→enforce flip)

1. **Four governance managers, each non-orphaned:** per-objective posture, LLM-first classifier, plan_proposed gate, budget tracker — each with a BUILD + a real hot-path WIRE call site + a passing Tier-2 wiring test proving the framework calls it (capability-roadmap §5.2, §5.4; `orphan-detection.md`, `facade-manager-detection.md`). Non-negotiable.
2. **LLM-first invariant holds:** no keyword/regex routing remains in the consequentiality decision path; the semantic verification is probe-driven (`agent-reasoning.md`, `probe-driven-verification.md`).
3. **The three-button non-coder surface** renders live SHADOW would-holds as plain-language cards, validated by a user-facing walk with scrubbed receipts (`user-flow-validation.md`).
4. **SHADOW never broke the live product** — governance ran in observe-only throughout; the SHADOW→enforce flip is a structural human gate the founder makes after reading the M1-17 readiness verdict (capability-roadmap §5.5).
