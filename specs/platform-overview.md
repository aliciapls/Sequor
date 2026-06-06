# Platform Overview — The Agnostic Agentic-Work Platform

> Status: TARGET-STATE (vision / not yet implemented). This spec describes the intended platform; the comms wedge (shipped) specs are separate.

This is the entry-point spec for the platform. It defines what the platform IS, the work-paradigm model it runs on, the agentic interface and the integration-layer inversion, the seven architectural layers at a glance, the four moat properties, the non-coder principle, and the black-box boundary. Each layer summary points to its detailed sibling spec (where one exists — two layers are honest TARGET-STATE gaps with no spec yet), which is the authority on that layer's flows, contracts, and invariants.

Grounding: every load-bearing claim cites `workspaces/future-of-work/02-plans/01-architecture.md` (the architecture plan), `workspaces/future-of-work/01-analysis/08-product-focus-80-15-5.md` (the reuse split), or `workspaces/future-of-work/01-analysis/01-research/08-work-disruption-thesis.md` (the conceptual spine). Effort, where mentioned, is in autonomous execution cycles, never human-days (per `rules/autonomous-execution.md`). The platform is described on its own terms with no positioning relative to any commercial product (per `rules/independence.md`).

---

## 1. Purpose

The platform is **one agent loop — governed and made transparent — reached through a non-coder work surface, connected to every business system through standard connectors** (architecture plan §0). It lets a non-technical person get *any* knowledge work done by stating an outcome to an AI agent, instead of personally crossing N siloed vertical systems (ERP → CRM → POS → spreadsheet → document → internal portal).

The problem it solves is structural, not cosmetic (work-disruption thesis Part 2). Today no single software system holds a whole task end-to-end, so the *human* becomes the integration layer: the person who carries the goal in their head, remembers how the company does the work, and shuttles data between screens by hand. That carrying-and-shuttling is pure overhead — it advances no goal; it only compensates for the fact that the goal was never represented anywhere whole (work-disruption thesis §1.3, the "swivel-chair work" definition). The platform removes that overhead by putting an agent where the human used to be.

**What the platform is NOT:** it is not another vertical tool, not a chatbot bolted onto one app, and not a no-code workflow builder. A single vertical vendor structurally *cannot* solve the cross-system problem — integration across competitors is adversarial to each vendor's interest, and company-specific process is un-ownable by a generic product (work-disruption thesis §2.4). The platform is the agnostic layer in the middle that no vertical vendor will build.

---

## 2. The work-paradigm model — every unit of work is OBJECTIVE / PROCESS / DATA

The platform rests on one model of work. **Every unit of enterprise work is the same three-part object** (work-disruption thesis Part 1; the brief's §2a/b/c):

> **W = ⟨ Objective, Process, Data ⟩**

The triple is **complete and irreducible** — remove any one element and the work cannot be specified (work-disruption thesis §1.1).

| Element | Plain-language meaning | What it is on the platform | Captured as |
| --- | --- | --- | --- |
| **OBJECTIVE** | The user's intent — the end-state that defines "done." Declarative: says *what*, not *how*. ("I want the Q3 financial report, accurate, in house format, sent to the CFO.") | The user's prompt / stated intent. Per-task, human-authored, transient. | A stated objective (in PACT terms an objective record decomposed into sub-requests) |
| **PROCESS / PROCEDURE** | The company-specific rules and procedures that govern *how* the objective may legitimately be reached. Lives in employees' heads, onboarding docs, "the way we do things here." Two companies with the identical objective follow materially different processes. | A body of reusable, company-specific **artifacts** — skills (institutional know-how), rules (the company's MUST / MUST-NOT), commands (named procedures with phases and gates). | Artifacts + memory (the artifact registry, Layer 5) |
| **DATA** | The information the work reads and writes — customer records, ledger entries, inventory counts, prior correspondence. Stateful, distributed across many systems, rarely complete in any one. | The business systems reached as governed tool connections. The systems become endpoints the agent calls, not destinations the human visits. | Connectors (MCP, Layer 1) |

