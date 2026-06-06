# 07 — Transparency, Intervention & Versioning Architecture: The Signature Differentiator

> **Purpose.** This is the architecture document for what makes Sequor structurally different from
> every other "an agent does your work" product. It turns the brief's hardest requirement — _every
> step is transparent, you can rewind to any past step and change it, and the consequences recompute
> while the old results survive as versions_ — into a decision-grade architecture a technical founder
> can act on. It is the engineering core of moats **M1** (transparent, versioned, intervene-from-any-step
> work) and **M2** (execution-time, posture-graded governance) from the strategic spine.
>
> **Audience.** A technical founder deciding whether to build this, and what to build first. Plain
> language throughout; every technical term is translated on first use (per
> `.claude/rules/communication.md`). Effort is in **autonomous execution cycles** — work an AI agent
> system completes, not human-days (per `.claude/rules/autonomous-execution.md`).
>
> **Grounding.** This document is a synthesis of three research files, read in full:
> `01-research/06-transparency-intervention-versioning.md` (the provenance/cascade/versioning core),
> `01-research/03-pact-governance.md` (the permission-envelope + approval engine), and
> `01-research/04-eatp-trust-posture.md` (the L1–L5 posture machinery, HITL/HOTL). It also draws on
> the brief (`briefs/01-vision.md` §3e–3f) and the strategic spine (Phase A). Every load-bearing
> claim cites one of these. Genuine uncertainty is flagged, not smoothed over.

---

## 0. The thesis in one paragraph

When an AI agent does a piece of knowledge work today — draft a report, reconcile an invoice, answer
a customer — you get the **answer** and almost nothing else. You cannot see why it did what it did,
you cannot change one decision it made three steps ago without redoing everything from scratch, and
when you do redo it, the old version is gone. Sequor's signature claim is that **agentic work becomes
a glass box with an undo-from-anywhere button**: every input, every decision the agent made, every
tool it called, every result, and every output is recorded and shown; you can rewind to any past
step, change an input or override a decision, and only the parts that actually depend on your change
recompute — while the previous results are preserved as named versions you can compare against and
return to. The only thing that stays opaque is the model's internal "thinking" (its hidden reasoning),
because no one — not even the model's maker — can faithfully record that. Research 06 §0 establishes
that roughly **80% of the substrate to build this already exists** across the Kailash/PACT/aegis
ecosystem; the genuinely new engineering is a single component — a _reactive cascade engine_ — plus a
non-coder-facing timeline UI. This document defines the contract, the data model, the posture surface,
the intervention semantics, what to reuse vs. build, and the honest risks.

---

## 1. Why this is the moat (and why it is also the hardest thing to build)

**The competitive logic, stated plainly.** The biggest threat in the strategic spine is Claude Cowork
(general availability April 2026), which embodies the _surface_ thesis — "an agent does your work in
one interface." Sequor must not compete on that surface; it competes on the _substrate_ underneath it.
Transparency-with-intervention-and-versioning is the part of the substrate that:

- **No competitor has productized for non-coders.** Research 06 §0 is explicit: the pieces exist _only
  as developer primitives_ — "durable execution," "time-travel debugging," "checkpoint replay" — tools
  a programmer uses, never a feature a non-coder business user can touch. Research 04 §6.3 confirms the
  rewind-and-re-run capability "does NOT exist as a primitive in any of the read sources."
- **Directly answers the market's #1 failure mode.** The spine cites MIT NANDA: ~95% of generative-AI
  pilots fail because generic tools "don't learn from / adapt to workflows," and Gartner projects >40%
  of agentic projects cancelled by 2027. A glass box you can correct and version is the structural
  answer to "the agent did the wrong thing and I had no way to see why or fix it without starting over."

**The honest other half (symmetric, per `.claude/rules/recommendation-quality.md` MUST-3).** This is
simultaneously the **strongest moat and the highest execution risk** in the entire product (spine, M1).
Two hard problems sit at its center and neither is fully solved anywhere:

1. **Non-determinism.** Large language models do not produce the same output twice from the same input.
   "Rewind and re-run" works cleanly for deterministic software (a spreadsheet recalculates the same
   way every time); it is genuinely hard when the steps being re-run are model calls that may
   legitimately answer differently the second time (Research 06 §3 gap 4, §8). We address this head-on
   in §5.
2. **Non-coder versioning UX.** Version control, branching, and "compare two timelines" are concepts
   even most _programmers_ find confusing (git is famously hard). Presenting them to a non-coder is an
   unsolved design problem (spine, M1: "non-coder versioning UX unsolved"). This is a UI/UX risk, not
   an engine risk, and it is called out as the dominant unknown in §10.

So the recommendation that runs through this whole document is: **build the engine on the existing
substrate (low risk, high reuse), and treat the non-coder UX as the actual frontier (high risk, where
the product is won or lost).** The transparency itself is what makes the non-coder UX tractable — you
can only let a non-expert intervene safely if they can _see_ what they are intervening in. This is the
spine's "transparency makes depth legible" point made concrete.

---

## 2. The transparency CONTRACT — drawing the line crisply

The brief's objective 3f: _"every activity and output is traced and made transparent. The only thing
not transparent is how the model (black box) thinks — but input and output are transparent."_ The
single most important thing this document does is **define that boundary precisely**, because a fuzzy
boundary is a broken promise — either you over-claim ("we show you everything the AI does," which is
false) or you under-deliver ("we just log the final answer," which is no different from today).

### 2.1 What is RECORDED and SURFACED (the glass box)

For every step a human or agent takes, Sequor records and can display:

| Recorded & shown                         | Plain-language meaning                                                                                                  | Why it matters                                                                              |
| ---------------------------------------- | ----------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------- |
| **Inputs**                               | Exactly what went into the step — the data, the documents, the prior results it consumed                                | You can see what the agent was working from                                                 |
| **Agent decisions, plans, and fan-outs** | The choices the agent made _before_ acting — e.g. "I will split this into 3 sub-tasks and run them in parallel"         | This is the brief's 3Q-report example; the _plan_ is a first-class, inspectable object      |
| **Tool calls**                           | Every external action requested: which tool, with what arguments — "send email to X," "query the sales database for Q3" | You see what the agent _tried to do in the world_, not just what it concluded               |
| **Tool results**                         | What each tool returned — the query rows, the API response, the file it read                                            | You see the ground truth the agent then reasoned over                                       |
| **Outputs**                              | What the step produced — the draft, the number, the decision, the message                                               | The deliverable, versioned                                                                  |
| **Metadata**                             | Model used, cost, time taken, and _which posture was in force when the step ran_                                        | "This ran on its own under Autonomous" vs. "a human approved this under One-Check" — see §4 |

This list is grounded in Research 06 §5.1 (the recorded I/O envelope) and is exactly the shape the
**OpenTelemetry GenAI Semantic Conventions** define — an industry-standard schema for tracing AI
systems that the whole observability industry (Datadog, Honeycomb, New Relic; the LangChain/CrewAI/
AutoGen agent frameworks) has converged on (Research 06 §5.1). We adopt that standard rather than
invent our own. The structure is a tree of spans (a "span" is one recorded operation with a start, an
end, and attributes): a top-level _agent-invocation_ span, with child _chat_ spans (one per model call)
and _tool-execution_ spans (one per external action). Research 06 §5.2 confirms the Kailash Core SDK
already emits this shape today via its tracing levels.

### 2.2 What is the BLACK BOX (and the one subtlety, 3f)

Not recorded — and deliberately so:

| NOT recorded (the black box)                                                        | Why we cannot / should not record it                                                                                                        |
| ----------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| The model's **chain-of-thought** — its internal step-by-step "scratchpad" reasoning | Often not exposed by the model's interface at all; unstable across model versions; frequently the most sensitive content (Research 06 §5.3) |
| The model's **internal activations / weights**                                      | These are billions of opaque numbers; recording them explains nothing a human could act on                                                  |
| **Token-level logits** — _why_ the model picked one word over another               | Not human-interpretable; explains nothing about the decision in business terms                                                              |

**The one subtlety the brief flags (3f), made crisp.** Some model providers now expose a _summarized
reasoning trace_ — a short, model-generated explanation of its approach — which is **distinct from**
the raw chain-of-thought. Where a model voluntarily emits such a summary at its output surface, Sequor
records it (the EATP SDK has an explicit `reasoning-traces` slot for exactly this — Research 06 §5.3).
The boundary is therefore stated precisely as:

> **We record everything the model emits at its input/output surface — including any reasoning summary
> it chooses to surface. We do not record, and do not claim to record, how the model actually computed
> its answer internally.**

This is the _only_ defensible boundary, and stating it this way protects against two failure modes at
once: it stops us from over-promising "explainability" (claiming to explain the unexplainable) and it
stops us from under-delivering (hiding a reasoning summary the model _did_ give us).

### 2.3 The honesty caveat that must travel with every trust claim

Research 03 §2.3 and Research 04 §2.2 both surface the same critical distinction, and it must be stated
in any marketing or product copy: **the system delivers _traceability_, not _accountability_.**

- **Traceability** (the machine guarantees this): every AI action can be traced back to its inputs,
  its decisions, and the human authority that permitted it.
- **Accountability** (no software can guarantee this): that a human actually _understood_, evaluated,
  and bears the consequences of what the agent did.

The transparency surface converts traceability into a _chance_ at real accountability — it makes
understanding _possible_ — but it cannot force understanding. We promise the glass box; we do not
promise that the human looked through it. Over-claiming here is both dishonest and legally hazardous.

---

## 3. The PROVENANCE LEDGER — the data model

"Provenance" means the recorded origin and history of every piece of work — what produced it, from
what, and when. The provenance ledger is the permanent, queryable record that makes everything in §2
possible. The central finding from Research 06 §1 is that **this data model already exists** — it is
the PACT platform's set of work-tracking records — it has simply never been wired to a rewind engine.

### 3.1 The three node kinds and the typed edges between them

The ledger is a **graph** (a network of records connected by typed relationships). It has exactly
three kinds of node and a small set of edge types (Research 06 §1.3, grounded in PACT's `Run`,
`AgenticArtifact`, and `AgenticDecision` models — Research 03 §6.1–6.2):

| Node kind    | Maps to existing PACT model | What it is                                                                          | Key properties                                                                                                                                                                                                       |
| ------------ | --------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Step**     | `Run`                       | One invocation — one model call, one tool call, one workflow run                    | `inputs_hash`, `outputs_hash`, `agent_id`, `posture_at_time`, the prompt reference, the tool calls made, status, start/end, cost. **Immutable.**                                                                     |
| **Output**   | `AgenticArtifact`           | One produced result                                                                 | `content_hash` (a fingerprint of the bytes), `version`, `parent_output_id` (the prior version it supersedes), `produced_by_step_id`, classification. **Immutable — a new version is a new row, never an overwrite.** |
| **Decision** | `AgenticDecision`           | A surfaced choice — a fan-out plan, a held action awaiting approval, a posture gate | status (pending / approved / rejected), who decided, `envelope_version`. **Immutable — resolving it creates a new linked record, never an edit.**                                                                    |

The edges (the typed relationships):

```
Step   --consumes-->  Output      (what this step took as input)
Step   --produces-->  Output      (what this step made)
Step   --depends_on-->Step        (the dependency that drives recompute — PACT's Request.depends_on)
Step   --gated_by-->  Decision    (this step waited on a surfaced decision)
Output --derived_from-->Output    (the version chain — parent_output_id)
```

### 3.2 Why "content-addressed" is the load-bearing trick

"**Content-addressed**" means every Step and Output is identified by a _fingerprint of its content_
(a SHA-256 hash — a short string that changes completely if even one byte of the content changes),
not by a sequential ID. This is the same idea behind how Git stores commits and how IPFS stores files
(Research 06 §1.3). It buys three things that make the whole rewind feature possible and cheap:

1. **Tamper-evidence / immutability for free.** If a recorded result is altered, its fingerprint no
   longer matches — so the record cannot be silently changed. This is the same property as the aegis
   signed posture anchors, where each record carries its `record_hash` and a back-pointer to its
   parent (Research 04 §4.5).
2. **Cheap branching via structural sharing.** When you fork a timeline (§6.2), the new branch _reuses
   the entire unchanged history by reference_ — only the part that changed is new data. This is why a
   "what-if" exploration does not cost a full re-run of everything (Research 06 §2.2).
3. **The "only recompute what changed" guarantee.** A step's identity is computed as
   `hash(its inputs + its code + the fingerprints of the steps it depends on)`. So two runs with
   identical inputs and identical upstream produce the _same_ identity — meaning the system can
   recognize "nothing actually changed here" and skip the re-run, reusing the cached result. This is
   exactly the mechanism behind build systems like Bazel and is the core of the cascade engine (§5,
   Research 06 §1.3, §6.1).

### 3.3 The ledger is the source of truth; telemetry feeds it

A clean architectural decision (Research 06 §8): the OpenTelemetry spans (§2.1) are the _live feed_ —
ephemeral telemetry streaming to the screen as work happens. The provenance ledger is the _permanent
record_ — durable, queryable, content-addressed, backed by the PACT DataFlow models. **Spans write
into the ledger; the ledger is the source of truth.** This avoids the "two databases that disagree"
problem and gives one clean place to query history. The persistence reuses the Kailash durable store
(`DBCheckpointStore` / `StoreFactory`) that already ships (Research 06 §3, §6).

### 3.4 The six invariants the ledger must always hold

These are the correctness rules the implementation must never violate (Research 06 §7.1). They are
listed here so they can be enforced — and so the work can be split correctly when it is planned (each
is a tracked invariant per `.claude/rules/autonomous-execution.md` § Per-Session Capacity Budget):

1. **Immutability** — a re-run never alters a prior Step or Output; it appends a new version.
2. **Tenant isolation** — every fingerprint, cache key, and graph query carries the customer's
   `tenant_id`. A shared fingerprint namespace across customers would be a cross-customer data leak
   (per `.claude/rules/tenant-isolation.md`; the existing Sequor comms product already uses
   schema-per-tenant — Research 06 §7.1).
3. **Determinism boundary** — model steps reuse the recorded output by fingerprint on rewind _unless_
   the user explicitly asks to regenerate; the engine never assumes a model call repeats identically
   (§5).
4. **Cascade minimality** — a downstream step whose recomputed inputs are unchanged _must_ be skipped.
   This is the "only affected downstream" promise; violating it makes rewind slow and expensive.
5. **Posture-at-time** — every Step records the posture in force when it ran, so a rewind can show
   "this ran on its own (Autonomous)" vs. "a human approved this (One-Check)."
6. **Audit completeness** — the intervention itself is an auditable action: _who_ rewound, _what_ they
   changed, _when_. It is a new audit record, never a silent edit.

---

## 4. POSTURE SURFACING — choosing how much rein the agent gets, beforehand

This is moat **M2**: governance set _before_ execution, per objective, not bolted on as after-the-fact
observability. The brief's worked example (3e): the user says "I want a 3Q financial report"; the agent
_decides_ to spin up 3 sub-agents; that decision is **surfaced on screen and recorded**, and the user
has **chosen a posture beforehand** — L5 Autonomous (agent goes ahead), L4 Supervised (agent asks once
before executing), L3 Step-by-step (agent pauses at each step).

### 4.1 The plan is surfaced and approvable BEFORE it runs

The key move — and the part that is genuinely new wiring (Research 06 §4.2, §7 item 3) — is that the
agent's **plan** (the fan-out: 3 sub-tasks, what each will do, the estimated cost) is captured as a
**Decision record** and shown to the user _before any of it executes_. The user sees the plan as an
inspectable object — a small diagram of "here is what I'm about to do" — and, depending on posture,
either watches it auto-approve, approves it once, or steps through it.

The pipeline to do this **already exists end to end** (Research 03 §5.3, §7; Research 04 §6.1):

- When an agent forms a plan, PACT's `EventBridge.on_plan_event` already fires per scheduled sub-task
  and streams it to the screen over a live connection (a WebSocket — a persistent two-way channel
  between the agent and the browser). "Decisions surfaced on screen" is _substantially built_.
- When something needs human approval, PACT's `HELD` mechanism already pauses the action, writes an
  approval record, and **blocks until a human approves or rejects** — surfaced as an approval queue on
  a dashboard (`ApprovalBridge.get_pending` → approve / reject). This is "the agent pauses and asks for
  one permission," realized in shipped code (Research 03 §5.1, the `return False` in `_PlatformHeldCallback`).

What is new is small: a new Decision _subtype_ — call it `plan_proposed` — that surfaces the _plan
itself_ (not just a near-a-limit governance trigger) as the approvable object, and the wiring that
makes the chosen posture decide whether that plan auto-approves, needs one approval, or pauses at each
step (Research 06 §4.2; Research 03 §8.4 item 2). Research 06 §4 estimates this at **~1 cycle of
integration, not greenfield.**

### 4.2 The L5/L4/L3 ladder, and the naming trap to avoid

The brief's three levels map onto the EATP/PACT posture machinery, which is **already built** — a
state machine that persists posture, records every transition, and enforces it at action time
(Research 04 §1.1, §2.4, §6.1). But Research 04 §1.4 flags a **real naming collision** the spec must
resolve: the brief's labels do _not_ line up cleanly with the canonical engine's labels (e.g. the brief
calls L4 "Supervised," but in the shipped engine "Supervised" is a _lower_, every-action-approved
level). Shipping the brief's labels as the engine's internal names would confuse every engineer who
knows the existing system.

