# M7 — The Single "Capability Proven" Demo (the end-to-end integration milestone)

> **What this milestone proves (plain language).** One continuous demonstration that the
> disrupted-work capability is _whole_: a non-technical person states an outcome in plain language;
> the agent does the work autonomously across **two systems that used to need a human to bridge
> them**, under a freedom-level the user chose _beforehand_; and the result is **traced** (you can see
> every step), **interveneable** (you can rewind any step and have only the affected downstream
> recompute), and **versioned** (old results are kept). This is the integration milestone — it does
> not build new capability; it _composes_ C0 (runtime), C1 (glass-box single-step), C2 (governance),
> C3 (self-service surface), C4 (≥2-system reach), and C5 (cascade engine) into one walk. (roadmap §12;
> plan 01 §9.)
>
> **Stated as one falsifiable claim** (roadmap §12.1): _A non-coder states an objective in plain
> language; the agent executes it autonomously across ≥2 formerly-siloed systems under a posture the
> user chose beforehand; and the resulting work is traced (glass box), interveneable (rewind any step
> and re-cascade), and versioned (old outputs kept)._ If all four properties hold in one continuous
> walk, the capability is proven. If any one fails, the capability is not yet whole — and the
> per-component falsifier names exactly which earlier proof to revisit.
>
> **What this demo deliberately omits, honestly** (roadmap §12.3; plan 03 §8.3): user-facing
> **branching** (deferred past v1 — linear retrace only); **cross-org** sharing (gated behind C6's
> trust-model design); and the **team** layer (the agent-comms bet — instrumented separately, never
> asserted here). Omitting these keeps the demo honest: it proves what is proven and does not stage
> what is still a bet.
>
> **It runs on the comms-wedge's small 4-step graph first** (Message → Classification → Retrieval →
> Response) — a graph small enough that non-coder legibility is _achievable_, so the demo's legibility
> falsifier is testable on a bounded surface before it is the headline. The demo is the literal user
> walk, with receipts. (roadmap §12.3, §8.2.)

---

## Dependency posture for this milestone

- **The demo depends on C0–C5 + C4.** Each property in the walk maps to a component proof with its
  real upstream milestone todos: posture-chosen-beforehand + plain-language objective → M3 (C3
  self-service surface) + M2 (C2 posture); plan surfaced before running → M2 (C2 plan-proposed gate);
  execution across ≥2 systems governed + least-privilege → the C4 two-system-reach milestone todos;
  traced glass box → M0-9 (C1 verdict) at scale; rewind + re-cascade → M4-1..M4-7 (C5 cascade engine);
  versioned + audited intervention → M4-4 + M4-9 (C5 versioning + retention). (roadmap §12.2;
  ledger §13.)
- **C7b (the comms lighthouse) runs concurrently, not after.** The demo is run against a real,
  painful, named cross-system workflow with a real design partner watching — converting "the
  capability runs" into "a specific buyer recognized it." This is temporally parallel with the
  component builds, sequenced "last" only in dependency order. (roadmap §11.2, §12.3.)
- **This is an INTEGRATION milestone — its todos WIRE and TEST the composition, they do not re-BUILD
  the components.** Each component's own milestone owns its BUILD. The risk here is the _seams_: the
  composed path (surface → posture → plan-gate → two-system execution → glass-box trace → rewind →
  version) producing the user's expected outcome end-to-end, which no single component test observes.

---

### M7-1 — Compose the objective-intake → posture-chosen-beforehand entry path

- **Type:** INTEGRATION
- **Implements:** specs/platform-overview.md §work-model + specs/trust-posture-and-governance.md §posture-before-work (+ plan: 02-plans/01 §9; roadmap §12.2)
- **What:** Wire the non-coder self-service surface so a user states an objective in plain language
  ("Produce the Q3 figures for the client and draft the cover note") AND chooses a posture
  _beforehand_ ("Ask me once") — and that chosen posture actually governs the run that follows. This
  is the first segment of the walk: surface + posture, composed.
- **Reuses → Builds:** the C3 self-service surface (objective intake, three-button posture chooser) +
  the C2 posture machinery (the chosen posture stamps the run) → the wired intake-to-posture path.
- **Invariants:** posture-at-time (the chosen posture is recorded as the operative posture for the
  run); posture safety-floor (operative = min(user-chosen, system-floor)); tenant-isolation
  (objective + posture are per-customer).
