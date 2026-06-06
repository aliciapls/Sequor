# 06 — Network Effects: The Five Behaviors, the Flywheel, and How to Ignite It

> Product analysis for the agentic-work-platform (`/analyze`, Phase 01). Maps the five
> network-effects behaviors — **ACCESSIBILITY, ENGAGEMENT, PERSONALIZATION, CONNECTION,
> COLLABORATION** — onto the platform's moat conjunction (M1–M4), identifies the **primary
> flywheel**, and recommends a cold-start ignition path.
>
> Grounding: every claim cites the brief (`briefs/01-vision.md`), the strategic spine (Phase A),
> or one of the four read research files — `01-coc-artifact-system.md`,
> `02-multi-operator-coordination.md`, `07-competitive-landscape.md`,
> `09-comms-wedge-mapping.md`. Genuine uncertainty is flagged **[UNCERTAIN]**;
> inferences not yet built are flagged **[INFERENCE]**.

---

## 0. Plain-language framing (read this first)

A **network effect** is the property that a product gets _more valuable to each user_ as more
people, data, systems, or artifacts join it. Search gets better with more pages; a marketplace
gets better with more sellers. The question this document answers is: **for an agentic work
platform — one agnostic interface where the agent is the integration layer and the human states
intent + governs (Strategic Spine, THE PRODUCT) — what makes it compound, and which compounding
loop should we deliberately turn on first?**

A **flywheel** is a loop where each turn makes the next turn easier: more X produces more Y,
which produces more X. The goal is to find the loop that, once spinning, is hard for a competitor
to stop — and to find the cheapest first push (the **cold-start** problem: a flywheel at rest
delivers no value, so nobody joins, so it stays at rest).

The five behaviors below — **ACCESSIBILITY, ENGAGEMENT, PERSONALIZATION, CONNECTION,
COLLABORATION** — are the COC `/analyze` network-behavior framework: the five behaviors this
analysis is required to evaluate for network effects. They are not an ad-hoc list; they are the
prescribed decomposition the analysis phase mandates covering. For each, this document gives: the
**mechanism** (how it works), the **compounding loop** (why it self-reinforces), and the
**honest risk** (where it breaks, stated symmetrically per `rules/recommendation-quality.md`
MUST-3).

A one-line preview of the conclusion: the strongest flywheel is **M4 — governed, versioned,
provenance-tracked cross-organization artifact exchange** (07 §9e, §11 "Fourth USP"), but it
**cannot ignite first** because it depends on an unbuilt trust model (the untrusted-publisher
problem, 01 §7c). The recommendation is therefore a **two-stage ignition**: spin the
within-org **PERSONALIZATION + ENGAGEMENT** loop first (it has no cold-start gap and runs
on the comms wedge today), and use the artifacts it produces as the seed inventory that lets
the M4 cross-org flywheel turn at all.

---

## 1. The five behaviors mapped to the moat

| Behavior            | Plain-language definition (what raises value)                                         | Primary moat element | Compounds across…            | Cold-start gap?                           |
| ------------------- | ------------------------------------------------------------------------------------- | -------------------- | ---------------------------- | ----------------------------------------- |
| **ACCESSIBILITY**   | Ease of completing a transaction — can a non-coder start and finish without friction? | Foundation + wedge   | _users_ (per-seat)           | **No** (proven by comms onboarding)       |
| **ENGAGEMENT**      | Info useful for completing a transaction — transparency, provenance, learning loop    | M1 + M2              | _sessions per user_          | **No** (more use → more legible context)  |
| **PERSONALIZATION** | Info curated for intended use — org artifacts, per-user/team postures, memory         | M2 + artifacts       | _depth per org_              | **No** (each session deepens the org)     |
| **CONNECTION**      | Sources connected one/two-way — MCP connectors to ERP/CRM/etc.                        | Foundation (MCP/A2A) | _systems per org_            | **Partial** (commodity layer)             |
| **COLLABORATION**   | Producers + consumers jointly working — multi-human + agent shared substrate          | **M3**               | _participants per workspace_ | **No** (substrate exists, UI is net-new)  |
| **(CROSS-ORG)**     | The M4 exchange that sits _above_ the five — artifacts flowing org→org                | **M4**               | _organizations_              | **YES** (untrusted-publisher trust model) |

The five behaviors are **per-org or per-workspace** loops; M4 is the **cross-org** loop that
sits on top of them. This separation is the spine of the whole recommendation: the five behaviors
have **no fundamental cold-start gap** (they compound inside one org, which is in your control),
while the cross-org M4 loop has the classic two-sided cold-start problem AND a genuinely-unbuilt
trust dependency. You ignite the five first; they feed M4 second.

