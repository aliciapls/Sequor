# Plan 01 — System Architecture: The Agnostic Agentic-Work Platform

> **Purpose.** This is the architecture plan for the platform the brief describes — a single,
> agnostic, transparent, team-oriented interface where non-coders get _all_ knowledge work done
> through an AI agent, instead of crossing N siloed vertical systems (ERP → CRM → POS → Excel →
> Word → portals). It turns the analysis layer's conclusions into a decision-grade layered
> architecture and the framework decisions a technical founder can act on: which parts to reuse,
> which to build, where the one runtime decision lives, and how the pieces fit into one data flow.
>
> **Lens.** This plan applies the `decide-framework` discipline: for each layer, name the existing
> ecosystem asset that already delivers it, decide REUSE vs NET-NEW against the 80/15/5 split
> (analysis 08), and recommend — not enumerate — with symmetric pros and cons.
>
> **Audience.** A non-technical founder. Plain language throughout; every technical term is
> translated on first use (per `rules/communication.md`). Effort is in **autonomous execution
> cycles** — work an AI agent system completes in a session — never human-days (per
> `rules/autonomous-execution.md`). Competitors are named factually, never as a product Sequor is
> "a version of" (per `rules/independence.md`).
>
> **Grounding.** Every load-bearing claim cites the brief (`briefs/01-vision.md`), an analysis
> file (`01-analysis/07-transparency-intervention-architecture.md`,
> `01-analysis/08-product-focus-80-15-5.md`), or a research file
> (`01-analysis/01-research/{03-pact-governance,04-eatp-trust-posture,05-cli-harness-universal-interface}.md`).
> Genuine uncertainty is flagged, not smoothed over.
>
> **Value framing this plan builds on.** The _why-it's-worth-building_ layer is established in two
> companion analyses, and this plan's layered architecture is the structural realization of them:
> `01-analysis/02-value-propositions.md` (the enterprise-buyer value claims, each tagged
> PROVEN/credible vs CONTINGENT) and `01-analysis/05-aaa-framework.md` (the three value axes —
> **Automate** removes the hands, **Augment** sharpens the head, **Amplify** clones the expert).
> Where this plan justifies _why a layer earns its place_, it cites the value/AAA source so the
> architecture decision traces back to a buyer-legible value claim, not just a technical one.

---

## 0. The architecture in one paragraph

The platform is **one agent loop, governed and made transparent, reached through a non-coder work
surface, connected to every business system through standard connectors.** The paradigm shift the
brief names (brief §1–§3) is structural: today the _human_ is the integration layer who carries data
across ERP, CRM, spreadsheets and portals; in the platform the _agent_ is the integration layer and
the human states intent and governs. Mechanically that means seven layers stacked from the user down
to the systems of record: a **Work Interface** the non-coder talks to (replacing the developer's
terminal/file/git mental model); an **Orchestration runtime** that runs the reason→act→verify loop
and owns the one decision everything hinges on; a **Governance substrate** (PACT envelopes + EATP
trust postures) that decides what the agent may do and when a human must say yes; a
**Provenance/versioning ledger + cascade engine** that records every step and lets a user rewind to
any past step and recompute only what changed; a **Coordination substrate** for many humans and
agents on one objective; an **Artifact system + cross-org registry** for reusable know-how; and a
**Connector (MCP) layer** that reaches SAP, Salesforce, Workday, Google, email and the rest. The
decisive finding across the analysis: **~80% of this stack already exists** as shipped or specced
ecosystem code (analysis 08 §2); the net-new is concentrated in three places — the non-coder
self-service surface, the rewind/cascade engine, and the untrusted-publisher trust model — and one
early experiment (the runtime-ownership spike) gates whether the strongest moat is buildable at all.

---

## 1. The layered architecture (the map)

The platform is seven layers. The diagram is the spine of this whole plan; every later section
expands one band.

```
┌──────────────────────────────────────────────────────────────────────────────┐
│ L7  WORK INTERFACE  — the non-coder surface (§2)                               │
│     intent box · "here's my plan, pick a posture" · timeline/rewind view ·     │
│     plain-language approval cards · business-object views (not files)          │
│     [BUILD — primary net-new UX; REUSE comms onboarding wizard + PACT web      │
│      objectives/approvals screens as scaffold]                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│ L6  COORDINATION  — many humans + many agents on one objective (§5, M3)        │
│     shared objective · claims/leases · agent↔agent messages as records ·       │
│     gate matrix (who approves what) · per-operator posture                     │
│     [REUSE the human-multiplicity half (loom multi-operator); BUILD the        │
│      agent↔agent message model]                                                │
├──────────────────────────────────────────────────────────────────────────────┤
│ L5  ARTIFACT SYSTEM + CROSS-ORG REGISTRY  — reusable know-how (§6, M4)         │
│     agents/skills/rules/hooks/commands · variant overlays · publish/subscribe  │
│     across orgs · provenance-tracked · recall/obsoletion                       │
│     [REUSE loom splitter wholesale; BUILD cross-org publish + the              │
│      untrusted-publisher trust model (design-first)]                           │
├──────────────────────────────────────────────────────────────────────────────┤
│ L4  PROVENANCE LEDGER + CASCADE ENGINE  — glass box + undo-from-anywhere (§4)  │
│     Step/Output/Decision graph · content-addressed · immutable versions ·      │
│     dirty-propagate + fingerprint-skip + branch timelines                      │
│     [REUSE PACT records + Kailash durable store; BUILD the cascade engine      │
│      (the one load-bearing net-new framework component, M1)]                   │
├──────────────────────────────────────────────────────────────────────────────┤
│ L3  GOVERNANCE SUBSTRATE  — what's allowed, when a human gates (§3, M2)        │
│     PACT envelopes (5-dim) · D/T/R accountability · EATP postures L1–L5 ·      │
│     verification gradient (auto/flag/HELD/block) · BudgetTracker · PostureStore │
│     [REUSE PACT + EATP wholesale; BUILD the plan_proposed gate + LLM-first     │
│      consequentiality classifier]                                             │
├──────────────────────────────────────────────────────────────────────────────┤
│ L2  ORCHESTRATION RUNTIME  — the reason→act→verify loop (§2.4, the pivot)      │
│     main loop · subagent fan-out · context/compaction · two-phase intent/      │
│     outcome signing · THE RUNTIME-OWNERSHIP DECISION lives here                 │
│     [ENVOY HYBRID: own a governed core runtime; gated by an early spike]       │
├──────────────────────────────────────────────────────────────────────────────┤
│ L1  CONNECTOR (MCP) LAYER  — reach any business system as a tool (§7)          │
│     MCP servers (OAuth 2.1) · "tools are dumb endpoints, LLM reasons" ·        │
│     governance sits BETWEEN agent and connector · record vs file model         │
│     [REUSE the MCP protocol + connectors; BUILD the governed curation]         │
└──────────────────────────────────────────────────────────────────────────────┘
```

**How to read it.** A user request enters at L7, the runtime (L2) plans and acts, every action is
checked by governance (L3) and recorded by the ledger (L4); the runtime reaches systems through
connectors (L1); many people and agents share the work through coordination (L6); the know-how that
makes any of it competent lives as artifacts (L5). The numbering is bottom-up by _dependency_ (L1
connectors and L2 runtime are the foundation everything stands on); the _user_ experiences it
top-down (L7 first). This dual ordering is deliberate — see §9 for build sequence, which is neither
purely bottom-up nor top-down.

---

## 2. L7 — The WORK INTERFACE (re-interfacing the harness for non-coders)

### 2.1 What this layer is, in plain language

