# Plan 02 — Capability Roadmap: Proving the Disrupted-Work Capability

> **Purpose.** This is the build sequence for the platform the brief describes — one agnostic,
> transparent, team-oriented interface where non-coders get _all_ knowledge work done through an AI
> agent, instead of crossing N siloed vertical systems. It turns Plan 01's seven-layer architecture
> into an **ordered sequence of capability PROOFS** — not go-to-market milestones — per **Decision B**
> (capability-first; GTM deferred, `briefs/01-vision.md` §4).
>
> **What "capability-first" means for this plan.** We sequence by _what each step decisively proves or
> disproves about whether the disrupted-work capability is buildable_ — not by what sells, not by what
> a beachhead vertical needs. The cheapest experiments that can _kill the whole thesis_ come first; the
> expensive assembly comes only after the killers have been survived. This is the opposite of a feature
> roadmap: each step's deliverable is **evidence**, and the unit of progress is "an uncertainty
> converted into a fact."
>
> **Audience.** A non-technical founder. Plain language throughout; every technical term is translated
> on first use (per `rules/communication.md`). Effort is in **autonomous execution cycles** — work an
> AI agent system completes in a session — never human-days (per `rules/autonomous-execution.md`).
> Competitors are named factually, never as a product Sequor is "a version of" (per
> `rules/independence.md`).
>
> **Grounding.** Every load-bearing claim cites the brief, an analysis file
> (`01-analysis/08-product-focus-80-15-5.md`, `01-analysis/09-risks-failure-points.md`,
> `01-analysis/03-unique-selling-points.md`), Plan 01 (`02-plans/01-architecture.md`), or a research
> file (`01-analysis/01-research/09-comms-wedge-mapping.md`). Genuine uncertainty is flagged, not
> smoothed over.
>
> **Value framing this roadmap sequences against.** "Capability-first" means sequencing by _value to
> the user_, so this roadmap's order rests on two companion analyses that establish what that value is:
> `01-analysis/02-value-propositions.md` (the enterprise-buyer value claims, each tagged
> PROVEN/credible vs CONTINGENT) and `01-analysis/05-aaa-framework.md` (the three value axes —
> **Automate** removes the hands, **Augment** sharpens the head, **Amplify** clones the expert). The
> sequence cheapest-falsifiers-first is a value-ordering: it proves the highest-value, highest-risk
> capabilities (M1 transparency, M2 governance) before the expensive assembly, so each value axis is
> proven (or killed) in priority order.

---

## 0. The roadmap in one paragraph

The platform is ~80% already-built primitives and ~5% genuinely-new, moat-bearing work (analysis 08
§2, §6). The risk is therefore **concentrated, not diffuse** (analysis 08 §6.2): a small number of
hard experiments decide whether the strongest moat (M1 — rewind-any-step) is even buildable, and
whether the whole thing degrades into "an agent does your work in one interface" — the surface Claude
Cowork already occupies (analysis 09 §5). So the sequence front-loads the **cheapest decisive
falsifiers**: a spike that answers "do we have to own the agent's engine?" and a small build that
answers "can we even see and replay one step?" Those two run first because a failed spike costs **one
session, not a program** (analysis 08 §6.2). Once survived, the sequence ships the **governance
foundation** (M2 — the most-proven, lowest-risk moat, analysis 03 §3.4), then the **two concentrated
net-new builds** (the non-coder self-service surface and the rewind/cascade engine), then a
**design-first decision** (the trust model for accepting work-recipes from outside companies) before
opening cross-org sharing, and finally **instruments the two unproven bets** (agents-talk-better-than-
humans, and comms-as-the-first-real-workflow) so they are _measured, never assumed_. The whole arc
converges on a single end-to-end demonstration: _a non-coder states an objective, agents execute it
across two formerly-separate systems, and the result is traced, interveneable, and versioned._

---

## 1. How to read this roadmap (the proof discipline)

Every capability below is written as a **proof**, with five fixed fields. This shape is what makes the
roadmap capability-first rather than feature-first.

| Field                | What it answers                                                                                                                                                                          |
| -------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Proof criterion**  | The single observable result that _confirms_ the capability works AND the single result that _falsifies_ it. If neither can be stated, the step is not a proof and does not belong here. |
| **Reuses vs builds** | Which shipped ecosystem primitive is re-pointed (the ~80%), and what is genuinely new (the ~5%) — per analysis 08 §2/§6.1 and Plan 01 §10.                                               |
| **Invariants held**  | The properties the implementation must never violate (tenant isolation, immutability, etc.) — the sharding budget axis per `autonomous-execution.md` § Per-Session Capacity Budget.      |
| **Sizing**           | Autonomous execution cycles, with sharding where load-bearing logic exceeds ~500 lines or ~5–10 simultaneous invariants.                                                                 |
| **Gate**             | What human decision (if any) this proof unblocks, and what it blocks if it fails.                                                                                                        |

**Two framing rules carried throughout (per the strategic spine):**

1. **A capability is "proven" only against real infrastructure and a real user-facing walk** — passing
   a unit test in isolation is necessary but insufficient (per `rules/testing.md` Tier 2/3 and
   `rules/user-flow-validation.md`). The orphan-detection discipline applies: a governance manager that
   ships without a real call site on the hot path AND a Tier-2 test proving the framework calls it is a
   _lie_, not a proof (analysis 08 §6.2; Plan 01 §3.5; `rules/orphan-detection.md`).
2. **The proofs are independent enough to parallelize** where they touch different layers (analysis 08
   §6.2; Plan 01 §11.1) — but the _ordering below is a dependency order_, not a wish-list. Steps marked
   "parallel-eligible" can overlap; steps marked "gates the next" cannot be reordered.

---

## 2. The sequence at a glance

```
  CAPABILITY PROOF SEQUENCE (each step = an uncertainty converted to a fact)

  ┌─ C0  RUNTIME-OWNERSHIP SPIKE ─────────── falsifier #1: do we own the loop? ─────┐
  │      "Can we get transparency + intervention + versioned-replay WITHOUT         │
  │       owning the agent's engine?"   → decides whether M1 is buildable at all    │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ gates everything (a "no" reshapes the whole build)
              ▼
  ┌─ C1  GLASS-BOX + SINGLE-STEP REPLAY ──── falsifier #2: is one step replayable? ─┐
  │      "Can we record one step transparently and replay it deterministically?"   │
  │      → with the loop settled (C0), prove the CONTENT primitive: content-        │
  │        addressed record + byte-exact replay of one step (the M1 substrate)      │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ gates C5 (the cascade engine)
              ▼
  ┌─ C2  GOVERNANCE FOUNDATION (M2) ──────────────── ship first; most-proven ──────┐
  │      "Can we set how-much-autonomy beforehand and enforce it live, on the       │
  │       real comms product, without breaking it?"  (SHADOW mode)                  │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ provides the posture-stamped step log C5 consumes; parallel-eligible w/ C3
              ▼
  ┌─ C3  NON-CODER SELF-SERVICE SURFACE ──────────── net-new build #1 ─────────────┐
  │      "Can a non-coder configure an objective's process/connectors/posture       │
  │       with zero engineering?"   → the 95%-pilot-failure escape                  │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ parallel-eligible with C2; both feed C5 + the end-to-end demo
              ▼
  ┌─ C4  AGENT REACHES ≥2 FORMERLY-SILOED SYSTEMS ── proves the inversion ─────────┐
  │      "Can one agent run an objective across two systems that used to need a     │
  │       human to bridge them — governed, least-privilege?"                        │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ gates the end-to-end demo (needs ≥2 systems)
              ▼
  ┌─ C5  RETRACE / CASCADE ENGINE (M1) ───────────── net-new build #2; the headline ┐
  │      "Can a non-coder rewind to a step, change it, and have ONLY the affected   │
  │       downstream recompute — with old versions kept?"                           │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ the headline moat; the end-to-end demo's climax
              ▼
  ┌─ C6  UNTRUSTED-PUBLISHER TRUST MODEL (M4) ─────── DESIGN-FIRST, then build ─────┐
  │      "Can org B safely run a work-recipe published by untrusted org A?"         │
  │      → design BEFORE opening cross-org; it constrains the registry             │
  └────────────────────────────────────────────────────────────────────────────────┘
              │ gates cross-org sharing (within-org sharing needs no new trust model)
              ▼
  ┌─ C7  THE TWO INSTRUMENTED BETS ───────────────── measure, never assume ────────┐
  │      C7a  agent-comms BET: do agent-mediated handoffs beat human handoffs?      │
  │      C7b  comms LIGHTHOUSE: is the proven capability paid-for-able on a real    │
  │           painful workflow with a real design partner watching?                 │
  └────────────────────────────────────────────────────────────────────────────────┘

  ═══ THE SINGLE "CAPABILITY PROVEN" DEMO (§11) sits on top of C0–C5 + C4 ═══
```