**An analytical refinement (not a contradiction): which of the five are genuine network effects
vs which are compounding-retention loops.** All five behaviors stay in scope — the framework
requires evaluating each. But evaluating them honestly (per the Strategic Spine HONEST CAUTIONS:
do not over-claim network effects) yields a sharper classification _within_ the five:

- **Genuine cross-side NETWORK EFFECTS** (value rises as more _parties_ join):
  - **COLLABORATION (M3)** — within-workspace multi-party: value rises as more humans + agents
    join one shared substrate.
  - **(CROSS-ORG, M4)** — across-org: value rises as more organizations publish/consume
    artifacts. (This is the cross-org loop _above_ the five; included here for completeness.)
- **Within-org RETENTION / ENGAGEMENT loops** (value compounds inside _one_ org — real and
  valuable, but they make _one_ org stickier rather than making the product more valuable to
  _other_ orgs): **ACCESSIBILITY**, **ENGAGEMENT** (inside one org), **PERSONALIZATION**, and
  **CONNECTION**.

This is a refinement of the same five behaviors, not a replacement: each behavior is still
evaluated below on its own terms. The refinement matters because conflating "compounds inside one
org" with "compounds across parties" is exactly how platforms over-promise a flywheel that is
really just good (and genuinely valuable) retention. This document keeps the distinction visible
so the recommendation in §8 rests on the true cross-party loops (M3, M4) while still crediting the
retention loops for the durable per-org value they deliver.

---

## 2. ACCESSIBILITY — ease of completing a transaction

### 2.1 Mechanism

ACCESSIBILITY is whether a non-coder can _start and finish a unit of work_ without hitting a
wall. Two ingredients, both already proven in the comms wedge (09 §1.7, §4.5):

1. **Non-coder interface.** The brief's first requirement (`briefs/01-vision.md` §3a: "Users
   don't have to be coders"). The comms wedge demonstrates this end-to-end: onboarding is **5
   non-technical steps, no app required, first account active in <10 minutes, documents optional**
   (09 §1.7, citing `specs/onboarding.md`). The "Configuration Complexity Budget" forbids
   requiring the user to understand vectors, embeddings, RAG, or confidence numbers (09 §1.7).
2. **Email-first, low-friction onboarding from the comms wedge.** The entire human interface
   is the inbox (09 §1.5): unresolved items arrive as structured emails; replying-to-resolve
   sends the response and captures the answer. No new surface to learn — the user already lives
   in email.

For the platform, ACCESSIBILITY generalizes from "cover a comms point in <10 min" to "state any
objective and let the agent compose the process" (09 §3, the objective/process/data triple).
The agnostic interface (Strategic Spine THE PRODUCT) is the accessibility lever: instead of
crossing ERP→CRM→POS→Excel→Word→portals (`briefs/01-vision.md` §1), the worker states intent in
one place.

### 2.2 The compounding loop

```
easier to complete a transaction
   → more transactions completed per user
      → more captured intent + more learned answers (feeds ENGAGEMENT/PERSONALIZATION)
         → agent gets better at THIS user's work
            → even easier to complete the next transaction
```

ACCESSIBILITY is the **entry valve** for every other loop. It is not itself a strong network
effect (it compounds per-user, not across users), but it is the **necessary precondition**:
a flywheel nobody can start spinning never spins. The comms wedge's <10-min onboarding is the
single most important de-risking fact for the whole network-effects thesis — it proves the
entry valve is open (09 §4.5).

### 2.3 The honest risk (symmetric)

**Pro:** Accessibility is the most de-risked behavior — it ships in production today (comms,
Vercel + Neon, 09 §0). The non-coder onboarding bar is met, not aspirational.

**Con (real, not glossed):** Accessibility on the comms wedge is for a _bounded, single-step_
objective (a message in, a response out — 09 §6.1). The platform's harder claim — multi-step
cross-system objectives — is **not yet exercised** (09 §6.1). The accessibility of "cover a
comms point" does not prove the accessibility of "produce the 3Q financial report across ERP +
Excel + Word." This is the **non-coder DEPTH** caution from the Strategic Spine: no-code dies at
"the last 20%" (07 §6). The platform's escape hatch (07 §6, §9d) is to make the LLM the depth
engine and make depth _legible_ via M1 transparency — but that is the riskiest claim and MUST
be proven, not asserted. **Accessibility at depth is a bet, not a delivered fact.**

---

## 3. ENGAGEMENT — info useful for completing a transaction

### 3.1 Mechanism

ENGAGEMENT is whether the system gives the user the _information they need to complete the
transaction well_ — and, critically, whether each completed transaction makes the system more
useful for the next. Three ingredients:

1. **Transparency / provenance.** Every working step is traced and made transparent
   (`briefs/01-vision.md` §3f). The substrate already realizes this: in comms, every state
   transition writes an append-only, immutable, PII-free **D/T/R audit row** (Doer/Type/Recipient
   — 09 §1.6, §2.3). At platform scale, the **signed, append-only, hash-chained coordination
   log** is "the transcript of all coordination activity… the 'every working step is traced and
   transparent' requirement, realized as a signed, append-only, tamper-evident event stream"
   (02 §2.2). This is M1 (transparent, versioned work) + M2 (posture-graded governance).
2. **Surfaced decisions.** The brief's example — "agent decides to spin up 3 agents → these
   decisions are surfaced on screen, recorded" (`briefs/01-vision.md` §3e) — is the engagement
   surface. The user sees what the agent is about to do and why, before it happens. PACT's
   `SupervisorOrchestrator` already surfaces + records governed decisions with event streaming
   (07 §7, citing `orchestrator.py`).
3. **Learning loop.** Each human intervention becomes durable knowledge. In comms, a human
   resolving an escalation by reply turns `{question, answer}` into an indexed knowledge chunk;
   coverage rises 0% → 60–70% over six months purely through usage (09 §1.3). This is the
   captured residue of a human correction — the same shape as the platform's codify→artifact
   loop (09 §2.2).

### 3.2 The compounding loop

```
agent surfaces its plan + provenance (transparency)
   → user can intervene precisely where it matters (M1)
      → the intervention is captured as durable knowledge (learning loop)
         → next time, the agent surfaces a better plan (fewer interventions needed)
            → user trusts the agent more → engages on harder objectives
               → richer interventions captured → ...
```

ENGAGEMENT is the **trust-deepening loop**. The MIT NANDA finding (07 §1) is the load-bearing
market evidence: ~95% of GenAI pilots fail because generic tools "don't learn from or adapt to
workflows." ENGAGEMENT _is_ the learning-and-adapting mechanism. A platform that visibly learns
from each intervention is on the winning side of the failure statistic; one that doesn't is on
the losing 95%.

### 3.3 The honest risk (symmetric)

