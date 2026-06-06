# 03 — Unique Selling Points

> Workspace: `future-of-work` · Phase 01 (analyze) · Product analysis
> Anchored on the strategic spine (Phase A) and the four moats **M1–M4**. Grounds every
> claim in `01-research/07-competitive-landscape.md` (esp. §9, §11), `06-transparency-intervention-versioning.md`,
> `01-coc-artifact-system.md`, `02-multi-operator-coordination.md`, or the brief.
> Effort framed in autonomous execution cycles, not human-days. Competitors named
> factually, never as "the X of Y" (Foundation-independence constraint).

---

## 0. What a USP is — and what this document refuses to do

A **value proposition** answers "why is this good?" A **unique selling point (USP)** answers a
harder question: **"why is this platform the ONLY credible choice for a specific buyer need —
and why can't a well-funded competitor simply copy it next quarter?"**

The difference matters because the market is loud. Research 07 §0 is blunt: "Almost every claim
in the vision is asserted by someone; very few are delivered well, and **nobody delivers the full
combination**." A USP that any competitor also markets is not a USP — it is table stakes wearing a
crown. So this document applies one filter to each candidate moat:

1. **Is it genuinely unoccupied?** (Does a real buyer need go unmet by every shipping product?)
2. **Is it defensible?** (Is there a moat — ecosystem DNA, a trust/provenance layer, or the
   conjunction itself — that survives a competitor's attempt to copy it?)
3. **Who is closest, and why do they not deliver THIS?** (The honest counter.)
4. **Is it PROVEN or a BET?** (Does the capability exist and work, or is it a hypothesis we hope holds?)

**Plain-language note for a non-technical reader.** Throughout, "the platform" means the proposed
product: one interface where a worker states what they want done, and AI agents do the cross-system
legwork (instead of the worker hopping between ERP, CRM, spreadsheets, documents, and portals).
Every technical term is translated on first use. Where a claim is a bet, it is labelled a **BET** —
not hidden behind confident prose.

**What this document refuses to do:** rank the surface thesis ("an agent does your work in one
interface") as a USP. It is not one. Research 07 §3 names the most direct embodiment of that surface —
**Claude Cowork** ("Claude Code for the rest of your work," GA April 2026) — and §10 warns: "If the
vision's only differentiation were 'agent does your work in one interface,' it would already be late."
The USPs below all live in the **substrate** beneath the surface, where Cowork has not yet built.

**The Cowork VELOCITY caveat (read the gap as present-tense, not static).** Every "where Cowork has not
yet built" claim in this document is a **snapshot of the present**, not a standing property. Cowork is
the **fastest shipper** in the category — research 07 §10 records "12 features in ~12 weeks" and ~2-week
iteration. The substrate moats below are unoccupied **NOW**; they are not guaranteed unoccupied later,
and the gap narrows every fortnight Cowork ships surface (and could close on a moat term outright if a
well-resourced incumbent productizes versioned cascade or multi-human coordination — the existential
case in 09 §5 _Competitive risk_). So read each USP's "Cowork doesn't deliver THIS" as **a window the
platform is racing to occupy**, not a permanent vacancy. This is why the recommendation (§8) sequences
on the conjunction and on speed-to-substrate, and why 09 §5 makes the competitive window a first-class
risk rather than a footnote.

---

## 1. The four candidate USPs (M1–M4), stated plainly

Before scrutiny, here are the four moats in one sentence each, as a buyer would hear them.

| Moat   | The USP, in one plain sentence                                                                                                                                                                                                                                                                                                             | Differentiator (research 07 §9)  |
| ------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------- |
| **M1** | "Rewind your work to any earlier step, change it, and only the affected results recompute\* — while the old results are kept as versions you can always go back to." (\*v1 default: untouched steps **reuse their recorded output** rather than re-running the AI, so the "only-affected" guarantee is bounded by determinism — see §2.2.) | (b) — the strongest moat         |
| **M2** | "Decide up front how much freedom the agent gets per task (do-it-all / ask-once / pause-at-every-step), with budgets, clearance, and an audited emergency override — all built into how the work runs, not bolted on after."                                                                                                               | (f)+(b) — file-verified DNA      |
| **M3** | "Multiple people AND multiple agents work on the same job at once, with a tamper-proof record of who did what, conflict-detection, and two-person sign-off on high-stakes actions."                                                                                                                                                        | (c-human) — partial whitespace   |
| **M4** | "Create a reusable piece of work-knowledge once, then share it across teams and organizations — with provenance, versioning, and a way to recall a bad one everywhere at once."                                                                                                                                                            | (e)+(g) — network-effects engine |

The rest of this document scrutinizes each — defensibility, the honest counter, and the
proven-vs-bet verdict — then ranks them and recommends a lead + sequencing.

---

## 2. M1 — Versioned, intervene-from-any-step agentic work

### 2.1 The USP, plainly

Today, when an AI agent does a multi-step job for you and step 4 of 9 was wrong, your options are
bad: re-run the whole thing (slow, expensive, and the agent may now produce a _different_ answer at
every step because AI is non-deterministic), or accept the flawed output. **M1 makes a third option
exist for a non-coder:** point at step 4, change the input or the decision, and the platform
recomputes **only what actually depended on step 4** — leaving steps 1–3 untouched and **keeping the
old version of everything** so nothing is lost and you can compare or roll back.

In the brief's own example (§3e): "I want a 3Q financial report" → the agent fans out to 3
sub-agents → you later realize the revenue assumption in one branch was wrong → you retrace to that
step, fix it, and only that branch and its dependents re-run; the original report survives as a prior
version.

### 2.2 The defensibility argument (the moat)

The moat here is **the conjunction of three things that exist separately but have never been combined
into a non-coder product**:

1. **The mechanism is proven — as a developer primitive only.** Research 07 §2 is precise: the
   "replay/time-travel capability LangGraph 1.2 ships is the single most important competitive fact"
   — the underlying engine (re-run a workflow from a saved checkpoint) **already exists as
   open-source.** But it is "only a developer primitive, never surfaced as a non-coder 'retrace any
   step and intervene; downstream re-runs; old outputs are versioned' product experience." The gap is
   **to productize, not invent** (§2 closing line).

2. **The 80% substrate already exists in the ecosystem.** Research 06 §1 found that the data model
   this needs is _already built_ in the PACT platform: work is recorded as immutable, content-fingerprinted
   steps and outputs (`Run`, `AgenticArtifact` with `content_hash` + `version` + `parent_artifact_id`),
   with dependency edges (`AgenticRequest.depends_on`) that are "already a DAG edge set." ("DAG" = a
   map of which step feeds which — the thing you walk to know what to recompute.) The genuinely-novel
   20% is one component: the **reactive cascade engine** that walks that map, recomputes only the
   dirty downstream steps, skips steps whose inputs did not actually change (the
   content-fingerprint trick that bounds cost), and writes each re-run as a new version (research 06 §7).

   **The determinism asterisk (carried plainly, not glossed).** The "only-affected recompute" guarantee
   rests on the content-fingerprint trick — a step is skipped because its input fingerprint is unchanged,
   so its _recorded_ output is reused. But AI steps are **non-deterministic**: re-running one does not
   reproduce the prior answer. The architecture handles this honestly (07 §5.3): on a rewind, **v1
   defaults to reuse-recorded-output** for every step the user did not explicitly change (deterministic
   "replay"), and only the steps the user _did_ change — plus their genuinely-affected downstream — are
   re-generated, with a per-step user choice (_"re-run with my edit / keep the recorded output"_) where
   it matters. So the "only-affected" claim is precise **for the reuse-recorded-output default** and
   **bounded by determinism** for the re-generate path (a re-run can legitimately diverge in ways that
   are correct but surprising). This is exactly the **reduced-M1 v1** that 09 §2.4 recommends shipping
   (linear retrace, reuse-recorded-output default, branching deferred) — the headline is the
   reuse-default guarantee, not an unqualified "everything else is frozen."

3. **The conjunction is the moat, not any one piece.** A competitor can copy time-travel (it is OSS).
   A competitor can copy audit trails. A competitor can copy versioning. What is hard to copy is **all
   of it composed into a surface a non-coder can drive, over non-deterministic AI steps, with the
   versioning UX solved.** Research 06 §0 names exactly this: "the genuinely novel 20% is the
   _composition_ — specifically the reactive-cascade re-execution over a content-addressed provenance
   DAG with branch/fork semantics, which no single repo in the ecosystem has assembled yet" — and no
   competitor has either.

### 2.3 The honest counter — who is close, and why they don't deliver THIS

- **LangGraph (on the M1 mechanism).** The closest on the _engine_. It ships first-class time-travel
  and checkpoint replay (research 07 §2). **Why it doesn't deliver THIS:** it is "developer-only; no
  non-coder surface" (07 §2 table). A business user cannot drive it; the versioning is a debugging
  tool for engineers, not a "rewind your report" experience. Also, per the Diagrid source cited in 07
  §2, checkpoints are not the same as durable execution — the mechanism has rough edges even for
  developers. M1's bet is to make this _legible and safe_ for someone who has never seen a terminal.

- **Compliance/audit tools (on transparency).** They record what happened. **Why they don't deliver
  THIS:** an audit trail is read-only history; M1 is _interactive history_ — you don't just see step
  4, you edit it and watch the consequences recompute. Research 07 §9(b): "audit trails exist in
  compliance tools" is in the "crowded" column; "versioned cascade re-execution" is in the empty one.

- **Claude Cowork (on the surface).** It does multi-step deliverables in one interface. **Why it
  doesn't deliver THIS:** research 07 §3 explicitly lists "no productized versioned cascade
  re-execution" as a Cowork gap. Cowork can redo work; it cannot rewind-and-selectively-recompute
  with old versions preserved.

### 2.4 Proven or a BET?

**The substrate is PROVEN; the headline experience is a BET — and it is the platform's single highest
execution risk.** Research 07 §10(3): "Versioned cascade re-execution is hard (non-deterministic LLM
steps; non-coder versioning UX). It is the best moat _and_ the highest execution risk." Research 06
§8 names the specific open product questions: _should_ a rewind re-run the AI (fresh answer) or reuse
the recorded one? (likely user-selectable per step); how do you prevent a change near the root from
re-running everything (cost-preview before committing); how does a non-coder even _see_ a branching
version history without it looking like a developer's git graph?

Verdict: **strongest moat, biggest bet.** The capability is buildable on existing parts (research 06
§7 estimates ~4–6 autonomous execution cycles to a working end-to-end version over the comms-wedge
flow, because L1/L2/event-stream/posture/durable-store are reused), but the non-coder UX over
non-deterministic steps is unsolved design work that no competitor has solved either — which is
exactly why it is the moat.

---

## 3. M2 — Execution-time, posture-graded governance

### 3.1 The USP, plainly

Before the agent starts a task, **you choose how much rope it gets** — and the platform enforces that
choice _as the work runs_, not as a report you read afterward. The brief's three levels (§3e):

- **L5 Autonomous** — the agent plans and executes the whole job on its own.
- **L4 Supervised** — the agent asks for one permission before it executes the plan.
- **L3 Step-by-step** — the agent pauses at every step for you.

Plus: spending **budgets** (stop at $X), **clearance** (this agent may not touch payroll data), and a
governed **emergency override** ("break glass" with a full audit trail and an auto-expiry). "Posture"
is just the plain idea of _a stance you set in advance for how supervised the agent is._

### 3.2 The defensibility argument (the moat)

The moat is **ecosystem DNA that bakes governance into the execution substrate itself** — the home-field
advantage research 07 §7 calls out by name. Most governance vendors _observe and gate someone else's
agents_ from the outside; the platform's DNA _bakes posture, approval, budget, emergency-bypass, and
signed audit into how the work actually runs._ This is verified against real files, not slides:

- The L5/L4/L3 ladder **already exists as a shipped 5-rung state machine** (research 07 §7 table;
  06 §4.3): the EATP/aegis `L1↔L5` posture ladder maps 1:1 onto the brief's ask. Downgrades fire
  automatically on a violation; upgrades require a human (research 02 §8.3) — so an agent can never
  promote itself.
- The "ask one permission before executing" gate **exists** (PACT `ApprovalBridge` persists a decision
  and blocks until a human approves — 07 §7, 06 §4.2).
- The "agent decides to spin up 3 agents → surfaced and recorded" pipeline **exists** (PACT
  `SupervisorOrchestrator` + a live agent→screen event stream — 06 §4.1).
- Governed "break glass" with audit and auto-expiry **exists** (PACT `EmergencyBypass`, time-limited
  4h/24h/72h tiers — 07 §7).

Research 06 §4.2 found the one genuinely-new piece is small: a new "plan*proposed" decision type that
surfaces the fan-out \_plan* as an inspectable object before execution, gated by the chosen posture —
"~1 cycle of integration, not greenfield."

### 3.3 The honest counter — who is close, and why they don't deliver THIS

- **AI governance / TRiSM vendors (the named category).** Research 07 §7: Gartner groups this as "AI
  TRiSM" (Trust, Risk, Security Management) — a fast-filling category of well-funded observability
  vendors. **Why they don't deliver THIS:** they are mostly **bolt-on observe-and-gate** — they watch
  agents and flag problems; they do not _run_ the agents. The platform's edge is being
  **execution-time native** (07 §10(6)). The risk, stated honestly: this edge "must be made legible to
  buyers or it reads as 'yet another governance tool.'"

- **Suite vendors (ServiceNow, Salesforce, SAP, Microsoft).** Each ships governed agent execution.
  **Why they don't deliver THIS:** their governance is suite-native and vertical by business model
  (07 §3) — it governs _their_ agents on _their_ data. It cannot govern an agnostic, cross-vendor
  workflow because that is against their model.

- **Claude Cowork.** Has enterprise controls (SCIM, groups). **Why it doesn't deliver THIS:** research
  07 §3 lists "no posture-graded L3/L4/L5 _pre-set_ intervention model" and "governance/audit is
  lighter than PACT-grade" as Cowork gaps. Cowork governs access; it does not let you pre-set, per
  objective, how autonomous the agent is — with budgets and clearance — enforced live.

### 3.4 Proven or a BET?

**Largely PROVEN.** This is the most file-verified of the four moats (research 07 §7 maps every brief
element to a real, running implementation). The regulatory tailwind is real (EU AI Act Article 14
human-oversight, enforceable Aug 2, 2026 — 07 §7), which makes this a _buyable_ USP, not just a clever
one. The residual risk is **positioning** (making "execution-time native" legible vs. bolt-on), not
**capability.** This is the safe-to-promise moat.

---

## 4. M3 — Multi-human + multi-agent shared work substrate

### 4.1 The USP, plainly

A whole team — **several humans and several agents** — works on one job at the same time, on one
shared record, without stepping on each other. The platform tracks who claimed which piece (so two
people don't redraft the same section), keeps a tamper-proof log of every action, and requires
**two different people** to sign off on high-stakes actions. "Substrate" just means _the shared
foundation everyone works on top of._

### 4.2 The defensibility argument (the moat)

The moat is **deep, rare DNA on the human-multiplicity half** — and the discipline to differentiate
there rather than on agent-to-agent coordination, which is already commoditized. Research 07 §9(c) is
explicit: agent↔agent coordination is "crowded" (the A2A protocol owns it — 150+ orgs, in production);
"multiple _humans_ coordinating on one shared agentic substrate" is "genuinely sparse."

The ecosystem has a complete, cryptographically-grounded substrate for exactly this (research 02 §0):
a signed, append-only coordination log; claims/leases with conflict classes (SAME / ADJACENT /
INDEPENDENT — research 02 §3); cryptographic attribution (every action signed, resolving to exactly
one person — 02 §4); a single-writer lease so two people don't clobber a shared deliverable (02 §5);
and **two-person sign-off** on high-stakes actions (the "4-eyes on person_id" gate — 02 §9.1). The
work-item model to generalize "claim a file" → "claim a task" already exists in PACT (02 §1.2). The
reuse read: ~80% exists, ~15% is re-targeting it from code files to general work items, ~5% is net-new
(giving agents their own signed identity so an agent's autonomous output is attributable to both the
agent and the human accountable for it — 02 §10.3).

There is a structural sub-argument that _is_ defensible and worth stating carefully: research 02 §2.3
shows the coordination log makes "who said what, when, and was it tampered with" a **cryptographic
question, not a he-said-she-said one** — two divergent records at the same position are a mathematical
contradiction that _names the equivocator._ That is a real, hard-to-copy property.

### 4.3 The honest counter — who is close, and why they don't deliver THIS

- **A2A and every multi-agent framework (on agent coordination).** They let agents "discover
  capabilities, negotiate task delegation, form teams" (07 §8). **Why they don't deliver THIS:** they
  coordinate _agents_, not _humans_. The brief's differentiator is the human-multiplicity half (07
  §9(c) verdict: "Differentiate on the human-multiplicity substrate, not on 'agents form teams' — A2A
  owns that"). Competing on agent-to-agent here would be competing where we lose.

- **Collaboration suites (the implicit incumbent).** Google Workspace / Microsoft 365 let many humans
  co-edit. **Why they don't deliver THIS:** they have no cryptographic attribution, no signed
  tamper-proof coordination log, no claims/leases over _agentic work items_, no two-person gate over
  agent actions. Co-editing a doc is not coordinating a multi-agent job.

### 4.4 Proven or a BET? — with one honest caution flagged loudly

**The substrate is PROVEN; one adjacent hypothesis is an UNPROVEN BET, and they must be kept separate.**

- **PROVEN:** the coordination substrate exists and runs today for human operators coordinating on a
  codebase (research 02 §0). Re-targeting it to general work is adaptation, not invention.
- **THE BET (flag loudly):** the brief's §3d hypothesis that _agent-to-agent communication is richer
  and less lossy than human-to-human_ is, per research 07 §10(2), "an unproven, contrarian
  hypothesis. No external evidence supports it; it could be wrong or culturally rejected. Treat as a
  research bet to validate, not a settled USP." Research 02 §10.2 confirms: the substrate _supports_
  the hypothesis structurally (an agent reading the full log has more context than a human reading a
  Slack thread) **but does not yet realize the channel** (agents today coordinate _through_ their
  human's identity, not as themselves).

**The discipline this forces:** M3's USP is "many humans + many agents on one tamper-proof shared
substrate" (proven, defensible). M3's USP is **NOT** "agent comms beat human comms" (a bet). Marketing
the bet as the USP would stake the platform's credibility on an unvalidated, possibly culturally-rejected
claim. Two open scaling risks also temper M3 (research 02 §11): the substrate was designed for ~12
operators on one repo; whether it survives thousands of participants is unproven, and whether a "same
work item" conflict should _halt_ (one writer) or _merge_ (both contribute) is an undecided product
question.

---

## 5. M4 — Governed, versioned, provenance-tracked cross-org artifact exchange

### 5.1 The USP, plainly

A team builds a reusable piece of work-knowledge once — a procedure, a checklist, a specialized
agent — and **shares it with other teams and other organizations**, with three things no marketplace
offers together: **provenance** (you can see who made it and where it came from), **versioning** (you
get updates and can roll back), and **recall** (if a shared artifact turns out to be bad, it can be
pulled from everyone who uses it, at once). "Artifact" here just means _a packaged, reusable bit of
how-to-do-the-work._

This is the brief's §3g ("artifacts easily created, modified, stored, and shared across organizations
and teams") and, per research 07 §11, the platform's **primary network-effects engine** — each shared,
governed artifact raises the value of the platform for everyone.

### 5.2 The defensibility argument (the moat)

The moat is **a trust/provenance layer on top of a commoditizing marketplace** — plus a genuinely-new
piece: a trust model for _untrusted_ publishers.

Research 01 §0 found the sharing machinery already exists and runs in production (the loom artifact
system: a five-layer taxonomy, a two-gate distribution model, variant overlays so one artifact adapts
per context, a proposal lifecycle, and — critically — a **recall primitive** that purges a bad artifact
from 30+ consumers on the next sync, 01 §2d). The reuse read (01 §0): ~80% directly reusable, ~15% to
adapt (cross-_org_ boundaries vs. cross-repo; a discovery/search surface; de-coupling from "codegen"),
~5% genuinely new.

The genuinely-new 5% **is** the moat (research 01 §7c): today's threat model is _bounded-trust_ — the
adversary is a legitimate team member. A cross-org marketplace faces **untrusted publishers**, and
"signed-artifact provenance from an _external_ publisher is not yet modeled." The cryptographic
substrate to build it exists (signing keys, hash-chained logs, quorum); the untrusted-publisher trust
model is the net-new design. Research 07 §9(e) verdict: "sharing is crowded; _governed + versioned +
provenance-tracked cross-org_ sharing is open. The moat is the trust/provenance layer, not the
marketplace itself."

### 5.3 The honest counter — who is close, and why they don't deliver THIS

- **Skills / MCP marketplaces (on the surface).** Research 07 §9(e): the market went "from one
  registry (Dec 2025) to eight by Q2 2026," 20,400+ skills, 9,900+ MCP servers, even enterprise
  "Agent Skills Registries." This is the most crowded surface of the four. **Why they don't deliver
  THIS:** they are "publish/consume directories; they lack the loom-style Gate-1/Gate-2 distribution,
  variant overlays, proposal lifecycle, and disclosure-scrub on intake" (07 §9(e)). They share; they
  do not _govern_ sharing. Critically, research 01 §7c: they lack the recall primitive and the
  untrusted-publisher trust model — the two things that make cross-org sharing _safe_ rather than just
  _possible._

- **Package registries (npm, PyPI — the structural analogy).** They have versioning and (weak)
  provenance. **Why they don't deliver THIS:** they have no governed distribution with human
  classification, no variant overlays (one artifact, many adaptations), no built-in recall that
  reaches every consumer, and they are for _code_, not non-coder work-knowledge.

### 5.4 Proven or a BET?

**The distribution machinery is PROVEN; the cross-org trust model is a BET.** The splitter, overlays,
proposal lifecycle, and recall run in production today (research 01 §2). The bet is the
untrusted-publisher trust model — and research 01 §7d flags it as a **novel-architecture decision that
must be designed before the registry surface is built, since it constrains it.** Estimated effort
(research 01 §7d, autonomous-execution framing): generalizing tiers + org-axis overlays ~1 session;
the cross-org publish/subscribe surface ~3–5 sessions; the untrusted-provenance trust model is
greenfield design (~2–3× first-session factor). A second honest caveat (research 01 §8): today's
artifacts are hand-authored Markdown/JS — the non-coder authoring UX ("observe my work, propose an
artifact") is itself unbuilt.

---

## 6. The foundation (NOT a USP) — agnosticism via MCP/A2A + multi-CLI parity

One thing the strategic spine is emphatic about, and this document honors: **agnosticism is the
foundation, not the headline.** "Agnostic" means the platform isn't locked to one vendor's AI model,
one suite, or one terminal — it talks to any system via open standards (MCP for tools, A2A for agents)
and runs identically across multiple agent harnesses (the envoy multi-CLI parity DNA — research 07 §9(a)).

Why this is foundation, not USP: research 07 §8 + §10(5) are unambiguous — **"Connectivity (MCP/A2A) is
commodity. Not a differentiator; only governed connectivity is."** MCP is an open standard donated to
the Linux Foundation; 97M monthly downloads; everyone gets it. Selling "we're agnostic" as the moat
would be selling table stakes. The _value_ of agnosticism is that it **enables** M1–M4 (it is what lets
the agent be the integration layer across all the worker's systems) — and it is real whitespace at the
_product_ layer (every shipping "AI workforce" is suite-locked by business model, 07 §9(a)). But it is
load-bearing infrastructure, not the pitch.

---

## 7. Ranking the USPs by defensibility

Defensibility = (genuine whitespace) × (hardness to copy) × (strength of the moat) — discounted by
execution risk and by whether the moat is proven or a bet. Here is the honest scoring.

| Rank | USP    | Whitespace (07 §9)            | Moat type                            | Proven / Bet                          | Execution risk | Defensibility verdict                                                                                                                                                   |
| ---- | ------ | ----------------------------- | ------------------------------------ | ------------------------------------- | -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1    | **M1** | Strongest (the empty one)     | The conjunction (composition)        | Substrate PROVEN; experience BET      | **Highest**    | **Highest ceiling.** Nobody is close on the non-coder versioned-cascade experience. Hardest to copy _and_ hardest to build.                                             |
| 2    | **M4** | Open (governance layer)       | Trust/provenance layer + recall      | Machinery PROVEN; cross-org trust BET | Medium         | **Strongest network-effects moat.** Each shared artifact compounds value; the trust layer is the un-copyable part.                                                      |
| 3    | **M2** | Crowded category, native edge | Ecosystem DNA (execution-native)     | Largely PROVEN                        | **Lowest**     | **Most defensible _today_** — file-verified, regulation-backed. Lower ceiling: the category is filling, so the edge is "native vs bolt-on," which must be made legible. |
| 4    | **M3** | Partial (human half)          | Cryptographic coordination substrate | Substrate PROVEN; "agent-comms" BET   | Medium-High    | **Real but narrowest.** Defensible on human-multiplicity; must NOT lean on the unproven agent-comms hypothesis; scaling unproven.                                       |

**Why M1 ranks first on defensibility despite the highest risk.** Defensibility is about _the moat_,
and M1's moat is the deepest: it is the one differentiator research 07 calls "the strongest moat" and
"the clearest 'almost nobody does this well'" (§9(b)). The mechanism is OSS (copyable) but the
_conjunction_ — non-coder surface + non-deterministic steps + solved versioning UX — is what no one has
assembled. A competitor copying M1 inherits the same hard problem we do; that is precisely what makes
it defensible.

**Why M2 ranks third on defensibility despite being the most proven.** M2 is the _safest_ moat but not
the _deepest._ The governance category (TRiSM) is actively filling with funded vendors (07 §10(6)). The
edge — execution-time-native vs. bolt-on — is real and file-verified, but it is an edge _within_ a
recognized category, not an unoccupied one. Defensibility ≠ readiness; M2 wins on readiness (§9) and
places third on defensibility.

---

## 8. Recommendation — lead USP, sequencing, and the symmetric trade-offs

### 8.1 The recommendation

**Lead with M1 (versioned, intervene-from-any-step) as the headline USP — but ship M2 (posture-graded
governance) FIRST as the credibility-and-revenue foundation, with M1 as the differentiating capability
built on top of it. Treat M4 as the long-game network-effects engine seeded in parallel, and M3 as a
supporting capability that rides M2+M3's shared coordination substrate — never as a standalone pitch,
and never leaning on the unproven agent-comms hypothesis.**

In one line: **M1 is the story you tell; M2 is the ground you stand on while you build the story; M4 is
the compounding asset; M3 is the team-scale enabler underneath.**

### 8.2 Why this sequencing (the implications)

- **M2 first** because it is the lowest-risk, most-proven, regulation-backed moat (research 07 §7,
  §11; EU AI Act Aug 2026). It is also the _substrate_ M1 needs: M1's "retrace any step" UI consumes
  the same recorded, posture-stamped step log that M2 produces (research 06 §6 — the transparency UI
  sits directly on the governed-execution layer). Building M2 first means M1 is built on running,
  trusted ground, not greenfield. M2 alone is a sellable product (governed agentic work), which de-risks
  the whole effort: there is a credible offering even if M1's hard UX takes longer than hoped.

- **M1 as the headline** because it is the only differentiator that cannot be matched by Cowork or a
  suite vendor in a quarter (research 07 §9(b), §10(1)). The surface ("agent does your work") is
  already late; M1 is the substrate property that is genuinely unoccupied. Leading the _story_ with M1
  while _shipping_ M2 first lets the platform be sellable early and differentiated deeply.

- **M4 in parallel, seeded early** because network effects compound over time (research 07 §11: "each
  shared, governed artifact raises platform value") and because its hardest piece — the
  untrusted-publisher trust model — "must be designed before the registry surface is built" (research
  01 §7d). Seeding the design early (even before the marketplace surface ships) prevents a costly
  re-architecture. The distribution machinery is already proven (01 §2), so the parallel cost is mostly
  the trust-model design, not a full build.

- **M3 underneath, not out front** because its defensible half (human-multiplicity coordination) shares
  the same signed-log + posture substrate as M2 (research 02 §10.1 — the mapping table shows M2 and M3
  reuse the same coordination log and posture ladder), so it is cheap to add once M2 exists; and because
  its tempting half (agent-comms-beat-human-comms) is an unvalidated bet (07 §10(2)) that must be run as
  a _research experiment_, not marketed as a USP.

### 8.3 The comms wedge as the proving ground (Decision A)

The recommendation has a concrete first vertical: **prove M1+M2 on the existing comms-coverage product
(Sequor) before generalizing.** Research 06 §6.2 shows the comms flow (Message → Classification →
Retrieval → Response → send/escalate) is "a small, concrete instance of the general DAG" — a 4-step
work graph. Wiring retrace-and-intervene to a 4-step flow proves the capability on a bounded surface
before facing arbitrary multi-agent objectives. This is the lowest-risk path to a _working_
demonstration of M1, on a product that already exists and already exercises the governance/audit
substrate M2 provides. It also honors Decision B (capability-first, beachhead deferred): proving M1+M2
on the wedge builds the horizontal capability without prematurely locking a GTM vertical.

### 8.4 Pros and cons of this recommendation (symmetric — the cons are real, not glossed)

**Pros:**

- **Sellable early, differentiated deeply.** M2-first means there is a credible, governed-agentic-work
  product to sell while M1's hard UX matures — the platform is not hostage to the riskiest moat shipping
  first.
- **M1 built on proven ground.** The transparency/intervention UI consumes M2's governed-execution log
  (research 06 §6), so the headline capability is built on a running substrate, not greenfield.
- **De-risked headline.** Leading the _story_ with M1 while _shipping_ M2 first decouples
  differentiation from execution risk — the pitch is deep even before M1 fully lands.
- **Compounding asset seeded early.** M4's trust-model design starts before the marketplace surface,
  avoiding the re-architecture research 01 §7d warns about.
- **Cheap M3.** M3's defensible half rides M2's substrate (research 02 §10.1), so team-scale
  coordination is near-free once M2 exists.

**Cons (real, not glossed):**

- **M1 may slip.** The headline USP is the highest-execution-risk item (07 §10(3)); the non-coder
  versioning UX over non-deterministic steps is unsolved by anyone. If it slips badly, the platform
  leads its _story_ with a capability it cannot yet fully ship — a credibility risk. **Mitigation:**
  the comms-wedge proving ground (§8.3) forces an early, bounded demonstration; if M1 cannot work on a
  4-step DAG, that is known before it is the headline.
- **M2 looks like "yet another governance tool" if positioning fails.** The category is filling (07
  §10(6)); "execution-time native vs. bolt-on" is a real edge but a subtle one to a buyer.
  **Mitigation:** M2's value becomes obvious _because_ it is what makes M1 possible — pairing them in
  the pitch makes the native-execution edge concrete ("this is why you can rewind your work").
- **M4's network effects are slow and depend on adoption.** A network-effects engine with no network is
  just a feature; M4's compounding value is back-loaded and depends on the platform reaching enough
  cross-org users to matter. **Mitigation:** seed it as design + within-org sharing first (proven
  machinery, 01 §2), so it delivers value at one-org scale before cross-org scale exists.
- **M3's tempting half is a trap.** The agent-comms hypothesis (07 §10(2)) is unproven and possibly
  culturally rejected; if the team lets it leak into the pitch, the platform stakes credibility on a
  bet. **Mitigation:** structurally separate "multi-human + multi-agent substrate" (the USP) from
  "agent-comms beat human-comms" (the research experiment) in all positioning.
- **Connectivity could be mistaken for the moat.** Agnosticism is necessary and impressive, but selling
  it as the USP would be selling commodity (07 §10(5)). **Mitigation:** the foundation is never the
  headline (§6); it is always framed as "what lets the agent be your integration layer," enabling
  M1–M4.

### 8.5 The alternative we considered and rejected

The obvious alternative is **lead with M2** (the safest, most-proven moat) and treat M1 as a future
enhancement. We reject it as the _lead_ because M2's whitespace is shallower (a native edge inside a
filling category, 07 §10(6)) — leading with M2 would position the platform as a governance vendor, where
it competes with funded TRiSM incumbents on their terms. Leading the _story_ with M1 positions the
platform in genuinely unoccupied space (07 §9(b)). The recommendation keeps M2's safety (ship it first)
while claiming M1's differentiation (lead the story with it) — capturing both, rather than trading one
for the other. The honest cost of this hybrid is execution complexity: it requires building two moats in
the right order rather than one, which is more coordination — justified because the autonomous-execution
model (research 07 §11, §06 §7) makes the substrate reuse (~80%) carry most of the load, concentrating
net-new effort on M1's cascade engine and M4's trust model.

---

## 9. Summary table — the four USPs at a glance

| USP    | Headline (plain)                                                                         | Moat (un-copyable part)                                               | Closest competitor → why they miss THIS                                    | Verdict                                   | Role in the recommendation           |
| ------ | ---------------------------------------------------------------------------------------- | --------------------------------------------------------------------- | -------------------------------------------------------------------------- | ----------------------------------------- | ------------------------------------ |
| **M1** | Rewind to any step, change it, only affected results recompute; old kept                 | The conjunction: non-coder + non-deterministic + solved versioning UX | LangGraph (dev-only, no non-coder surface); Cowork (no versioned cascade)  | Substrate PROVEN, experience **BET**      | **Lead the story** (headline)        |
| **M2** | Pre-set how autonomous the agent is, enforced live; budgets, clearance, audited override | Governance baked into the execution substrate (native, not bolt-on)   | TRiSM vendors (bolt-on observe-and-gate); Cowork (no pre-set L3/L4/L5)     | Largely **PROVEN**                        | **Ship first** (foundation)          |
| **M4** | Share reusable work-knowledge across orgs; provenance, versioning, recall                | Trust/provenance layer + recall + untrusted-publisher model           | Skills marketplaces (publish/consume, no governance, no recall)            | Machinery PROVEN, cross-org trust **BET** | **Seed in parallel** (compounding)   |
| **M3** | Many humans + many agents on one tamper-proof shared job                                 | Cryptographic coordination substrate (human-multiplicity half)        | A2A (agent↔agent, owns it); suites (no crypto attribution over agent work) | Substrate PROVEN, "agent-comms" **BET**   | **Build underneath** (enabler)       |
| —      | (Foundation) Agnostic, runs across any model/suite/harness                               | _Not a moat_ — commodity connectivity (only governed connectivity is) | Everyone gets MCP/A2A; suites are vertical by business model               | Table stakes                              | **Never the headline** (enables all) |

---

## 10. Sources

**Research files (read before writing):**

- `01-analysis/01-research/07-competitive-landscape.md` — esp. §0 (synthesis), §3 (Cowork as the
  threat), §7 (governance home-field DNA), §8 (connectivity is commodity), §9 (the differentiators
  scrutinized — a/b/c/d/e), §10 (threats & cautions), §11 (USP positioning + effort framing).
- `01-analysis/01-research/06-transparency-intervention-versioning.md` — §0–§2 (the M1 hard problem +
  existing substrate), §4 (decision-surfacing + posture pipeline for M2), §6 (target architecture, 80%
  exists), §7 (the novel 20% cascade engine + cycle estimates), §8 (M1 risks/open questions).
- `01-analysis/01-research/01-coc-artifact-system.md` — §0, §2 (splitter + recall primitive), §7
  (cross-org marketplace mapping: 80/15/5, the untrusted-publisher 5%) for M4.
- `01-analysis/01-research/02-multi-operator-coordination.md` — §0, §2.3 (cryptographic
  non-equivocation), §3 (conflict classes), §4 (attribution), §8 (posture ladder), §10 (the mapping
  table + the agent-comms-is-a-bet finding) for M3.
- `briefs/01-vision.md` — §3d (team/comms hypothesis — flagged as a bet), §3e/§3f (transparency,
  posture, retrace, versioning), §3g (cross-org artifact sharing), Decisions A & B.

**Strategic spine (Phase A):** M1–M4 definitions, the conjunction-is-the-moat thesis, the Cowork
threat framing, the honest cautions (agent-comms bet; M1 = best-moat-hardest-build; depth-needs-M1;
governed-connectivity-only), and Decisions A (comms wedge) + B (capability-first) — aligned to, not
re-derived.