- **Sizing:** ~1 cycle.
- **Depends on:** M3 (C3 self-service surface todos), M2 (C2 governance/posture todos).
- **Acceptance (confirm / falsify):** **Confirm:** a plain-language objective + a beforehand posture
  choice produce a run governed by that posture (no code, no engineer). **Falsify:** the posture
  choice does not demonstrably change the run's behavior (it's a label, not a control). Real-infra
  Tier-2 + a non-coder walk segment with receipts.

### M7-2 — Compose the plan-proposed gate (fan-out surfaced before execution)

- **Type:** INTEGRATION
- **Implements:** specs/trust-posture-and-governance.md §plan-approval-gate (+ plan: 02-plans/01 §3, §9; roadmap §12.2)
- **What:** Wire the agent's plan (fan-out: pull figures · draft note) to be surfaced on screen as an
  inspectable object _before_ it runs, so under "Ask me once" the user approves exactly once at the
  plan→execute boundary, then execution proceeds. This is the governance seam between intake and
  two-system execution.
- **Reuses → Builds:** the C2 plan-proposed gate (the fan-out plan as an approvable decision object) +
  the live decision-to-screen stream → the wired surface-the-plan-then-gate path in the demo flow.
- **Invariants:** no-orphaned-governance (the gate has a real hot-path call site + a Tier-2 wiring
  test proving the framework calls it); LLM-first (the consequentiality judgment is LLM-judged, not
  keyword-matched); tenant-isolation.
- **Sizing:** ~1 cycle.
- **Depends on:** M2 (C2 governance/plan-proposed-gate todos), M7-1.
- **Acceptance (confirm / falsify):** **Confirm:** the fan-out plan appears on screen as an
  inspectable object before any action runs; "Ask me once" gates exactly once; approval lets execution
  proceed within the envelope and blocks anything outside it. **Falsify:** the plan runs before it is
  surfaced, OR the gate is a facade with no hot-path call site (the orphan pattern). Real-infra Tier-2
  wiring test + non-coder walk segment with receipts.

### M7-3 — Compose execution across ≥2 formerly-siloed systems, governed + least-privilege

- **Type:** INTEGRATION
- **Implements:** specs/connectors-and-integration.md §governed-connectivity (+ plan: 02-plans/01 §7, §9; roadmap §12.2, §7)
- **What:** Wire the approved objective to run across two formerly-separate systems — read from the
  records/ledger system, write to the document system — with governance sitting _between_ the agent
  and each connector (a write to a system of record can be HELD until a human approves), the agent
  granted only the minimum tool/clearance envelope the objective needs, and all reasoning in the
  logged model I/O (tools are dumb endpoints, the LLM reasons). This proves the inversion: the agent
  is the integration layer, not the human.
- **Reuses → Builds:** the C4 governed-curation + least-privilege envelope + the connector protocol +
  C2 governance as the between-agent-and-connector enforcement point → the wired two-system run in the
  demo flow.
- **Invariants:** tools-dumb (no decision logic in tool code); least-privilege per objective
  (narrow-and-earned, not the union of everything connected); governed-connectivity (a write to a
  system of record requires the envelope to permit it or a human gate); tenant-isolation on every
  connector call.
- **Sizing:** ~1 cycle (composition; C4 owns the connector BUILD).
- **Depends on:** the C4 two-system-reach milestone todos (governed connectors + least-privilege
  envelope), M7-2.
- **Acceptance (confirm / falsify):** **Confirm:** the objective runs across two systems that used to
  need a human bridge, governed between agent and each connector, with a least-privilege envelope and
  all reasoning visible in logged model I/O. **Falsify:** cross-system sequencing requires burying
  business logic in tool code (breaking the transparency contract), OR the agent must be
  over-provisioned with broad standing access to function. Real-infra Tier-2 over the two-system path.

### M7-4 — Compose the live glass-box trace at scale (the four-step flow recorded + streamed)

- **Type:** INTEGRATION
- **Implements:** specs/transparency-and-provenance.md §transparency-contract (+ plan: 02-plans/01 §4, §9; roadmap §12.2)
- **What:** Wire every input, tool call, result, decision, and output of the four-step run to be
  recorded as a content-fingerprinted step and streamed live to the screen as version 1 — with the
  black-box boundary holding (model I/O recorded; internal thinking not claimed). This is C1's
  single-step glass box composed across the whole flow.