Why this order and not another is argued in full in §10. In brief: **C0 and C1 are first because they
are the two cheapest things that can kill the whole thesis — and they test two distinct questions, not
the same one twice.** C0 tests **loop-control**: must the platform own the agent's runtime to stage
intent, gate, and re-execute from a prior point? C1 tests the **content primitive**: assuming the loop
is settled, can a single step be recorded as a content-addressed record and replayed byte-for-byte
without re-calling the model? C0 can pass while C1 fails (you own the loop but cannot fingerprint a
step stably) and vice versa — so both are required, neither is redundant (analysis 08 §6.3; analysis
09 §7.2; Plan 01 §8.3, §4.4). **C2 ships before C5** because governance is the most-proven moat AND it produces the exact
posture-stamped step log the rewind engine reads (analysis 03 §8.2; Plan 01 §3, §4.5). **C6 is
design-first and gated before cross-org** because the trust model constrains the registry's shape
(analysis 08 §4.1; analysis 03 §5.4; Plan 01 §6.4). **C7 is last** because the two bets are _not
USPs_ — they are experiments the platform must not stake its value on (analysis 03 §4.4, §8.4;
analysis 09 §3).

---

## 3. C0 — The runtime-ownership spike (the gating falsifier)

### 3.1 What it proves, plainly

Every later capability rests on one unanswered question: **to make work transparent, interveneable,
and replayable, do we have to own the "engine" that drives the agent — or can we sit on top of an
engine someone else built (Claude Code, Codex, Gemini)?** (Plan 01 §8.2; analysis 08 §6.3; research 05
§4.4 cited there). "Own the engine" means we control the loop that gathers context, takes an action,
checks the result, and repeats — and crucially, we can record what the agent _intended_ before it acts
and replay from any earlier point. An existing commercial engine exposes only coarse, per-action
yes/no permission prompts (Plan 01 §8.2) — possibly too coarse for the rewind-and-intervene promise.

### 3.2 Proof criterion

- **Confirms (own-the-engine NOT required):** a spike harness, sitting on an existing harness's
  introspection surface, can (a) record the agent's _intent before the action_, (b) pause/gate on a
  pre-set posture, and (c) re-execute from a prior recorded step with downstream re-derivation —
  _without_ the platform reimplementing the loop. If all three hold on the existing surface, the
  platform can sit _on_ harnesses (cheaper) — subject to the independence constraint below.
- **Falsifies (own-the-engine REQUIRED):** any of the three cannot be done through introspection alone
  — the harness's permission model is binary/per-call and cannot stage intent, OR replay-from-step is
  impossible without loop control. Then transparency + intervention + replay is a _runtime_ capability,
  which means owning a runtime abstraction (the envoy precedent — Plan 01 §8.2).

The honest expectation (flagged): the evidence already tilts toward **"own the loop"** — the sister
project envoy chose exactly this, for exactly this reason (Plan 01 §8.2). A hard independence
constraint also bites: `rules/independence.md` forbids _depending on_ a proprietary SDK in the product
core, which rules out the purest "build on a commercial harness" option regardless of the spike (Plan
01 §8.2). So the realistic outcome is the **envoy-hybrid**: own the _governed core_ runtime so M1/M2
are native, while still _developing the product_ using the commercial harnesses (Plan 01 §8.3). The
spike's job is to _convert this tilt into evidence before the build commits_ — not to re-open the
recommendation.

### 3.3 Reuses vs builds

- **Reuses:** the existing harnesses' introspection surfaces (the thing under test); the envoy
  `KailashRuntime` abstraction as the reference design for the own-the-loop arm (Plan 01 §8.2).
- **Builds:** a throwaway spike harness only. No production code. The deliverable is a written verdict
  with evidence (the three checks pass/fail), not a shipped component.

### 3.4 Invariants held

The spike itself holds none (it is throwaway). But it must produce evidence honest enough to bet a
program on — so the spike's _report_ must show the literal walk (record-intent → pause-on-posture →
replay-from-step) actually executed, with receipts (per `rules/user-flow-validation.md`). A spike that
reports "looks feasible" without the three checks demonstrably run is not a proof.

### 3.5 Sizing and gate

- **Sizing:** ~1 cycle. This is the highest-leverage early experiment precisely because it is cheap and
  decisive (analysis 08 §6.3). A failed spike costs one session.
- **Gate (structural, human):** the spike's verdict sets the runtime architecture for everything after.
  A "must own the loop" result raises the cost of C1/C5 (you reimplement context management the
  commercial SDKs give free — Plan 01 §8.3 cons) but makes M1/M2 _native_. The founder confirms the
  runtime direction here, once, before assembly. **This is the one decision everything hinges on**
  (Plan 01 §8, §12 unknown #1).

---

## 4. C1 — Glass-box + single-step replay (the smallest M1 falsifier)

### 4.1 What it proves, plainly

Before building the full rewind engine (C5 — the hardest thing in the plan), prove its _smallest unit_:
can we record **one** step of agent work transparently — its inputs, the tool calls, the result, the
output — and then **replay** that exact step deterministically (show what happened last time, without
calling the AI again)? (Plan 01 §4.2, §4.4 "Replay"). If we cannot even do one step's glass box and
deterministic replay, the cascade over many steps (C5) is hopeless — so this is the cheap canary for
the expensive build.

**What C1 proves that C0 did not.** C0 proves only that we _can drive_ the loop the way M1 needs —
loop-control: stage intent before an action, gate on posture, and re-execute from a prior point (a
_runtime_ property). C1 proves the orthogonal _content_ property the loop cannot supply on its own:
that one step can be turned into a **content-addressed, glass-box record** and **replayed
byte-for-byte by fingerprint** without re-calling the model. Owning the loop (C0) does not make a step
fingerprintable or deterministically replayable (C1); C1 is the first proof of the M1 _substrate_,
where C0 was the proof of M1's _runtime feasibility_. The two are sequential, not duplicative.

### 4.2 Proof criterion

- **Confirms:** a single agent step is recorded as a content-fingerprinted record (a record identified
  by a hash of its contents, so any tampering is self-evident — Plan 01 §4.3); the recorded inputs,
  tool calls, results, and output are surfaced legibly; and **replay** reproduces the recorded output
  byte-for-byte by fingerprint _without_ a fresh model call. The black-box boundary holds: we record
  what the model emits at its input/output surface, and we do _not_ claim to record how it thought
  internally (Plan 01 §4.2).
- **Falsifies:** the step cannot be fingerprinted stably (the same inputs yield different fingerprints,
  so "only recompute what changed" can never be built), OR replay cannot reuse the recorded output and
  always re-calls the model (then "show me exactly what happened" is impossible and the determinism
  boundary is broken).

### 4.3 Reuses vs builds

- **Reuses:** PACT's record models — `Run` (a step), `AgenticArtifact` (an output with version +
  parent-pointer), `AgenticDecision` (a surfaced choice) — and the Kailash durable store; the
  OpenTelemetry GenAI recording conventions as the live-telemetry feed into the ledger (Plan 01 §4.3,
  §10.1). Content-addressing (hash-as-identity) already ships in Kailash for crash-recovery and
  idempotency (Plan 01 §4.4).
- **Builds:** the wiring that unifies these into one content-addressed step record, and the
  deterministic-replay path (reuse-recorded-output-by-fingerprint). Small — this is the substrate
  _under_ the cascade, not the cascade.

### 4.4 Invariants held (the M1 ledger invariants, at single-step scale)

From Plan 01 §4.3's six ledger invariants, four bind at this scale: (1) **immutability** — a re-run
appends, never alters; (2) **tenant isolation** — every fingerprint and query carries the customer's
`tenant_id` or it is a cross-customer leak (per `rules/tenant-isolation.md`; analysis 09 §4.4); (3)
**determinism boundary** — replay reuses the recorded output unless the user explicitly asks to
regenerate; (5) **posture-at-time** — the step records the posture in force when it ran. (Invariants 4
"cascade minimality" and 6 "audit completeness of the intervention" arrive with C5.)

