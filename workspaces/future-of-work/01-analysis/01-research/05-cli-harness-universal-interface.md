# Research 05 — The CLI Agent Harness as a Universal Work Interface

> Scope: Brief 01 objectives **4** (CLI re-interfaced for all work), **5a/5b/5c**
> (transparency, intervenable steps, posture-before-execution). Decision A (comms as wedge)
> and Decision B (capability-first, GTM deferred) frame the analysis.
>
> Method: grounded in actual repo files (cited inline by absolute path) + 2025–2026 web facts
> on agent-CLI harness architecture. Where a claim rests on a single source or is uncertain, it
> is flagged explicitly. Effort estimated in **autonomous execution cycles/sessions**, never
> human-days (per `.claude/rules/autonomous-execution.md`).
>
> Independence note (per `.claude/rules/independence.md`): this document describes the platform
> on its own terms. Commercial harnesses are named **only as factual ecosystem references**
> (what exists, what it does), never as a parent the platform is "a version of."

---

## 0. The thesis in one sentence

The autonomous agent CLI harness — the main loop + artifacts (agents/skills/rules/hooks/commands) +
tools (MCP) + subagent delegation — is **already a domain-agnostic work runtime that happens to ship
configured for coding**. Re-interfacing it "for all work" is **~70% a re-skinning + re-connecting
problem and ~30% a genuinely-hard runtime/UX problem**, not a from-scratch build. The hard 30% is
exactly the part Terrene's own ecosystem (envoy's runtime abstraction, pact's governance engine,
eatp's trust plane, loom's artifact distribution) has already specced — and that the commercial
harnesses do **not** offer: transparent, intervenable, posture-gated, versioned human↔agent and
agent↔agent work.

---

## 1. Anatomy of an agent CLI harness (current state, 2025–2026)

### 1.1 The main agent loop