- **Reuses → Builds:** the C1 content-addressed step records + the live telemetry feed into the
  ledger → the composed live-trace surface for the full 4-step run.
- **Invariants:** immutability; tenant-isolation (every fingerprint carries `tenant_id` — the
  content-addressed namespace cross-tenant leak vector, hard gate); determinism-boundary;
  posture-at-time (each step shows the posture in force when it ran).
- **Sizing:** ~1 cycle (composition; C1 owns the substrate BUILD).
- **Depends on:** M0-9 (C1 verdict — stable content-fingerprint + byte-exact single-step replay
  confirmed), M7-3.
- **Acceptance (confirm / falsify):** **Confirm:** the user watches every step's inputs/tool-calls/
  results/decisions/outputs recorded and streamed live as v1; the black-box boundary is stated
  honestly (no claim to record internal thinking). **Falsify:** steps are not legibly surfaced, OR the
  trace over-claims (presents reconstructed internal reasoning as recorded). Real-infra Tier-2 +
  non-coder walk segment with receipts.

### M7-5 — Compose the interveneable rewind + re-cascade segment (with cost-preview + re-run/replay choice)

- **Type:** INTEGRATION
- **Implements:** specs/intervention-and-versioning.md §cascade-engine (+ plan: 02-plans/01 §4, §9; roadmap §12.2, §8.4)
- **What:** Wire the demo so the user spots a wrong assumption two steps back, rewinds to that step,
  changes the input; the cost-preview shows "this re-runs N steps"; only the affected downstream
  recomputes while the unrelated branch is skipped on fingerprint match; and the user is asked the
  explicit per-step choice — re-run with my edit, or keep the recorded output (re-run vs replay). This
  is C5 composed into the live demo.
- **Reuses → Builds:** the C5 cascade engine (dirty-propagation + fingerprint-skip + cost-preview +
  reuse-recorded-vs-regenerate) wired into the demo's hot path → the interveneable segment of the walk.
- **Integration note (spend model):** the C5 cost-preview hard gate (M4-6) and the M1 budget HELD gate
  compose into ONE coherent non-coder spend model — the rewind shows "this will cost N steps to re-run"
  (cost-preview) and, if a re-run would exceed the user's configured budget, the M1 budget gate HELDs it
  with "this exceeds your limit." The two MUST read as a single spend story to the non-coder, not two
  unrelated dialogs: one says how much, the other says when it is too much.
- **Invariants:** cascade-minimality (only affected downstream recomputes; unrelated branch skipped);
  determinism-boundary (the per-step re-run/replay choice is explicit, not silent); tenant-isolation;
  immutability.
- **Sizing:** ~1 cycle (composition; C5/M4 owns the engine BUILD).
- **Depends on:** M4-1 through M4-7 (C5 cascade engine: dirty-propagation + fingerprint-skip +
  cost-preview + reuse-recorded-vs-regenerate + the comms-wedge wire), M7-4.
- **Acceptance (confirm / falsify):** **Confirm:** rewind → edit → cost-preview names the minimal
  re-run count → only affected downstream recomputes → explicit re-run-vs-keep choice surfaced.
  **Falsify (both C5 falsifiers checked here too):** (1) the engine can't bound the cascade or there's
  no comprehensible cost-preview; (2) the non-coder can't tell "which version is current" in seconds.
  Real-infra Tier-2 over the 4-step graph + non-coder walk segment with receipts.

### M7-6 — Compose the versioned + audited-intervention segment (compare + revert)

- **Type:** INTEGRATION
- **Implements:** specs/intervention-and-versioning.md §immutable-versioning (+ plan: 02-plans/01 §4, §9; roadmap §12.2)
- **What:** Wire the demo so the original figures + note survive as version 1, the corrected ones are
  version 2 with a back-pointer, the user can compare v1 vs v2 and revert, and the intervention itself
  is audited (who changed what, when). This closes the walk's fourth property: versioned.
- **Reuses → Builds:** the C5 version-on-rerun + intervention-audit + revert/compare read paths → the
  versioned segment of the demo flow.
- **Invariants:** immutability (v1 survives untouched); audit-completeness (the intervention is
  recorded); tenant-isolation (version + audit rows carry `tenant_id`).