Why this model is load-bearing: it sorts cleanly onto the reuse split (reuse-split §1). The *machinery* that runs any objective is the agnostic core (the 80%, built once); the *company-specific process* is the self-service configuration surface (the 15%, configured by a non-coder, captured as artifacts); only the genuinely external residue is custom (the 5%). Dropping PROCESS is the single most dangerous failure mode — the agent then does plausible-but-wrong-for-here work (wrong approval chain, wrong tone, a compliance step skipped). This is exactly the documented market failure: ~95% of enterprise GenAI pilots fail because generic tools "don't learn from or adapt to workflows" (reuse-split §1, MIT NANDA). Capturing PROCESS as self-service artifacts is the survival condition, not a convenience.

---

## 3. The agnostic agentic interface and the integration-layer inversion

### 3.1 The inversion

Today's world puts software at the **nodes** (one app per function) and the **human in the edges** (the seams between apps). The platform inverts this: it puts a single agnostic agent at the **center** and lets the human state intent at the boundary (work-disruption thesis §3.1).

```
   VERTICAL WORLD (today)                 AGENTIC WORLD (the platform)

   human ── carries O,P,D ──┐                      human
     │                      │                        │  states OBJECTIVE (intent)
   ┌─▼─┐  ┌───┐  ┌───┐  ┌───▼┐                       ▼
   │ERP│  │CRM│  │POS│  │ XLS│             ┌──────── agent ────────┐
   └───┘  └───┘  └───┘  └────┘             │  holds OBJECTIVE        │
   the HUMAN is the integration            │  applies PROCESS        │
   layer between every pair of systems     │  reads/writes DATA      │
                                           └──┬────┬────┬────┬───────┘
                                            ERP  CRM  POS  XLS
                                       systems are TOOL ENDPOINTS;
                                       the AGENT is the integration layer
```

The human supplies the one thing only a human can supply — the objective and the authority behind it. The agent supplies the integration the human used to supply by hand. **The agent integrates; the human states intent and governs.**

### 3.2 The interface is agnostic — re-interfacing the harness for all work

The developer's agent CLI ("command-line interface" — the text terminal a programmer types into) is already a domain-agnostic work engine that *happens* to ship configured for coding (architecture plan §2.1). The reason→act→verify loop, the artifact system, sub-agent fan-out, and the connector protocol are all domain-neutral; the coding-specificity lives entirely in the tools and artifacts layered on top (work-disruption thesis §3.2, §5.1). The platform does not rebuild this engine — it **re-interfaces** it: the engine stays, the surface the human touches changes. Three concrete shifts (architecture plan §2.2):

- **From terminal to intent surface.** The user states an outcome in plain language plus a live timeline of what the agent is doing — not a command prompt.
- **From file/git to business-object/work-timeline.** The unit of work is a record in a system of record (a purchase order, an opportunity, a ticket), and a rewindable work timeline — not a file and a git branch graph.
- **From per-tool-call permissions to per-objective posture.** The user picks how much rein the agent gets *for this job, beforehand* — not a binary yes/no on each tool call.

The interface is **CLI-neutral by design**: the engine underneath may be reached through any harness, and the platform owns its governed-core runtime so transparency and intervention are native rather than bolted on (architecture plan §8.3, the envoy-hybrid; gated by an early runtime-ownership spike). Foundation independence requires owning the governed core rather than depending on any proprietary SDK (per `rules/independence.md`; architecture plan §8.2).

### 3.3 The integration-layer inversion, stated as a contract

The platform is "proven" when one end-to-end run exhibits all six properties (work-disruption thesis §5.2, the falsifiable acceptance test):

1. **Objective in, intent only** — the human states a real objective in natural language and supplies no step-by-step procedure.
2. **Process applied from artifacts** — the agent's behavior visibly conforms to ≥1 company-specific artifact and deviates from the generic default in a way only that artifact explains.
3. **Crosses ≥2 formerly-siloed systems** — the run reads from system A and writes to / reconciles with system B, where A and B do not natively integrate.
4. **Traced output** — every decision the agent made is recorded and inspectable: which steps/sub-agents it chose, what it read, what it wrote, under what posture.
5. **Interveneable** — the human chose a posture beforehand, can rewind to any prior step and intervene, downstream outputs recompute, and prior outputs are versioned.
6. **No swivel-chair** — the human never opens system A or system B directly during the run.