**Recommendation (Research 04 §1.4, §6.4):** keep the **canonical EATP enum as the internal source of
truth** (it is the shipped, persisted, signed primitive) and present a **plain-language 3-button UX** on
top of it. The user never sees "L5_DELEGATED"; they see three plain choices:

| User-facing button (what the user picks)  | Internal engine posture | Per-step behaviour                                                                   | Human's relationship to the work                                 |
| ----------------------------------------- | ----------------------- | ------------------------------------------------------------------------------------ | ---------------------------------------------------------------- |
| **"Go ahead"** (Autonomous)               | `AUTONOMOUS` (level 5)  | Auto-approve within the permission envelope; anything outside it is blocked          | **HOTL** — human watches, can abort, but does not gate each step |
| **"Ask me once"** (One check)             | `DELEGATING` (level 4)  | Auto-approve within the envelope; **one** approval gate at the plan→execute boundary | **HOTL + one gate** — one structural checkpoint                  |
| **"Step through with me"** (Step-by-step) | `SUPERVISED` (level 3)  | Every consequential action pauses for approval                                       | **HITL** — human is a blocking node inside the path              |

### 4.3 HITL vs HOTL — what these mean and why posture _is_ the choice between them

These two terms recur in the brief (3e) and the research; here they are, translated:

- **HITL — "human in the loop":** the human is a **blocking node inside the execution path**. The agent
  _cannot proceed_ past a consequential action without the human. This is the "Step through with me"
  posture (Research 04 §3).
- **HOTL — "human on the loop":** the human is a **monitor outside the execution path**. The agent
  proceeds; the human observes and can intervene or abort, but does not gate every step. This is the
  "Go ahead" and "Ask me once" postures (Research 04 §3).

The crucial insight from Research 04 §3, §5 is that **the posture level _is_ the choice between HITL and
HOTL** — it is not a separate control. Picking "Step through with me" puts the human in the loop; picking
"Go ahead" puts them on the loop. Mechanically, the posture chooses _which class of gate blocks the
agent_: at high posture only _structural_ gates (approve-the-plan, authorize-a-release) stop it; at low
posture, _every consequential_ step also blocks (Research 04 §5).

### 4.4 The safety floor and the emergency path (both already built)

Two governance facts complete the posture picture, and both ship today:

- **The operative posture is `min(user-chosen, system-floor)`** (Research 04 §6.2 Gap C). The user can
  _opt up_ to more autonomy, but the system keeps a safety floor that auto-_downgrades_ on detected
  problems. The governing principle (the "Mirror Thesis," Research 04 §1.2, §4.2): **upgrades are
  human-gated; downgrades fire automatically on detection.** A repeated violation instantly drops the
  agent to the most restrictive posture. This is why "Go ahead" is safe to offer — it is not a blank
  cheque; it is a ceiling the system can lower the instant something looks wrong.
- **Emergency bypass with audit** (Research 03 §5.4). A senior human can grant a time-limited expansion
  of the agent's permissions for a genuine emergency — but it is tiered (4h / 24h / 72h, never longer),
  cannot grant more than the approver themselves holds, is rate-limited, and _aborts if it cannot write
  an audit record_ ("governance mutations require an audit trail"). This is the "break glass" path that
  stays accountable.

One reuse caution carried from Research 04 §3 (the "⚠ reuse caveat"): PACT's existing code decides
"is this action consequential?" by **matching keywords** (`write`, `send`, `delete`…). Sequor's own
rules forbid keyword/regex routing in agent decision paths (`agent-reasoning.md`, CLAUDE.md Directive 6).
The platform must replace that keyword classifier with an **LLM-judged** consequentiality assessment —
keeping PACT's _verdict_ machinery (pause / block / auto-approve) but not its keyword decision path.
Research 04 §3 calls this "a small, well-scoped rewrite, not a re-architecture," but flags the
latency/cost tradeoff of an LLM call on every action as an open design question (§7 item 5; see §10
below).

---

## 5. INTERVENTION + CASCADE RE-EXECUTION — the genuinely new core

This is the heart of the product and the only piece that is mostly net-new (Research 06 §7). The brief
(3e): _"Users can retrace any previous step and intervene from there; downstream/cascading outputs change
accordingly, but old outputs are versioned."_

### 5.1 The mechanism, step by step

The established art Sequor borrows from is **reactive computational notebooks** (tools like ipyflow
that, when you change one cell, automatically re-run only the cells that depend on it) layered over the
content-addressed graph from §3 (Research 06 §2.1). The flow:

1. **The user retraces to Step N.** The UI reads the provenance graph (§3) and shows Step N's recorded
   inputs, the prompt that went in, the tool calls it made, and the output it produced — the
   transparency surface from §2.
2. **The user changes an input or overrides a decision at N.** This creates a _new_ Step N′ with a new
   inputs-fingerprint. The old Step N and its Output are **untouched** — they remain as a prior version
   (immutability, §3.4; this _is_ "old outputs are versioned").
3. **Dirty-marking.** The engine walks _all descendants of N_ — every step downstream that could be
   affected — and marks them "potentially dirty" (potentially needing re-run). The graph operation to
   find descendants already exists in the Kailash `WorkflowDAG` (Research 06 §2.1).
4. **The "only affected downstream" guarantee.** The engine re-runs dirty steps in order. For each, it
   recomputes the inputs-fingerprint from its (possibly-unchanged) upstream. **If the new fingerprint
   equals the recorded one, it skips the step and reuses the cached output.** Only steps whose inputs
   _actually_ changed re-run. A step that depended on N but whose _other_ inputs dominate may produce an
   identical result and **halt the cascade early** — the change does not propagate further (Research 06
   §2.1 step 4).
5. **Versioning.** Each re-run step's output is written as a _new version_ with a back-pointer to the
   prior version. Nothing is overwritten (Research 06 §2.1 step 5).