- **Sizing:** ~1 cycle (composition; C5/M4 owns the version BUILD).
- **Depends on:** M4-4 (C5 version-on-rerun + audited-intervention) and M4-9 (version retention),
  M7-5.
- **Acceptance (confirm / falsify):** **Confirm:** v1 survives, v2 has a back-pointer, compare + revert
  work without re-running, the intervention is audited. **Falsify:** the original is lost (overwrite),
  OR the intervention leaves no audit trail. Real-infra Tier-2 with read-back of every version write +
  non-coder walk segment with receipts.

### M7-7 — End-to-end "capability proven" walk: one continuous run, receipts, on the comms 4-step graph

- **Type:** TEST
- **Implements:** specs/platform-overview.md §capability-proof (+ plan: 02-plans/01 §9; roadmap §12.1–§12.3)
- **What:** Run the four properties as ONE continuous walk on the comms-wedge 4-step graph (objective
  → posture → plan-gate → two-system execution → live trace → rewind + re-cascade → versioned),
  performed by a non-coder, captured with receipts (verbatim actions + what they saw + their
  disposition at each step). This is the integration test that proves the composition, not the
  individual components.
- **Reuses → Builds:** M7-1 through M7-6 (the composed segments) → the single end-to-end
  capability-proof walk.
- **Invariants:** all six ledger invariants hold across the composed path; no-orphaned-governance on
  the wired gates; tenant-isolation as a hard gate end-to-end (the content-addressed namespace must
  not leak across tenants anywhere in the composed flow).
- **Sizing:** ~1 cycle (the composition test; the per-component cycles are in their own milestones).
- **Depends on:** M7-1 through M7-6; C0–C5 + C4.
- **Acceptance (confirm / falsify):** **Confirm:** all four properties hold in one continuous
  non-coder walk with receipts — the capability is proven whole. **Falsify:** any one property fails
  in the composed run (even where the component passed in isolation) — the per-component falsifier
  names which proof to revisit. The literal walk per `user-flow-validation.md` is mandatory; passing
  component tests is necessary but INSUFFICIENT. Real-infra Tier-2/3 over the 4-step comms graph +
  the non-coder usability walk with receipts.

### M7-8 — Lighthouse instrumentation: run the demo against a real named workflow with a design partner watching

- **Type:** INTEGRATION
- **Implements:** specs/platform-overview.md §capability-proof + specs/business-model.md §design-partner (+ plan: 02-plans §11.2, §12.3)
- **What:** Run the end-to-end walk (M7-7) against a real, painful, _named_ cross-system workflow with
  a real design partner watching — not a synthetic demo — and instrument it: does the partner say "I
  would pay for that against _this_ workflow"? This converts "the capability runs" into "a specific
  buyer recognized it against a real painful workflow." Runs concurrently with the component builds,
  not after.
- **Reuses → Builds:** the comms wedge wholesale (a sunk asset) + the M7-7 walk → the design-partner
  instrumentation (the business-falsifiability layer).
- **Invariants:** treat the lighthouse as evidence, not gravity (do not re-verticalize the horizontal
  product to one partner's idiosyncrasies); named-human-on-decision via the posture-gated HELD path;
  tenant-isolation.
- **Sizing:** concurrent with C2–C5 (coordination cycles, not a sequential build).
- **Depends on:** M7-7 (the walk must exist to run it against a partner).
- **Acceptance (confirm / falsify):** **Confirm:** a specific design partner watches the walk against
  their own real workflow and says they would pay for it against _that_ workflow. **Falsify:** the
  walk completes and the immediate next question is "now which vertical?" with no evidence-backed
  answer, OR every buyer conversation requires the buyer to _imagine_ their use-case rather than
  _recognize_ it (the generic-tool tell). Run against a real partner, with receipts.

---

## Milestone-level acceptance

The capability is **proven** when the single continuous walk (M7-7) holds all four properties on the
comms 4-step graph under real infrastructure AND a non-coder completes it with receipts — and is
**recognized** when M7-8's design partner says they would pay for it against a real named workflow.
If any property fails in the composed run, report which earlier proof to revisit (the per-component
falsifiers name it). Be honest about the two omissions held back from this demo by design (branching,
cross-org) and about the legibility frontier — the demo proves what is proven and does not stage what
is still a bet.