Properties 3 and 6 are the load-bearing pair: crossing-two-systems and no-swivel-chair are what distinguish the platform from a chatbot on a single app (work-disruption thesis §5.2).

---

## 4. The seven architectural layers at a glance

> **Two different "L1–L5" scales — do not confuse them.** This section numbers the *architecture* as **Layer 1 through Layer 7** (a structural map of what the platform is made of). Separately, the platform's *trust posture* runs on a **Posture L1–L5** ladder — how much rein the agent gets (plain-language buttons: "Step through" / "Ask me once" / "Go ahead"). Architecture layers and posture rungs are unrelated scales that happen to share the letter "L"; this spec writes **"Layer N"** for architecture and **"Posture L1–L5"** for the trust ladder throughout, adopting the resolution in `trust-posture-and-governance.md` §1.1. Wherever the source brief used a bare "L3/L4/L5" as a posture label, this spec attaches the plain-language button so the reader can always tell which scale is meant.

The platform is seven layers (architecture plan §1). The numbering is bottom-up by *dependency* (Layer 1 connectors and Layer 2 runtime are the foundation everything stands on); the *user* experiences it top-down (Layer 7 first). A user request enters at Layer 7; the runtime (Layer 2) plans and acts; every action is checked by governance (Layer 3) and recorded by the ledger (Layer 4); the runtime reaches systems through connectors (Layer 1); many people and agents share the work through coordination (Layer 6); the know-how that makes any of it competent lives as artifacts (Layer 5).

Each layer below has a one-paragraph summary and a pointer to its detailed sibling spec. **The sibling spec is the authority** on that layer's flows, contracts, constraints, edge cases, and invariants; this overview states only what each layer is and how it fits. Two layers — Layer 7 (work interface) and Layer 2 (orchestration runtime) — have **no detailed sibling spec yet**; those are honest TARGET-STATE gaps tracked in plans `02-plans/01-architecture.md` (§2 and §8 respectively), not specs that exist and were merely omitted.

