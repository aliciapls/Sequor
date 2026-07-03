# M0 — Foundational Spikes (C0 runtime-ownership + C1 glass-box single-step replay)

> **What this milestone is, in plain language.** Before we commit a whole program to building the
> platform, we run two cheap, throwaway experiments that can each kill the hardest part of the vision
> for the cost of a single session. The first asks: _do we have to own the engine that drives the
> agent, or can we sit on top of one someone else built?_ The second asks: _can we record one step of
> an agent's work transparently and replay it exactly, without calling the AI again?_ Neither writes
> production code. Each delivers a **written verdict with receipts** — a literal walk that shows the
> three (C0) / two (C1) checks actually ran, pass or fail.
>
> **Why spikes, not builds.** A failed spike costs one session, not a program (capability-roadmap §3.5,
> §10.3). The deliverable of M0 is _evidence_ — an uncertainty converted to a fact — not a shipped
> component. C0 is the **single gating structural decision** the whole architecture hinges on
> (architecture §8, §12 unknown #1; capability-roadmap §3.5). The honest expectation, flagged up front:
> the evidence already tilts toward **"own the loop"** via the **envoy-hybrid** (own the governed-core
> runtime, develop the product on commercial harnesses) — the spike's job is to convert that tilt into
> evidence _before_ the build commits, not to re-open the recommendation (architecture §8.2–§8.3;
> capability-roadmap §3.2).
>
> **Reading note.** Effort is in autonomous execution cycles, never human-days (per
> `autonomous-execution.md`). Delegation is named neutrally ("delegate to analyst") per
> `cross-cli-artifact-hygiene.md`. Every spike's acceptance requires a literal walk with receipts per
> `user-flow-validation.md` — for a spike, the "user" is the founder reading the verdict, and the walk
> is the recorded execution of each check.

---

## Milestone dependency shape

```
  M0-1  C0 spike scaffold (throwaway harness)
     │
     ├──> M0-2  C0 check A — record intent BEFORE the action (introspection-only)
     ├──> M0-3  C0 check B — pause/gate on a pre-set posture (introspection-only)
     └──> M0-4  C0 check C — re-execute from a prior recorded step
                    │
                    └──> M0-5  C0 VERDICT (own-the-loop vs build-on-harness; envoy-hybrid expectation)
                              │  ← GATES the entire downstream build (structural, human gate)
                              ▼
  M0-6  C1 spike scaffold (single-step record fixture)
     │
     ├──> M0-7  C1 check A — content-addressed single-step record (stable fingerprint)
     └──> M0-8  C1 check B — byte-exact replay by fingerprint, no fresh model call
                    │
                    └──> M0-9  C1 VERDICT (is one step replayable? gates C5 cascade engine)
```

C0 (M0-1..M0-5) gates everything; C1 (M0-6..M0-9) proves the M1 substrate and gates the C5 cascade
engine. C1 may begin once the C0 verdict settles the runtime direction (the record/replay surface
depends on whether we own the loop). The two checks within each spike are parallel-eligible (different
introspection surfaces) but share the same throwaway scaffold.

---

### M0-1 — C0 spike scaffold: a throwaway harness over an existing introspection surface

- **Type:** SPIKE
- **Implements:** specs/platform-overview.md §4 (Layer 2 runtime — TARGET-STATE gap) (+ plan: 02-plans/01-architecture.md §8.2–§8.3; capability-roadmap §3.1, §3.3)
- **What:** Stand up a throwaway test harness that sits on an existing agent harness's introspection surface (the thing under test) plus a reference to the envoy `KailashRuntime` abstraction as the own-the-loop arm. No production code — the harness exists only to run the three C0 checks (M0-2, M0-3, M0-4) and capture receipts.
- **Reuses → Builds:** existing harnesses' introspection surfaces + envoy `KailashRuntime` as the reference own-the-loop design → a single throwaway spike harness (deleted after the verdict).
- **Invariants:** none held by the spike itself (it is throwaway); but the harness MUST be able to capture a literal receipt (verbatim command + verbatim output) for each check per `user-flow-validation.md` — a spike that reports "looks feasible" without the checks demonstrably run is not a proof (capability-roadmap §3.4).
- **Sizing:** ~0.5 cycle (greenfield spike scaffold; first-session ~2–3× factor per `autonomous-execution.md`, but the scaffold is small).
- **Depends on:** none
- **Acceptance (confirm / falsify):** CONFIRM — the harness loads, can drive a trivial agent action through the introspection surface, and emits a captured receipt for that trivial action. FALSIFY (kill-signal) — the introspection surface cannot be programmatically driven at all (no observable hook into the loop), which itself is partial evidence toward "own the loop." Receipt: verbatim harness invocation + verbatim first-action capture embedded in the spike's verdict file.

### M0-2 — C0 check A: can we record the agent's INTENT before the action, via introspection alone?

- **Type:** SPIKE
- **Implements:** specs/trust-posture-and-governance.md §4 (plan is approvable BEFORE execution), specs/transparency-and-provenance.md §5.1 (plan_proposed Decision before execution) (+ plan: 02-plans/01-architecture.md §8.2; capability-roadmap §3.2)
- **What:** Using only the existing harness's introspection surface, attempt to capture what the agent _intends to do_ (its planned action / fan-out) BEFORE the action executes. Record whether the surface exposes pre-action intent or only post-action results.
- **Reuses → Builds:** the harness introspection surface → a recorded pass/fail finding with a receipt.
- **Invariants:** none (throwaway); receipt MUST show the literal capture attempt and its actual output per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (live feedback loop — each capture attempt is testable against a fixture action; higher budget per `autonomous-execution.md` § Feedback Loops).
- **Depends on:** M0-1
- **Acceptance (confirm / falsify):** CONFIRM — the harness records the agent's intent before the action fires, with a verbatim receipt showing the intent captured ahead of execution. FALSIFY — the surface exposes only per-call binary yes/no permission prompts and cannot stage intent ahead of the action (architecture §8.2). Either outcome is a recorded finding; the FALSIFY case is direct evidence toward "own the loop."

### M0-3 — C0 check B: can we pause/gate on a PRE-SET posture, via introspection alone?

- **Type:** SPIKE
- **Implements:** specs/trust-posture-and-governance.md §2 (posture choice IS the HITL/HOTL gate), §4.1 (verification gradient: HELD pauses) (+ plan: 02-plans/04 §2, §4; capability-roadmap §3.2)
- **What:** Using only the introspection surface, attempt to hold/pause an agent action against a posture chosen _beforehand_ (e.g. "step through pauses every consequential action"). Record whether the surface supports a graduated, pre-set gate or only coarse per-call prompts.
- **Reuses → Builds:** the harness introspection surface + the three-button posture concept (Go-ahead / Ask-once / Step-through) as the gate semantics under test → a recorded pass/fail finding with a receipt.
- **Invariants:** none (throwaway); receipt MUST show the literal pause attempt and observed behavior per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (live feedback loop against a fixture action).
- **Depends on:** M0-1
- **Acceptance (confirm / falsify):** CONFIRM — a pre-set posture demonstrably changes the harness's live pause behavior (an action that should pause under "step through" actually pauses), verbatim receipt attached. FALSIFY — the harness's permission model is binary/per-call and cannot honor a graduated pre-set posture (architecture §8.2). The FALSIFY case is evidence toward "own the loop."

### M0-4 — C0 check C: can we re-execute from a PRIOR recorded step, via introspection alone?

- **Type:** SPIKE
- **Implements:** specs/intervention-and-versioning.md §3 (retrace-to-any-step), §4.1 (re-derive forward) (+ plan: 02-plans/01-architecture.md §8.2; capability-roadmap §3.2)
- **What:** Using only the introspection surface, attempt to re-execute the agent from a prior recorded step with downstream re-derivation — without reimplementing the loop. Record whether replay-from-step is possible without loop control.
- **Reuses → Builds:** the harness introspection surface → a recorded pass/fail finding with a receipt.
- **Invariants:** none (throwaway); receipt MUST show the literal replay-from-step attempt and observed result per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (live feedback loop; this is the hardest of the three checks).
- **Depends on:** M0-1
- **Acceptance (confirm / falsify):** CONFIRM — the harness re-executes from a prior recorded step with downstream re-derivation through introspection alone, verbatim receipt attached. FALSIFY — replay-from-step is impossible without owning the loop (the harness cannot rewind to a prior point) (architecture §8.2; capability-roadmap §3.2). The FALSIFY case — the most likely per the honest expectation — is the strongest evidence toward "own the loop."

### M0-5 — C0 VERDICT: own-the-loop vs build-on-harness (the gating structural decision)

- **Type:** SPIKE
- **Implements:** specs/platform-overview.md §3.2 (CLI-neutral, owned governed core), §9 (Foundation independence decision) (+ plan: 02-plans/01-architecture.md §8.3, §12 unknown #1; capability-roadmap §3.5, §10.1)
- **What:** Synthesize M0-2/M0-3/M0-4 into a single written verdict: does introspection alone satisfy record-intent + pause-on-posture + replay-from-step (build-on-harness viable), or must the platform own a runtime abstraction (own-the-loop)? State the verdict against the independence constraint (`independence.md` forbids depending on a proprietary SDK in the product core, which rules out the purest build-on-commercial-harness option regardless of the checks — architecture §8.2). Land the envoy-hybrid recommendation if the evidence holds: own the governed-core runtime so M1/M2 are native; develop the product on commercial harnesses. Delegate to analyst for the failure-point synthesis; delegate to reviewer to confirm the verdict's checks are demonstrably run, not asserted.
- **Reuses → Builds:** the three check findings (M0-2..M0-4) → one decision-grade verdict document (no production code).
- **Invariants:** honesty — the verdict MUST show the literal walk (record-intent → pause-on-posture → replay-from-step) actually executed with receipts per `user-flow-validation.md` + `capability-roadmap §3.4`; symmetric pros/cons per `recommendation-quality.md` (own-the-loop raises C1/C5 cost but makes M1/M2 native — architecture §8.3 cons). No silent dismissal of a FALSIFY check.
- **Sizing:** ~0.5 cycle (synthesis + write-up; the checks already ran).
- **Depends on:** M0-2, M0-3, M0-4
- **Acceptance (confirm / falsify):** CONFIRM — a verdict file exists stating own-the-loop-vs-build-on-harness with all three checks' receipts inline, a single recommendation (expected: envoy-hybrid) with symmetric pros/cons, and the independence-constraint note; the founder can read it and confirm the runtime direction once. FALSIFY of the milestone — the verdict asserts a direction without the three checks' receipts (a "looks feasible" verdict is BLOCKED per `capability-roadmap §3.4`). **STRUCTURAL HUMAN GATE:** this verdict sets the runtime architecture for everything downstream — the founder confirms the runtime direction here, once, before assembly (architecture §8, §12 #1; capability-roadmap §3.5).

### M0-6 — C1 spike scaffold: a single-step record fixture over the reuse substrate

- **Type:** SPIKE
- **Implements:** specs/transparency-and-provenance.md §2.1 (Step/Output/Decision node model), §2.5 (ledger is source of truth) (+ plan: 02-plans/01-architecture.md §4.3–§4.4; capability-roadmap §4.1, §4.3)
- **What:** Stand up a throwaway fixture that records ONE agent step — its inputs, the tool calls, the result, the output — reusing the PACT `Run` / `AgenticArtifact` / `AgenticDecision` record models and the Kailash durable store, fed by the OpenTelemetry GenAI span shape. No production code; the fixture exists only to run the two C1 checks (M0-7, M0-8) and capture receipts. Delegate to dataflow-specialist for the record-model reuse (the PACT models are DataFlow `@db.model` records).
- **Reuses → Builds:** PACT `Run`/`AgenticArtifact`/`AgenticDecision` + Kailash durable store + OTel GenAI span shape + Kailash content-addressing (hash-as-identity already ships) → a throwaway single-step record fixture (deleted after the verdict).
- **Invariants:** none held by the spike itself (throwaway); but the fixture MUST stamp `tenant_id` on the record even at spike scale, so the fingerprint/query design does not bake in a cross-tenant leak the real build would inherit (per `tenant-isolation.md`; transparency-and-provenance §2.6 invariant 2 — the highest-severity invariant). Receipt-capable per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (substrate is reused; the fixture is small). Live feedback loop — the recorded step is testable against the fixture.
- **Depends on:** M0-5 (the record/replay surface design depends on the settled runtime direction)
- **Acceptance (confirm / falsify):** CONFIRM — the fixture records one agent step into a unified content-addressed record with `tenant_id` present, and emits a verbatim receipt of the recorded step (inputs, tool calls, result, output legibly surfaced). FALSIFY — the reuse substrate cannot be wired into a single unified step record at all (the records are too divergent to unify), which is a cheap early signal that the M1 substrate needs rework before C5 (capability-roadmap §4.5).

### M0-7 — C1 check A: is one step content-fingerprintable STABLY?

- **Type:** SPIKE
- **Implements:** specs/transparency-and-provenance.md §2.3 (content-addressing — `step_id = hash(inputs + code + upstream fingerprints)`) (+ plan: 02-plans/01-architecture.md §4.3; capability-roadmap §4.2)
- **What:** Record the same single step twice with identical inputs and confirm the content fingerprint is identical both times (stable), and changes completely when one byte of input changes (tamper-evident). This is the precondition for "only recompute what changed" — without a stable fingerprint, the cascade engine (C5) can never be built.
- **Reuses → Builds:** Kailash content-addressing (hash-as-identity, already ships for crash-recovery/idempotency) → a recorded pass/fail finding with a receipt showing two identical-input fingerprints matching + a one-byte-change fingerprint diverging.
- **Invariants:** determinism of the fingerprint function over identical inputs; `tenant_id` in the fingerprint namespace (transparency-and-provenance §2.6 invariants 2, 3). Receipt MUST show the literal fingerprint values per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (live feedback loop against the fixture).
- **Depends on:** M0-6
- **Acceptance (confirm / falsify):** CONFIRM — identical inputs yield an identical `step_id` across two recordings, and a one-byte input change yields a completely different `step_id`; verbatim fingerprint receipt attached. FALSIFY (kill-signal for the cascade) — the same inputs yield different fingerprints (unstable), so "only recompute what changed" can never be built (capability-roadmap §4.2). This FALSIFY kills C5; surfacing it cheaply here is the point.

### M0-8 — C1 check B: can replay reuse the recorded output BYTE-FOR-BYTE without a fresh model call?

- **Type:** SPIKE
- **Implements:** specs/intervention-and-versioning.md §6.1 (Replay = reuse recorded answer by fingerprint, fully deterministic), specs/transparency-and-provenance.md §2.6 invariant 3 (determinism boundary) (+ plan: 02-plans/01-architecture.md §4.4; capability-roadmap §4.2)
- **What:** Replay the recorded single step by its fingerprint and confirm the output reproduces byte-for-byte from the recorded record, with NO fresh model call. Confirm the black-box boundary holds: we record what the model emits at its input/output surface and do not claim to record internal reasoning (transparency-and-provenance §1.3).
- **Reuses → Builds:** the recorded step (M0-6) + content-addressed lookup → a recorded pass/fail finding with a receipt showing replay output == recorded output and zero model calls during replay.
- **Invariants:** determinism boundary (replay reuses recorded output unless the user explicitly regenerates — invariant 3); immutability (replay reads, never mutates — invariant 1); receipt MUST show byte-equality + a model-call count of zero per `user-flow-validation.md`.
- **Sizing:** ~0.5 cycle (live feedback loop against the fixture).
- **Depends on:** M0-6
- **Acceptance (confirm / falsify):** CONFIRM — replay-by-fingerprint reproduces the recorded output byte-for-byte with zero model calls; verbatim receipt shows the byte-equality and the model-call counter at zero. FALSIFY (kill-signal) — replay cannot reuse the recorded output and always re-calls the model, so "show me exactly what happened" is impossible and the determinism boundary is broken (capability-roadmap §4.2).

### M0-9 — C1 VERDICT: is one step replayable? (gates the C5 cascade engine)

- **Type:** SPIKE
- **Implements:** specs/intervention-and-versioning.md §6.2 (determinism resolution), specs/transparency-and-provenance.md §2.6 (the four single-step-scale invariants) (+ plan: 02-plans/01-architecture.md §4.4–§4.5; capability-roadmap §4.5, §10.1)
- **What:** Synthesize M0-7 (stable fingerprint) and M0-8 (byte-exact replay) into a written verdict: is the M1 _substrate_ sound at single-step scale? State which of the four single-step invariants held (immutability, tenant-isolation, determinism-boundary, posture-at-time). A clean verdict unblocks C5 (the cascade engine); a failure is a cheap signal that the M1 mechanism needs rework before the cascade is attempted. Delegate to analyst for synthesis; delegate to reviewer to confirm the two checks are demonstrably run.
- **Reuses → Builds:** the two check findings (M0-7, M0-8) → one decision-grade verdict document (no production code).
- **Invariants:** honesty — the verdict MUST show the literal record→replay walk actually executed with receipts per `user-flow-validation.md` + `capability-roadmap §1` framing rule 1; the four single-step invariants explicitly checked (capability-roadmap §4.4). No silent dismissal of a FALSIFY check.
- **Sizing:** ~0.5 cycle (synthesis + write-up; the checks already ran).
- **Depends on:** M0-7, M0-8
- **Acceptance (confirm / falsify):** CONFIRM — a verdict file exists stating "one step is recordable and deterministically replayable" with both checks' receipts inline and the four single-step invariants confirmed; this unblocks the C5 cascade build. FALSIFY of the milestone — the verdict asserts replayability without M0-7/M0-8 receipts (BLOCKED per `capability-roadmap §1`). **EXECUTION GATE (autonomous convergence):** a clean C1 verdict unblocks C5; a failure here is a cheap, intended signal that the M1 mechanism needs rework before the expensive cascade build (capability-roadmap §4.5).

---

## M0 exit criteria (both verdicts before any production build)

1. **C0 verdict (M0-5)** sets the runtime direction (expected: envoy-hybrid — own the governed core). Structural human gate — the founder confirms once.
2. **C1 verdict (M0-9)** confirms (or falsifies) that one step is recordable + deterministically replayable. Gates the C5 cascade engine.
3. All spike code is **deleted** after the verdicts land — M0's deliverable is two written verdicts with receipts, not shipped components (capability-roadmap §3.3, §4.3).
4. Each verdict carries verbatim receipts of every check actually executing (per `user-flow-validation.md`) — a "looks feasible" verdict without receipts is BLOCKED.