The combination — _dirty-propagation_ (from reactive notebooks) + _fingerprint-skip_ (from build
systems) — is precisely what delivers "downstream cascades re-execute, but only the affected ones, and
old outputs survive." Research 06 §6.1 makes the unifying observation that this is the _same_ skip
operation Kailash already performs in three other places (crash-recovery, idempotency, within-run node
skipping) — just _generalized_ from "within one run" to "across runs, keyed on content fingerprint."
That is why this is a **20% novel composition, not an 80% greenfield build**: the hard primitive
(content-addressed memoization) already ships; the new work lifts its scope.

### 5.2 Branching the timeline — explore without destroying

"Retrace and intervene" implies the user may _not_ want to overwrite the original — they may want to
explore an alternative. The model is **Git-like branching over the provenance graph** (Research 06 §2.2):

- An intervention at Step N can either **advance the main timeline** (N′ supersedes N; descendants
  recompute in place as new versions) or **fork a branch** (N′ starts a new timeline that shares all
  history up to N by reference, diverging after).
- Because everything is content-addressed and immutable, **a fork is cheap** — it shares the entire
  unchanged ancestor history by fingerprint reference; only the divergent suffix is new data (§3.2).
- A "timeline" is then just a named pointer to a head of the graph (exactly like a Git branch). "Compare
  two timelines" is a fingerprint-by-fingerprint diff of their histories.

The precedent already exists: the aegis posture-anchor chain is a single-parent, content-addressed,
signed ledger (each anchor names its parent, carries its hash, and is signed — Research 04 §4.5).
Generalizing "single parent" to "support divergence + named heads" yields a branchable provenance graph
(Research 06 §2.2). Estimated ~1 cycle (Research 06 §7 item 2).

### 5.3 The HARD problem, addressed honestly: non-determinism → re-run vs. replay vs. branch

This is the part the brief's vision glosses and this document must not. **Model steps are
non-deterministic — the same prompt can yield a different answer next time.** That breaks the naive
assumption behind "rewind and re-run": that re-running a step reproduces what was there before. Three
distinct things a user might mean by "redo," with different correct behaviours (Research 06 §3 gap 4,
§8; Research 04 §6.3):

| The user's intent                                             | Term       | What the engine does                                                                                                             | Determinism handling                                                                                                                          |
| ------------------------------------------------------------- | ---------- | -------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| "I changed an input three steps back; flow my change forward" | **Re-run** | Re-execute the affected downstream steps with the changed input                                                                  | Model steps _will_ re-run and _may_ legitimately differ. This is correct and expected — the input changed, so a new answer is appropriate.    |
| "Show me exactly what happened last time, don't re-compute"   | **Replay** | Reconstruct the past state from the recorded outputs by fingerprint — **reuse the recorded answer, do not call the model again** | Fully deterministic, because we are reading recorded results, not re-generating. This is the safe default for steps the user did _not_ touch. |
| "Try a different path without losing the original"            | **Branch** | Fork a new timeline at Step N (§5.2)                                                                                             | The original is preserved by reference; the new branch re-runs its divergent suffix.                                                          |

**The design decision that makes this work** (Research 06 §3 gap 4, §7.1 invariant 3): on a rewind, the
engine **reuses the recorded output by fingerprint** for every step the user did _not_ explicitly change,
and only re-generates the steps the user _did_ change (and their genuinely-affected downstream). It
**never assumes a model call replays identically.** This is the same trick mature durable-execution
systems use (recording the result of a non-deterministic operation and replaying the _recorded value_,
not re-executing — Research 06 §3 gap 4). The user is given an explicit, per-step choice when it matters:
_"re-run this with my edit (get a fresh answer)"_ vs. _"keep the recorded output, only re-run what
depended on it"_ (Research 06 §8). That choice is a product decision surfaced in the UI, not a hidden
default — because either behaviour is sometimes what the user wants, and guessing wrong silently is
the worst outcome.