The developer's agent CLI ("command-line interface" — the text terminal a programmer types into) is
already a domain-agnostic work engine that _happens_ to ship configured for coding (research 05 §0,
§2). It does not need to be rebuilt to do general work; it needs to be **re-interfaced** — the engine
stays, the surface the human touches changes. This layer is that new surface.

### 2.2 What changes from a developer CLI — the three re-interfaces

The brief (§3a–§3c) is explicit: users don't have to be coders, the interface is no longer
restricted to building programs, and it's re-interfaced for _all_ work in one place. Research 05 §3
identifies exactly what must change. Three concrete shifts:

| Developer CLI assumption                              | Non-coder re-interface                                                                                                                                                                                                                               | Why it matters                                                                                                                                                                                | Source                                  |
| ----------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------- |
| **The user types commands in a terminal**             | An **intent surface** — a plain box where the user states an outcome ("I want the 3Q financial report"), plus a live timeline showing what the agent is doing. The terminal is the engine _behind_ a conversational surface, not the surface itself. | A terminal is "a coder's native habitat and a non-coder's wall" (research 05 §3.1). The comms wedge already proves the surface can be email/chat-first with no separate app (analysis 08 §3). | research 05 §3.1; brief §3a–§3c         |
| **The unit of work is a _file_; versioning is _git_** | A **business-object/record model** (a purchase order, an opportunity, a ticket) reached through connectors, and a **work timeline** the user can rewind (L4), not a git branch graph they must understand.                                           | Business work's unit is a record in a system of record, not a file (research 05 §3.2). Git is hard for _programmers_; a non-coder cannot be asked to "rebase" (analysis 07 §1, §10).          | research 05 §3.2–§3.3; analysis 07 §5.2 |
| **Permission prompts are per-tool-call and binary**   | **Posture chosen beforehand, per objective** — three plain buttons ("Go ahead" / "Ask me once" / "Step through with me") that decide how much rein the agent gets for _this_ job.                                                                    | The harness's permission modes are coarse and developer-framed — structurally inadequate for graduated, intervenable trust (research 05 §2, §3.5).                                            | research 05 §3.5; analysis 07 §4.2      |

### 2.3 Business-system connectors at the surface

The user never configures a connector by writing code. They pick which systems to plug in from a
list ("connect my Gmail, my Salesforce, my company drive") — exactly the way the comms wedge's
onboarding wizard already lets a non-technical person choose channels in under 10 minutes with no app
(analysis 08 §3, research 09 cited there). The wiring underneath is the MCP connector layer (L1, §7);
at _this_ layer it is a selection surface, part of the 15% self-service band (analysis 08 §3).

### 2.4 Recommendation for L7

**BUILD the non-coder self-service surface as the primary net-new UX, reusing the comms onboarding
wizard and PACT's web objectives/approvals screens as scaffold.** This is where the bulk of net-new
UX work lives (analysis 08 §6.1; research 04 §6.2 Gap B: "multiple sessions"). This layer is the seat
of the platform's primary value claim — the **Automate** axis ("the agent becomes the integration
layer the human used to be," analysis 05 §1.2), which is the buyer-facing answer to "what's actually
different here?" (analysis 02 §0.2). The surface is built here precisely because that value cannot be
delivered to a non-coder without it.

- **Pros:** directly attacks the documented #1 failure mode (analysis 08 §1 — MIT NANDA: ~95% of
  enterprise GenAI pilots fail because generic tools "don't learn from or adapt to workflows"); the
  engine underneath is shipped, so this is a _surface_ build not an _engine_ build; the comms wizard
  de-risks the pattern against real users.
- **Cons (real):** non-coder configuration depth is exactly where no-code tools historically die — at
  "the last 20%" of any company's process (analysis 08 §3.1, §7). A wizard that handles 90% but needs
  an engineer for the final 10% is a wizard customers stop trusting. **Mitigation:** pair this surface
  _tightly_ with the L4 transparency/rewind — when the configured process runs, the user can see every
  step and intervene, which makes the un-configured 10% legible and fixable in-flight rather than
  silently wrong (analysis 08 §3.1; analysis 07 §7.2 "transparency makes depth legible").

---

## 3. L3 — The GOVERNANCE substrate (PACT + EATP) — moat M2, ship first

> Placed before L2 in the prose because governance is the most-proven, lowest-risk, ship-first moat
> (strategic spine: "M2 most-proven, ship first") and because the runtime decision (L2, §2.4 of the
> diagram) is better understood _after_ the reader sees what governance demands of it.

### 3.1 What this layer decides

Governance answers one question structurally, before any action runs: _is this agent, in this
objective, allowed to take this action right now — and if not, who has to say yes?_ (research 03 §1).
This is moat **M2**: governance set **beforehand, per objective**, not bolted on as after-the-fact
observability (analysis 07 §4).

### 3.2 The pieces, all of which already ship

| Capability (plain language)                                                                                                                          | Existing asset                                                                                                              | What it gives the platform                                                                                                     | Source                             |
| ---------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------- |
| **Permission envelope** — the 5-dimension box an agent works inside (money, allowed actions, time windows, what data it can touch, what it can send) | PACT `ConstraintEnvelopeConfig` + monotonic tightening (a sub-agent can only get a _tighter_ box, never wider)              | "A manager with $50K can delegate $10K but not $75K" — the structural budget/scope guarantee                                   | research 03 §3                     |
| **Accountability for free** — every agent (and every spun-up sub-agent) carries a computable chain of the humans answerable for it                   | PACT D/T/R address grammar (`accountability_chain`)                                                                         | "Every step is traced to a human" is _computed from the address_, not a UI afterthought                                        | research 03 §2                     |
| **Trust postures L1–L5** — how much the agent does alone, chosen beforehand                                                                          | EATP `PostureStateMachine` + `PostureStore` (3 independent shipped implementations)                                         | The per-objective "Go ahead / Ask me once / Step through" control                                                              | research 04 §1, §2.4               |
| **The verification gradient** — every action is auto-approved, flagged, HELD (paused for a human), or blocked                                        | PACT/EATP 4-level gradient                                                                                                  | The structural answer to "surface decisions on screen, intervene"                                                              | research 03 §4.2; research 04 §2.2 |
| **Pause-and-ask-a-human** — a soft-limit breach becomes a paused, on-screen, human-gated decision                                                    | PACT `SupervisorOrchestrator` → HELD callback → `ApprovalBridge` → approval queue                                           | "The agent asks for one permission before executing," realized in shipped code (the `return False` in `_PlatformHeldCallback`) | research 03 §5.1, §5.2             |
| **Decisions streamed to screen live**                                                                                                                | PACT `EventBridge` (WebSocket — a persistent two-way browser channel)                                                       | "These decisions are surfaced on screen," substantially built                                                                  | research 03 §5.3                   |
| **Cost ceilings per objective** with 80%/95%/exhausted alerts                                                                                        | EATP `BudgetTracker` (integer microdollars, crash-safe)                                                                     | A ready-made cost progress widget per objective                                                                                | research 04 §2.3                   |
| **Emergency break-glass, still auditable**                                                                                                           | PACT `EmergencyBypass` (tiered 4h/24h/72h, can't grant more than the approver holds, aborts if it can't write an audit row) | The accountable emergency path                                                                                                 | research 03 §5.4                   |
| **Safe rollout under the live product**                                                                                                              | PACT `EnforcementMode.SHADOW` (observe what _would_ be held/blocked; never block)                                           | Turn governance on under the comms wedge without breaking it                                                                   | research 03 §5.5                   |

### 3.3 The L5/L4/L3 ladder and the naming trap

The brief's three levels map onto the EATP posture machinery, which is already built — but the labels
collide. The brief calls L4 "Supervised," yet in the shipped engine "Supervised" is a _lower_ level
where the human approves _every_ action (research 04 §1.4). Shipping the brief's labels as the
engine's internal names would confuse every engineer who knows the existing system.