### 4.5 Sizing and gate

- **Sizing:** ~1–2 cycles. Has a live feedback loop (each recorded/replayed step is testable against a
  fixture), so it can run at the higher per-session budget per `autonomous-execution.md` § Feedback
  Loops Multiply Capacity.
- **Gate (execution, autonomous convergence):** a clean single-step glass-box + replay unblocks C5. A
  failure here is a _cheap_ signal that the M1 mechanism needs rework before the cascade is attempted —
  exactly the point of proving the unit before the system.

---

## 5. C2 — The governance foundation (M2): ship first

### 5.1 What it proves, plainly

**Can a user decide up front how much freedom the agent gets for a job — and can the platform enforce
that choice _as the work runs_, not as a report read afterward?** (analysis 03 §3.1). Three plain
choices: **"Go ahead"** (the agent does the whole job alone, within limits), **"Ask me once"** (one
approval at the plan→execute boundary), **"Step through with me"** (every consequential action pauses)
— mapped onto the shipped trust-posture engine, with the engine's canonical labels kept internal and
the three plain buttons shown to the user (Plan 01 §3.3; analysis 08 §3.1). Plus spending budgets,
clearance ("this agent may not touch payroll data"), and a governed emergency override.

This ships **first** among the moats because it is the **most-proven, lowest-risk, regulation-backed**
one (analysis 03 §3.4; EU AI Act Article 14 human-oversight, enforceable Aug 2026, cited there) AND it
produces the **posture-stamped step log the rewind engine (C5) reads** (analysis 03 §8.2; Plan 01 §3
header). Building governance first means the headline capability (C5) is built on running, trusted
ground (analysis 03 §8.4).

### 5.2 Proof criterion

- **Confirms:** on the real, deployed comms product, a posture chosen _beforehand_ changes live
  behavior — "Step through" pauses every consequential action; "Ask me once" gates exactly once at the
  plan→execute boundary; "Go ahead" auto-approves within the envelope and _blocks anything outside it_.
  A budget ceiling halts the run at its limit. The fan-out plan ("the agent decided to spin up 3
  sub-agents") is surfaced on screen as an inspectable object _before_ execution. And — the critical
  proof against the orphan failure mode — a **Tier-2 integration test proves the framework actually
  calls the governance manager on the hot path**, with an externally observable effect (an audit row,
  a held action) (analysis 08 §6.2; Plan 01 §3.5; `rules/facade-manager-detection.md`).
- **Falsifies:** governance ships as a facade that never executes on the hot path (the Phase-5.11
  orphan pattern — beautifully implemented, zero production call sites; analysis 08 §6.2). If the
  posture choice does not demonstrably change live behavior with a passing Tier-2 wiring test, M2 is a
  no-op security promise, which is worse than no promise.

### 5.3 Reuses vs builds

- **Reuses (wholesale, ~80% / ~15% glue — the platform-wide canonical 80/15/5 ratio per analysis 08
  §1, here at the governance layer):** the PACT engine (envelopes, the auto/flag/HELD/block
  verification gradient, `ApprovalBridge`, the live `EventBridge` decision-to-screen stream,
  `EmergencyBypass`, the 17 data models) and the EATP posture machinery (`PostureStateMachine`,
  `PostureStore`, `BudgetTracker`) — three independent shipped posture implementations to draw on (Plan
  01 §3.2; analysis 08 §2 rows 3–4). Roll in under PACT `EnforcementMode.SHADOW` — observe what
  _would_ be held or blocked without blocking anything — so governance turns on under the live comms
  product _without breaking it_ (Plan 01 §3.2, §3.5).
- **Builds (small, ~5%):** (1) the `plan_proposed` gate — a decision subtype that surfaces the agent's
  fan-out plan as the approvable object before execution (~1 cycle of integration, analysis 03 §3.2;
  Plan 01 §3.4); (2) **replacing PACT's keyword-matching "is this action consequential?" classifier
  with an LLM-judged one** — mandatory per the LLM-first discipline (`CLAUDE.md` Directive 6;
  `rules/agent-reasoning.md`), keeping PACT's verdict machinery but not its keyword decision path (Plan
  01 §3.4); (3) the three-button presentation layer over the canonical posture enum (Plan 01 §3.3).

### 5.4 Invariants held

- **No orphaned governance** — every wired manager has a real hot-path call site _and_ a Tier-2 test
  proving the framework calls it (`rules/orphan-detection.md`, `rules/facade-manager-detection.md`;
  analysis 08 §6.2). This is the single most important invariant for C2 and is non-negotiable.
- **LLM-first decisions** — no keyword/regex routing in the consequentiality classifier
  (`rules/agent-reasoning.md`; `CLAUDE.md` Directive 6).
- **Posture safety floor** — operative posture is `min(user-chosen, system-floor)`; upgrades are
  human-gated, downgrades are automatic on a detected problem (Plan 01 §3.3). This is what makes "Go
  ahead" safe to offer: a ceiling the system can instantly lower, not a blank cheque.
- **Tenant isolation** on every audit row and posture record (per `rules/tenant-isolation.md`).

### 5.5 Sizing, sharding, and gate

- **Sizing:** the reuse is integration glue across several parallel-eligible shards; the net-new is
  small. The `plan_proposed` gate is ~1 cycle; the LLM-first classifier is "a small, well-scoped
  rewrite, not a re-architecture" (Plan 01 §3.4).
- **Sharding (load-bearing):** the LLM-first classifier is a decision-path rewrite — keep it within one
  shard (the classifier is the load-bearing logic; the verdict machinery is reused unchanged). The
  wiring-into-the-hot-path-plus-Tier-2-test is its own shard per governance manager, because each wired
  manager carries the orphan-detection invariant set (call site + test) — shard one manager at a time
  (analysis 08 §6.2; `autonomous-execution.md` § Shard When Any Threshold Is Exceeded).
- **Gate (structural for the SHADOW→enforce flip):** SHADOW-mode observation runs autonomously;
  flipping from observe to enforce on the live product is a human gate (it changes real user behavior).

---

## 6. C3 — The non-coder self-service surface (net-new build #1)

### 6.1 What it proves, plainly