**Pro:** The transparency + audit substrate is the platform's **home-field advantage** (07 §7).
Most governance vendors observe and gate _someone else's_ agents (bolt-on); this platform bakes
posture, approval, and signed audit into the execution substrate itself (07 §7 "Critical
reading"). The learning loop is proven cheap in comms — no separate "training" step, the human
just replies (09 §4.2).

**Con (real):** Comms learns _data-level_ knowledge (Q→A pairs); the platform must learn
_process-level_ knowledge (artifacts — procedures, rules, skills). Comms does **not yet** capture
process artifacts from human intervention (09 §2.2 [INFERENCE], §6.5). And the learning system's
raw observation stream currently captures **code-session signals** (`file_counts.pythonFiles`);
how `/codify`-from-observed-work generalizes to **non-coding** work is an open question (01 §8.3,
02 §10.3). The engagement loop is proven for one knowledge type (answers) and one work type
(code sessions); generalizing it to arbitrary knowledge work is real, unbuilt work.

---

## 4. PERSONALIZATION — info curated for intended use

### 4.1 Mechanism

PERSONALIZATION is whether the system holds _this org's_ way of working — its artifacts, its
postures, its memory — so the agent acts the way this org needs, not the way a generic tool acts.
Three ingredients:

1. **Org-specific artifacts.** The brief's premise (`briefs/01-vision.md` §1b: "Processes/
   procedures… vary from company to company") becomes the platform's central claim: company
   process is a **configurable artifact, not bespoke code** (09 §2.5). The comms wedge already
   does this for one process: routing/escalation/response policy is per-account JSONB + template
   selection (09 §2.5). The general form is the COC five-layer artifact system —
   agents/skills/rules/hooks/commands — which is **domain-agnostic by construction**
   (01 §0, §7a: "`cc-artifacts.md` is about _artifact shape_, not codegen").
2. **Per-user / per-team postures.** The L1–L5 trust posture ladder, chosen beforehand per
   objective (`briefs/01-vision.md` §3e; 02 §8.1). Posture is **per-`person_id`**, folded from
   signed `posture-event` records, with operative posture = `min(operator_posture, repo_floor)`
   (02 §4). One team can run an objective at L5 Autonomous while another runs the same objective
   at L3 Step-by-step — personalized governance.
3. **Memory.** Team-memory — shared, signed, one-fact-per-file institutional knowledge
   (02 §4.4) — plus the decisions log (signed `DECISION` entries). This is "the team's shared,
   attributable, tamper-evident institutional memory… what the team knows and has agreed"
   (02 §4.4).

### 4.2 The compounding loop

```
org authors / accumulates artifacts + memory + postures
   → agent acts more like THIS org wants
      → more work runs through the platform (because it fits)
         → more artifacts/memory/postures accumulate
            → switching cost rises (the org's way-of-working now LIVES here)
               → deeper personalization → ...
```

PERSONALIZATION is the **switching-cost loop** — the strongest _retention_ engine among the
five. The MIT NANDA evidence (07 §1, Strategic Spine MARKET) directly supports it: generic tools
fail because they don't adapt; processes vary co-to-co and must be captured as adaptable
artifacts/memory (brief 1b). The deeper an org's artifact/memory store, the more the platform
is _their_ platform, not a generic one — and the harder to leave.

### 4.3 The honest risk (symmetric — the privacy/tenant-isolation tension)

**Pro:** The isolation half is built and battle-tested. Comms uses **schema-per-tenant**
PostgreSQL isolation, explicitly built to the Singapore PDPA compliance bar with a 72-hour
breach clock (09 §1.4, §2.4, §4.4). Schema names pass `validate_identifier()` before any DDL
interpolation (09 §1.4), consistent with `rules/dataflow-identifier-safety.md`. Hard isolation
by default is a delivered fact, not a promise.

**Con (real — this is the central PERSONALIZATION risk):** PERSONALIZATION and PRIVACY/TENANT-
ISOLATION pull in opposite directions. The _more_ the platform curates per-org artifacts, the
_more_ per-org data it concentrates — and the more catastrophic a cross-tenant leak becomes
(per `rules/tenant-isolation.md`: "the difference between an API that scales to a thousand
customers and a P0 incident that destroys the company's reputation"). Comms tenants are **sealed
silos by design** (09 §2.4, §6.3) — which is _safe_ but is the exact opposite of the M4 cross-org
sharing the flywheel needs. The personalization-vs-privacy tension is not a bug to fix; it is a
**permanent design tension** the platform must hold: isolation strong enough to protect every
tenant, permeable enough to deliberately share artifacts when the org chooses (09 §2.4 calls
this "the controlled-permeability half"). Getting the permeability wrong in either direction is
fatal: too sealed and there is no cross-org flywheel; too permeable and one leak ends the
company. **This tension is why M4 cannot ignite first (§8).**

---

## 5. CONNECTION — sources connected one-way / two-way

### 5.1 Mechanism

CONNECTION is how many systems the platform reaches: ERP, CRM, POS, Excel, Drive, Gmail, internal
portals — each connected via **MCP** (Model Context Protocol, the open standard for agent↔tool
connectivity — 07 §8). The mechanism is the agnostic foundation (Strategic Spine FOUNDATION):
the agent is the integration layer, so every new connector adds a system the worker no longer
has to cross to manually (09 §3: "the inbox is one data source; an ERP is another. Nothing in
the comms architecture is hostile to adding ERP/CRM connectors — they are more MCP tools the same
agent calls").

### 5.2 The compounding loop

```
more systems connected (more MCP connectors)
   → agent can complete more objectives end-to-end (no human tool-crossing)
      → more value per worker → more usage
         → more demand for the next connector
            → more systems connected → ...
```

This is the **"more systems = more value"** loop the prompt names. It is real but it is the
weakest moat of the five, for one structural reason stated plainly below.

### 5.3 The honest risk (symmetric)

**Pro:** MCP is the structural enabler of agnosticism (07 §8, §9a) — the independent-analyst
view names MCP as "the structural counterforce to vendor capture" (07 §8). Adoption is massive:
~97M monthly SDK downloads, 10,000+ public servers, donated to the Linux Foundation (07 §8).
Connectivity is a solved, growing substrate the platform rides for free.

**Con (real — and decisive for positioning):** **Connectivity is a commodity; it is NOT a moat**
(Strategic Spine FOUNDATION + HONEST CAUTIONS; 07 §8 "Critical reading", §10.5). Everyone gets
MCP — every suite vendor, every framework, Cowork (07 §3, connectors to Drive/Gmail/DocuSign/
FactSet). Positioning CONNECTION as the differentiator would be a losing bet. **Only _governed_
connectivity differentiates** (Strategic Spine; 07 §8): MCP's missing per-agent/per-team
authorization layer (07 §8 "any consumer can invoke any tool the server exposes") is exactly the
PACT/EATP clearance + posture model. So CONNECTION compounds value (more systems = more useful)
but does not _defend_ value — the defense is the M2 governance layer that sits on top of the
connectors, not the connectors themselves. Treat CONNECTION as **table-stakes plumbing that
enables the moat, never as the moat.**

---

## 6. COLLABORATION — producers + consumers jointly working

### 6.1 Mechanism

COLLABORATION is the **M3** behavior: multiple humans AND multiple agents working on one shared
substrate, with every step attributable and interveneable (`briefs/01-vision.md` §3d). This is
the only one of the five (besides M4) that is a _true_ multi-party network effect — value rises
as more _participants_ join a shared workspace, not just as one user does more.

The mechanism is the **complete, cryptographically-grounded multi-operator coordination
substrate** that already runs (02 §0):

- A **signed, append-only, hash-chained coordination log** — one file, the single rendezvous
  primitive (02 §2.1, §2.2). Every record carries `verified_id` + `person_id` + `seq` +
  `prev_hash` + `sig`.
- **Claims / leases** over work units with SAME/ADJACENT/INDEPENDENT conflict semantics (02 §3) —
  two workers on the same task halt-and-report; on sibling tasks, advisory; on unrelated work,
  silent.
- **Distinct-person gates** — 4-eyes approval requiring a distinct `person_id` AND distinct
  GitHub-collaborator-login (02 §4.1, §9.1; `rules/multi-operator-coordination.md` MUST-3).
- The **work-item ontology** is already generalized by PACT: `AgenticObjective → AgenticRequest →
AgenticWorkSession → AgenticArtifact → AgenticDecision/ReviewDecision` (02 §1.2). The brief's
  "3Q financial report → 3 agents" example maps 1:1 (02 §1.2).

This is M3 — and the Strategic Spine is explicit: **differentiate on the HUMAN-multiplicity
half**, since agent-to-agent coordination is commoditized by A2A (07 §9c; Strategic Spine M3).

### 6.2 The compounding loop

```
more participants (humans + agents) on a shared workspace
   → richer, lossless, signed shared context + memory carried in every handoff (the fold —
     PROVEN: the substrate persists signed, attributable context across participants)
      → less context lost at each handoff than re-explaining across Slack/email/docs
        [BET — unproven, see 09 §agent-comms: that this makes coordination *superior to*
         human↔human comms, not merely lossless, is the brief's contrarian hypothesis]
         → teams prefer to work HERE rather than across Slack/email/docs
            → more participants join the workspace → ...
```

COLLABORATION is the **team-gravity loop**: a workspace with the whole team's signed activity
log is more valuable to join than an empty one. The brief's bet (`briefs/01-vision.md` §3d) is
that agent-mediated coordination is richer/less lossy than human↔human comms. The substrate
_supports the hypothesis structurally_: fork detection makes equivocation "a mathematical
contradiction that names the liar" (02 §2.3) — "who said what, when, and was it tampered with"
becomes a cryptographic question, not a he-said-she-said one (02 §2.3, §10.2).

### 6.3 The honest risk (symmetric)

**Pro:** The substrate is ~80% built and runs today (02 §10.3). The human-multiplicity half is
**genuinely sparse in the market** — agent↔agent is crowded (A2A, every multi-agent framework),
but multi-_human_-on-one-shared-substrate is rare (07 §9c "the human-coordination half is
genuinely sparse"). This is real, file-verified differentiation, not a slide.

**Con (real, several):**

- **The brief's core hypothesis is UNPROVEN.** "Agent-comms beat human-comms" is "an unproven,
  contrarian hypothesis. No external evidence supports it; it could be wrong or culturally
  rejected" (07 §10.2; Strategic Spine HONEST CAUTIONS). The substrate _supports_ the hypothesis
  but **does not yet realize it as a channel** — today agents coordinate _through_ their human
  operator's signed session, not as themselves (02 §0, §10.2). Treat M3 as a research bet, not
  a settled USP.
- **Net-new work is real.** Realizing the channel requires: an **agent identity class**
  (`host_role: agent`) with two-level attribution (agent + accountable human), **direct
  agent→log writes**, and a **non-developer UI** surfacing the log/posture/claims as a screen
  (today: CLI prose + JSONL) (02 §10.3 net-new list).
- **Scale is unproven.** The substrate is designed for "~12 operators" against one repo; a
  product workspace may have hundreds of agents + humans. "Does the fold survive 10K+
  participants / 1M+ records?" is open (02 §11.1).
- **SAME-class on knowledge work: halt vs merge is undecided.** For code, SAME halts (one
  writer); for a report section, two contributors merging may be desirable (02 §11.2). The
  product must decide per-work-item-type.

---

## 7. The behaviors, ranked by network-effect strength

Before naming the primary flywheel, rank the behaviors by how _defensibly_ they compound
(plain-language: how hard for a competitor to neutralize):

| Rank | Behavior            | Network-effect strength | Defensibility source                                 | Why not #1                                   |
| ---- | ------------------- | ----------------------- | ---------------------------------------------------- | -------------------------------------------- |
| 1    | **M4 cross-org**    | **Strongest**           | Untrusted-publisher trust/provenance (genuinely-new) | **Cold-start gap + unbuilt trust model**     |
| 2    | **COLLABORATION**   | Strong (true NE)        | Multi-human substrate (sparse in market, M3)         | Core hypothesis unproven; non-dev UI net-new |
| 3    | **PERSONALIZATION** | Strong (retention)      | Switching cost (org artifacts/memory/postures)       | Compounds per-org, not across orgs           |
| 4    | **ENGAGEMENT**      | Medium (retention)      | Trust-deepening learning loop                        | Compounds per-user; process-learning unbuilt |
| 5    | **ACCESSIBILITY**   | Weak (entry valve)      | Non-coder onboarding (proven)                        | Per-user; necessary precondition, not a moat |
| 5    | **CONNECTION**      | Weak (commodity)        | None alone — only _governed_ connectivity defends    | Commodity; everyone gets MCP                 |

The ranking yields the central tension: **the strongest flywheel (M4) has the worst cold-start
problem.** Resolving that tension is the recommendation.

---

## 8. RECOMMENDATION — the primary flywheel and how to ignite it

### 8.1 The recommendation

**Primary flywheel: M4 — governed, versioned, provenance-tracked cross-organization artifact
exchange** (the cross-org loop above the five behaviors). It is the platform's strongest network
effect and the "primary network-effects engine" the Strategic Spine and research already name
(M4; 07 §11 "Fourth USP"; 09 §6.3; 01 §7).

**But M4 MUST NOT be the first loop you push.** Ignite it in **two stages**:

- **Stage 1 (ignite now, no cold-start gap): the within-org PERSONALIZATION + ENGAGEMENT loop**,
  running on the comms wedge and generalized via `/codify`-from-observed-work. Each org
  accumulates artifacts + memory + learned process — the **seed inventory**.
- **Stage 2 (ignite once seeded + trust model built): the cross-org M4 exchange**, using
  Stage-1 artifacts as the initial catalog and the loom splitter (Gate-1/Gate-2 +
  variant-overlay + obsoletion recall) as the distribution control plane.

In one sentence per `rules/communication.md`: **build the loop that makes each org's own work
compound first (because you control both sides and it works today), and use the artifacts it
produces as the inventory that lets the cross-org marketplace turn — because a marketplace with
nothing in it never starts.**

### 8.2 Why M4 is the primary flywheel (mechanism)

The mechanism is unusually well-matched to existing DNA. loom already does cross-_repo_ artifact
distribution for one org's codegen artifacts across ~6 targets and 30+ downstream consumers
(01 §0). The machinery — the five-layer taxonomy, the **two-gate `/sync` splitter** (Gate-1
human-classify + disclosure-scrub; Gate-2 distribute with variant overlays), the **proposal
lifecycle** (`pending_review→reviewed→distributed`), and the **obsoletion/recall primitive**
(one declarative entry purges a bad artifact from every consumer on next sync — 01 §2d) — is the
"share across orgs" engine, 80% reusable (01 §7a). The M4 loop:

```
org A authors a good artifact (a "month-end close" procedure)
   → publishes it (governed, versioned, provenance-tracked)
      → org B discovers + adopts it (saving the build cost)
         → org B improves it, publishes the improvement back (variant overlay)
            → the catalog grows + improves
               → more orgs join FOR the catalog → more authoring → ...
```

This is a **two-sided network effect**: more publishers → richer catalog → more consumers →
more demand → more publishers. It is the only loop that compounds across _organizations_ — which
is why it is the strongest, and why no competitor occupies it: skills/MCP marketplaces exist
(8+ by Q2 2026, 20,400+ skills — 07 §9e) but are "publish/consume directories" that **lack
governed + versioned + cross-org provenance + trust-classification** (07 §9e, §11; 09 §6.3).
The moat is the trust/provenance layer, not the marketplace itself (07 §9e verdict).

### 8.3 Why M4 cannot ignite first (the cold-start + trust dependency)

Two structural blockers, both honest:

1. **The untrusted-publisher trust model is genuinely-new and unbuilt.** loom's threat model is
   **bounded-trust** — "the adversary is a legitimate team member with repo write access"
   (02 §0; `rules/multi-operator-coordination.md` §1.1). A cross-org marketplace faces
   _untrusted publishers_ (01 §7c). The cryptographic substrate (commit-signing keys, hash-chained
   log, 2-of-N quorum, `refs/coc/**` server rulesets) is a strong starting point, but
   **signed-artifact provenance from an _external_ publisher (vs an enrolled operator) is not yet
   modeled** (01 §7c). This is the Strategic Spine M4 "genuinely-new = the UNTRUSTED-publisher
   trust model." It is a **novel-architecture decision** that must be designed _before_ the
   registry surface, because it constrains it (01 §7d). Estimated sizing per `autonomous-
execution.md`: the untrusted-provenance trust model is greenfield (~2–3× first-session factor);
   the registry surface is ~3–5 autonomous sessions but **gated on the trust model landing first**
   (01 §7d).
2. **Classic two-sided cold-start.** An empty catalog has no value to consumers, so nobody
   consumes; with no consumers, nobody publishes. The marketplace at rest delivers nothing. You
   cannot ask orgs to publish into a void.

The personalization-vs-privacy tension (§4.3) compounds blocker 1: the very permeability M4
needs is the permeability that, done wrong, leaks one tenant's data into another. M4 is the
highest-value AND highest-risk loop — exactly the M1-style "best moat AND hardest build" pattern
the Strategic Spine flags.

### 8.4 The ignition path (how to cold-start, concretely)

**Stage 1 — spin the within-org loop on the comms wedge (no cold-start gap, ~runs today).**

The comms wedge already proves the trust/feedback/transparency/isolation spine against real
users and real data (09 §0, §6.5). Use it as the **landing vertical** while the orchestration
spine is built (09 §6.5). Concretely:

- Generalize the comms **learning loop** (Q→A capture, 09 §1.3) toward **process-artifact
  capture** — `/codify`-from-observed-work for non-coding sessions (01 §7b.4, §8.3). Each org's
  human interventions become reusable artifacts (the seed inventory).
- Generalize tiers from `cc`/`co`/`coc`/language to **work-domain tiers** (finance, legal, ops) —
  "mechanically identical to adding a tier in `sync-manifest.yaml`" (01 §7b.3), ~1 session
  (01 §7d).
- Add an **org-axis variant** (`variants/<org>/rules/foo.md` overriding `rules/foo.md`) — the
  variant engine generalizes from language×CLI to org-default-vs-org-override unchanged
  (01 §7a.3), ~1 session (01 §7d).

This stage has **no cold-start gap** because both sides of the loop (the org authoring and the
org consuming) are the _same_ org — you are not waiting for a second party. It compounds
PERSONALIZATION (switching cost) + ENGAGEMENT (learning) immediately, and it produces the
artifact inventory Stage 2 needs.

**Stage 2 — design the untrusted-publisher trust model, then open the cross-org exchange.**

- **First**, design the trust model (the 5% genuinely-new — 01 §7c): signed-provenance from
  external publishers, asymmetric publish/consume governance (the `aegis-fork-relationship.md`
  precedent already exists: generic registry artifact ↔ org-specific override; upstream-generic-
  only, product→fork client-leakage BLOCKED — 01 §7c.2), and marketplace-grade
  versioning/licensing/attribution (01 §7c.3). This is the gating dependency.
- **Then** build the registry/publish-subscribe surface on top of the loom splitter as the
  **artifact control plane** — "a thin discovery+publish surface ON TOP of it, not a rewrite"
  (01 §7d). Seed the catalog with the best Stage-1 artifacts (curated by the platform operator,
  not user-published — solving the cold-start by being the first publisher yourself).
- The **obsoletion/recall primitive** (01 §2d) is the marketplace "unpublish a bad artifact"
  requirement, already shipping — a key trust feature for an untrusted-publisher catalog.

### 8.5 Implications (what this means for the user/business)

- **You get a revenue-bearing, real-user landing vertical (comms) NOW**, while the highest-value
  flywheel (M4) is built behind it (09 §6.5). You are not betting the company on the unproven
  cross-org loop before proving the spine.
- **Each org's accumulated artifacts become switching cost immediately** (Stage 1
  PERSONALIZATION) — even if M4 never ships, you have a sticky per-org product. M4 is upside,
  not survival-critical.
- **The cross-org flywheel, once lit, is the durable moat** no competitor occupies — but it
  arrives _seeded_ (your Stage-1 artifacts) and _trusted_ (the trust model built first), avoiding
  both the empty-catalog and the toxic-publisher failure modes.
- **Effort framing (autonomous cycles, not human-days):** Stage-1 tier + org-axis work is ~1–2
  sessions each (mechanical, high feedback loop — 01 §7d); the untrusted-publisher trust model is
  a greenfield novel-architecture decision (~2–3× first-session factor); the registry surface is
  ~3–5 sessions, gated on the trust model (01 §7d). Parallelize Stage-1 across the comms-wedge
  generalization and the artifact-system generalization (independent surfaces).

### 8.6 Symmetric pros and cons of the recommendation

**Pros:**

- No cold-start gap blocks Stage 1 — it ships on the proven comms substrate.
- The strongest flywheel (M4) is preserved as the endgame, not abandoned — it is _sequenced_,
  not deferred-without-value (per `rules/value-prioritization.md`, the value-anchor is the
  brief's §3g "artifacts shared across organizations and teams").
- Each stage delivers standalone value (Stage 1 = sticky per-org product; Stage 2 = cross-org
  moat), so a halt at any stage still leaves a viable product.
- The trust model is built _before_ the surface that depends on it — avoiding the rework that
  building the registry first would force (01 §7d).

**Cons (real, not glossed):**

- Stage 1's process-artifact capture for non-coding work is **unbuilt and unproven** — the
  learning loop today captures code-session signals (02 §10.3, 01 §8.3). The seed-inventory
  thesis depends on generalizing it, which is real risk.
- M4's network effect is the strongest _in theory_ but **unrealized** — no part of it ships
  today (09 §6.3). The recommendation bets that the trust model is solvable; if the untrusted-
  publisher problem proves intractable, M4 stays a within-org effect and the platform's network-
  effect strength collapses to COLLABORATION (#2) — strong but not category-defining.
- Sequencing M4 second means a fast-moving competitor (e.g., a skills-marketplace vendor adding
  governance, 07 §9e) could occupy the cross-org-governance whitespace first. The mitigation is
  that the trust/provenance layer is the hard part and the platform's DNA is uniquely matched to
  it (01 §7, 07 §9e) — but "we have a head start on the hard part" is an advantage, not a
  guarantee.
- The COLLABORATION loop (#2, M3) rests on the brief's **unproven** core hypothesis (agent-comms
  beat human-comms — 07 §10.2). If that hypothesis is culturally rejected, the team-gravity loop
  weakens, and the platform leans harder on PERSONALIZATION (retention) than on true multi-party
  network effects.

---

## 9. Summary table — behavior → loop → risk → disposition

| Behavior           | Compounding loop (1-line)                         | Strongest honest risk                                   | Disposition                                   |
| ------------------ | ------------------------------------------------- | ------------------------------------------------------- | --------------------------------------------- |
| ACCESSIBILITY      | easier transaction → more transactions → learning | depth at "last 20%" unproven (07 §6)                    | Entry valve — keep open; prove depth via M1   |
| ENGAGEMENT         | transparency → precise intervention → learning    | process-learning (vs Q→A) unbuilt (09 §6.5)             | Stage-1 loop — generalize learning to process |
| PERSONALIZATION    | org artifacts → fit → more work → more artifacts  | personalization vs tenant-isolation tension (§4.3)      | **Stage-1 primary** — switching-cost engine   |
| CONNECTION         | more systems → more end-to-end objectives         | commodity; only _governed_ connectivity defends (07 §8) | Table-stakes plumbing — never the headline    |
| COLLABORATION      | more participants → richer fold → team gravity    | core hypothesis unproven (07 §10.2); non-dev UI net-new | Differentiator #2 — build on M3 substrate     |
| **M4 (cross-org)** | **publishers → catalog → consumers → publishers** | **untrusted-publisher trust model unbuilt (01 §7c)**    | **PRIMARY flywheel — ignite Stage 2, seeded** |

---

## 10. Sources consulted

- Brief: `~/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md`
- Strategic Spine (Phase A) — provided in the analysis invocation (THE PRODUCT, M1–M4,
  FOUNDATION, BIGGEST THREAT, HONEST CAUTIONS, DECISIONS, MARKET).
- `01-analysis/01-research/01-coc-artifact-system.md` (five-layer artifacts; loom splitter;
  variant overlays; obsoletion/recall; 80/15/5; untrusted-publisher trust model §7c; sizing §7d).
- `01-analysis/01-research/02-multi-operator-coordination.md` (coordination log; claims/leases;
  distinct-person gates; PACT work-item ontology; posture ladder; agent↔agent channel §10.2;
  scale risk §11).
- `01-analysis/01-research/07-competitive-landscape.md` (whitespace map §0/§9; Cowork threat §3;
  MCP commodity §8; governance home-field §7; cross-org provenance whitespace §9e; cautions §10;
  USP positioning §11; MIT NANDA / Gartner §1).
- `01-analysis/01-research/09-comms-wedge-mapping.md` (comms as wedge; objective/process/data
  triple §3; 80/15/5 §5; learning loop §1.3/§2.2; schema-per-tenant §1.4/§2.4; gaps §6;
  spine-not-whole-vision §6.5).