**The legitimate-divergence caveat, stated plainly:** when a re-run _does_ re-generate a model step, the
new answer may differ from the old in ways that are _correct_ but _surprising_ to a non-coder ("I only
changed the date and now the whole tone of the report is different"). The product must make this legible
— show _what changed and why_ between versions — rather than pretend re-runs are deterministic. This is
a UX obligation, and it is part of why the non-coder UX is the dominant risk (§10).

### 5.4 A worked example (the brief's 3Q report)

To make all of the above concrete, trace the brief's own example through the architecture:

1. **User states intent:** "I want a 3Q financial report." Posture chosen beforehand: **"Ask me once."**
2. **Agent plans a fan-out:** spin up 3 sub-agents — one each for revenue, costs, and cash flow. This
   plan is captured as a `plan_proposed` Decision (§4.1) and **shown on screen before anything runs.**
   Because posture is "Ask me once," the user gets **one** approval gate. They approve.
3. **Execution & recording:** each sub-agent runs as a chain of Steps; every input, tool call (e.g.
   "query the ledger for Q3 revenue"), tool result, and output is recorded in the provenance ledger
   (§3), streamed live to the screen (§2.1). Each output gets a content fingerprint and version 1.
4. **The report is assembled** from the three sub-outputs into a final Output (also versioned).
5. **The user retraces.** Reviewing the revenue section, they spot that the agent used the wrong
   exchange-rate assumption two steps back. They **rewind to that step** (§5.1 step 1), see exactly what
   it consumed and produced (§2.1), and **change the assumption** (step 2).
6. **The cascade recomputes only what's affected** (step 3–4): the revenue sub-agent's downstream steps
   and the final report re-run; the _costs_ and _cash-flow_ sub-agents are **untouched** because their
   inputs did not change (their fingerprints match → skipped). The user is asked whether the revenue
   model step should be _re-generated with the new assumption_ or just have its downstream re-flow (§5.3).
7. **Versions preserved:** the original revenue section and original report survive as version 1; the
   corrected ones are version 2, with a back-pointer. The user can compare v1 vs v2 side by side, and
   revert if they prefer the original.
8. **The intervention is itself audited** (§3.4 invariant 6): _user X changed the exchange-rate
   assumption at step N at time T_ is a permanent record.

Every numbered step above is grounded in an existing primitive _except_ the cascade in step 6 and the
timeline/version UI in steps 5–7 — which is exactly the 80/20 split this document keeps returning to.

---

## 6. What already exists vs. what is genuinely new

This is the build-vs-reuse picture a founder needs. The architecture is four layers, bottom to top
(Research 06 §6). The reuse percentages are from Research 03 §8.5 (the governance stack is ~80% reuse /
~15% glue / ~5% new) and Research 06 §6–7 (the provenance/cascade stack).

### 6.1 The layer cake

```
┌──────────────────────────────────────────────────────────────────────┐
│ L4  TRANSPARENCY + INTERVENTION UI                                     │
│     timeline view · "rewind to step N" + edit · live decision stream   │
│     · approve/reject queue · the 3-button posture selector             │
│     [EXISTS: live event stream + approval queue API + PACT's web        │
│      objectives/approvals screens as scaffold.  NEW: the timeline +     │
│      rewind UI + plan-approval surface + non-coder version UX]          │
├──────────────────────────────────────────────────────────────────────┤
│ L3  REACTIVE CASCADE ENGINE   ◄── THE NOVEL CORE (~5% of total)        │
│     dirty-propagation over descendants · fingerprint-skip (reuse        │
│     unchanged) · version-on-rerun · branch/fork timelines              │
│     [NEW — but a generalization of skip logic Kailash already has]     │
├──────────────────────────────────────────────────────────────────────┤
│ L2  GOVERNED EXECUTION + DECISION GATING                               │
│     plan → HELD → approval queue → approve/reject · posture gate        │
│     (Go-ahead / Ask-once / Step-through)                               │
│     [EXISTS: PACT SupervisorOrchestrator + ApprovalBridge + EATP        │
│      posture state machine.  NEW: plan_proposed decision subtype +      │
│      LLM-first consequentiality classifier (replaces keyword one)]     │
├──────────────────────────────────────────────────────────────────────┤
│ L1  PROVENANCE LEDGER (content-addressed, immutable)                   │
│     Step / Output(version+parent) / Decision · depends_on edges ·       │
│     append-only · durable persistence · I/O recording (no chain-of-     │
│     thought)                                                           │
│     [EXISTS: PACT DataFlow models + Kailash durable store + OTel        │
│      GenAI conventions.  NEW: wiring them as a unified provenance DAG]  │
└──────────────────────────────────────────────────────────────────────┘
```

### 6.2 The ecosystem inventory — what's already in the box

| Capability the brief needs                                               | Existing asset that delivers it                                                                          | Source                                 |
| ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------- | -------------------------------------- |
| Step / Output / Decision records, content-hashed, versioned              | PACT DataFlow models (`Run`, `AgenticArtifact` with `version` + `parent_artifact_id`, `AgenticDecision`) | Research 03 §6.1–6.2; Research 06 §1.1 |
| Dependency edges for cascade                                             | `AgenticRequest.depends_on` (already a graph edge-set)                                                   | Research 06 §1.1                       |
| Append-only, immutable audit                                             | PACT audit anchors + Sequor's `AuditEntry` (immutable, ON DELETE RESTRICT)                               | Research 06 §1.2; Research 03 §4.2     |
| Durable persistence + crash-resume                                       | Kailash `ExecutionTracker`, `DurableRequest`, `Checkpoint`, `DBCheckpointStore`                          | Research 06 §3                         |
| Within-run "skip completed, reuse cached" (the cascade primitive's seed) | `ExecutionTracker` node-skip; `IdempotentExecutor`                                                       | Research 06 §3, §6.1                   |
| Plan/decision streamed to screen live                                    | PACT `EventBridge` + `EventBus` (WebSocket fan-out)                                                      | Research 03 §5.3; Research 06 §4.1     |
| Pause-and-await-human approval                                           | PACT `HELD` → `_PlatformHeldCallback` → `ApprovalBridge` (approve/reject queue)                          | Research 03 §5.1–5.2; Research 04 §6.1 |
| The L5/L4/L3 posture machinery (persisted, signed, with auto-downgrade)  | EATP `PostureStateMachine` + `SQLitePostureStore` + the COC posture ladder                               | Research 04 §2.4, §4                   |
| Per-objective cost ceilings with alerts                                  | EATP `BudgetTracker` (80%/95%/exhausted callbacks)                                                       | Research 04 §2.3                       |
| Tamper-evident signed history (retrace spine)                            | aegis posture anchors (hash-chained, Ed25519-signed)                                                     | Research 04 §4.5                       |
| I/O-envelope recording standard (no chain-of-thought)                    | OpenTelemetry GenAI conventions; Kailash already emits the shape                                         | Research 06 §5.1–5.2                   |
| Safe rollout under the live Sequor comms product                         | PACT `EnforcementMode.SHADOW` (observe, never block)                                                     | Research 03 §5.5                       |
| Web scaffold for objectives/approvals screens                            | PACT's Next.js `objectives` + `approvals` dashboard                                                      | Research 04 §6.1                       |

### 6.3 The genuinely-new list (the 20%, concentrated)

Everything else exists or is industry-standard. The novel engineering is concentrated and small
(Research 06 §7; Research 03 §8.4):

1. **The reactive cascade engine** (L3) — dirty-propagation + fingerprint-skip + version-on-rerun, generalizing Kailash's intra-run skip to cross-run. _~1–2 cycles; has a live feedback loop (each cascade is testable against a fixture graph), so it can run at higher budget per `autonomous-execution.md`._
2. **Branch/fork timelines** over the provenance graph — Git-like named heads with structural sharing. _~1 cycle._
3. **The `plan_proposed` decision subtype + posture-gated plan approval** — surface the fan-out plan as an approvable object before execution. _~1 cycle of integration._
4. **The LLM-first consequentiality classifier** — replace PACT's keyword classifier per `agent-reasoning.md`. _Small, well-scoped rewrite._
5. **The non-coder timeline + rewind + version UI** — render the graph, let the user pick a step, edit, and trigger the cascade; show the live decision stream and version comparisons. _~1–2 cycles for a first version; the design problem is open-ended (§10)._

**Effort headline (Research 06 §7):** an end-to-end working rewind-and-intervene over the _comms-wedge_
4-step flow is estimated at **~4–6 autonomous execution cycles**, because the substrate (L1, L2, the
event stream, the posture machine, the durable store) is reused rather than rebuilt. Generalizing beyond
the wedge to arbitrary multi-agent objectives is incremental once L3 exists.

### 6.4 Where the comms wedge plugs in (Decision A)

The strategic spine folds the existing Sequor communication product in as an early vertical. Research 06
§6.2 shows it is a _small, concrete instance_ of the general graph:
`Message → Classification → RAG-retrieval → Response → (auto-send | Escalation)`. Each is a Step;
`Response.content` is a versioned Output; the classification reasoning and retrieved passages are
recorded I/O. The comms product's _existing_ "log a correction as a new audit row" discipline is
literally the retrace-and-version primitive **already specified in prose** — a user correcting a
classification should create a new version and re-derive the downstream response. **Wiring the comms
wedge to the cascade engine is the natural first vertical:** it proves rewind-and-intervene on a 4-step
flow before generalizing. And `EnforcementMode.SHADOW` (Research 03 §5.5) is how governance slots under
the live product without breaking it — observe what _would_ be held/blocked before turning on teeth.

---

## 7. Recommendation — the target architecture, with symmetric pros and cons

### 7.1 The recommendation

**Build the four-layer stack of §6.1 by reusing L1 and L2 wholesale, building the L3 cascade engine as
the single net-new framework component, and treating the L4 non-coder UI as the real product frontier.
Prove it first on the comms wedge (4-step flow), then generalize. Run governance in SHADOW mode under
the existing product during rollout.**

Concretely, in priority order:

1. **Stand up the provenance ledger (L1)** by unifying the PACT models + Kailash durable store + OTel
   recording into one content-addressed graph. Mostly wiring; reuses shipped models. (Research 06 §1, §3.)
2. **Wire governed execution + posture gating (L2)** — adopt PACT's orchestrator/approval/event stack;
   add the `plan_proposed` decision subtype and the LLM-first classifier; map the 3 buttons to the
   canonical posture enum. (Research 03 §8; Research 04 §6.4.)
3. **Build the reactive cascade engine (L3)** — the one load-bearing net-new component. Shard carefully
   against the six invariants of §3.4. (Research 06 §7.)
4. **Build the non-coder timeline/rewind/version UI (L4)** on PACT's web scaffold — the frontier; treat
   as iterative discovery, not a one-shot build. (Research 04 §6.2 Gap B.)

### 7.2 Implications

- **For the product:** the moat is real and structural — it is the conjunction the spine names, and it
  lands in _one_ non-coder interface that no competitor has assembled (Research 06 §0). The transparency
  surface is also what makes the non-coder _depth_ problem tractable (you can let a non-expert intervene
  because they can see what they are touching) — directly de-risking the "no-code dies at the last 20%"
  threat from the spine.
- **For the build:** because ~80% is reuse, the **engineering risk is concentrated in two places** — the
  L3 cascade engine (a known, bounded problem) and the L4 non-coder UX (an open design problem). Effort
  is small in _cycles_ but the UX work is open-ended in _iterations_.
- **For governance posture:** keep the canonical EATP enum internal, present 3 plain buttons; default to
  the safer SUPERVISED-equivalent and let users opt up; keep `min(user-chosen, system-floor)` as the
  safety floor (Research 04 §6.2 Gap C).
- **For dependencies:** the cascade engine should live as a framework-level module (operating over the
  DataFlow models + WorkflowDAG), _not_ inside the Sequor app — consistent with the spine's
  capability-first stance and Decision B (build the horizontal capability; the wedge consumes it).
  Confirm placement with the framework specialists at design time (Research 06 §8 last bullet).

### 7.3 Pros and cons (symmetric, per `recommendation-quality.md` MUST-3)

**Pros:**

- **Highest reuse, lowest reinvention.** ~80% of the substrate ships; the new work is one engine + one
  UI, not a platform from scratch (Research 06 §0, §6; Research 03 §8.5).
- **The strongest moat in the product.** It is the part of the substrate the surface-thesis competitors
  (Cowork) have not productized for non-coders (spine M1; Research 06 §0).
- **Directly answers the market's documented failure mode** (pilots fail because tools don't adapt; a
  correctable, versioned glass box is the structural answer — spine, MIT NANDA citation).
- **Honest by construction.** The traceability-not-accountability and black-box boundaries are stated
  crisply (§2.2–2.3), which protects against over-claiming.
- **Incremental rollout is safe.** SHADOW mode lets governance run under the live comms product without
  blocking anything until calibrated (Research 03 §5.5).

**Cons (real, not glossed):**

- **The non-coder versioning UX is genuinely unsolved.** Git-like branching is hard for _programmers_;
  presenting it to non-coders is the dominant unknown (spine M1; §10 below). This is where the product
  is most likely to fail, and no research file resolves it.
- **Non-determinism makes "redo" semantically ambiguous.** Re-run vs. replay vs. branch is a real
  conceptual burden we are partly _pushing onto the user_ via the per-step choice (§5.3). If users find
  that choice confusing, the feature feels unpredictable.
- **Cost/latency of LLM-on-every-action.** Replacing the keyword classifier with an LLM judge adds a
  model call to consequentiality checks; on a step-heavy objective this is real latency and cost
  (Research 04 §7 item 5). Mitigation (classify once per step-type, cache the verdict shape) is itself
  unproven at scale.
- **Storage grows without bound** under immutable versioning unless a retention/compaction policy is
  built; content-addressing dedupes identical bytes but does not bound version _count_ (Research 06 §8).
- **PACT is a facade-heavy codebase.** The platform must enforce `orphan-detection.md` /
  `facade-manager-detection.md` — every governance manager wired into the hot path needs a real call
  site + integration test, or it becomes a security promise that silently never executes (Research 03
  §8.5; this is the exact failure those rules exist to prevent).
- **The cost-preview problem.** A change near the root of a wide graph can legitimately invalidate
  everything downstream; without a cost-preview before committing a cascade, a single edit can trigger a
  large, surprising re-run (Research 06 §8).

### 7.4 The alternative considered and rejected

The alternative is to **build a bespoke provenance/versioning system from scratch** rather than reuse
the PACT/EATP/Kailash substrate. Rejected because: it discards ~80% of working, tested code (Research 06
§0, §6.2); it would re-derive the content-addressing, posture state machine, approval queue, and durable
store that already ship; and it conflicts with Decision B (capability-first reuse of the ecosystem DNA).
The _only_ argument for it — "a clean-room design avoids PACT's facade-heaviness" — is better addressed
by enforcing the orphan-detection rules on the reused code than by rewriting it.

---

## 8. The highest-risk unknowns (flagged, not resolved)

Per `.claude/rules/spec-accuracy.md` and the analyst discipline, these are genuine uncertainties that a
spec/redteam phase must resolve. They are ranked by how likely they are to sink the feature.

| #     | Unknown                                                  | Why it's hard                                                                                                                                                            | Where it must be resolved                                                                              |
| ----- | -------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------ |
| **1** | **Non-coder versioning/branching UX**                    | Git is hard for experts; "rewind, fork, compare timelines, revert" for a non-coder is an unsolved design problem and the single biggest risk in M1                       | UX design + user testing; treat as iterative discovery (§7.2). Spine flags it as the dominant M1 risk. |
| **2** | **Re-run vs. replay vs. branch as a user-facing choice** | The per-step "re-generate / keep recorded" decision (§5.3) may confuse non-coders; guessing the default wrong silently is the worst outcome                              | Product decision + user testing (Research 06 §8)                                                       |
| **3** | **Cascade cost explosion**                               | A root-level edit legitimately invalidates everything downstream; needs a cost-preview before committing a cascade (estimate from historical metrics)                    | Engine design — `ExecutionMetric` history is the estimate source (Research 06 §8)                      |
| **4** | **LLM-classifier latency/cost**                          | An LLM call on every consequentiality check is slower and costlier than a keyword match; the caching mitigation is unproven                                              | Design decision (Research 04 §7 item 5)                                                                |
| **5** | **Storage growth / retention policy**                    | Every re-run is a new version forever; needs compaction. Content-addressing dedupes bytes but not version count                                                          | Operational policy (Research 06 §8; aegis `compaction-checkpoint` precedent)                           |
| **6** | **The live event bus is single-process**                 | PACT's `EventBus` is in-memory (one process); a multi-replica deployment needs a durable/distributed bus                                                                 | Infrastructure (Research 06 §8; the `SQLTaskQueue` or Redis fan-out is the in-ecosystem path)          |
| **7** | **Posture composition across multiple humans**           | The brief is team-oriented (3d). When _many_ stakeholders share one objective, how does posture compose across them? (loom uses `min(operator, floor)` + 4-eyes upgrade) | Spec decision (Research 04 §7 item 4) — also touches moat M3                                           |
| **8** | **Posture naming/label unification**                     | Three posture ladders exist with colliding labels; shipping the brief's labels as the engine enum confuses everyone                                                      | Spec decision; adopt canonical enum internally, 3-button UX externally (Research 04 §1.4)              |
| **9** | **Where the cascade engine lives**                       | Framework-level vs. app-level placement affects reuse and the M-series moats                                                                                             | Confirm with framework specialists at design time (Research 06 §8)                                     |

The three at the top (the non-coder UX, the re-run/replay/branch semantics, and cascade cost) are the
ones that decide whether the signature feature is _usable_ by its target audience — not whether it can
be _built_. The engine is the tractable part; the legibility-for-non-coders is the frontier. That is
the honest shape of the bet.

---

## 9. Source ledger

All claims above resolve to one of:

- **`briefs/01-vision.md`** §3e (posture, retrace-and-intervene, versioning), §3f (black-box boundary),
  §4 Decisions A/B — the authoritative requirement surface.
- **`01-research/06-transparency-intervention-versioning.md`** — §0 (80/20 framing), §1 (provenance
  data model), §2 (intervention semantics + branching), §3 (durable execution + the determinism gap),
  §4 (decision surfacing + posture gate), §5 (black-box boundary + OTel conventions), §6 (layer-cake
  synthesis), §7 (the novel 20% + invariants), §8 (risks).
- **`01-research/03-pact-governance.md`** — §2 (D/T/R accountability), §3 (envelopes), §4 (verification
  gradient), §5 (SupervisorOrchestrator / ApprovalBridge / EventBridge / EmergencyBypass /
  EnforcementMode), §6 (the 17 DataFlow models), §8 (critical synthesis: 80/15/5, the two posture
  vocabularies, the facade-heaviness caution).
- **`01-research/04-eatp-trust-posture.md`** — §1 (the canonical L1–L5 ladder + the naming collision +
  the 3-button mapping), §2 (TrustPlane, gradient, BudgetTracker, PostureStore), §3 (HITL/HOTL + the
  keyword-classifier caveat), §4 (set/upgrade/downgrade/anchors), §5 (structural vs execution gates),
  §6 (the synthesis, the three gaps, the recommended posture architecture), §7 (open questions).
- **The strategic spine (Phase A)** — moats M1–M4, the Cowork threat, the "transparency makes depth
  legible" point, the MIT NANDA / Gartner market evidence, Decisions A and B.
- **COC rules** — `recommendation-quality.md` (symmetric pros/cons), `communication.md` (plain
  language), `autonomous-execution.md` (effort in cycles), `tenant-isolation.md`, `orphan-detection.md`
  / `facade-manager-detection.md`, `agent-reasoning.md` (LLM-first), `spec-accuracy.md` (flag, don't
  paper over, uncertainty).
