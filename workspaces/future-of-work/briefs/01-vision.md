# Brief 01 — Vision: The Agentic Work Platform

> Captured verbatim from the user's `/analyze` invocation (2026-06-05), plus the two
> scoping decisions made at the start of analysis. This is the authoritative input surface.

## 1. The disruption thesis

> "I want to totally disrupt and change the way enterprise workers use tools to advance their work."

Staff always have three things:

- **a. An objective/task** to complete
- **b. Processes/procedures** to follow — these vary from company to company
- **c. Data/information** to use

Today, staff must cross **multiple tools and interfaces**: ERP → CRM → POS → Excel → Word → internal systems → website portals, and so on. Each is a vertical silo with its own UI, data model, and learning curve.

## 2. The enabling shift

With today's autonomous agent CLI harnesses (Claude Code, Codex, Gemini), staff **don't have to exit the CLI** to get work done. They engage the main agent, and the agent utilizes all the **artifacts** (agents, skills, rules, hooks, commands) with **tools** (MCP) to execute everything.

## 3. The future of work (target state)

- **a.** Users don't have to be coders.
- **b.** The CLI is no longer restricted to creating/developing programs (its current primary work).
- **c.** The CLI is **re-interfaced for all work** — users get everything done in that single interface.
- **d.** The interface is **team-oriented** — disrupting team communication too. Hypothesis: _human-to-human communication is incomplete, inefficient, and easily misconstrued_ compared to the wealth of info and memory agents can use when talking to / instructing other agents.
- **e.** Pursue **PACT/EATP** and the projects **Envoy** and **Aegis** to see how HITL, HOTL, trust postures, and permission envelopes are used. Make **all human↔agent and agent↔agent communications/working steps transparent and interveneable.**
  - Example: user says "I want 3Q financial report" → agent decides to spin up 3 agents → **these decisions are surfaced on screen, recorded**, and users can choose a **posture beforehand**:
    - **L5 Autonomous** — agent goes ahead
    - **L4 Supervised** — agent asks for one permission before executing
    - **L3 Step-by-step** — agent pauses at each step
  - Users can **retrace any previous step and intervene from there**; downstream/cascading outputs change accordingly, but **old outputs are versioned**.
- **f.** In essence, **every activity and output is traced and made transparent.** The only thing not transparent is how the model (black box) thinks — but **input and output are transparent.**
- **g.** For maximal usability and best practices, **artifacts are easily created, modified, stored, and shared across organizations and teams.**

## 4. Scoping decisions (made at analysis start)

### Decision A — Comms is a wedge, not the product

The existing Sequor product (an AI email/WhatsApp **communication-coverage layer**: RAG, tenant isolation, daily digest, deployed on Vercel + Neon) is **subsumed as one early vertical/wedge** inside the broader platform. The analysis targets the platform AND shows how the comms capability slots in as a landing use-case.

### Decision B — Capability-first; GTM deferred

> "It's too early to decide [the beachhead]. We build the capability from a disrupted work habit/approach (from vertical systems like ERP/CRM to agnostic-agentic-driven autonomous work) first, then we decide [GTM] later."

The analysis prioritizes proving the **core capability** — the work-paradigm shift from vertical systems to an agnostic, agentic, autonomous work interface. It keeps the architecture horizontal/agnostic (the reusable core). It does **not** prematurely lock a beachhead vertical, though it may surface candidates.

### Decision C — D/T/R confirmed (analysis-review gate, 2026-06-15)

Confirmed by the owner: in this platform **D/T/R = Department / Team / Role** (the PACT accountability/addressing grammar), NOT "Decision / Task / Review". The target-state specs already use the correct expansion; this confirmation makes it authoritative for all downstream phases.

### Decision D — Agent-mediated communication is a SETTLED founding thesis (analysis-review gate, 2026-06-15)

Confirmed by the owner: the premise that **agent-mediated communication is richer / less lossy than human↔human communication** (brief §3d) is **settled** — a **founding assumption** of the product, not a hypothesis to validate-first.

- **Effect on downstream phases:** the platform is BUILT on this premise. `/todos` and the plans MUST NOT gate the build behind an "agent-comms validation spike"; agent-mediated team coordination (the multi-human + multi-agent substrate) is foundational. The prior `[BET]` / "unproven, validate-first" framing in the analysis corpus (esp. `09-risks-failure-points.md`, `06-network-effects.md`, `03-unique-selling-points.md`) is **superseded by this decision for forward planning.**
- **Honest carry-forward (advisor note, retained):** external evidence for the premise remains thin, so investor/buyer-facing material should present it as the product's **founding conviction** (not as externally-established fact), and the comms lighthouse should still gather corroborating evidence opportunistically — at zero gating cost.

## 5. Reference material (located during discovery, 2026-06-05)

The platform's trust/governance/coordination DNA already exists across the Terrene/Kailash ecosystem. The analysis MUST ground in these:

| Project                         | Path                                                    | Relevance                                                                                                                                                                                                                                                                    |
| ------------------------------- | ------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **loom**                        | `~/repos/loom`                                          | COC artifact management platform — the five-layer artifact system (agents/skills/rules/hooks/commands), variant overlays, Gate-1/Gate-2 distribution. Source of "artifacts created/modified/stored/shared."                                                                  |
| **kailash-coc-claude-py / -rs** | `~/repos/loom/kailash-coc-claude-{py,rs}`               | USE-templates: how artifacts + multi-operator coordination are packaged for a project.                                                                                                                                                                                       |
| **pact**                        | `~/repos/terrene/contrib/pact`                          | Governance: D/T/R accountability, operating envelopes, knowledge clearance, SupervisorOrchestrator, ApprovalBridge, EventBridge, EmergencyBypass, Decision/ReviewDecision models.                                                                                            |
| **eatp**                        | `~/repos/loom/kailash-py` (+ skill `26-eatp-reference`) | Enterprise Agent Trust Plane: TrustPlane / BudgetTracker / PostureStore. HITL/HOTL realization.                                                                                                                                                                              |
| **aegis**                       | `~/repos/dev/aegis`                                     | Commercial Quartet (CARE/PACT/EATP/CO) implementation: progressive posture **L1–L5 state machines**, cryptographic trust anchors, multi-operator coordination, onboard/certify lifecycle hooks. Closest existing implementation of the "posture + interveneable steps" idea. |
| **envoy**                       | `~/repos/dev/envoy`                                     | Multi-CLI parity + deployment specs (Claude Code / Codex / Gemini), cross-language bindings. Foundation for an interface that is harness-agnostic.                                                                                                                           |
| **Sequor (this repo)**          | `~/repos/projects/Sequor`                               | Current comms-coverage product (the wedge) + this COC setup.                                                                                                                                                                                                                 |

## 6. What this analysis must deliver

Per the `/analyze` COC phase: deep research (`01-analysis/01-research/`), product analysis (value propositions, USPs, platform model, AAA framework, network effects, the 80/15/5 reuse breakdown, risks), plans (`02-plans/`), user flows (`03-user-flows/`), and target-state `specs/`. Then red-team for gaps and brief→spec traceability.