**Can a non-technical operator configure an objective's process, connectors, posture, knowledge, and
roster — with zero engineering?** (analysis 08 §3; Plan 01 §2, §10.2). This is the brief's "processes
vary company-to-company" surface (brief 1b) and it MUST be self-service, or the platform inherits the
documented **95%-of-pilots-fail** mode (MIT NANDA: generic tools "don't learn from or adapt to
workflows" — analysis 08 §1). The comms onboarding wizard already proves a non-technical person can
configure this layer in under 10 minutes with no app (analysis 08 §3; research 09 §1.7, §5.2) — so
this is a _surface_ build on a proven pattern, generalizing the wizard from "configure comms coverage"
to "configure any objective."

### 6.2 Proof criterion

- **Confirms:** a non-coder, in a usability walk, configures a new objective end-to-end — picks the
  systems to connect, sets the process, chooses a posture, points at the knowledge — _without writing
  code and without an engineer_, and the configured objective then runs. The literal user walk is
  performed with receipts (per `rules/user-flow-validation.md`), not just a passing test.
- **Falsifies (the "last 20%" death):** the wizard handles ~90% of a real company process but needs an
  engineer for the final ~10% (conditional logic, edge cases) — the exact place no-code tools
  historically die (analysis 09 §2.1; analysis 08 §3.1). If the non-coder gets stuck at depth and the
  only fix is code, the self-service promise fails _and_ the platform re-acquires the 95%-failure mode.

### 6.3 Reuses vs builds

- **Reuses:** the comms onboarding wizard as the scaffold (analysis 08 §3; Plan 01 §2.4); PACT's web
  objectives/approvals screens as additional scaffold for the approval surface (Plan 01 §2.4).
- **Builds (the bulk of net-new UX):** the generalized configuration surface — the intent box, the
  business-object views (a purchase order, a ticket — not files), the connector-selection surface, the
  three-button posture chooser, the knowledge-and-roster config. This is "multiple sessions" of work
  and the single largest net-new UX investment (analysis 08 §6.1; Plan 01 §10.2).

### 6.4 The mitigation that ties C3 to C5 (load-bearing)

The "last 20%" risk is mitigated by pairing C3 _tightly_ with the C5 transparency/rewind: when the
configured process runs, the user _sees every step and can intervene_, which makes the un-configured
10% **legible and fixable in-flight rather than silently wrong** (analysis 08 §3.1; analysis 09 §2.2;
Plan 01 §2.4). This is why C3 is _not_ fully provable until C5 exists — its falsifier (depth-death) is
only neutralized by the rewind engine. **Implication for the founder:** C3 and C5 are a _pair_; C3
alone is a wizard, C3+C5 is a wizard whose gaps are visible and correctable. The cons are symmetric:
the mitigation (transparency makes depth legible) is _itself one of the two hardest builds_ (analysis
08 §3.1), so C3's success is partly hostage to C5's success — and to whether a non-coder can actually
read the trace (analysis 09 §2.2, the legibility bet).

### 6.5 A second hard sub-proof: who authors the process artifacts?

The non-coder authoring paradox (analysis 09 §6.2): process is captured as artifacts, but artifacts are
today authored by developer-adjacent people. If every customer needs a technical person to encode its
process, the non-coder promise is compromised. **The mitigation (a sub-proof inside C3):** the agent
authors the _first draft_ of the process artifacts from observed work and natural-language description;
the non-coder _describes and corrects_, the agent _encodes_, and C5's transparency lets the non-coder
verify the encoding by watching it run (analysis 09 §6.2). Its falsifier: the agent encodes a
plausible-but-wrong process the non-coder cannot detect (analysis 09 §6.2) — coupling this, again, to
the legibility bet.

### 6.6 Invariants, sizing, gate

- **Invariants:** non-coder configuration depth (no code required for the common case); tenant
  isolation on all per-customer config; the self-service config is captured as artifacts + memory, not
  bespoke code (analysis 08 §3, §5).
- **Sizing:** multiple cycles (the bulk of net-new UX). UX work is iterative and open-ended; size by
  the usability-walk milestones (a non-coder completes config; a non-coder corrects an agent-drafted
  artifact), not LOC.
- **Parallel-eligible with C2** (different layer — surface vs governance), per analysis 08 §6.2.
- **Gate (execution):** usability evidence is the convergence signal; the founder observes the walks
  but does not block (analysis autonomous-execution § Structural vs Execution Gates).

---

## 7. C4 — The agent reaches ≥2 formerly-siloed systems (proving the inversion)

### 7.1 What it proves, plainly

This is the **paradigm-shift proof**: today the _human_ is the integration layer carrying data across
ERP, CRM, spreadsheets, portals; the platform makes the _agent_ the integration layer and the human
states intent and governs (brief §1–§3; Plan 01 §0). C4 proves the inversion at its minimum:
**can one agent run an objective across _two_ systems that previously required a human to bridge them
— with governance between the agent and each system, and least-privilege scoping?** (Plan 01 §7;
analysis 09 §4.3). Comms today exercises one tool-cluster (the inbox + knowledge base); it does _not_
prove cross-system orchestration — that gap is the platform's real build (research 09 §6.1).

### 7.2 Proof criterion

- **Confirms:** an objective runs across two formerly-separate systems (e.g. read from a ledger/records
  system, write to a document/output system) through standard connectors, with the "tools are dumb
  endpoints, the LLM does the reasoning" discipline holding (all reasoning is in the logged model I/O;
  Plan 01 §7.2), governance sitting _between_ the agent and each connector (a write to a system of
  record can be HELD until a human approves; Plan 01 §7.3), and the agent granted only the _minimum_
  tool/clearance envelope the objective needs — not the union of everything connected (analysis 09
  §4.3; Plan 01 §7).
- **Falsifies:** cross-system sequencing cannot be done without burying business logic inside tool code
  (which would make the work opaque and break the C1/C5 transparency contract — Plan 01 §7.2), OR the
  agent must be over-provisioned with broad standing access to function (re-acquiring the
  concentrated-blast-radius risk — analysis 09 §4.3).

### 7.3 Reuses vs builds

- **Reuses:** the MCP connector protocol and the >1,000 existing connectors (Plan 01 §7.1, §10.1);
  comms' own channel adapters as the first connector instances (research 09 §3); C2's governance as the
  between-agent-and-connector enforcement point (Plan 01 §7.3).
- **Builds:** the **governed curation** — wrapping each connector in the dumb-endpoints discipline and
  putting governance between agent and connector (Plan 01 §7.5); the per-objective least-privilege
  envelope derivation (analysis 09 §4.3). Connector porting itself is boilerplate-heavy and scales ~5×
  further before sharding triggers (analysis 08 §6.1).

### 7.4 Invariants, sizing, gate

- **Invariants:** **tools are dumb endpoints** (no decision logic in tool code — `rules/agent-reasoning.md`;
  Plan 01 §7.2); **least-privilege per objective** (narrow-and-earned, not broad-and-assumed — analysis
  09 §4.3); **governed connectivity** (a write to a system of record requires the envelope to permit it
  or a human gate — analysis 09 §4.2, §4.3); tenant isolation on every connector call. **Honest
  tension flagged:** the least-privilege envelope derivation must _not itself become decision-logic in
  tools_, or it violates the dumb-endpoints rule (analysis 09 §4.3; Plan 01 §7 open question).
- **Sizing:** connector work is boilerplate-heavy (single shards stamp out the pattern, ~5× the base
  budget — analysis 08 §6.1); the governed-curation + least-privilege logic is the load-bearing part
  and shards separately.
- **Gate (execution):** C4 gates the end-to-end demo (§11), which by definition needs ≥2 systems.

---

## 8. C5 — The retrace / cascade engine (M1): net-new build #2, the headline

### 8.1 What it proves, plainly

This is the **strongest moat and the hardest build** (analysis 03 §2.4; analysis 08 §6.1; Plan 01 §4).
**Can a non-coder rewind to an earlier step of a multi-step job, change something there, and have
_only the affected downstream_ recompute — while old versions are kept?** (brief §3e; analysis 03
§2.1). In the brief's example: "I want the 3Q report" → the agent fans out → you later spot a wrong
revenue assumption two steps back → you fix it there → only that branch and its dependents re-run; the
original survives as a prior version (analysis 03 §2.1).

### 8.2 Proof criterion

- **Confirms:** on the comms-wedge's small 4-step work graph (Message → Classification → Retrieval →
  Response, a concrete instance of the general dependency map — analysis 03 §8.3; research 09 §6.2), a
  non-coder rewinds to a step, changes an input, and the engine: creates a new step (old one untouched
  as a version); marks descendants "potentially needs re-run"; **recomputes only genuinely-changed
  steps and skips steps whose recomputed inputs match their recorded fingerprint** (the
  only-affected-downstream guarantee — Plan 01 §4.4); writes each re-run as a new version with a
  back-pointer; and shows a **cost-preview** ("this change will re-run N steps") _before_ committing.
  The intervention itself is audited (who rewound, what changed, when).
- **Falsifies (two distinct ways):** (1) **the engine** can't bound the cascade — a change near the
  root legitimately re-runs everything and there is no comprehensible cost-preview, so a non-coder
  won't trust it (the canary per analysis 09 §2.3); or (2) **the legibility bet fails** — even when the
  engine works, a non-coder cannot answer "which version of this output is current?" within seconds, or
  cannot read a branching history without it looking like a developer's git graph (analysis 09 §2.1,
  §2.3; analysis 03 §2.4; Plan 01 §12 unknowns #2–#3). **Both falsifiers must be checked** — the engine
  is the _tractable_ part; legibility-for-non-coders is the _frontier_ (Plan 01 §12).

### 8.3 The deliberately-reduced first form (the risk mitigation)

Per analysis 09 §2.4, ship M1 in a **deliberately reduced** first form: **linear retrace** (not
arbitrary), **reuse-recorded-output as the default** with an explicit per-step "regenerate" opt-in, and
**no user-facing branching in v1**; and treat the **cost-preview as a hard acceptance gate, not a
nice-to-have**. This sequences the moat by tractability and proves legibility on a graph small enough
that legibility is _achievable_ (analysis 09 §2.4). The reduced form still beats the field — no
competitor productizes _any_ non-coder versioned cascade (analysis 03 §5.3; analysis 09 §2.4).
**Symmetric con:** a reduced M1 is _less differentiated_ than the full vision, and marketing the moat
on its strongest claim while shipping its weakest form risks an expectation gap — so the reduced scope
must travel with honest messaging (analysis 09 §2.4).

### 8.4 The three meanings of "rewind" the engine must separate