### Layer 7 — Work Interface (the non-coder surface)
The surface the non-coder talks to: a plain intent box, a live timeline of what the agent is doing, a "here's my plan — pick a posture" approval card, a timeline/rewind view, plain-language approval cards, and business-object views (records, not files). It replaces the developer's terminal/file/git mental model with a conversational, record-oriented surface. **Reuse vs net-new:** REUSE the comms onboarding wizard and PACT's web objectives/approvals screens as scaffold; BUILD the non-coder self-service surface and the timeline/rewind/version UI as the primary net-new UX (architecture plan §2.4; reuse-split §3). The non-coder versioning/branching UX is the dominant open unknown (architecture plan §12 #2). → *No detailed sibling spec yet — TARGET-STATE gap; see plans `02-plans/01-architecture.md` §2 for the work-interface design intent.*

### Layer 2 — Orchestration Runtime (the reason→act→verify loop)
The engine that gathers context, takes an action, checks the result, and repeats — plus sub-agent fan-out, context management/compaction, and **two-phase signing** (recording intent before the action and outcome after, both signed). This is where the one decision everything hinges on lives: the runtime-ownership decision. **Reuse vs net-new:** the envoy-hybrid — OWN the product runtime for the governed core (so transparency, two-phase signing, posture gating, and intervenable replay are native), built on Kailash-native frameworks, while developing the product itself on commercial harnesses; gated by an early spike that determines whether the strongest moat (M1) is buildable at all (architecture plan §8). The single coding advantage that does NOT transfer is the compiler/test as free ground truth — most knowledge work has no compiler, which is *why* the transparency/posture stack (Layer 3 + Layer 4) is load-bearing for correctness (architecture plan §8.1). → *No detailed sibling spec yet — TARGET-STATE gap; see plans `02-plans/01-architecture.md` §8 for the runtime-ownership decision.*

### Layer 3 — Governance Substrate (what's allowed, when a human gates)
Decides, structurally and before any action runs: *is this agent, in this objective, allowed to take this action right now — and if not, who has to say yes?* It comprises permission envelopes (a 5-dimension box: money, allowed actions, time windows, data it can touch, what it can send), D/T/R accountability — the **Department/Team/Role** addressing grammar that lets every agent carry a computable chain of the humans answerable for it (which department, which team, which role is on the hook) — trust postures (Posture L1–L5; see §4 note below), a verification gradient (auto-approve / flag / HELD-pause-for-human / block), per-objective cost ceilings, and accountable emergency break-glass. **Reuse vs net-new:** REUSE the PACT engine and EATP posture machinery wholesale (`/Users/esperie/repos/terrene/contrib/pact`, `/Users/esperie/repos/loom/kailash-py`; both shipped end-to-end); BUILD the `plan_proposed` gate (surfacing the agent's fan-out plan as the approvable object before execution) and replace PACT's keyword consequentiality classifier with an LLM-first one per `rules/agent-reasoning.md`; roll in under SHADOW mode (architecture plan §3). The reuse caution: PACT is facade-heavy — every wired governance manager needs a real call site plus a Tier-2 test, or the security promise is a silent no-op (per `rules/orphan-detection.md`, `rules/facade-manager-detection.md`). → *Detailed sibling spec: `trust-posture-and-governance.md`.*

### Layer 4 — Provenance Ledger + Cascade Engine (glass box + undo-from-anywhere)
Makes agentic work a glass box with an undo-from-anywhere button. Every input, decision, tool call, tool result, and output is recorded as a content-addressed Step/Output/Decision graph (immutable versions, fingerprinted, tamper-evident). The user rewinds to any past step, changes an input or overrides a decision, and **only the parts that actually depend on the change recompute** (dirty-propagation + fingerprint-skip), while previous results survive as named versions. **Reuse vs net-new:** REUSE PACT records + the Kailash durable store + OpenTelemetry recording unified into one content-addressed graph (mostly wiring); BUILD the reactive cascade engine as the single net-new framework component — a ~20% novel composition (dirty-propagation from reactive notebooks + fingerprint-skip from build systems) over primitives that already ship (architecture plan §4). The engine separates re-run (changed input → re-execute) from replay (show exactly what happened, reuse the recorded answer) from branch (fork a new timeline), and never assumes a model call replays identically (architecture plan §4.4). → *Detailed sibling specs: `transparency-and-provenance.md` (the glass-box ledger) and `intervention-and-versioning.md` (rewind/cascade/versioning).*

### Layer 6 — Coordination Substrate (many humans + many agents on one objective)
The shared substrate that lets many humans and many agents work one objective safely: a shared objective, claims/leases over work scopes, agent↔agent messages as first-class surfaced records, a gate matrix (who approves what, distinct-person 4-eyes), and per-operator posture composed as `min(operator, floor)`. **Reuse vs net-new:** REUSE the loom multi-operator coordination substrate for the human-multiplicity half wholesale (`/Users/esperie/repos/loom`; signed hash-chained coordination log, claims/leases, SAME/ADJACENT/INDEPENDENT adjacency, 4-eyes gates); BUILD the agent↔agent message model (architecture plan §5). Carry the caution explicitly: the brief's "agent-comms beats human-comms" thesis is an unproven, contrarian research bet — the substrate gives a place to *test* it; the platform MUST NOT stake its value proposition on it. The defensible position: disrupt the *handoff/coordination* substrate of team communication, not human↔human communication itself (work-disruption thesis §4.3). → *Detailed sibling spec: `coordination-and-teams.md`.*

### Layer 5 — Artifact Registry + Cross-Org Exchange (reusable know-how)
The unit of reusable know-how — agents (judgment + procedure), skills (knowledge + reference), rules (guardrails), hooks (deterministic gates), commands (workflow orchestration) — with variant overlays (per-company/per-language overrides), publish/subscribe across orgs, provenance tracking, and recall/obsoletion. This is where company PROCESS lives. **Reuse vs net-new:** REUSE the loom splitter wholesale (`/Users/esperie/repos/loom`; the five-layer artifact system, variant overlays, two-gate distribution, proposal lifecycle, obsoletion/recall — all shipped for coding artifacts; the re-interface carries business-domain artifacts instead); BUILD cross-org publish/subscribe and the untrusted-publisher trust model (design-first, because it constrains the registry). loom's existing trust model is bounded-trust (the adversary is a legitimate team member with repo write access); a cross-*company* marketplace faces *untrusted* publishers whose artifacts must be signed, provenance-tracked, and recallable without trusting the publisher (architecture plan §6; reuse-split §4.1). Ignite network effects within-org first, then cross-org after the trust model is designed. → *Detailed sibling spec: `artifact-system-and-registry.md`.*

### Layer 1 — Connector (MCP) Layer (reach any business system as a tool)
The universal connector. MCP ("Model Context Protocol" — the standard way an agent reaches an external system as a tool) connects the agent to SAP, Salesforce, Workday, Google, email, and the rest exactly as it connects a coding agent to `git` and `filesystem` today. The keystone discipline: **tools are dumb endpoints; the LLM reasons** — an MCP tool MUST be `get_order(id) → record`, never `handle_order_issue(...)` with business logic buried in tool code. Governance sits *between* the agent and the connector, so a HELD verdict blocks a write until a human approves. **Reuse vs net-new:** REUSE the MCP protocol and the existing connector ecosystem; BUILD the governed curation (wrap each connector in the dumb-endpoints discipline and put governance between agent and connector). Connectivity is a commodity; only *governed* connectivity differentiates (architecture plan §7; reuse-split §6.1). The dumb-endpoints rule is what makes the Layer 4 transparency contract possible: if all reasoning lives in the logged LLM and tools only move logged data, everything except the model's internal cognition is transparent. → *Detailed sibling spec: `connectors-and-integration.md`.*

---

## 5. The four moat properties (M1–M4) — platform-defining characteristics

The platform's defensibility is the **conjunction** of four properties (strategic spine; architecture plan §10.1, §11.1; reuse-split §6.2). Anyone can call an agent loop — that is the reused 80% and is necessary but not defensible. The moat is the net-new combination almost no one ships:

| Moat | Property | Plain-language meaning | Home layer |
| --- | --- | --- | --- |
| **M1** | **Transparent, versioned, intervene-from-any-step** | The work is a glass box you can rewind to any past step, change one decision, and only the affected downstream recomputes — while old versions survive. | Layer 4 (provenance ledger + cascade engine) |
| **M2** | **Execution-time, posture-graded governance** | How much rein the agent gets is chosen *beforehand, per objective* on the **Posture L1–L5** ladder (the common rungs: "Step through" = Posture L3, "Ask me once" = Posture L4, "Go ahead" = Posture L5), and enforced live at every action — not bolted on as after-the-fact observability. (These are posture rungs, not architecture layers — see the §4 note.) | Layer 3 (governance substrate) |
| **M3** | **Multi-human + multi-agent shared substrate** | Many people and many agents work one objective on one governed substrate, with claims, distinct-person gates, and composed posture. | Layer 6 (coordination substrate) |
| **M4** | **Governed, provenance-tracked, cross-org artifact exchange** | Company know-how (artifacts) is published, consumed, and recalled across organizations — signed and provenance-tracked even from untrusted publishers. | Layer 5 (artifact registry) |

The conjunction matters: the moat is **M1 AND M2 AND M3 AND M4 held simultaneously**, not any one alone. M2 is the most-proven, lowest-risk property and ships first (PACT + EATP are shipped end-to-end). M1 is the strongest and hardest — and the gating runtime-ownership spike decides whether it is buildable at all (architecture plan §8.3, §12 #1). If M1 fails, the platform degrades to "an agent does your work in one interface" — a commodity surface that does not defend itself (reuse-split §6.2). M4 is the network-effects engine, gated by the design-first untrusted-publisher trust model.

---

## 6. The non-coder principle

**The user is not a coder, and never has to become one** (work-disruption thesis §5.1; reuse-split §3; the brief's §3a). The user states intent and governs; everything else — the integration, the procedure execution, the data movement — is the agent's job. This principle is not a UX nicety; it is the survival condition (reuse-split §1):

- The company-specific PROCESS (the 15%) MUST be configurable by a non-technical operator with **zero engineering**. If configuring "how this company does the work" requires a developer, the platform inherits the documented ~95%-pilot-failure mode and does not scale past a handful of clients.
- The non-coder never writes a connector, never edits a rule file, never reads a stack trace. They pick which systems to plug in from a list, they pick a posture from three plain buttons, and they intervene by reading a plain-language timeline.
- Every choice the platform surfaces to the user is presented in business terms with a recommendation, implications, and plain language — never a code snippet or unexplained jargon (per `rules/communication.md`, `rules/recommendation-quality.md`).

The honest seam: no-code depth historically dies at "the last 20%" of any company's process (reuse-split §3, §7 item 2). The mitigation is structural — pair the self-service surface *tightly* with the Layer 4 transparency/rewind, so when the configured process runs the user can see every step and intervene, which makes the un-configured 10% legible and fixable in-flight rather than silently wrong (architecture plan §2.4).

---

## 7. The black-box boundary

The platform draws one boundary crisply, because a fuzzy boundary is a broken promise (architecture plan §4.2; work-disruption thesis §3.4):

- **Transparent (the glass box) — recorded and surfaced:** every input; the agent's decisions, plans, and fan-outs; every tool call and its arguments; every tool result; every output; and metadata (model, cost, time, and the posture in force when the step ran). Any reasoning *summary* the model chooses to surface at its output is also recorded.
- **Opaque (the black box) — deliberately NOT recorded:** the model's internal chain-of-thought, activations, and token-level reasoning — because no one, not even the model's maker, can faithfully record it.

Stated exactly: **we record everything the model emits at its input/output surface, and we do not record — and do not claim to record — how the model actually computed its answer internally.** Model reasoning is opaque; inputs, decisions, and outputs are transparent.

The honesty caveat that travels with every trust claim (architecture plan §4.2): the system delivers **traceability, not accountability.** Traceability (the machine guarantees it) = every AI action traces back to its inputs, decisions, and the human authority that permitted it. Accountability (no software can guarantee it) = a human actually *understood* and bears the consequences. The glass box makes understanding *possible*; it cannot force it. The platform MUST NOT over-claim accountability where it can only deliver traceability.

The connector-layer discipline (Layer 1: "tools are dumb endpoints, the LLM reasons") is what makes this boundary holdable. If all reasoning lives in the LLM whose input/output is logged, and tools only move data which is also logged, then everything *except* the model's internal cognition is transparent (architecture plan §7.2). Decision logic buried in tool code would silently widen the black box; the dumb-endpoints rule forbids it.

---

## 8. Reuse-vs-new summary (the 80/15/5 picture)

The platform is overwhelmingly **assembly and re-pointing of shipped ecosystem code, not invention** (reuse-split §0, §8; architecture plan §10). The single most important caveat: "~80% exists" is true at the level of *primitives* — a primitive is not a finished product, and the glue plus the net-new 5% carry the real cost and the real moat.

- **~80% — agnostic core (REUSE).** The work engine, governance (PACT, `/Users/esperie/repos/terrene/contrib/pact`), posture (EATP, `/Users/esperie/repos/loom/kailash-py`; aegis, `/Users/esperie/repos/dev/aegis`), the artifact system and splitter (loom, `/Users/esperie/repos/loom`), the multi-operator coordination substrate (loom), multi-CLI parity (envoy, `/Users/esperie/repos/dev/envoy`), the MCP protocol, and the deployed comms-wedge spine — all shipped or specced (reuse-split §2).
- **~15% — client self-service (BUILD).** Their processes, connectors, postures, knowledge, and roster/governance — all configurable by a non-coder, zero engineering, captured as artifacts and config. The bulk of the net-new UX (reuse-split §3).
- **~5% — true custom + the boundary build.** Novel connectors with no existing MCP server; regulated-industry controls. At the boundary (a one-time core build, NOT per-client): the untrusted-publisher trust model — design-first (reuse-split §4).

The concentrated net-new list (architecture plan §10.4): (1) the reactive cascade engine [Layer 4]; (2) the non-coder self-service surface + timeline/rewind/version UI [Layer 7]; (3) the untrusted-publisher trust model [Layer 5]; (4) the `plan_proposed` gate + LLM-first consequentiality classifier [Layer 3]; (5) the agent↔agent message model [Layer 6]. The moat lives in this net-new list, not in the reused 80%.

---

## 9. Decisions carried into this spec

- **Comms = subsumed wedge (Decision A).** The existing Sequor communication-coverage product is subsumed as one early, revenue-bearing wedge that de-risks the trust/feedback/transparency/isolation spine against real users — but it proves the *foundation*, not the orchestration headline (M1, M3-team, M4). The comms-wedge specs (the shipped `specs/*.md` siblings) are separate and describe shipped behavior; this spec describes the target platform (reuse-split §2.1, §5).
- **Capability-first (Decision B).** It is too early to fix a beachhead vertical. The platform proves the horizontal, beachhead-free capability first (objective → agentic execution across ≥2 formerly-siloed systems → traced, posture-governed, interveneable, versioned output, human never swivel-chairing) and keeps the architecture agnostic; GTM is deferred (work-disruption thesis Part 5).
- **Foundation independence.** The platform owns its governed-core runtime rather than depending on any proprietary SDK — this is what keeps it independent *and* what makes M1/M2 native rather than retrofitted (architecture plan §8.2; per `rules/independence.md`).

---

## 10. Source ledger

- `workspaces/future-of-work/02-plans/01-architecture.md` — the seven-layer architecture, per-layer REUSE/BUILD recommendations, the runtime-ownership pivot (§8), the moat homes, the transparency contract (§4.2), the concentrated net-new list (§10.4), the top unknowns (§12).
- `workspaces/future-of-work/01-analysis/08-product-focus-80-15-5.md` — the 80/15/5 sorting rule, the agnostic-core inventory (§2), the self-service surface and last-20% caution (§3), the untrusted-publisher clarification (§4.1), the moat-in-the-5% framing (§6.2).
- `workspaces/future-of-work/01-analysis/01-research/08-work-disruption-thesis.md` — the OBJECTIVE/PROCESS/DATA trinity (Part 1), the swivel-chair critique (Part 2), the integration-layer inversion (Part 3), the human-comms hypothesis and its defensible position (Part 4), the capability-first acceptance test (Part 5).
- **Ecosystem DNA (reuse sources, cited by path):** loom (`/Users/esperie/repos/loom`) — artifact splitter, variant overlays, proposal lifecycle, recall, multi-operator coordination; pact (`/Users/esperie/repos/terrene/contrib/pact`) — D/T/R, envelopes, clearance, SupervisorOrchestrator/ApprovalBridge/EventBridge/EmergencyBypass; eatp (`/Users/esperie/repos/loom/kailash-py`) — TrustPlane/BudgetTracker/PostureStore; aegis (`/Users/esperie/repos/dev/aegis`) — posture L1–L5, multi-operator coordination; envoy (`/Users/esperie/repos/dev/envoy`) — multi-CLI parity, owned-runtime precedent.
- **COC rules** governing this spec: `independence.md`, `autonomous-execution.md`, `communication.md`, `recommendation-quality.md`, `orphan-detection.md` / `facade-manager-detection.md`, `agent-reasoning.md`, `tenant-isolation.md`, `spec-accuracy.md`, `cross-cli-artifact-hygiene.md`.