**Recommendation (research 04 §1.4, §6.4; analysis 07 §4.2):** keep the **canonical EATP enum as the
internal source of truth** (it is the shipped, persisted, signed primitive) and present **three
plain-language buttons** on top of it. The user never sees `L5_DELEGATED`; they see:

| User-facing button                        | Internal engine posture | Per-step behaviour                                                          | Human's relationship                                        |
| ----------------------------------------- | ----------------------- | --------------------------------------------------------------------------- | ----------------------------------------------------------- |
| **"Go ahead"** (Autonomous)               | `AUTONOMOUS` (5)        | Auto-approve within the envelope; anything outside it is blocked            | **HOTL** — human watches, can abort, doesn't gate each step |
| **"Ask me once"** (One check)             | `DELEGATING` (4)        | Auto-approve within the envelope; **one** gate at the plan→execute boundary | **HOTL + one gate**                                         |
| **"Step through with me"** (Step-by-step) | `SUPERVISED` (3)        | Every consequential action pauses for approval                              | **HITL** — human is a blocking node inside the path         |

**HITL = "human in the loop"** (the agent can't proceed past a consequential action without the
human); **HOTL = "human on the loop"** (the agent proceeds; the human observes and can abort). The
crucial mechanism: **the posture level _is_ the choice between HITL and HOTL** — it is not a separate
control (research 04 §3). The safety floor is `min(user-chosen, system-floor)`: the user opts _up_
toward autonomy, but the system auto-_downgrades_ on detected problems (upgrades human-gated,
downgrades automatic — the "Mirror Thesis," research 04 §4.2). This is why "Go ahead" is safe to
offer: it is a ceiling the system can lower the instant something looks wrong, not a blank cheque.

### 3.4 The one reuse caution and the two net-new pieces

**Caution (LLM-first, non-negotiable per CLAUDE.md Directive 6 / `agent-reasoning.md`):** PACT's
shipped code decides "is this action consequential?" by **matching keywords** (`write`, `send`,
`delete`…). The platform's own rules forbid keyword/regex routing in agent decision paths. The
platform MUST replace that keyword classifier with an **LLM-judged** consequentiality assessment —
keeping PACT's _verdict_ machinery (pause/block/auto-approve) but not its keyword decision path
(research 04 §3; analysis 07 §4.4). Research calls this "a small, well-scoped rewrite, not a
re-architecture," but flags the latency/cost of an LLM call on every action as an open question (§8
unknown #4).

**Net-new (small):** (1) a `plan_proposed` decision _subtype_ that surfaces the agent's fan-out plan
itself as the approvable object _before_ execution (the brief's "agent decides to spin up 3 agents →
surfaced on screen → user picks a posture beforehand"), estimated ~1 cycle of integration (analysis
07 §4.1); (2) the LLM-first classifier above.

### 3.5 Recommendation for L3

**REUSE the PACT engine and EATP posture machinery wholesale; the net-new is the `plan_proposed`
gate and the LLM-first classifier. Roll in under SHADOW mode.** This layer's split tracks the
platform-wide canonical 80/15/5 ratio (analysis 08 §1): for L3 specifically, ~80% reuse / ~15% glue /
~5% new (research 03 §8.5).

- **Pros:** shipped end-to-end with a web dashboard (research 03 §5); three independent posture
  implementations to draw on (analysis 08 §2 row 3); SHADOW mode makes rollout safe.
- **Cons (real):** **PACT is a facade-heavy codebase** (managers, bridges, stores). Reusing it risks
  shipping governance that _never executes_ on the hot path — the exact Phase-5.11 orphan failure the
  `orphan-detection.md` / `facade-manager-detection.md` rules exist to prevent (research 03 §8.5;
  analysis 08 §6.2). **Mitigation is structural and mandatory:** every governance manager wired into
  the data path needs a real call site _plus_ a Tier-2 integration test proving the framework actually
  calls it — or the security promise is a silent no-op.

---

## 4. L4 — The PROVENANCE/VERSIONING ledger + CASCADE engine — moat M1, lead the story

### 4.1 What this layer is, in plain language

When an AI does a piece of work today you get the _answer_ and almost nothing else — you can't see
why it did what it did, you can't change one decision three steps back without redoing everything, and
when you redo it the old version is gone (analysis 07 §0). This layer makes agentic work a **glass box
with an undo-from-anywhere button**: every input, decision, tool call, result and output is recorded
and shown; you rewind to any past step, change an input or override a decision, and _only the parts
that actually depend on your change recompute_ — while the previous results survive as named versions
you can compare and return to. This is moat **M1** — the strongest moat and the hardest build
(strategic spine; analysis 07 §1).

### 4.2 The transparency contract — drawing the line crisply

The single most important thing this layer does is define the boundary precisely, because a fuzzy
boundary is a broken promise (analysis 07 §2). **Recorded and surfaced (the glass box):** inputs;
the agent's decisions/plans/fan-outs; every tool call and its arguments; every tool result; every
output; and metadata (model, cost, time, _and the posture in force when the step ran_). **The black
box (deliberately not recorded):** the model's internal chain-of-thought, activations, and
token-level reasoning — because no one, not even the model's maker, can faithfully record it
(analysis 07 §2.1–§2.2). The defensible boundary, stated exactly: _we record everything the model
emits at its input/output surface — including any reasoning summary it chooses to surface — and we do
not record, and do not claim to record, how the model actually computed its answer internally._

**The honesty caveat that must travel with every trust claim** (analysis 07 §2.3; research 03 §2.3;
research 04 §2.2): the system delivers **traceability, not accountability.** Traceability (the machine
guarantees this) = every AI action traces back to its inputs, decisions, and the human authority that
permitted it. Accountability (no software can guarantee this) = a human actually _understood_ and
bears the consequences. The glass box makes understanding _possible_; it cannot force it.

### 4.3 The data model — the provenance ledger

The ledger is a **graph** (records connected by typed relationships) with three node kinds, each
mapping onto an existing PACT model (analysis 07 §3.1; research 03 §6.1–§6.2):

- **Step** (PACT `Run`) — one invocation (one model call, one tool call, one workflow run). Immutable.
- **Output** (PACT `AgenticArtifact`) — one produced result, with `version` + `parent_output_id`. A
  new version is a new row, never an overwrite.
- **Decision** (PACT `AgenticDecision`) — a surfaced choice (a fan-out plan, a held action, a posture
  gate). Resolving it creates a new linked record, never an edit.