The non-determinism problem, addressed honestly (Plan 01 §4.4; analysis 03 §2.4): a model step does not
produce the same answer twice, so "re-run from step 4" is ambiguous. The engine MUST separate:
**Re-run** (user changed an input → re-execute affected downstream; model steps _may_ legitimately
differ — correct); **Replay** (show exactly what happened last time → reuse the recorded answer by
fingerprint, no model call — fully deterministic, proven in C1); **Branch** (try a different path
without losing the original — _deferred to a later form_, not v1). On rewind, the engine reuses the
recorded output by fingerprint for every untouched step and **surfaces the choice "re-run with my edit
/ keep the recorded output" as an explicit per-step product decision** — because guessing wrong
silently is the worst outcome (Plan 01 §4.4).

### 8.5 Reuses vs builds

- **Reuses:** the C1 content-addressed step records + the durable store + the OpenTelemetry recording;
  the descendant-walk that already exists in Kailash's `WorkflowDAG`; content-addressed memoization
  (skip-and-reuse-if-fingerprint-matches) that already ships in Kailash for crash-recovery, idempotency,
  and within-run skipping (Plan 01 §4.4). This is why C5 is a **~20% novel composition, not an 80%
  greenfield build** (Plan 01 §4.4).
- **Builds (the one ≥500-LOC load-bearing net-new framework component):** the **reactive cascade
  engine** — dirty-propagation (from reactive notebooks) + fingerprint-skip (from build systems) +
  version-on-rerun — generalizing memoization's scope from "within one run" to "across runs, keyed on
  content fingerprint" (Plan 01 §4.4, §10.4). Placed as a **framework-level module** over the data
  models + WorkflowDAG, _not inside the Sequor app_, so the horizontal capability is reused and the
  wedge consumes it (Plan 01 §4.5).

### 8.6 Invariants held (all six ledger invariants now bind)

The six from Plan 01 §4.3, now all live: immutability; tenant isolation (every fingerprint, cache key,
graph query carries `tenant_id` — and the M1 content-addressed namespace is a _specific named
cross-tenant leak vector_ per analysis 09 §4.4, so this is enforced as a hard gate); determinism
boundary (reuse-recorded unless told to regenerate); **cascade minimality** (a downstream step with
unchanged recomputed inputs MUST be skipped); posture-at-time (every step records the posture in force);
**audit completeness** (the intervention is itself auditable). These six are exactly the simultaneous-
invariant set that _forces sharding_: the engine is the ≥500-LOC load-bearing piece holding 6
invariants — over the §autonomous-execution budget on the invariant axis alone.

### 8.7 Sizing, sharding, gate

- **Sizing:** an end-to-end working rewind-and-intervene over the comms-wedge 4-step flow is ~4–6
  cycles, because the substrate is reused; the cascade engine itself is ~1–2 cycles (analysis 03 §2.4;
  Plan 01 §4.5). It has a _live feedback loop_ (each cascade is testable against a fixture graph), so it
  can run at the higher per-session budget (Plan 01 §4.5; `autonomous-execution.md`).
- **Sharding (mandatory, load-bearing):** the cascade engine carries ≥500 LOC of load-bearing logic AND
  6 simultaneous invariants — it MUST be sharded at `/todos` time, before implementation (Plan 01
  §11.1; `autonomous-execution.md` § Shard When Any Threshold Is Exceeded). Suggested shards, each one
  invariant-focused: (1) dirty-propagation over the dependency graph (descendant-walk + dirty-mark); (2)
  fingerprint-skip + cascade-minimality (the only-affected guarantee); (3) version-on-rerun +
  audit-completeness of the intervention; (4) the cost-preview gate. The non-coder-facing timeline/
  rewind/version UI is a _separate_ surface shard (it lives in C3's surface layer, consuming this
  engine). **Do not** combine the engine and its UI in one shard.
- **Gate:** C5 is the headline moat and the end-to-end demo's climax. Its two falsifiers (engine cost-
  bounding; non-coder legibility) are _execution-convergence_ signals for the engine and _usability-
  evidence_ signals for the legibility — the founder observes both. **If C5's legibility falsifier fires
  and cannot be resolved**, the honest fallback (per analysis 03 §8.1 and Plan 01 §11.2) is that the
  platform leads its story with a capability it cannot fully ship — a credibility risk the reduced-form
  (§8.3) and comms-wedge proving ground (C7b) exist to surface _early_, on a 4-step graph, before it is
  the headline.

### 8.8 The storage and cost cautions (symmetric, real)