Every harness — Claude Code, Codex CLI, Gemini CLI — runs the same fundamental loop. Anthropic's
own framing (the Claude Agent SDK engineering post,
[claude.com/blog/building-agents-with-the-claude-agent-sdk](https://claude.com/blog/building-agents-with-the-claude-agent-sdk))
states it as: **gather context → take action → verify work → repeat**. The low-level mechanism, as
documented in this repo's own guide at
`/Users/esperie/repos/projects/Sequor/.claude/guides/claude-code/13-agentic-architecture.md` (lines
17–131):

```
send message → check stop_reason → execute tools → append results → repeat
```

Three load-bearing invariants the guide flags (and the `30-claude-code-patterns` skill restates at
`/Users/esperie/repos/projects/Sequor/.claude/skills/30-claude-code-patterns/SKILL.md:26–35`):

- `stop_reason == "end_turn"` is the **only** termination signal (never parse prose for "I'm done").
- Never use arbitrary iteration caps; trust the model's signal.
- The model returns text AND `tool_use` in the same response — check `stop_reason`, not content type.

**This loop is domain-neutral.** Nothing in it is coding-specific. It is a generic "reason → act →
observe → reason" engine. The coding-specificity lives entirely in the _tools_ and _artifacts_ layered
on top.

### 1.2 The artifact layers (the COC five-layer system)

This is the part the platform's DNA already owns. From
`/Users/esperie/repos/projects/Sequor/.claude/skills/30-claude-code-patterns/SKILL.md:14–22`:

| Layer           | Type        | Purpose                                                   | Domain-agnostic?                               |
| --------------- | ----------- | --------------------------------------------------------- | ---------------------------------------------- |
| L1 Intent       | **Agent**   | Teach judgment + procedure (150–400 lines)                | **Yes** — "judgment + procedure" is any-domain |
| L2 Context      | **Skill**   | Teach knowledge + reference (progressive disclosure)      | **Yes** — knowledge packaging is any-domain    |
| L3 Guardrails   | **Rule**    | Enforce boundaries (path-scoped via `paths:` frontmatter) | **Yes** — boundaries are any-domain            |
| L4 Instructions | **Command** | Orchestrate workflows (`/analyze`, `/todos`, …)           | **Yes** — workflow orchestration is any-domain |
| L3 Guardrails   | **Hook**    | Deterministic prevention (JS, 25 lifecycle events)        | **Yes** — deterministic gates are any-domain   |

The loom platform (`~/repos/loom`) already treats these five layers as a **distributable artifact
product** with variant overlays and Gate-1/Gate-2 distribution to 30+ downstream repos
(`.claude/rules/artifact-flow.md`). Brief objective **3g** ("artifacts easily created, modified,
stored, and shared across organizations and teams") is _literally already built_ in loom — for coding
artifacts. The re-interface is: make the same machinery carry _business-domain_ agents/skills/rules.

### 1.3 Subagents / Task delegation

Confirmed current (2025–2026) across sources:

- **Hub-and-spoke topology**: one coordinator, specialized subagents around the perimeter
  (`/Users/esperie/repos/projects/Sequor/.claude/guides/claude-code/13-agentic-architecture.md:134–164`).
- **Memory isolation is the defining property**: subagents do NOT share memory with the coordinator
  or each other; each starts with a fresh context window and returns only its output (guide lines
  166–177; SKILL.md:37–39). The Claude Agent SDK docs confirm subagents "use their own isolated
  context windows, and only send relevant information back to the orchestrator"
  ([platform.claude.com/docs/en/agent-sdk/subagents](https://platform.claude.com/docs/en/agent-sdk/subagents)).
- **Parallelization**: subagents spin up concurrently for independent subtasks. This repo's rules
  govern it tightly — `.claude/rules/worktree-isolation.md` Rule 4 caps cold-start concurrency at ~3
  Opus-tier agents with an adaptive throttle-aware back-off.

Anthropic's Dec-2025 **Agent Teams** feature (Claude Code v2.0) lets multiple sessions run in
parallel with a shared task list
([codeant.ai 2026 comparison](https://www.codeant.ai/blogs/claude-code-cli-vs-codex-cli-vs-gemini-cli-best-ai-cli-tool-for-developers-in-2025)) —
the harness vendors are themselves moving toward the multi-agent/team-oriented surface Brief
objective **3d** describes.

### 1.4 MCP tool servers

MCP (Model Context Protocol) is the **universal connector**. Current state (2025–2026):

- MCP servers are now officially **OAuth 2.1 Resource Servers** (spec 2025-06-18); clients are OAuth
  2.1 clients ([modelcontextprotocol.io authorization](https://modelcontextprotocol.io/specification/draft/basic/authorization),
  [auth0.com MCP specs update](https://auth0.com/blog/mcp-specs-update-all-about-auth/)).
- **Remote MCP servers** (HTTP+SSE / Streamable HTTP) behind OAuth are the enterprise transport
  (vs local stdio for dev tools).
- **>1,000 connectors** existed by early 2025; enterprise servers (Salesforce, HubSpot, Snowflake,
  Datadog, Okta, Atlassian) increasingly built by the vendors themselves
  ([Atlassian remote MCP](https://www.atlassian.com/blog/announcements/remote-mcp-server),
  [hauerpower MCP guide](https://www.hauerpower.com/en/insights-posts/what-is-mcp-model-context-protocol)).
- The Claude Agent SDK ships MCP integrations for Slack, GitHub, Asana, Google Drive "handling
  authentication automatically."

This is the single most important fact for the universal-interface thesis: **the same protocol that
connects the harness to `git` and `filesystem` today connects it to SAP, Salesforce, Workday, and
NetSuite tomorrow.** The connector substrate is not coding-specific.

### 1.5 Permission modes + hooks lifecycle

- **Permission modes** (Claude Code, 2025–2026): `default`, `acceptEdits`, `plan`, `dontAsk`,
  `bypassPermissions` ([code.claude.com/docs/en/permissions](https://code.claude.com/docs/en/permissions)).
  These are coarse, binary-ish, and developer-framed — they are **not** the graduated, per-objective,
  intervenable postures the brief wants (see §3.3).
- **Hooks lifecycle**: ~25 distinct lifecycle points; key blocking events are `PreToolUse` (the
  primary security checkpoint — exit 2 stops the tool), `PermissionRequest`, `Stop`/`SubagentStop`,
  `UserPromptSubmit`, `SessionStart`, `PreCompact`
  ([claudefa.st hooks guide](https://claudefa.st/blog/tools/hooks/hooks-guide)).
- This repo already operates a deep hooks layer: `session-start.js`, `user-prompt-rules-reminder.js`
  (injects workspace context every turn), plus the multi-operator coordination substrate's
  `integrity-guard.js`, `operator-gate.js`, `adjacency-leasecheck.js`
  (`.claude/rules/multi-operator-coordination.md` §2, §5).

### 1.6 Context management

The harness's hardest engineering problem is context, and the SDK exposes the tools: agentic search
(`grep`/`tail` to selectively load), file-system-as-context, semantic/vector search, subagent context
isolation, and automatic compaction with CLAUDE.md re-read after compaction
([claude.com SDK blog](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)). This
repo's `SKILL.md:96–111` catalogs the failure modes: progressive-summarization trap (transactional
data like `$247.83` compressed to "customer wants refund"), lost-in-the-middle, attention dilution
(14+ items → inconsistent depth).

---

## 2. What makes it powerful for coding — and which capabilities are domain-agnostic

The key analytical move: **separate the loop+artifacts+MCP substrate (domain-agnostic) from the
coding-specific configuration (replaceable).**

| Capability                            | Why it's powerful for coding           | Domain-agnostic?                | What it becomes for general work                                                                                                      |
| ------------------------------------- | -------------------------------------- | ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------- |
| Main agent loop (reason→act→verify)   | Iterates on compile/test feedback      | **Fully agnostic**              | Iterates on _any_ verifiable outcome (a filed expense, a sent invoice, a booked meeting)                                              |
| File system as workspace              | Code lives in files                    | **Mostly agnostic**             | Documents, spreadsheets, generated reports, structured records — but business "objects" often live in _systems_, not files (gap §3.2) |
| Tool use via MCP                      | `git`, linters, test runners           | **Agnostic protocol**           | ERP/CRM/POS/calendar/email MCP servers                                                                                                |
| Subagents / Task delegation           | Parallel implement + review + security | **Fully agnostic**              | "Spin up 3 agents for the 3Q report" (Brief 3e example) is the _same_ primitive                                                       |
| Agents (judgment+procedure)           | dataflow-specialist, security-reviewer | **Fully agnostic**              | accounts-payable-specialist, contract-reviewer, sales-ops-specialist                                                                  |
| Skills (knowledge packaging)          | SDK patterns, cheatsheets              | **Fully agnostic**              | Company SOPs, compliance procedures, domain playbooks                                                                                 |
| Rules (path-scoped guardrails)        | "no raw SQL", "real infra in tests"    | **Fully agnostic**              | "no payment over $X without approval", "PII never leaves region"                                                                      |
| Hooks (deterministic gates)           | block `rm -rf /`, enforce imports      | **Fully agnostic**              | block out-of-policy transactions, enforce approval gates                                                                              |
| Commands (workflow orchestration)     | `/analyze` → `/todos` → `/implement`   | **Fully agnostic**              | `/close-the-books`, `/onboard-customer`, `/quarterly-report`                                                                          |
| Permission modes                      | acceptEdits / plan / bypass            | **Coding-framed, NOT adequate** | Must be replaced by graduated trust postures (§3.3)                                                                                   |
| Verification (lint, tests, LLM-judge) | compile + test = ground truth          | **Partially agnostic**          | Business work often lacks a "compiler" — verification is the harder problem for non-code                                              |
| Context mgmt (compaction, search)     | navigate large codebases               | **Fully agnostic**              | navigate large document/record corpora                                                                                                |

**Conclusion of §2:** Of the harness's ~12 core capabilities, **~9 are fully domain-agnostic and 2
are agnostic-with-caveats; only 1 (permission modes) is structurally inadequate for general work and
must be replaced.** This is the empirical basis for the "80% reuse" claim in the brief's framing.

The single biggest _coding-specific advantage that does NOT transfer cleanly_ is **the compiler/test
as automatic ground truth**. Code work has a free, instant, deterministic verifier. Most knowledge
work does not — which is why the brief's emphasis on transparency, intervention, and human-on-the-loop
posture (objectives 5a–5f) is not optional polish; it is the **substitute for the missing compiler**.

---

## 3. Gap analysis — what must be re-interfaced to serve non-coders

### 3.1 Terminal UX → conversational / multi-surface UX

**Gap:** The terminal is a coder's native habitat and a non-coder's wall. The brief (objective 3a,
3b, 3c) is explicit: users don't have to be coders; the CLI is no longer restricted to developing
programs; it is re-interfaced so users "get everything done in that single interface."

**Re-interface:** The _loop and artifacts_ stay; the _surface_ changes. Note the brief itself says
"don't have to exit the CLI" (objective 2) but Decision B keeps it capability-first — the surface is
an implementation choice deferred to plans. The realistic surface is **not a raw terminal** but a
chat-first interface (the brief's own Sequor wedge is email/WhatsApp-first per
`/Users/esperie/repos/projects/Sequor/specs/channel-coordination.md` — "email-first interface, no
separate app"). The harness becomes the _engine behind_ a conversational surface, not the surface
itself.

Evidence the ecosystem already thinks this way: envoy's `specs/channel-adapters.md` (22KB) and
`grant-moment.md` route human-facing decision moments through **channel adapters** (email, chat,
etc.), not a fixed terminal. The "surface is pluggable" design already exists in spec form.

### 3.2 File-centric model → object/record-centric model

**Gap (the deepest one).** The harness assumes the unit of work is a **file**. Business work's unit
is a **record in a system of record**: a purchase order in the ERP, an opportunity in the CRM, a
ticket in the ITSM. The agent SDK's "file system as context" is powerful for code but only partially
maps to enterprise data.

**Re-interface:** Two complementary moves:

1. **MCP servers as the object layer** — the ERP/CRM record _is_ the file-equivalent, reached
   through a business-system MCP server. The agent reads/writes records the way it reads/writes
   files. This is the cleaner path and rides the existing MCP momentum.
2. **A data-fabric / virtual-workspace layer** — where DataFlow (`pip install kailash-dataflow`)
   provides governed, multi-tenant, audited access to records as first-class objects. The platform's
   own stack already mandates DataFlow over raw SQL (`CLAUDE.md` Framework-First) and ships
   tenant-isolation + classification + audit rules
   (`.claude/rules/tenant-isolation.md`, `.claude/rules/dataflow-classification.md`).

**Uncertainty flag:** Whether business objects should be surfaced _as files in a virtual FS_ (so the
existing file tools work unchanged) or _as a distinct record-tool API_ is an open architectural
question — both are viable; neither is yet specced for this platform. (Flag for plans.)

### 3.3 Git-centric versioning → universal work versioning + intervenable replay

**Gap:** Coders get versioning for free (git). The brief (objective 5e–5f) wants something _git does
not provide_: "retrace any previous step and intervene from there; downstream/cascading outputs
change accordingly, but old outputs are versioned" + "every activity and output is traced and made
transparent."

**Re-interface — and this is where the platform's DNA is strongest.** This is not git. It is an
**append-only, signed, replayable work ledger with intervention points**. The envoy ledger spec
(`/Users/esperie/repos/dev/envoy/specs/ledger.md`, 35KB) and `runtime-abstraction.md` two-phase
signing (Phase A intent pre-execution, Phase B outcome post-execution, both signed; lines 44–49,
135–137) are exactly this:

- Every action is a signed Ledger entry with a hash chain (`ledger_append` is byte-identical hash
  chain, `runtime-abstraction.md:55`).
- Two-phase signing means _intent is recorded before the action_ — so you can intervene at the intent
  stage (the brief's "agent decides to spin up 3 agents → surfaced on screen, recorded, choose a
  posture beforehand").
- The pact platform persists the work graph in DataFlow models —
  `AgenticObjective`, `AgenticRequest`, `AgenticWorkSession`, `AgenticDecision`, `AgenticReviewDecision`,
  `Run`, `ExecutionMetric`
  (`/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py`). These ARE the
  "every activity traced" data model.

**Brief 5f's exact line** — "the only thing not transparent is how the model (black box) thinks — but
input and output are transparent" — is precisely the envoy/pact design: the _records_ (intent,
envelope, decision, outcome) are signed and transparent; the model's internal reasoning is not
claimed to be.

### 3.4 Dev-tool MCP → business-system MCP

**Gap:** Today's MCP servers in a coding harness are `git`, `filesystem`, `playwright`, `github`.

**Re-interface:** Swap the connector set. This is the _lowest-risk, highest-leverage_ gap because MCP
is already the standard and enterprise vendors are already shipping servers (§1.4). The platform
work is: (a) curate/build the business-system connector set, (b) wrap each in the
**"tools are dumb data endpoints; the LLM does all reasoning"** discipline
(`.claude/rules/agent-reasoning.md`), and (c) put governance (auth, classification, audit) _between_
the agent and the connector — which is what pact's `ApprovalBridge` + DataFlow classification already
do.

### 3.5 Permission prompts → graduated, posture-gated, intervenable trust

**Gap:** Harness permission modes are binary-ish and per-tool-call. The brief (objective 5e) wants
**L5 Autonomous / L4 Supervised / L3 Step-by-step** chosen _beforehand_ per objective.

**Re-interface:** This already exists across THREE Terrene implementations — the convergence is
striking:

| Source          | Ladder                                                                          | Path                                                                    |
| --------------- | ------------------------------------------------------------------------------- | ----------------------------------------------------------------------- |
| This repo (COC) | L1_PSEUDO_AGENT → L5_DELEGATED, per-repo, human-gated upgrades, auto-downgrades | `.claude/rules/trust-posture.md` (full ladder table)                    |
| envoy           | PSEUDO/TOOL/SUPERVISED/DELEGATING/AUTONOMOUS, envelope-pinned                   | `specs/posture-ladder.md`, `sub-agent-delegation.md:99`                 |
| aegis           | L1–L5 progressive posture state machines + cryptographic trust anchors          | `~/repos/dev/aegis/.claude/rules/trust-posture.md` (per brief §5 table) |

The brief's L5/L4/L3 maps almost 1:1 onto these. The platform does **not** need to invent the
posture model — it needs to _lift it from a per-repo CLI guardrail into a per-objective user-facing
control_.

---

## 4. Harness-agnosticism — can the product sit ON multiple harnesses, or must it own its own?

This is the central architectural decision the brief points at via envoy's multi-CLI parity thesis.
The evidence is unusually concrete because envoy already chose, and loom already operates the
multi-CLI machinery.

### 4.1 What "multi-CLI parity" actually means in the ecosystem today

loom emits the **same underlying artifact** (rule/agent/skill/command) to **three CLI targets** —
Claude Code, Codex, Gemini — with a strict parity contract
(`/Users/esperie/repos/dev/envoy/.claude/rules/cross-cli-parity.md`):

- The **neutral-body slot** is byte-identical across all three emissions (hard-block on drift).
- Only the **examples slot** (delegation syntax) may diverge: CC uses `Agent(subagent_type=...)`,
  Codex uses native delegation / `apply_patch`, Gemini uses `@specialist`.
- Frontmatter `priority`/`scope` identical across CLIs.

The hard-won lesson (`.claude/rules/cross-cli-artifact-hygiene.md`): each CLI has _different
primitives_ — different delegation syntax, different tool nouns (`Read` vs `read_file` vs
`@filesystem.read`), different hook event names (`PreToolUse` vs Codex `pre-tool` vs Gemini
`@hooks.tool_use`), different baseline files (`CLAUDE.md` / `AGENTS.md` / `GEMINI.md`). **Parity is
achievable but it is real, ongoing engineering** — the drift audit exists precisely because parity
fails silently at user time.

The Codex integration is the deepest evidence of the cost: Codex has no native hook layer, so loom
ships a **`codex-mcp-guard`** that intercepts `apply_patch` and translates CC `Edit|Write` policies
into Codex MCP policies via a bijection (`.claude/rules/multi-operator-coordination.md` §7, MUST-6).
That is a substantial bridge to give one competing harness the guardrails CC has natively.

### 4.2 The runtime-abstraction precedent (envoy's actual answer)

envoy did NOT build on a CLI harness at all for its runtime. It built a **`KailashRuntime` ABC**
(`/Users/esperie/repos/dev/envoy/specs/runtime-abstraction.md`) with two shipped implementations
(`kailash-py` pure-Python, `kailash-rs-bindings` Rust-accelerated), a **runtime picker** at first run,
and a byte-identical contract (BET-6) across runtimes. envoy's CHARTER
(`/Users/esperie/repos/dev/envoy/CHARTER.md`) is explicit: "Nothing in Envoy's distribution requires
payment, registration, commercial license acceptance, or a hosted service… A fully-open-source
runtime (`kailash-py`) is always available as a one-flag install."

**This is the most important strategic signal in the entire grounding set:** the sister project that
most directly tackles "autonomous AI where you set the boundaries" chose to **own its runtime via an
abstraction layer**, not to ride a commercial harness. It uses the CC/Codex/Gemini _artifact_ layer
(via loom) for its own development tooling, but the _product runtime_ is Foundation-owned.

### 4.3 The three architectural options (option space only — no recommendation per brief)

| Option                                                                                                                                | What it is                                                                                                                                                                                                                                                                   | Pros                                                                                                                                                                                                                                                                                                                          | Cons                                                                                                                                                                                                                                                                                                                                                                                                 |
| ------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **A. Build ON the Claude Agent SDK** (or sit on top of ≥1 commercial harness)                                                         | Use the SDK's loop+context+subagents+MCP as the engine; layer business artifacts + governance on top                                                                                                                                                                         | Fastest to a working agent loop (the SDK "handles the entire agent execution loop internally"); inherits compaction, subagent isolation, MCP auth for free; rides vendor R&D                                                                                                                                                  | **Independence conflict** — `.claude/rules/independence.md` forbids depending on a proprietary SDK; couples the product's core to one vendor's pricing/availability/roadmap; governance (posture, ledger, intervention) must be bolted _around_ a loop you don't control; the brief's "intervene at any prior step + version downstream" is hard to retrofit onto a closed loop                      |
| **B. Multi-harness parity layer** (sit ON TOP of several harnesses; product = the artifact+governance layer that targets all of them) | The loom model generalized: product ships neutral artifacts + a governance plane; each user runs whichever harness they have (CC/Codex/Gemini/OpenCode)                                                                                                                      | Meets users where they are; no runtime to maintain; the parity machinery already exists in loom; hedges vendor risk by spanning many                                                                                                                                                                                          | **Parity is perpetual tax** (evidenced by cross-cli-parity drift audits + the codex-mcp-guard bridge); lowest-common-denominator capability (Codex has no native hooks → governance is weaker there); you do NOT control the loop on ANY harness, so transparency/intervention (5e/5f) is gated by each harness's introspection surface; non-coders would still face per-harness install/terminal UX |
| **C. Build native on Kailash (Nexus/Kaizen) + own a runtime abstraction** (the envoy path)                                            | The agent loop is Kaizen (`pip install kailash-kaizen`, LLM-first agents, ReAct, Pipeline.router); the multi-channel surface is Nexus (`pip install kailash-nexus`, API+CLI+MCP unified); governance is pact+eatp; data is DataFlow; runtime is a `KailashRuntime`-style ABC | Full control of the loop → transparency, two-phase signing, intervenable replay, posture gating are _native_, not bolted on; Foundation-independent (no proprietary dependency); the entire DNA (pact models, envoy ledger, eatp posture, loom artifacts) plugs in directly; one surface for non-coders (Nexus multi-channel) | Highest build cost — you reimplement context management, compaction, subagent orchestration that the commercial SDKs give free; Kaizen/Nexus maturity for this exact use case is unproven at harness scale (uncertainty flag); slowest to first working demo; you carry the model-adapter + provider-risk surface yourself (envoy's `model-adapter.md` shows how large that is)                      |

**Hybrid worth noting (do not pre-decide):** A pragmatic middle path is **C-for-the-governed-core,
A/B-for-developer-tooling** — i.e., own the _product_ runtime (so transparency/intervention/posture
are native) while continuing to _develop the product itself_ using the CC/Codex/Gemini harnesses via
loom (as envoy already does). The brief explicitly says recommend none yet; this is the option-space
map, not a pick.

### 4.4 The decisive criterion the options turn on

The choice is **not** primarily "build speed vs cost." It is **"can the brief's transparency +
intervention + versioned-replay requirement (5e/5f) be satisfied without owning the loop?"**

- If the answer is "yes, harness introspection is enough" → Option A or B.
- If the answer is "no — you must record intent before action, gate on posture, and replay from any
  prior step with downstream re-derivation" → that is a _runtime_ capability (envoy's two-phase
  signing + ledger), which strongly implies Option C for the governed core.

The evidence (envoy chose C for exactly this reason; the commercial harnesses' permission modes are
binary and per-call, not intent-staged) tilts the _analysis_ toward "the hard requirements live in
the runtime" — but the recommendation is deferred to plans per Decision B.

---

## 5. MCP as the universal connector to enterprise systems

### 5.1 Current state (2025–2026 facts)

- **Protocol maturity:** MCP is the de-facto standard; the Claude Agent SDK, Codex, and Gemini all
  speak it. >1,000 connectors by early 2025.
- **Auth:** OAuth 2.1; MCP servers are Resource Servers, clients are OAuth clients; remote transport
  (HTTP+SSE / Streamable HTTP) since spec 2025-06-18. Enterprise pattern: a **gateway** centralizes
  OAuth flows for consistency, end-to-end logging, single point of token management
  ([mcpmanager.ai OAuth for MCP](https://mcpmanager.ai/blog/oauth-for-mcp/)).
- **Enterprise connectors:** Salesforce, HubSpot, Snowflake, Datadog, Okta, Atlassian — increasingly
  vendor-built. (Within this very session, deferred MCP tools for Atlassian, Figma, Gmail, Google
  Calendar, Google Drive were available — a live datapoint that business connectors are already at
  hand in the harness.)

### 5.2 The "tools are dumb data endpoints" principle (agent-reasoning rule)

The platform's strongest design conviction, and it maps perfectly onto MCP. From
`/Users/esperie/repos/projects/Sequor/.claude/rules/agent-reasoning.md`:

> "The LLM IS the router, classifier, extractor, evaluator. Tools are dumb data endpoints — fetch,
> store, relay. They do not decide."

Concretely (rule MUST-2): an MCP tool MUST be `get_order(id) → record`, NOT
`handle_order_issue(...)` with `if order.status == "delivered": process_return()`. **Decision logic
in tools is invisible to the LLM's reasoning trace** → unexplainable, untestable, un-improvable. This
is _the_ enforcement that makes Brief 5f's transparency possible: if reasoning lives in the LLM (whose
input/output is logged) and tools only move data (also logged), then **everything except the model's
internal cognition is transparent** — exactly the brief's claim.

This is a competitive differentiator: many enterprise "AI agents" bury business logic in tool code.
The platform's rule forbids it, which is what _enables_ the intervenable, transparent surface.

### 5.3 Governance must sit between agent and connector

The "tools are dumb" principle plus the brief's intervention requirement means the platform needs an
**enforcement point between the LLM's tool request and the actual ERP/CRM write**. pact already has
it: `ApprovalBridge` + the `_PlatformHeldCallback` pattern
(`/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/orchestrator.py:59–91`) — when a
governance verdict is `HELD`, the callback persists an `AgenticDecision` and **returns `False` to
block the action until a human approves**. That is the L4_Supervised "agent asks for one permission
before executing" of Brief 5e, already implemented.

---

## 6. Feasibility assessment — "re-interface the CLI for all work"

### 6.1 What is genuinely ready (the reusable 70–80%)

| Ready asset                                            | Where                                                                                   | Re-use for general work                                        |
| ------------------------------------------------------ | --------------------------------------------------------------------------------------- | -------------------------------------------------------------- |
| The agent loop + subagent isolation + MCP + compaction | Claude Agent SDK / any harness; Kaizen for native                                       | Domain-neutral; works as-is                                    |
| Five-layer artifact system + variant distribution      | loom + `.claude/` (this repo)                                                           | Carry business agents/skills/rules instead of coding ones      |
| Graduated trust postures L1–L5                         | `.claude/rules/trust-posture.md`, envoy `posture-ladder.md`, aegis                      | Lift to per-objective user control (Brief 5e)                  |
| Two-phase signing + append-only signed ledger          | envoy `runtime-abstraction.md`, `ledger.md`                                             | The "every step traced + intervenable" substrate (Brief 5e/5f) |
| Governed work data model                               | pact `AgenticObjective/Request/WorkSession/Decision/ReviewDecision/Run/ExecutionMetric` | The schema for transparent work tracking                       |
| Human-gate / approval bridge                           | pact `ApprovalBridge`, `SupervisorOrchestrator`, `EmergencyBypass`                      | L4-supervised execution, HITL                                  |
| "Tools are dumb endpoints" discipline                  | `.claude/rules/agent-reasoning.md`                                                      | Makes MCP connectors transparent + intervenable                |
| Multi-channel surface                                  | Nexus (`kailash-nexus`); envoy `channel-adapters.md`                                    | Non-coder-facing surface (email/WhatsApp/chat), not a terminal |
| Multi-operator coordination                            | `.claude/rules/multi-operator-coordination.md`                                          | Team-oriented work (Brief 3d) — claims, leases, gate matrix    |
| MCP enterprise connectors + OAuth 2.1                  | Ecosystem (Salesforce/SAP/Atlassian/Google)                                             | The ERP/CRM/etc. integration layer                             |

### 6.2 The hard part (the genuine 20–30%)

1. **Verification without a compiler.** Code gets free ground truth; business work does not. The
   substitute is the transparency/intervention/posture stack — which means that stack is _load-bearing
   for correctness_, not just UX. This is the single hardest conceptual problem.
2. **The object/record model (§3.2).** Bridging "files" to "systems-of-record" cleanly — whether via
   virtual-FS-over-MCP or a record-tool API — is unspecced and architecturally consequential.
3. **Intervenable replay with downstream re-derivation (Brief 5e).** "Retrace any step, intervene,
   downstream outputs change, old outputs versioned" is a _dataflow-graph re-execution_ problem. The
   ledger records it; _re-running from a mid-graph intervention point and re-deriving cascades_ is
   non-trivial. envoy's two-phase signing gives the intent/outcome anchors but not the re-derivation
   engine.
4. **Non-coder UX at the boundary moments.** Surfacing "agent will spin up 3 agents — pick a posture"
   in plain language a non-coder can act on, per `.claude/rules/communication.md` and
   `.claude/rules/recommendation-quality.md` (recommend, don't menu; translate every term). The
   harness's developer-framed prompts fail this; envoy's `grant-moment.md` is the closest spec.
5. **The runtime-ownership decision (§4)** and its cost — owning the loop buys native transparency but
   means reimplementing context management the commercial SDKs give free.
6. **Governance-at-connector enforcement that doesn't become decision-logic-in-tools** — the
   approval point must gate without violating the agent-reasoning rule.

### 6.3 Effort framing (autonomous execution cycles, not human-days)

Per `.claude/rules/autonomous-execution.md`, this is a **greenfield-leaning** program (first sessions
run ~2–3x, not the mature-COC ~10x). The work is highly _shardable_ because the reusable assets are
independent: the artifact layer, the posture layer, the ledger layer, the connector layer, and the
surface layer can each be brought up in parallel worktree shards. The _load-bearing_ shards (the
intervenable-replay engine, the object/record model, the runtime-ownership core) carry the
≤500-LOC-load-bearing / ≤5–10-invariant caps and must be sharded carefully at `/todos` time. The
_connector + artifact-porting_ shards are boilerplate-heavy and scale ~5x further before sharding
triggers. No human-day estimate is given per the rule; the honest statement is: **the reusable 70–80%
is assembly across many parallel sessions; the hard 20–30% is a small number of high-invariant
sessions that gate the rest.**

### 6.4 Honest risks / uncertainties (flagged)

- **Kaizen/Nexus at harness scale (Option C) is unproven for this exact use case** — uncertainty flag;
  needs a spike.
- **Whether harness introspection (Option A/B) can satisfy 5e/5f** is the pivotal unknown that decides
  the runtime architecture; it should be the first thing a spike resolves.
- **Object/record-model choice** (virtual-FS vs record-API) is open.
- **The brief's hypothesis** (objective 3d: "agent↔agent communication is more complete/efficient than
  human↔human") is asserted, not yet evidenced; the multi-operator-coordination + a2a-messaging specs
  give a substrate to _test_ it, but it remains a hypothesis.
- **Independence constraint hard-blocks Option A's purest form** — any design that _depends on_ a
  proprietary SDK violates `.claude/rules/independence.md`. Option A is therefore only viable as
  "develop with it, don't depend on it," which collapses toward B/C for the product core.

---

## 7. Synthesis for the platform design

1. **The harness is already a universal work runtime configured for coding.** The re-interface is
   substitution (coding artifacts → business artifacts; dev MCP → business MCP; file model → record
   model) plus _addition_ of the governance/transparency layer the commercial harnesses lack.
2. **The platform's competitive moat is not the loop — it is the transparency+intervention+posture
   layer.** Anyone can call the Claude Agent SDK. Almost no one ships signed two-phase intent/outcome
   records, graduated per-objective postures, and intervenable replay. Terrene already specced all
   three (envoy/pact/eatp). That is the 5e/5f differentiation, and it is _also_ the compiler-substitute
   that makes non-code work trustworthy.
3. **"Tools are dumb endpoints, LLM reasons" is the keystone rule** — it is simultaneously the
   MCP-connector design principle, the transparency enabler, and the differentiator vs logic-in-tools
   competitors.
4. **The runtime-ownership question is the one decision everything hinges on**, and the brief is right
   to defer it to plans. The analysis surfaces the criterion (can 5e/5f be met without owning the
   loop?) and notes envoy's prior answer (own a runtime abstraction) as the strongest precedent — but
   recommends nothing here.
5. **The Sequor comms wedge slots in cleanly as a first vertical** (Decision A): it is already
   conversational-surface-first (`specs/channel-coordination.md`), already governed
   (`specs/response-accuracy.md` D/T/R), already RAG-over-business-data
   (`specs/rag-pipeline.md`) — i.e., a narrow instance of "business MCP + LLM reasoning + governed
   transparent output" that proves the horizontal capability on one domain.

---

## Sources

**Repo files (absolute paths):**

- `/Users/esperie/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md`
- `/Users/esperie/repos/projects/Sequor/.claude/skills/30-claude-code-patterns/SKILL.md`
- `/Users/esperie/repos/projects/Sequor/.claude/guides/claude-code/13-agentic-architecture.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/agent-reasoning.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/trust-posture.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/multi-operator-coordination.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/artifact-flow.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/autonomous-execution.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/independence.md`
- `/Users/esperie/repos/projects/Sequor/.claude/rules/communication.md`, `recommendation-quality.md`, `tenant-isolation.md`, `cc-artifacts.md`
- `/Users/esperie/repos/projects/Sequor/specs/_index.md`, `channel-coordination.md`, `rag-pipeline.md`, `response-accuracy.md`
- `/Users/esperie/repos/dev/envoy/.claude/rules/cross-cli-parity.md`, `cross-cli-artifact-hygiene.md`, `deployment.md`
- `/Users/esperie/repos/dev/envoy/specs/runtime-abstraction.md`, `model-adapter.md`, `sub-agent-delegation.md`, `posture-ladder.md`, `channel-adapters.md`, `ledger.md`, `grant-moment.md`
- `/Users/esperie/repos/dev/envoy/CHARTER.md`
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/engine/orchestrator.py`
- `/Users/esperie/repos/terrene/contrib/pact/src/pact_platform/models/__init__.py`
- `~/repos/dev/aegis/.claude/rules/trust-posture.md` (per brief §5 table; not re-opened this session — cited from brief)

**Web (2025–2026):**

- [Building agents with the Claude Agent SDK](https://claude.com/blog/building-agents-with-the-claude-agent-sdk)
- [Agent SDK overview — Claude API Docs](https://platform.claude.com/docs/en/agent-sdk/overview)
- [Subagents in the SDK](https://platform.claude.com/docs/en/agent-sdk/subagents)
- [Configure permissions — Claude Code Docs](https://code.claude.com/docs/en/permissions)
- [Claude Code Hooks: All lifecycle events](https://claudefa.st/blog/tools/hooks/hooks-guide)
- [Claude Code vs Codex CLI vs Gemini CLI 2026 benchmark](https://www.codeant.ai/blogs/claude-code-cli-vs-codex-cli-vs-gemini-cli-best-ai-cli-tool-for-developers-in-2025)
- [Every CLI coding agent, compared](https://michaellivs.com/blog/cli-coding-agents-compared/)
- [MCP Authorization spec](https://modelcontextprotocol.io/specification/draft/basic/authorization)
- [MCP specs update — all about auth (Auth0)](https://auth0.com/blog/mcp-specs-update-all-about-auth/)
- [OAuth for MCP explained (MCP Manager)](https://mcpmanager.ai/blog/oauth-for-mcp/)
- [Atlassian Remote MCP Server](https://www.atlassian.com/blog/announcements/remote-mcp-server)
- [What is MCP — complete guide 2026 (HauerPower)](https://www.hauerpower.com/en/insights-posts/what-is-mcp-model-context-protocol)