Edges: `Step --consumes/produces--> Output`, `Step --depends_on--> Step` (the dependency that drives
recompute — PACT's `AgenticRequest.depends_on`), `Step --gated_by--> Decision`, `Output
--derived_from--> Output` (the version chain).

**The load-bearing trick is "content-addressing"** (analysis 07 §3.2): every Step and Output is
identified by a _fingerprint of its content_ (a SHA-256 hash that changes completely if one byte
changes), not a sequential ID. This is how Git stores commits and IPFS stores files. It buys three
things at once: tamper-evidence for free (an altered record no longer matches its fingerprint —
exactly the aegis signed-anchor property, research 04 §4.5); cheap branching (a "what-if" fork reuses
all unchanged history _by reference_ — only the changed part is new data); and the "only recompute
what changed" guarantee (a step's identity is `hash(inputs + code + fingerprints of upstream steps)`,
so identical inputs produce identical identity and the engine can skip the re-run and reuse the cached
result — the mechanism behind build systems like Bazel).

**The ledger is the source of truth; live telemetry feeds it** (analysis 07 §3.3): the
OpenTelemetry-shaped spans streaming to the screen are the ephemeral live feed; the content-addressed
ledger (backed by PACT DataFlow models + the Kailash durable store) is the permanent record. Spans
write into the ledger; this avoids the "two databases that disagree" problem.

**Six invariants the ledger must always hold** (analysis 07 §3.4; each is a tracked invariant for
sharding per `autonomous-execution.md`): (1) **immutability** — a re-run appends, never alters; (2)
**tenant isolation** — every fingerprint, cache key and graph query carries the customer's
`tenant_id`, or it's a cross-customer leak (per `tenant-isolation.md`; the comms wedge already does
schema-per-tenant); (3) **determinism boundary** — model steps reuse the recorded output by
fingerprint on rewind _unless_ the user explicitly asks to regenerate; (4) **cascade minimality** —
a downstream step whose recomputed inputs are unchanged MUST be skipped; (5) **posture-at-time** —
every Step records the posture in force when it ran; (6) **audit completeness** — the intervention
itself is auditable (who rewound, what they changed, when).

### 4.4 The cascade engine — the genuinely new core

This is the heart of the product and the only mostly-net-new piece (analysis 07 §5). It borrows from
**reactive computational notebooks** (tools that, when you change one cell, auto-re-run only the cells
that depend on it) layered over the content-addressed graph. The flow when a user rewinds to Step N
and changes an input:

1. A _new_ Step N′ is created with a new inputs-fingerprint. Old Step N and its Output are untouched
   — they remain a prior version ("old outputs are versioned").
2. **Dirty-marking:** the engine walks all descendants of N and marks them "potentially needing
   re-run" (the descendant walk already exists in Kailash's `WorkflowDAG`).
3. **The "only affected downstream" guarantee:** for each dirty step, recompute its inputs-fingerprint
   from its (possibly unchanged) upstream. If the new fingerprint equals the recorded one, **skip and
   reuse the cached output**. Only genuinely-changed steps re-run; a step whose other inputs dominate
   may produce an identical result and **halt the cascade early**.
4. **Versioning:** each re-run output is a new version with a back-pointer; nothing is overwritten.

The combination — dirty-propagation (from notebooks) + fingerprint-skip (from build systems) — is
precisely "downstream cascades re-execute, but only the affected ones, and old outputs survive." This
is a **~20% novel composition, not an 80% greenfield build**: the hard primitive (content-addressed
memoization) already ships in Kailash for crash-recovery, idempotency, and within-run skipping; the
new work generalizes its scope from "within one run" to "across runs, keyed on content fingerprint"
(analysis 07 §5.1, §6.1).

**The hard problem, addressed honestly — non-determinism** (analysis 07 §5.3): model steps don't
produce the same output twice. "Rewind and re-run" has three distinct meanings the engine must
separate: **Re-run** (the user changed an input — re-execute affected downstream; model steps _may_
legitimately differ, which is correct); **Replay** (show exactly what happened last time — reuse the
recorded answer by fingerprint, do not call the model again — fully deterministic); **Branch** (try a
different path without losing the original — fork a new timeline). The design decision that makes this
work: on rewind, the engine **reuses the recorded output by fingerprint for every step the user did
not touch**, re-generates only what they changed, and **never assumes a model call replays
identically** — surfacing the choice "re-run with my edit / keep the recorded output" as an explicit,
per-step product decision, because guessing wrong silently is the worst outcome.

### 4.5 Recommendation for L4

**Stand up the provenance ledger by unifying the PACT records + Kailash durable store + OpenTelemetry
recording into one content-addressed graph (mostly wiring). Build the reactive cascade engine as the
single net-new framework component. Place it as a framework-level module operating over the DataFlow
models + WorkflowDAG — not inside the Sequor app — so the horizontal capability is reused and the
wedge consumes it.** (analysis 07 §7.1, §7.2; analysis 08 §6.1 row "Provenance/versioning".)

- **Pros:** the records, the durable store, and the I/O-recording standard all ship; the cascade
  engine has a _live feedback loop_ (each cascade is testable against a fixture graph), so it can run
  at higher budget per `autonomous-execution.md`; it is the strongest moat and the structural answer
  to the market's documented failure mode.
- **Cons (real):** **storage grows without bound** under immutable versioning unless a
  retention/compaction policy is built (content-addressing dedupes identical bytes but not version
  count — analysis 07 §7.3, §8 unknown #5); a change near the root of a wide graph can legitimately
  invalidate everything downstream, so a **cost-preview before committing a cascade** is needed
  (analysis 07 §8 unknown #3); and the non-coder versioning/branching UX is genuinely unsolved (the
  dominant risk — §8 below).

**Sizing:** an end-to-end working rewind-and-intervene over the comms-wedge 4-step flow is estimated
at **~4–6 autonomous execution cycles**, because the substrate (the ledger, governance, the event
stream, the posture machine, the durable store) is reused rather than rebuilt; the cascade engine
itself is ~1–2 cycles (analysis 07 §6.3; analysis 08 §6.1).

---

## 5. L6 — The COORDINATION substrate (multi-human + multi-agent) — moat M3

### 5.1 What this layer is

The brief is team-oriented (§3d): the interface disrupts _team communication_ too, on the hypothesis
that human-to-human communication is "incomplete, inefficient, and easily misconstrued" compared with
the memory and context agents can use when instructing other agents. This layer is the shared
substrate that lets many humans and many agents work one objective safely.

### 5.2 What's reused vs net-new

**REUSE the human-multiplicity half wholesale.** The loom multi-operator coordination substrate
already ships: a signed, hash-chained coordination log; claims/leases over paths and work scopes; a
SAME/ADJACENT/INDEPENDENT adjacency relation that decides whether two operators collide; a gate matrix
enforcing distinct-person approval (4-eyes); and per-operator posture as `min(operator, repo_floor)`
(analysis 08 §2 row 8; research 05 §6.1; `rules/multi-operator-coordination.md`). The harness vendors
are themselves moving toward this surface (research 05 §1.3 notes parallel multi-session "agent teams"
features), which validates the direction but does not give the governed substrate.

**BUILD the agent↔agent message model.** The existing coordination substrate routes _work_ and
coordinates _humans_; it does not yet model inter-agent _messages_ as first-class, surfaced,
interveneable records (research 03 §8.4 item 4 — a new `AgenticMessage`-style model + an EventBridge
hook, ~1 session). This is what makes the brief's §3d hypothesis _testable_ — but it remains a
hypothesis, not a USP. **Caution carried from the analysis (analysis 08 §7 item 6; strategic spine):**
"agent-comms beats human-comms" is an unproven, contrarian research bet. The platform MUST NOT stake
its value proposition on it; the substrate gives a place to test it.

### 5.3 The open design decision

Posture composition across _many_ stakeholders on one objective is unresolved: loom uses
`min(operator, floor)` + 4-eyes upgrade for a small team; an enterprise objective with many human
stakeholders needs a spec decision on how posture composes across them (analysis 07 §8 unknown #7;
research 04 §7 item 4). Flagged for the spec phase; touches M3.

### 5.4 Recommendation for L6

**REUSE the loom multi-operator substrate for the human-multiplicity half; BUILD the agent↔agent
message model as the differentiator, treating the "agent-comms beats human-comms" thesis as a
hypothesis to test, never as a promise.** Pros: the hard concurrency/identity/gate machinery ships;
agent↔agent messaging is ~1 cycle. Cons: the underlying thesis is unproven (3-day brief estimate per
the spine), and a multi-replica deployment needs a durable/distributed event bus — PACT's current
`EventBus` is single-process in-memory (analysis 07 §8 unknown #6; the in-ecosystem path is the
`SQLTaskQueue` or a Redis fan-out).

---

## 6. L5 — The ARTIFACT system + CROSS-ORG registry — moat M4 (the network-effects engine)

### 6.1 What this layer is

"Artifacts" are the unit of reusable know-how: **agents** (judgment + procedure), **skills**
(knowledge + reference), **rules** (guardrails), **hooks** (deterministic gates), **commands**
(workflow orchestration). All five layers are domain-agnostic — "judgment + procedure" and "knowledge
packaging" are any-domain, not coding-specific (research 05 §1.2). The brief (§3g) wants artifacts
"easily created, modified, stored, and shared across organizations and teams." This is moat **M4** —
the network-effects engine, because a published/consumed work-artifact is the platform's primary
transaction (strategic spine).

### 6.2 What's reused vs net-new

**REUSE the loom splitter wholesale.** loom already ships the five-layer artifact system with variant
overlays (per-company/per-language overrides), a two-gate `/sync` distribution to 30+ downstream
consumers, a proposal lifecycle, and obsoletion/recall (analysis 08 §2 rows 2 and 10; research 05
§1.2). Brief §3g is _literally already built_ — for coding artifacts. The re-interface is to carry
_business-domain_ agents/skills/rules instead of coding ones (~1 session of mechanical
manifest/overlay work — analysis 08 §6.1 row "Artifact system").

**BUILD cross-org publish/subscribe + the untrusted-publisher trust model.** loom's existing trust
model is _bounded-trust_ — "the adversary is a legitimate team member with repo write access" — but a
cross-_company_ marketplace faces _untrusted publishers_ whose artifacts must be signed,
provenance-tracked, and recallable _without trusting the publisher_ (analysis 08 §4.1, research 01 §7c
cited there). loom already ships the crypto substrate (commit-signing keys, a hash-chained log, 2-of-N
quorum, server-side rulesets, disclosure-scrub on intake, the obsoletion/recall primitive); the
genuinely-new piece is signed-artifact provenance from an _external_ publisher plus marketplace-grade
licensing/attribution.

### 6.3 The critical clarification and sequencing

The untrusted-publisher trust model is **a one-time core build, not per-client custom work** — it
belongs conceptually in the 80% (built once, every client inherits cross-org sharing for free), but
it is _genuinely new_ rather than already-existing, so it sits at the 5% boundary (analysis 08 §4.1).
The reason to call it out: prevent the costly misclassification of treating "trust for external
publishers" as re-solved per engagement.

### 6.4 Recommendation for L5

**REUSE the loom control plane for the artifact system; DESIGN the untrusted-publisher trust model
FIRST, then BUILD the cross-org registry — and design the trust model before the registry surface,
because it constrains the registry.** Ignite network effects **within-org first**, then cross-org
after the trust model is designed (strategic spine; analysis 08 §6).

- **Pros:** the splitter, variant overlays, and recall all ship; the within-org loop is already live
  in the comms wedge (knowledge-contribution loop); cross-org is the adapt layer on top.
- **Cons (real):** the untrusted-publisher model is greenfield novel architecture (first-session
  ~2–3× factor per `autonomous-execution.md`) and it gates the entire registry, so a wrong call is
  expensive to unwind (analysis 08 §4.1, §7 item 3). Registry surface ~3–5 cycles _after_ the trust
  model is designed.

---

## 7. L1 — The CONNECTOR (MCP) layer

### 7.1 What this layer is

MCP ("Model Context Protocol" — the now-standard way an agent reaches an external system as a tool)
is the universal connector. The single most important fact for the whole platform: **the same
protocol that connects the harness to `git` and `filesystem` today connects it to SAP, Salesforce,
Workday, and NetSuite tomorrow** (research 05 §1.4). MCP servers are OAuth 2.1 resource servers;

> 1,000 connectors existed by early 2025; enterprise vendors (Salesforce, Snowflake, Atlassian,
> Google) increasingly ship their own (research 05 §5.1). The connector substrate is _not_
> coding-specific.

### 7.2 The keystone discipline — "tools are dumb endpoints, the LLM reasons"

The platform's strongest design conviction maps perfectly onto MCP (research 05 §5.2, citing
`rules/agent-reasoning.md`): an MCP tool MUST be `get_order(id) → record`, NOT
`handle_order_issue(...)` with `if order.status == "delivered": process_return()`. **Decision logic
buried in tool code is invisible to the LLM's reasoning trace** — unexplainable, untestable,
un-improvable. This is _the_ enforcement that makes the L4 transparency contract possible: if all
reasoning lives in the LLM (whose input/output is logged) and tools only move data (also logged), then
everything except the model's internal cognition is transparent — exactly the brief's §3f claim. It is
also a competitive differentiator: many enterprise "AI agents" bury business logic in tool code; the
platform's rule forbids it, which is what _enables_ the intervenable surface.

### 7.3 Governance sits between the agent and the connector

The "tools are dumb" principle plus the intervention requirement means an enforcement point _between_
the LLM's tool request and the actual ERP/CRM write — which is exactly L3's `ApprovalBridge` + HELD
pattern (research 05 §5.3). A HELD verdict blocks the write until a human approves; this is how
"governed connectivity" (the differentiator) is realized, versus raw connectivity (a commodity).

### 7.4 The open architectural decision — record model vs virtual files

Whether business objects should be surfaced _as files in a virtual file system_ (so the harness's
existing file tools work unchanged) or _as a distinct record-tool API_ is an open, consequential
question; both are viable and neither is yet specced (research 05 §3.2, §6.4). Flagged for the spec
phase.

### 7.5 Recommendation for L1

**REUSE the MCP protocol and the existing connector ecosystem; BUILD the governed curation — wrap
each connector in the "dumb endpoints" discipline and put governance between agent and connector.**
Pros: MCP is standard and >1,000 connectors exist; connector porting is boilerplate-heavy and scales
~5× further before sharding triggers (analysis 08 §6.1 row "MCP connector framework"). Cons:
connectivity is a commodity — only _governed_ connectivity differentiates, so the connector work is
only valuable when the governance-between-agent-and-connector ships with it (analysis 08 §7 item 4);
and a system with no existing MCP server is genuine 5% custom until that server exists (analysis 08
§4).

---

## 8. L2 — The ORCHESTRATION RUNTIME and the RUNTIME-OWNERSHIP DECISION (the pivot)

> This is the one decision everything hinges on (analysis 08 §6.3; research 05 §4). It is placed last
> in the prose because its right answer is only clear after seeing what L3 (governance) and L4
> (transparency/intervention) demand of the loop.

### 8.1 What the runtime is

The runtime is the **reason→act→verify loop** — the engine that gathers context, takes an action,
checks the result, and repeats — plus subagent fan-out, context management/compaction, and (the part
that matters here) **two-phase signing**: recording _intent before the action_ and _outcome after_,
both signed (research 05 §1.1, §4.2). This loop is domain-neutral; the coding-specificity lives
entirely in the tools and artifacts layered on top (research 05 §2). The single coding advantage that
does _not_ transfer cleanly is the **compiler/test as free, instant ground truth** — most knowledge
work has no compiler, which is _why_ the transparency/intervention/posture stack (L3+L4) is
load-bearing for correctness, not just polish (research 05 §2, §6.2).

### 8.2 The decision, framed plainly

The question is **not** "build speed vs cost." It is: **can the brief's transparency + intervention +
versioned-replay requirement (§3e–§3f) be satisfied without owning the loop?** (research 05 §4.4).

- If harness introspection is enough → the platform can sit _on_ existing harnesses (lower build cost,
  but `rules/independence.md` forbids _depending_ on a proprietary SDK, and you don't control the
  loop).
- If not — if you must record intent before action, gate on posture, and replay from any prior step
  with downstream re-derivation — then that is a _runtime_ capability, which implies owning a runtime
  abstraction.

The evidence tilts toward "own the governed core's runtime": **envoy** — the sister project that most
directly tackles "autonomous AI where you set the boundaries" — chose to own its runtime via a
`KailashRuntime` abstraction precisely so two-phase signing and intervenable replay are native, not
bolted on (research 05 §4.2). The commercial harnesses' permission modes are binary and per-call, not
intent-staged (research 05 §3.5). But the brief defers the recommendation to plans (Decision B), so
this plan surfaces the criterion and recommends the spike rather than pre-deciding the engine.

### 8.3 The envoy-hybrid recommendation

**Recommend the envoy-hybrid: OWN the _product_ runtime for the governed core (so transparency,
two-phase intent/outcome signing, posture gating, and intervenable replay are _native_), built on
Kailash-native frameworks — Kaizen for the LLM-first agent loop, Nexus for the multi-channel surface,
PACT+EATP for governance, DataFlow for data — while continuing to _develop the product itself_ using
the commercial CC/Codex/Gemini harnesses (via loom), exactly as envoy already does.** (research 05
§4.3 hybrid; §7.4.)

This is **not** "build on a commercial harness" (option A — blocked in its pure form by
`independence.md` and by the difficulty of retrofitting intervene-at-any-step onto a closed loop) and
**not** "multi-harness parity layer" (option B — perpetual parity tax, lowest-common-denominator
governance because Codex has no native hooks, and no control of the loop on any harness). It is option
C _for the governed core_ with A/B _for development tooling_ (research 05 §4.3).

**The gating spike (do this first).** Before committing the assembly, run one early experiment to
resolve §8.2's criterion: **can harness introspection satisfy the transparency + intervention +
versioned-replay requirement, or must the loop be owned?** This is the highest-leverage early
experiment because it determines whether M1 (the strongest moat) is buildable at all (analysis 08
§6.3). A failed spike costs one session, not a program. The honest expectation: the evidence tilts
toward "own the loop," and envoy already chose exactly this — but the spike converts the tilt into
evidence before the build commits.

- **Pros of the envoy-hybrid:** full control of the loop → M1/M2 are native, not retrofitted;
  Foundation-independent (no proprietary dependency — satisfies `independence.md`); the entire DNA
  (PACT models, the posture machine, the artifact distributor, the durable store) plugs directly into
  a loop you own; one multi-channel surface for non-coders via Nexus.
- **Cons (real):** highest build cost of the three options — you reimplement context management,
  compaction, and subagent orchestration that the commercial SDKs give for free; **Kaizen/Nexus
  maturity at harness scale for this exact use case is unproven** (uncertainty flag — needs the spike;
  research 05 §6.4); slowest to a first working demo; and you carry the model-adapter + provider-risk
  surface yourself (research 05 §4.3, §6.4). **Mitigation:** the comms wedge ships on the existing
  deployed stack and provides a revenue-bearing landing vertical _while_ the governed runtime is
  built (analysis 08 §6.2).

---

## 9. One objective, end-to-end (the data flow through all seven layers)

Trace the brief's own example (§3e) through the architecture. The user has chosen posture **"Ask me
once"** beforehand.

```
[L7 WORK INTERFACE]
 1. User types intent: "I want a 3Q financial report."  Posture: "Ask me once."
        │
        ▼
[L2 RUNTIME]  forms a plan: fan out 3 sub-agents (revenue, costs, cash-flow).
        │   The plan is captured as a `plan_proposed` Decision (L4) BEFORE anything runs.
        ▼
[L3 GOVERNANCE]  posture "Ask me once" → ONE approval gate at plan→execute.
        │   Plan streamed to screen via EventBridge; user sees the fan-out diagram.
        ▼
[L7]  User approves the plan once.  (Accountability: each sub-agent carries a D/T/R
        │   address whose chain names the humans answerable for it — L3.)
        ▼
[L2 RUNTIME → L1 CONNECTORS]  each sub-agent runs as a chain of Steps. The revenue
        │   sub-agent calls an MCP tool: get Q3 revenue from the ledger system.
        │   Tools are dumb endpoints; the LLM does the reasoning (L1 keystone).
        ▼
[L3 GOVERNANCE]  every consequential action checked against the envelope + gradient.
        │   Within budget/scope → auto-approve. BudgetTracker accrues cost; 80% alert armed.
        ▼
[L4 LEDGER]  every input, tool call, tool result, decision, and output is recorded as a
        │   content-addressed Step/Output, streamed live to the screen, fingerprinted, version 1.
        ▼
[L2 RUNTIME]  the 3 sub-outputs are assembled into the final report Output (also versioned).
        │
        ▼
[L7]  User reviews. Spots a wrong exchange-rate assumption two steps back in the revenue section.
        │
        ▼
[L4 CASCADE]  User rewinds to that Step (reads the ledger graph — L4), sees exactly what it
        │   consumed and produced (transparency contract — L4), and changes the assumption.
        │   → new Step N′; dirty-mark descendants; recompute ONLY the revenue sub-agent's
        │     downstream + the final report. Costs and cash-flow sub-agents are UNTOUCHED
        │     (their fingerprints match → skipped). User is asked: re-generate the revenue
        │     model step with the new assumption, or keep the recorded output and only
        │     re-flow downstream? (re-run vs replay — L4 §4.4)
        ▼
[L4 VERSIONS]  original revenue section + report survive as version 1; corrected ones are
        │   version 2 with a back-pointer. User compares v1 vs v2 side by side; can revert.
        ▼
[L4 AUDIT]  the intervention itself is recorded: user X changed the exchange-rate assumption
            at Step N at time T (invariant 6 — audit completeness).

[L6 COORDINATION]  throughout, if a teammate shares this objective, their claims/leases and
                   per-operator posture compose; agent↔agent messages are surfaced records.
[L5 ARTIFACTS]     the company's "how we build the 3Q report" know-how is a reusable artifact;
                   a correction the user makes can be codified back into it (within-org loop).
```

Every numbered step is grounded in an existing primitive **except** the cascade in the rewind step and
the timeline/version UI — which is exactly the 80/20 split this plan keeps returning to (analysis 07
§5.4).

---

## 10. What is REUSED vs NET-NEW (the 80/15/5 picture)

Per analysis 08, the platform is overwhelmingly **assembly and re-pointing, not invention**. The
single most important caveat, carried throughout: "80% exists" is true at the level of _primitives_; a
primitive is not a finished product, and the glue + the net-new 5% carry the real cost and the real
moat (analysis 08 §0, §7). The reuse/net-new split below is the _cost_ picture; the _value_ picture it
maps onto is the AAA frame — the reused 80% engine delivers **Automate**, the L3/L4 governance and
transparency layers deliver **Augment** (the decision layer where there is no compiler), and the L5
artifact registry delivers **Amplify** (analysis 05 §0; analysis 02 §0.2). The 5% that is genuinely
new is exactly where the defensible value concentrates.

### 10.1 The 80% — agnostic core, REUSE

| Layer                 | Reused asset                                                                               | Disposition                                      | Source                 |
| --------------------- | ------------------------------------------------------------------------------------------ | ------------------------------------------------ | ---------------------- |
| L2 runtime (loop)     | Kaizen-native loop / harness loop                                                          | **REUSE** (own the governed core's runtime — §8) | research 05 §1.1, §4.2 |
| L3 governance         | PACT engine (envelopes, gradient, ApprovalBridge, EventBridge, EmergencyBypass, 17 models) | **REUSE wholesale**                              | research 03 §5–§6      |
| L3 posture            | EATP `PostureStateMachine` + `PostureStore` + `BudgetTracker`                              | **REUSE** (re-key agent→objective, ~1 cycle)     | research 04 §2, §6     |
| L4 records            | PACT `Run`/`AgenticArtifact`/`AgenticDecision` + Kailash durable store + OTel recording    | **REUSE the records**                            | analysis 07 §3, §6.2   |
| L5 artifacts          | loom five-layer system + variant overlays + splitter                                       | **REUSE + adapt** (~1 cycle)                     | analysis 08 §2 row 2   |
| L6 coordination       | loom multi-operator substrate (claims, leases, gate matrix)                                | **REUSE the human-multiplicity half**            | research 05 §6.1       |
| L1 connectors         | MCP protocol + OAuth 2.1 + >1,000 connectors                                               | **REUSE the protocol**                           | research 05 §1.4       |
| transparency boundary | OpenTelemetry GenAI conventions (industry standard)                                        | **REUSE the standard**                           | analysis 07 §2.1       |
| safe rollout          | PACT `EnforcementMode.SHADOW`                                                              | **REUSE**                                        | research 03 §5.5       |
| comms-wedge spine     | confidence routing, AuditEntry, learning loop, schema-per-tenant, escalation               | **REUSE as-is** (de-risking evidence)            | analysis 08 §2.1       |

### 10.2 The 15% — client self-service, BUILD (non-coder configured, zero engineering)

Their processes (captured as artifacts + memory), their connectors (MCP selections), their postures
(per objective), their knowledge (knowledge store), their roster/governance (D/T/R + approval config)
— **all configurable by a non-technical operator**, or the platform inherits the 95%-pilot-failure
mode (analysis 08 §1, §3). This is the bulk of the net-new UX (the L7 surface) — **BUILD, reusing the
comms onboarding wizard as scaffold.**

### 10.3 The 5% — true custom + the boundary build

True custom (kept small on purpose): novel connectors with no existing MCP server; regulated-industry
controls (analysis 08 §4). **At the boundary** (a one-time core build, NOT per-client): the
untrusted-publisher trust model — design-first, then build (§6.4).

### 10.4 The concentrated net-new list

1. **The reactive cascade engine** (L4) — dirty-propagation + fingerprint-skip + version-on-rerun.
   The one ≥500-LOC load-bearing piece; has a live feedback loop. ~1–2 cycles (analysis 07 §6.3).
2. **The non-coder self-service surface + timeline/rewind/version UI** (L7) — the bulk of net-new UX;
   open-ended in iterations (analysis 08 §6.1; analysis 07 §6.3 item 5).
3. **The untrusted-publisher trust model** (L5) — design-first; novel architecture (~2–3× first
   session); gates the registry (analysis 08 §4.1).
4. **The `plan_proposed` gate + LLM-first consequentiality classifier** (L3) — small, well-scoped
   (analysis 07 §4; research 04 §3).
5. **The agent↔agent message model** (L6) — ~1 cycle (research 03 §8.4).

---

## 11. The overarching architecture recommendation

**Recommend: build the seven-layer stack as a ~3–5-shard parallel assembly of shipped primitives,
own the governed core's runtime per the envoy-hybrid (gated by the early runtime-ownership spike),
concentrate the two net-new builds (the non-coder self-service surface + the rewind/cascade engine)
and the one design-first decision (the untrusted-publisher trust model), prove it first on the comms
wedge's 4-step flow, then generalize, and run governance in SHADOW mode under the live product during
rollout.** (analysis 07 §7.1; analysis 08 §6.2; research 05 §7.)

### 11.1 Implications (what this means for the business)

- **Time-to-first-capability is short** because most of the engine is shipped — this is a re-pointing
  of proven machinery at a new audience, not a from-scratch build (analysis 08 §6.2).
- **The risk is concentrated, not diffuse.** Two builds (cascade engine, self-service surface) and one
  design (trust model) carry almost all the execution risk; each is spike-able early, converting
  uncertainty into evidence before the assembly commits (analysis 08 §6.2).
- **The moat is in the net-new 5%, not the reused 80%.** Anyone can call an agent loop; almost no one
  ships transparent step-level intervention, per-objective posture, and governed cross-org exchange
  (analysis 08 §6.2; research 05 §7.2). The reused 80% is necessary but not defensible.
- **The shards are independent** — artifact layer, posture layer, governance layer, connector layer,
  surface layer can each come up in parallel worktree sessions — so the throughput multiplier applies
  (analysis 08 §6.2). The _load-bearing_ shards (cascade engine, runtime core) carry the ≤500-LOC /
  ≤5–10-invariant caps and must be sharded carefully at `/todos` time (analysis 07 §3.4).
- **Independence is structural:** owning the governed-core runtime (not depending on a proprietary
  SDK) is what keeps the platform Foundation-independent _and_ what makes M1/M2 native (research 05
  §4.2, §6.4).

### 11.2 Pros and cons of this architecture (symmetric)

**Pros:**

- Highest reuse, lowest reinvention — ~80% of the substrate ships; the new work is one engine + one
  surface + one trust model, not a platform from scratch (analysis 07 §6; analysis 08 §2).
- The strongest moat (M1) is _native_ to an owned runtime, not retrofitted onto a closed loop
  (research 05 §4.2).
- Directly answers the market's documented failure mode — a correctable, versioned glass box is the
  structural answer to "the tool did the wrong thing and I had no way to see why or fix it" (analysis
  07 §7.3; analysis 08 §1).
- Honest by construction — the traceability-not-accountability and black-box boundaries are stated
  crisply, protecting against over-claiming (analysis 07 §2.2–§2.3).
- Incremental rollout is safe — SHADOW mode runs governance under the live comms product without
  blocking anything until calibrated (research 03 §5.5).

**Cons (real, not glossed):**

- **The non-coder versioning UX is genuinely unsolved** — git-like branching is hard for _programmers_;
  presenting rewind/fork/compare to a non-coder is the dominant unknown, and no research file resolves
  it (analysis 07 §8 unknown #1; analysis 08 §6.2).
- **Owning the runtime is the highest-cost option** — Kaizen/Nexus maturity at harness scale for this
  exact use case is unproven; you reimplement context management the commercial SDKs give free; slowest
  to first demo (research 05 §4.3, §6.4).
- **PACT is facade-heavy** — reuse risks shipping governance that never executes on the hot path; the
  `orphan-detection.md` / `facade-manager-detection.md` discipline (real call site + Tier-2 test per
  wired manager) is mandatory, not optional (research 03 §8.5; analysis 08 §6.2).
- **The reuse story can lull** — "80% exists" is true of primitives; the integration glue (re-key
  posture, replace the keyword classifier, wire PACT into the hot path) is real work the headline
  hides (analysis 08 §7 item 1).
- **If M1 fails, the platform degrades to "an agent does your work in one interface"** — which is
  exactly the surface Claude Cowork (general availability April 2026) already embodies; competing on
  that surface is the failure case (analysis 08 §6.2; strategic spine).
- **Storage growth and cascade cost** need a retention/compaction policy and a cost-preview before a
  cascade commits, or a single root-edit triggers a large, surprising re-run (analysis 07 §7.3, §8).

### 11.3 The alternative considered and rejected

Build a bespoke runtime + provenance/versioning system from scratch instead of reusing the
PACT/EATP/Kailash/loom substrate. **Rejected:** it discards ~80% of working, tested code (analysis 07
§7.4; analysis 08 §6.2), re-derives content-addressing, the posture state machine, the approval queue,
and the durable store that already ship, and conflicts with Decision B (capability-first reuse of the
ecosystem DNA). The only argument for it — "a clean-room design avoids PACT's facade-heaviness" — is
better addressed by _enforcing_ the orphan-detection rules on the reused code than by rewriting it
(analysis 07 §7.4).

---

## 12. The top architectural unknowns (flagged, not resolved)

Ranked by how likely each is to sink the architecture, for the spec/redteam phase to resolve. The
three at the top decide whether the signature feature is _usable_ by non-coders — not whether it can
be _built_. The engine is the tractable part; legibility-for-non-coders is the frontier (analysis 07
§8).

| #      | Unknown                                                                                                                              | Why it's hard                                                                                                                      | Where it resolves                                             | Source                               |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------- | ------------------------------------ |
| **1**  | **Runtime ownership** — can harness introspection satisfy transparency + intervention + versioned-replay, or must the loop be owned? | Determines whether M1 is buildable at all; gates the whole architecture                                                            | **The early spike (§8.3) — do this first**                    | analysis 08 §6.3; research 05 §4.4   |
| **2**  | **Non-coder versioning/branching UX**                                                                                                | Git is hard for experts; rewind/fork/compare/revert for a non-coder is unsolved                                                    | UX design + user testing; iterative discovery                 | analysis 07 §8 #1                    |
| **3**  | **Re-run vs replay vs branch as a user-facing choice**                                                                               | The per-step "re-generate / keep recorded" choice may confuse non-coders; guessing the default wrong silently is the worst outcome | Product decision + user testing                               | analysis 07 §8 #2                    |
| **4**  | **Cascade cost explosion**                                                                                                           | A root-level edit legitimately invalidates everything downstream; needs a cost-preview before committing                           | Engine design (history-metric estimate)                       | analysis 07 §8 #3                    |
| **5**  | **Object/record model vs virtual files**                                                                                             | How business objects surface (virtual FS so file tools work, vs a record-tool API) is unspecced and consequential                  | Spec decision                                                 | research 05 §3.2, §6.4               |
| **6**  | **LLM-classifier latency/cost**                                                                                                      | An LLM call on every consequentiality check is slower/costlier than a keyword match; caching mitigation unproven                   | Design decision (classify per step-type, cache)               | research 04 §7 #5; analysis 07 §8 #4 |
| **7**  | **Untrusted-publisher trust model**                                                                                                  | Cross-org publishing needs signed provenance + recall without trusting the publisher; greenfield, gates the registry               | Design-first, before the registry                             | analysis 08 §4.1                     |
| **8**  | **Storage growth / retention policy**                                                                                                | Every re-run is a new version forever; content-addressing dedupes bytes, not version count                                         | Operational policy                                            | analysis 07 §8 #5                    |
| **9**  | **Single-process event bus**                                                                                                         | PACT's `EventBus` is in-memory; multi-replica needs a durable/distributed bus                                                      | Infrastructure (SQLTaskQueue / Redis fan-out)                 | analysis 07 §8 #6                    |
| **10** | **Posture composition across many humans**                                                                                           | When many stakeholders share one objective, how does posture compose?                                                              | Spec decision; touches M3                                     | analysis 07 §8 #7; research 04 §7 #4 |
| **11** | **Posture naming/label unification**                                                                                                 | Three posture ladders with colliding labels; shipping the brief's labels as the enum confuses everyone                             | Spec decision — canonical enum internal, 3-button UX external | analysis 07 §8 #8; research 04 §1.4  |
| **12** | **Where the cascade engine lives**                                                                                                   | Framework-level vs app-level placement affects reuse and the M-series moats                                                        | Confirm with framework specialists at design time             | analysis 07 §8 #9                    |

**The honest shape of the bet:** the engine is the tractable part; the legibility-for-non-coders is
the frontier, and the runtime-ownership spike is the gate that decides whether the strongest moat is
buildable before any assembly commits.

---

## 13. Source ledger

- **`briefs/01-vision.md`** — §1 (the vertical-silo problem + the a/b/c triple), §3a–§3c (CLI
  re-interfaced for non-coders, all work, one interface), §3d (team-oriented + the agent-comms
  hypothesis), §3e (posture beforehand, retrace-and-intervene, versioning), §3f (black-box boundary),
  §4 Decisions A (comms as wedge) + B (capability-first, GTM deferred).
- **`01-analysis/07-transparency-intervention-architecture.md`** — §0 (80/20 framing), §2 (transparency
  contract + black-box boundary), §3 (provenance data model + content-addressing + six invariants), §4
  (posture surfacing + the `plan_proposed` gate + the naming trap), §5 (intervention + cascade +
  non-determinism), §6 (layer cake + ecosystem inventory + net-new list), §7 (recommendation + symmetric
  pros/cons + rejected alternative), §8 (the highest-risk unknowns).
- **`01-analysis/08-product-focus-80-15-5.md`** — §1 (the sorting rule + the 95%-failure survival
  condition), §2 (the agnostic core inventory + comms-wedge placement), §3 (the self-service surface +
  the last-20% caution), §4 (true custom + the untrusted-publisher clarification), §6 (the BUILD/REUSE/
  DEFER recommendation + the runtime-ownership pivot), §7 (symmetric cautions). The canonical 80/15/5
  ratio statement this plan cites lives in §1 of this file; this plan does not restate a different split.
- **`01-analysis/02-value-propositions.md`** — §0.2 (the four buyer questions + "what's actually
  different here?" inversion), §0 (PROVEN/credible vs CONTINGENT tagging) — the buyer-value layer the L7
  surface (§2.4) and the 80/15/5 cost picture (§10) realize.
- **`01-analysis/05-aaa-framework.md`** — §0 (the three value axes: Automate removes the hands, Augment
  sharpens the head, Amplify clones the expert), §1 (Automate = agent-as-integration-layer) — the value
  frame that maps onto this plan's reuse/net-new layers (§10).
- **`01-analysis/01-research/05-cli-harness-universal-interface.md`** — §1 (harness anatomy: loop,
  artifacts, subagents, MCP, hooks), §2 (which capabilities are domain-agnostic + the missing
  compiler), §3 (the three re-interfaces for non-coders), §4 (the runtime-ownership options + envoy
  precedent + the decisive criterion), §5 (MCP + dumb-endpoints + governance-at-connector), §6
  (feasibility + the hard 20–30%), §7 (synthesis).
- **`01-analysis/01-research/03-pact-governance.md`** — §2 (D/T/R accountability), §3 (envelopes), §4
  (verification gradient + clearance), §5 (SupervisorOrchestrator / ApprovalBridge / EventBridge /
  EmergencyBypass / EnforcementMode), §6 (the 17 DataFlow models), §8 (synthesis: 80/15/5, two posture
  vocabularies, facade-heaviness caution).
- **`01-analysis/01-research/04-eatp-trust-posture.md`** — §1 (the canonical L1–L5 ladder + the naming
  collision + the 3-button mapping), §2 (TrustPlane, gradient, BudgetTracker, PostureStore), §3
  (HITL/HOTL + the keyword-classifier caveat), §4 (set/upgrade/downgrade/anchors), §5 (structural vs
  execution gates), §6 (the synthesis + the three gaps + the recommended posture architecture), §7
  (open questions).
- **The strategic spine (Phase A)** — moats M1–M4, the Claude Cowork threat, "transparency makes depth
  legible," the MIT NANDA / Gartner market evidence, Decisions A and B, the agent-comms hypothesis as
  an unproven bet.
- **COC rules** — `communication.md` (plain language), `recommendation-quality.md` (single
  recommendation + symmetric pros/cons), `autonomous-execution.md` (effort in cycles + sharding caps),
  `independence.md` (Sequor is the product), `tenant-isolation.md`, `orphan-detection.md` /
  `facade-manager-detection.md` (no orphaned governance), `agent-reasoning.md` (LLM-first), `spec-accuracy.md`
  (flag, don't paper over, uncertainty), `cross-cli-artifact-hygiene.md` (CLI-neutral prose).