Immutable versioning grows storage without bound unless a retention/compaction policy is built
(content-addressing dedupes identical bytes but not version count — Plan 01 §4.5, §12 unknown #8); and
a root-level edit can legitimately invalidate everything downstream, which is exactly why the
cost-preview is a _hard gate_ not a nice-to-have (analysis 09 §2.3; Plan 01 §4.5). Both are named here
so they are designed in, not discovered in production.

---

## 9. C6 — The untrusted-publisher trust model (M4): design-first, then build

### 9.1 What it proves, plainly

M4 is the network-effects engine: a team builds a reusable work-recipe (a procedure, a checklist, a
specialized agent) once and shares it — with **provenance** (who made it), **versioning** (updates +
rollback), and **recall** (pull a bad one from everyone at once) (analysis 03 §5.1). The genuinely-new,
moat-bearing piece is the **untrusted-publisher trust model**: when company A publishes a work-recipe
and company B runs it, **B is running A's instructions inside B's agent against B's connected systems**
— so a malicious or careless A could exfiltrate data, skip a compliance step, or take an action B never
intended, _with B's authority_ (analysis 09 §4.1; analysis 03 §5.2). This is the supply-chain problem
("can this recipe be trusted to run against my systems?"), not the marketplace problem ("is it good
quality?") — and **no shipping product solves it** (analysis 03 §5.3; analysis 09 §4.1).

### 9.2 Why design-first, and why it gates cross-org

The trust model is a **novel-architecture decision** (greenfield; ~2–3× first-session factor per
`autonomous-execution.md`) and it **constrains the registry's shape** — so it MUST be designed _before_
the cross-org publish/subscribe surface is built, or a wrong call forces an expensive re-architecture
(analysis 08 §4.1; analysis 03 §5.4; Plan 01 §6.4). The sequencing implication for the founder:
**ignite network effects within-org FIRST** (which needs _no_ new trust model — the loom machinery
already handles bounded-trust within one org) and open **cross-org only after C6's design lands**
(analysis 08 §6; Plan 01 §6.4).

### 9.3 Proof criterion

- **Confirms (design proof, then build proof):** _Design proof_ — a written trust model in which every
  cross-org recipe **declares its required tool/clearance envelope**, the consumer's posture (M2) gates
  whether that envelope is auto-granted or human-approved, and **a recipe cannot escalate beyond its
  declared envelope at runtime** (default-deny intake fence — analysis 09 §4.1). _Build proof_ — a
  consumed recipe runs only against the scopes it declared and the consumer pre-approved; intake review
  _mechanically_ detects "this 'format a report' recipe also wants write-access to the payments system"
  (the leading indicator of a poisoned recipe — analysis 09 §4.1); and recall pulls a bad recipe from
  every consumer.
- **Falsifies:** intake cannot mechanically detect over-broad scope requests (then the fence is
  unenforced), OR capability-scoping is too coarse for heterogeneous enterprise systems — a "format a
  report" recipe needs "access the ERP" and that envelope is technically scoped but practically broad
  (analysis 09 §4.1, the honest con). The cross-org channel _intentionally_ crosses tenant boundaries,
  so tenant-isolation-by-`tenant_id` is necessary but **insufficient** here — M4 needs an additional
  explicit cross-tenant-grant model that is itself net-new design (analysis 09 §4.4).

### 9.4 Reuses vs builds

- **Reuses (the crypto substrate is a strong starting point):** loom's commit-signing keys, the
  hash-chained coordination log, 2-of-N quorum, the `refs/coc/**` server-side rulesets, disclosure-scrub
  on intake, and the obsoletion/recall primitive (already purges a bad artifact from 30+ consumers on
  the next sync) — plus the Gate-1 human-classify intake step as the supply-chain fence (analysis 08
  §4.1; analysis 09 §4.1; Plan 01 §6.2). aegis's fork-relationship asymmetry (upstream-generic-only, no
  client leakage) is the right governance shape, already a baseline rule (analysis 08 §4.1).
- **Builds:** signed-artifact provenance from an _external_ publisher (vs an enrolled operator), plus
  marketplace-grade licensing/attribution, plus the cross-tenant-grant model (analysis 08 §4.1;
  analysis 09 §4.4). The registry surface itself is ~3–5 cycles _after_ the trust model is designed
  (analysis 08 §6.1; Plan 01 §6.4).

### 9.5 Invariants, sizing, gate

- **Invariants:** default-deny on the consume path; capability-scoped recipes (a recipe runs only
  against its declared, consumer-approved envelope); recall reaches every consumer; tenant isolation
  _plus_ an explicit cross-tenant-grant model on the one channel that deliberately crosses the boundary
  (analysis 09 §4.1, §4.4).
- **Sizing:** the trust model is greenfield design (~2–3× first-session factor); the registry surface
  is ~3–5 cycles after the design lands (analysis 08 §6.1).
- **Gate (structural, human):** C6's _design_ is gated before any cross-org build — it is the one place
  a wrong call is expensive to unwind. **Symmetric con:** default-deny + per-envelope approval adds
  friction to the consume path, which directly taxes the network-effects engine M4 depends on (every
  approval gate is a place adoption leaks) — but trust-by-reputation is rejected because the first
  high-reputation poisoned recipe is the category-defining incident (analysis 09 §4.1).

---

## 10. The sequence recommendation (single rec + implications + symmetric pros/cons)

### 10.1 The recommendation

**Sequence the build as: C0 spike → C1 single-step replay → (C2 governance ‖ C3 self-service surface,
in parallel) → C4 ≥2-system reach → C5 cascade engine → C6 trust-model-design-then-cross-org → C7
instrument the two bets — proving every step on the comms wedge's 4-step graph before generalizing, and
running governance in SHADOW mode under the live product throughout.** This is capability-first: the
cheapest decisive falsifiers (C0, C1) gate the expensive builds; the most-proven moat (C2) ships first
and feeds the headline moat (C5); the genuinely-new trust model (C6) is designed before the surface it
constrains; the two unproven bets (C7) are measured last, never assumed.

### 10.2 Why this order (the implications, in business terms)

- **Time-to-first-evidence is short and cheap.** C0 + C1 are ~2–3 cycles combined and they answer the
  two questions that could kill the thesis (is M1 buildable? is its smallest unit sound?). The founder
  gets the most decisive information for the least spend — and a "no" costs one session, not a program
  (analysis 08 §6.2, §6.3).
- **The platform is sellable-shaped early even though GTM is deferred.** C2 (governance) is a coherent,
  regulation-backed capability on its own (analysis 03 §3.4) and ships first on the _already-deployed_
  comms product — so there is a credible, governed-agentic-work capability proven even if the headline
  M1 (C5) takes longer (analysis 03 §8.4). This de-risks the whole arc: the platform is not hostage to
  the riskiest moat shipping first.
- **The order tracks the value axes, in priority of defensibility.** Each capability proof delivers a
  value claim the buyer can act on: C2 (governance) + C4 (≥2-system reach) prove **Augment** and
  **Automate** — the PROVEN/credible value buyers can pay for today; C5 (transparency/rewind) is the
  CONTINGENT M1 bet that, once proven, makes Augment defensible; C6 (cross-org registry) proves
  **Amplify** (analysis 05 §0; analysis 02 §0). Sequencing the PROVEN axes ahead of the CONTINGENT one
  is the value-ordering that keeps the platform credible to a skeptical budget-holder at every stage.
- **The risk is concentrated into spike-able units, not smeared across the build.** Two builds (C5
  cascade, C3 surface) and one design (C6 trust model) carry almost all the execution risk; each is
  surfaced early, on a bounded surface, before the assembly commits (analysis 08 §6.2; Plan 01 §11.1).
- **The moat is in the net-new 5%, not the reused 80%.** Anyone can call an agent loop; almost no one
  ships transparent step-level intervention (C5), pre-set posture (C2), and governed cross-org exchange
  (C6) (analysis 08 §6.2). The reused 80% is necessary but _not defensible_; the sequence concentrates
  effort exactly on the defensible 5%.
- **Network effects ignite within-org first, then cross-org.** C6's design-first gate means within-org
  sharing (proven loom machinery) delivers value at one-org scale before the cross-org trust model
  exists — avoiding a network-effects-engine-with-no-network (analysis 03 §8.4; analysis 08 §6).

### 10.3 Pros (of this sequence)

- **Maximizes reuse of shipped, real-user-tested code** — lowest invention cost (analysis 08 §6.2).
- **Isolates risk into spike-able units** — a failed spike costs one session, not a program (analysis 08
  §6.2).
- **Keeps the architecture horizontal/agnostic per Decision B** — no beachhead is prematurely locked
  (analysis 08 §6.2).
- **Leads with the most-proven moat (C2) while building the headline (C5) on its log** — decoupling
  differentiation from execution risk (analysis 03 §8.4).
- **The comms wedge is a revenue-bearing, real-user landing vertical _while_ the orchestration spine is
  built** (analysis 08 §6.2; research 09 §6.5).

### 10.4 Cons (real, not glossed)

- **The reuse story can lull.** "80% exists" is true of _primitives_; a primitive is not a product. The
  integration glue (re-key posture, replace the keyword classifier, wire PACT into the hot path) is real
  work the "80%" headline hides (analysis 08 §6.2; Plan 01 §11.2). The sizing fields above count the
  glue explicitly as the mitigation.
- **The two net-new builds are the hardest things in the plan AND the most load-bearing.** C5
  (cascade) is the strongest moat and highest execution risk — non-deterministic steps and non-coder
  versioning UX are both unsolved by anyone (analysis 09 §2; analysis 03 §2.4). If C5's legibility
  falsifier fires, the platform degrades to "an agent does your work in one interface" — exactly the
  surface Claude Cowork already embodies (analysis 08 §6.2; analysis 09 §5). Competing on that surface
  is the failure case.
- **Orphan risk is structural in the reused governance.** PACT is facade-heavy; reusing it risks
  shipping governance that never runs on the hot path (the Phase-5.11 pattern). The mitigation —
  real call site + Tier-2 wiring test per manager — is mandatory, not optional, and is baked into C2's
  proof criterion (analysis 08 §6.2; Plan 01 §3.5).
- **Parallelizing C2 ‖ C3 means two moats build at once** — more coordination than a single-term sprint.
  Justified because the shards are independent (different layers) and the reuse carries most of the load
  (analysis 08 §6.2; analysis 03 §8.5) — but it is a real coordination cost, not free.
- **The deferred-GTM choice (Decision B) creates the "lands nowhere" risk** even as it mitigates the
  build-the-wrong-thing-fast risk (analysis 09 §1). C7b (the comms lighthouse) is the specific defense:
  run the capability proof _against a real, painful, named workflow with a real design partner watching_
  — converting an unfalsifiable business bet into a falsifiable one at near-zero added cost (analysis
  09 §1.4). **The con of even that:** a single lighthouse risks _anchoring_ the horizontal product to
  one vertical's idiosyncrasies — the re-verticalization trap — requiring discipline to treat the
  lighthouse as evidence, not gravity (analysis 09 §1.4).

### 10.5 The alternative considered and rejected

**All-in on C5 (M1) as the lead — race to ship the cascade engine first, before governance.** Rejected
because it stakes the entire competitive position on winning a race for the _hardest-to-build_ term
against better-resourced competitors; if that race is lost, the platform has nothing else far enough
along to fall back on (analysis 03 §8.5; analysis 09 §5.3). The recommended sequence keeps C2's safety
(ship it first) while still leading the _story_ with C5 — capturing both, rather than trading one for
the other (analysis 03 §8.5). The honest cost of the hybrid is execution complexity (two moats in the
right order), justified because the ~80% reuse carries most of the load (analysis 03 §8.5).

---

## 11. C7 — The two instrumented bets (measure, never assume)

These are sequenced last because **neither is a USP** — both are research bets the platform must _not_
stake its value proposition on (analysis 03 §4.4, §8.4; analysis 09 §3, §6.5). They are instrumented so
the platform learns whether they hold, cheaply, from data the platform records anyway.

### 11.1 C7a — The agent-comms BET

- **The bet (brief §3d):** agent-mediated handoffs are more complete and less lossy than human-to-human
  handoffs (because agents carry full context and durable memory). This is the _only_ rationale for
  extending into team work (M3).
- **Proof criterion (cheap, instrumented):** the comms wedge's HITL escalation _is already_ a
  human↔agent handoff under a confidence gate (analysis 09 §3.4). Instrument it: measure whether
  agent-mediated handoffs reduce round-trips, "I thought you were doing that" failures, and re-keying —
  the steelman's specific claims (analysis 09 §3.4). **Confirms:** the metrics improve. **Falsifies:**
  in lighthouse usage, users keep routing real handoffs through email/chat and treat the agent as a
  side-tool, OR users ask for an "informal / off-the-record" mode (signalling the
  ambiguity-preservation need is real and unmet — analysis 09 §3.3).
- **Reuses vs builds:** reuses the audit trail the platform records anyway (near-zero incremental build
  — analysis 09 §3.4); builds the agent↔agent message model as first-class surfaced records (~1 cycle —
  Plan 01 §5.2) _and_ an explicit **"informal / not-an-objective" mode** that is not auto-structured or
  auto-recorded-as-decision (analysis 09 §3.4, the ambiguity-preservation feature).
- **Invariant (load-bearing, from CARE):** a _named human_ stays on every consequential decision via the
  posture-gated HELD path — accountability is never delegated to the channel (analysis 09 §3.1 point 2,
  §3.4). The team-comms story is marketed only as far as the evidence reaches — handoffs and
  coordination — **never** as "agents communicate better than you do" (analysis 03 §4.4; analysis 09
  §3.4).
- **Symmetric con:** the narrowed claim ("we make handoffs lossless") is _less exciting_ than the bold
  version and may under-sell the team vision; and the informal-mode adds an ungoverned path that
  complicates the clean "everything is traced" story and is a place security risk can hide (analysis 09
  §3.4).

### 11.2 C7b — The comms lighthouse (the business-falsifiability instrument)

- **The bet (Decision B's risk):** the capability, once proven, is _paid-for-able_ — not just runnable.
  Capability-first defers the beachhead _build_, not the beachhead _hypothesis_ (analysis 09 §1.2).
- **Proof criterion:** run the end-to-end "capability proven" demo (§12) against a _real, painful,
  named_ cross-system workflow with a _real design partner watching_ — not a synthetic demo. The comms
  wedge is the natural first lighthouse: it already ships and already proves four of the six acceptance
  properties (analysis 09 §1.4). **Confirms:** a specific design partner watches it and says "I would
  pay for that against _this_ workflow." **Falsifies:** the capability proof completes and the immediate
  next question is "now which vertical?" with no evidence-backed answer; or every customer conversation
  requires the buyer to _imagine_ their use-case rather than _recognize_ it — the generic-tool tell
  from the MIT NANDA finding (analysis 09 §1.3).
- **Reuses vs builds:** reuses the comms wedge wholesale (a sunk asset — analysis 09 §1.4); builds only
  the design-partner instrumentation. **This runs concurrently with the capability proof**, not after it
  (analysis 09 §1.4) — so it is sequenced "last" in dependency order but _temporally parallel_ with
  C2–C5.
- **Symmetric cons:** carrying a design-partner relationship costs coordination cycles a pure capability
  sprint would not (analysis 09 §1.4); and if comms is _unrepresentative_ (it is "easier" than ERP/CRM),
  a clean lighthouse result can give _false confidence_ about the hard heterogeneous-systems case
  (analysis 09 §1.4) — which is exactly why C4 (real ≥2-system reach) is a separate, earlier proof and
  not folded into the comms lighthouse.

---

## 12. The single "capability proven" demo (the end-to-end target)

Everything above converges on **one demonstration** that proves the disrupted-work capability whole.
It composes C0's runtime, C2's governance, C3's surface, C4's two-system reach, C1+C5's transparency
and rewind — traced through Plan 01's data flow (Plan 01 §9). The demo is the literal user walk, with
receipts (per `rules/user-flow-validation.md`).

### 12.1 The demo, stated as one falsifiable claim

> **A non-coder states an objective in plain language; the agent executes it autonomously across ≥2
> formerly-siloed systems under a posture the user chose beforehand; and the resulting work is traced
> (glass box), interveneable (rewind any step and re-cascade), and versioned (old outputs kept).**

If all four properties hold in one continuous walk, the capability is proven. If any one fails, the
capability is not yet whole — and the §-by-§ falsifiers above name exactly which proof to revisit.

### 12.2 The walk (the four properties, in sequence)

```
 OBJECTIVE (non-coder, plain language)
   "Produce the Q3 figures for the client and draft the cover note."
   Posture chosen beforehand: "Ask me once."                              ← C3 surface + C2 posture
        │
        ▼
 AGENTIC EXECUTION ACROSS ≥2 FORMERLY-SILOED SYSTEMS
   Agent forms a plan (fan out: pull figures · draft note).
   The plan is surfaced on screen as an inspectable object BEFORE running. ← C2 plan_proposed gate
   User approves once. Agent reads from the records/ledger system and
   writes to the document system — two systems that used to need a human
   to bridge them — tools dumb, LLM reasons, governance between agent and  ← C4 two-system reach,
   each connector, least-privilege envelope.                                  governed + least-privilege
        │
        ▼
 TRACED (glass box)
   Every input, tool call, result, decision, output recorded as a
   content-fingerprinted step, streamed live, version 1. The black-box       ← C1 single-step glass box
   boundary holds: model I/O recorded, internal thinking not claimed.           at scale
        │
        ▼
 INTERVENEABLE (rewind any step, re-cascade)
   User spots a wrong assumption two steps back. Rewinds to that step,
   changes the input. Cost-preview shows "this re-runs N steps." Only the     ← C5 cascade engine
   affected downstream recomputes; the unrelated branch is skipped              (the headline)
   (fingerprint match). User is asked: re-run with my edit, or keep the
   recorded output? (re-run vs replay — the explicit per-step choice.)
        │
        ▼
 VERSIONED (old outputs kept)
   Original figures + note survive as version 1; corrected ones are
   version 2 with a back-pointer. User compares v1 vs v2; can revert.         ← C5 version-on-rerun
   The intervention itself is audited: who changed what, when.                   + audit completeness
```

### 12.3 Why this demo is the right capability proof (and what it deliberately omits)

- **It proves the _inversion_** (agent as integration layer across two systems — the brief's core
  thesis) AND the _moat conjunction's two proven-first terms_ (C2 governance, C5 transparency) in one
  continuous walk — exactly the orchestration spine the comms wedge alone does _not_ prove (research 09
  §6.5).
- **It runs on the comms-wedge's small graph first** (analysis 03 §8.3; research 09 §6.2) — a 4-step
  flow small enough that non-coder legibility is _achievable_ (analysis 09 §2.4), so the demo's
  legibility falsifier (C5 §8.2) is testable on a bounded surface before it is the headline.
- **It deliberately omits** (per the reduced-form discipline, §8.3): user-facing _branching_ (deferred
  past v1), _cross-org_ sharing (gated behind C6's design, §9), and the _team_ layer (M3 / the
  agent-comms bet — instrumented in C7, never asserted). Omitting these keeps the demo honest: it proves
  what is proven and does not stage what is still a bet (analysis 03 §8.4; analysis 09 §3).
- **It is run against a real design partner (C7b)**, converting "the capability runs" into "a specific
  buyer recognized it against a real painful workflow" — the difference between capability-proven and
  the 40%-cancelled projects that also "ran" before they were cancelled (analysis 09 §1.2).

---

## 13. The proof-sequence ledger (one-screen summary)

| #       | Capability proof                                            | Falsifier (the kill signal)                                  | Reuses → Builds                                                                               | Key invariants                                                                       | Sizing                                                | Gate                                       |
| ------- | ----------------------------------------------------------- | ------------------------------------------------------------ | --------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------ | ----------------------------------------------------- | ------------------------------------------ |
| **C0**  | Runtime ownership decidable                                 | Introspection can't stage intent / replay-from-step          | harness surfaces, envoy ref → throwaway spike                                                 | (throwaway; honest receipts)                                                         | ~1 cycle                                              | **Structural** — sets runtime architecture |
| **C1**  | Glass-box + single-step replay                              | Step can't fingerprint stably / replay always re-calls model | PACT records, durable store, OTel, content-addressing → unify + replay path                   | immutability, tenant-iso, determinism-boundary, posture-at-time                      | ~1–2 cycles (feedback loop)                           | Execution — gates C5                       |
| **C2**  | Posture set-beforehand, enforced live (M2)                  | Governance is a facade with no hot-path call site (orphan)   | PACT engine + EATP posture + SHADOW → plan_proposed gate + LLM-first classifier + 3-button UX | **no-orphan (call site + Tier-2 test)**, LLM-first, posture safety-floor, tenant-iso | glue (parallel shards) + small net-new                | Structural for SHADOW→enforce flip         |
| **C3**  | Non-coder configures an objective, zero code                | "Last 20%" depth-death needs an engineer                     | comms wizard + PACT web screens → generalized config surface                                  | non-coder depth, config-as-artifact, tenant-iso                                      | multiple cycles (bulk net-new UX)                     | Execution; **paired with C5**              |
| **C4**  | Agent runs across ≥2 formerly-siloed systems                | Needs logic-in-tools / broad standing access                 | MCP protocol + connectors + comms adapters → governed curation + least-privilege              | tools-dumb, least-privilege, governed-connectivity, tenant-iso                       | connector boilerplate (~5×) + load-bearing curation   | Execution — gates the demo                 |
| **C5**  | Rewind a step, re-cascade only affected, keep versions (M1) | Engine can't bound cascade / non-coder can't read the trace  | C1 records + WorkflowDAG walk + Kailash memoization → reactive cascade engine                 | all 6 ledger invariants (cascade-minimality, audit-completeness, …)                  | ~4–6 cycles; **MUST shard** (≥500 LOC, 6 invariants)  | Execution + usability; the headline        |
| **C6**  | Org B safely runs org A's untrusted recipe (M4)             | Intake can't mechanically detect over-broad scope            | loom crypto substrate + recall + Gate-1 → external-publisher provenance + cross-tenant-grant  | default-deny, capability-scoped, recall-reaches-all, cross-tenant-grant              | trust-model greenfield (~2–3×) → registry ~3–5 cycles | **Structural** — design gates cross-org    |
| **C7a** | Agent handoffs beat human handoffs (BET)                    | Users keep using email/chat; ask for off-record mode         | audit trail → agent↔agent message model + informal mode                                       | named-human-on-decision, accountability-not-in-channel                               | ~1 cycle (instrumentation)                            | Measured, not asserted                     |
| **C7b** | The capability is paid-for-able (BET)                       | "Now which vertical?" with no evidence-backed answer         | comms wedge wholesale → design-partner instrumentation                                        | treat lighthouse as evidence not gravity                                             | concurrent with C2–C5                                 | Business-falsifiability                    |

---

## 14. The honest shape of the whole bet

- **The engine is the tractable part; legibility-for-non-coders is the frontier** (Plan 01 §12). C0–C2,
  C4, and the _engine half_ of C5 are largely assembly of proven primitives. The _frontier_ is whether a
  non-coder can read the trace and drive the rewind (C5's legibility falsifier; C3's depth falsifier) —
  and the two are coupled: C3's "last 20%" survival _depends_ on C5's legibility working (§6.4).
- **The moat is the conjunction, and the conjunction survives losing one term** (analysis 09 §0,
  §5.3). If C5's legibility fails, the platform still owns a unique C2+C4+C6 combination (agnostic,
  natively-governed, governed-cross-org) that no suite vendor (vertical by construction) and no
  horizontal harness (governance not native) can match (analysis 09 §5.3). The sequence hedges the most
  contested term (C5) by shipping the most-proven (C2) first — so a lost M1 race is survivable, not
  fatal.
- **Decision B is both the mitigation and the risk, and the roadmap treats it as both** (analysis 09
  §0). Capability-first (C0–C5) mitigates building-the-wrong-thing-fast and tipping off competitors; it
  _creates_ the "lands nowhere" risk that C7b's lighthouse exists to falsify _early_. The two pull
  against each other; running capability-proof and beachhead-discovery _concurrently_ (not
  sequentially) is the resolution (analysis 09 §1.4).
- **Every claim above is grounded and every uncertainty is flagged.** The genuine unknowns are
  enumerated in Plan 01 §12 (runtime ownership, non-coder versioning UX, re-run-vs-replay default,
  cascade cost, record-vs-file model, classifier latency, trust model, storage, event bus, posture
  composition, posture naming, engine placement). This roadmap _orders the work so the unknowns that can
  kill the thesis are resolved first_ — which is the entire meaning of capability-first.

---

## 15. Source ledger

- **`briefs/01-vision.md`** — §1 (vertical-silo problem + a/b/c triple), §3a–§3c (CLI re-interfaced for
  non-coders), §3d (team + agent-comms hypothesis), §3e (posture beforehand, retrace-and-intervene,
  versioning), §3f (black-box boundary), §3g (cross-org artifact sharing), §4 Decisions A + B.
- **`01-analysis/08-product-focus-80-15-5.md`** — §1 (sorting rule + 95%-failure survival condition;
  the canonical 80/15/5 ratio statement this roadmap cites — it does not restate a different split),
  §2 (agnostic-core inventory + comms placement), §3 (self-service surface + last-20% caution), §4
  (true custom + untrusted-publisher clarification), §6 (BUILD/REUSE/DEFER recommendation + runtime
  pivot + symmetric pros/cons), §7 (honest cautions).
- **`01-analysis/02-value-propositions.md`** — §0 (PROVEN/credible vs CONTINGENT value tagging), §0.2
  (the four buyer questions + the inversion) — the value layer this roadmap sequences against (§10.2).
- **`01-analysis/05-aaa-framework.md`** — §0 (the three value axes: Automate / Augment / Amplify), §1
  (Automate = agent-as-integration-layer) — the value frame the proof sequence proves in priority order
  (§10.2).
- **`01-analysis/09-risks-failure-points.md`** — §0 (the conjunction-bet shape), §1 (PMF / lands-nowhere
  - lighthouse mitigation), §2 (M1 cascade + last-20% death + reduced-form mitigation), §3 (agent-comms
    bet + narrowed position + instrumentation), §4 (trust/security cluster: untrusted publishers,
    injection, blast radius, tenant isolation, L5 liability), §5 (competitive window + race-on-conjunction),
    §6 (adoption + non-coder authoring paradox), §7 (dependency / runtime ownership).
- **`01-analysis/03-unique-selling-points.md`** — §2 (M1: substrate proven, experience bet), §3 (M2:
  largely proven, ship-first), §4 (M3: substrate proven, agent-comms bet), §5 (M4: machinery proven,
  cross-org trust bet), §7 (defensibility ranking), §8 (lead M1 / ship M2 first / seed M4 / M3
  underneath + symmetric pros/cons + rejected alternative).
- **`02-plans/01-architecture.md`** — §0–§1 (seven-layer map), §2 (L7 non-coder surface), §3 (L3
  governance + naming trap + LLM-first caution + facade caution), §4 (L4 provenance ledger + cascade
  engine + six invariants + non-determinism), §5 (L6 coordination + agent-comms caution), §6 (L5
  artifact system + untrusted-publisher trust model design-first), §7 (L1 connectors + dumb-endpoints +
  governed connectivity), §8 (L2 runtime + the runtime-ownership spike + envoy-hybrid), §9 (one
  objective end-to-end), §10 (REUSED vs NET-NEW 80/15/5), §11 (overarching recommendation + symmetric
  pros/cons), §12 (top unknowns).
- **`01-analysis/01-research/09-comms-wedge-mapping.md`** — §2 (comms features are platform-primitive
  instances), §3 (objective/process/data triple), §4 (what comms de-risks), §5 (80/15/5 split), §6 (the
  honest seam: comms proves the spine, not the orchestration half — §6.1 no multi-step cross-system,
  §6.2 no step-level retrace/cascade, §6.3 no cross-org sharing, §6.5 synthesis).
- **The strategic spine (Phase A)** — moats M1–M4, the conjunction-is-the-moat thesis, the Claude Cowork
  threat framing, "transparency makes depth legible," the MIT NANDA / Gartner market evidence, Decisions
  A (comms wedge) + B (capability-first, GTM deferred), the agent-comms hypothesis as an unproven bet.
- **COC rules** — `communication.md` (plain language), `recommendation-quality.md` (single rec +
  symmetric pros/cons), `autonomous-execution.md` (cycles + sharding caps + structural vs execution
  gates), `independence.md` (Sequor is the product), `tenant-isolation.md`, `orphan-detection.md` /
  `facade-manager-detection.md` (no orphaned governance), `agent-reasoning.md` (LLM-first),
  `user-flow-validation.md` (walk + receipts), `spec-accuracy.md` (flag, don't paper over, uncertainty),
  `cross-cli-artifact-hygiene.md` (CLI-neutral prose).
