# 05 — The AAA Framework: Automate, Augment, Amplify

> **Scope.** This document develops the platform's three-axis value framework — **Automate**, **Augment**, **Amplify** — each defined precisely in this platform's context, each grounded in a concrete mechanism the platform's DNA already supplies, and each illustrated with a worked example drawn from the brief's own "I want the 3Q financial report" objective plus the comms wedge (Decision A). It closes with the buyer's cost-reduction logic for each axis, a map of where the AAA frame exposes a gap in competing offerings, and a single recommendation on which of the three is the sharpest wedge — with symmetric pros and cons.
>
> **Authority.** Subordinate to `workspaces/future-of-work/briefs/01-vision.md`. Where this document and the brief disagree, the brief wins.
>
> **Grounding.** Every claim cites a research file in this analysis (`08-work-disruption-thesis.md`, `05-cli-harness-universal-interface.md`, `09-comms-wedge-mapping.md`) or the brief. Where the platform's ecosystem does **not** yet supply something, the gap is flagged explicitly rather than asserted as built.
>
> **Constraint compliance.** Per `.claude/rules/independence.md` and the brief's CONSTRAINTS clause, the platform is described on its own terms. Competing offerings are named **factually** (what exists, what it does) — never as a parent the platform is "a version of." Per `.claude/rules/autonomous-execution.md`, effort is estimated in autonomous execution cycles/sessions, never human-days. Per `.claude/rules/recommendation-quality.md`, the final recommendation carries a single pick, implications, and symmetric pros/cons in plain language.

---

## Part 0 — Why three axes, and what each one is for

The disruption thesis (research 08, Part 0) says every unit of enterprise work is the triple **⟨objective, process, data⟩**, and that today **the human is the integration layer** shuttling data between siloed systems by hand. The inversion puts an agent in the middle: the human states intent, the agent integrates. That single move creates value along three distinct cost surfaces, and conflating them produces a muddy pitch. The AAA framework separates them cleanly:

| Axis         | What it attacks                              | Whose cost falls                            | The plain-language promise                                                                 |
| ------------ | -------------------------------------------- | ------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Automate** | **Operational cost** — the doing of the work | The line worker who runs the steps          | "The work runs itself across your systems; you stop being the integration layer."          |
| **Augment**  | **Decision cost** — the judging of the work  | The person accountable for the decision     | "You decide better and faster, because every choice is surfaced, graded, and explainable." |
| **Amplify**  | **Expertise cost** — the scaling of the work | The organization that owns scarce expertise | "One expert's procedure becomes a tool any non-expert can run, here and across orgs."      |

A one-sentence way to hold the three apart: **Automate removes the hands, Augment sharpens the head, Amplify clones the expert.** They are not three names for the same thing; they attack three different line items on the buyer's cost sheet. The rest of this document develops each in turn.

**A note on the relationship to AAU/HITL framings.** "Automate / Augment" is sometimes used loosely to mean "do it for you vs. help you do it." This framework is stricter: Augment is not "a weaker Automate." Augment is the **decision layer that sits on top of automation** — it is the brief's posture-graded approval and transparent provenance (brief §3e/§3f), and it is load-bearing precisely because most knowledge work lacks the free, instant verifier that code work gets from a compiler (research 05, §2: "the single biggest coding-specific advantage that does NOT transfer cleanly is the compiler/test as automatic ground truth"). Where there is no compiler, the human judgment surfaced by Augment **is** the verifier. That is why Augment is a peer of Automate, not a dilution of it.

---

## Part 1 — AUTOMATE: collapsing operational cost

### 1.1 Precise definition in this platform's context

> **Automate (this platform).** The agent executes a stated objective **end-to-end across two or more formerly-siloed systems**, performing the data-shuttling, format-reconciliation, and step-sequencing that the human used to perform by hand. The unit removed is **swivel-chair work** — research 08's term for "the portion of a knowledge worker's effort spent being the integration layer between systems that will not talk to each other" (research 08, §1.3, Definition box).

This is a narrower and more defensible definition than "the agent does tasks." A chatbot bolted onto one application also "does tasks" — but it does not remove swivel-chair work, because swivel-chair work lives in the _seams between_ systems, not inside any one of them (research 08, §2.1: "the cost does not accrue inside any tool… it accrues in the seams between tools, and the seams are staffed by humans"). The platform's Automate claim is specifically: **the agent becomes the integration layer that the human used to be.**

The load-bearing test (research 08, §5.2, properties 3 and 6): a genuine Automate run **crosses ≥2 heterogeneous systems** AND the **human never opens those systems directly during the run**. If the human still swivels, the integration layer is still human and Automate has not happened.

### 1.2 The concrete mechanism — the integration-layer inversion

The mechanism is not "we wrote automation scripts." It is the structural inversion of research 08, §3.1, realized on an existing runtime:

- **The objective becomes the prompt.** A free-text intent stated once to the main agent (research 08, §3.2: Objective → prompt).
- **The process becomes artifacts.** The company's procedures live as skills/rules/commands the agent applies — not the vendor's generic model, but _this institution's_ rules (research 08, §3.3; research 05, §1.2: all five artifact layers are domain-agnostic).
- **The data becomes governed tool connections.** Each formerly-siloed system is reached as an MCP (Model Context Protocol — the universal connector that lets the agent call a system as an endpoint) server. "The same protocol that connects the harness to `git` today connects it to SAP, Salesforce, Workday tomorrow" (research 05, §1.4).

The inversion is what makes this Automate and not mere scripting. **Per-tool automation — macros, point integrations, workflow builders — is brittle by construction** because each "encodes a _specific_ path, not the _capability_ to find a path" (research 08, §2.4). The agent-as-integration-layer finds the path at run time from the objective, the artifacts, and the available connectors. This is why the (N+1)-th system does not require rebuilding N integrations: the agent composes across whatever connectors exist (research 08, §2.1, on super-linear seam growth).

**What is inherited vs. what is net-new (honest accounting, research 08 §3.5 + research 05 §6).** The agent loop, subagent fan-out, MCP protocol, and context management are domain-agnostic and largely ready — research 05, §2 finds "~9 of ~12 core harness capabilities are fully domain-agnostic." The genuine build is the **breadth of business-system connectors** ("MCP breadth is a genuine build, not an inheritance" — research 08, §3.5) and the **object/record model** that bridges the harness's file-centric assumption to enterprise systems-of-record (research 05, §3.2 — flagged as "the deepest gap," architecturally open).

### 1.3 Worked example — Automate on "I want the 3Q financial report"

The brief's own example (brief §3e), decomposed against the trinity in research 08, §1.2:

| Element       | Content                                                                                                                                 |
| ------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **Objective** | A Q3 financial report exists, is accurate, is in house format, has reached the CFO by deadline.                                         |
| **Process**   | This company's close procedure: authoritative ledger, manual accruals, sign-off chain, report template, revenue-recognition rule.       |
| **Data**      | Ledger entries (ERP), bookings (CRM), receipts (POS), prior-quarter report (a document), manual adjustments (a spreadsheet), CFO email. |

**The swivel-chair version (today).** A finance analyst opens the ERP, exports the trial balance; opens the spreadsheet, keys in manual accruals; opens the CRM to reconcile bookings; opens last quarter's report to copy the template; assembles the draft in a document; routes it for sign-off by hand; emails the CFO. Research 08, §1.2: _"No existing vertical tool holds more than one column of one row of this table."_ The objective O **exists nowhere in software** — only in the analyst's head.

**The Automate version (the platform).** The analyst states: _"I want the Q3 financial report."_ The agent:

1. Reads the ledger via the ERP connector, the bookings via the CRM connector, the receipts via the POS connector, the adjustments from the spreadsheet, the template from the prior report — **the agent crosses five formerly-siloed systems** (property 3 satisfied).
2. Applies the company's close artifacts — the revenue-recognition rule, the house template, the accrual procedure — so the output is _right-for-here_, not the generic finance model (research 08, §3.3).
3. Produces the draft. **The analyst never opened the ERP, CRM, or POS** (property 6 satisfied; research 08, §5.2).

The operational cost removed is the entire swivel-chair circuit. What remains for the human is sign-off — which is **Augment's** territory, not Automate's (Part 2).

**The comms-wedge instance (Decision A).** The wedge already proves a _narrow_ Automate: a secretary's inbound message is classified, the knowledge base is retrieved, and a response is produced or escalated — collapsing "email + WhatsApp + knowledge base + escalation tooling (4 interfaces) into one email-first interface" (research 09, §3). But the wedge's Automate is **single-step within one tool-cluster** — it does not yet cross heterogeneous systems of different classes (research 09, §6.1: "Comms' agent calls one knowledge base, not an ERP and a CRM and a spreadsheet in sequence"). So the wedge demonstrates the _shape_ of Automate (data via tool connectors, agent loop) but not its _breadth_. The 3Q report is the breadth demonstration the platform must add.

### 1.4 The buyer's cost-reduction logic for Automate

Framed in autonomous-execution terms (per `.claude/rules/autonomous-execution.md` — no human-day estimates):

- **The cost line attacked is operational throughput per objective.** Today a multi-system objective consumes one worker's attention across O(k) context switches (research 08, §2.1) — and research 08, §2.2 grounds the magnitude: ~60% of knowledge-worker time is "work about work," ~1,200 app toggles/day, ~23 minutes to refocus after an interruption. The integration-specific slice of that is the addressable surface.
- **Qualitative logic, not a headcount-reduction pitch.** The honest framing is _throughput per objective_, not _bodies removed_. An autonomous agent runs the swivel-chair circuit continuously, without the attention residue, state loss, and transcription error that make the human seam _qualitatively_ lossy (research 08, §2.3). The buyer's gain is **objectives completed per unit time, at higher accuracy** — the silent-data-corruption failure of the hand-typed spreadsheet column (research 08, §2.3) goes away because the data is no longer hand-carried.
- **The buyer-legible sentence.** "Your people stop being the glue between your systems. The work that used to take a worker an afternoon of clicking between five screens runs as one stated request, and the data is never re-typed by hand — so it is faster _and_ more accurate."

---

## Part 2 — AUGMENT: collapsing decision cost

### 2.1 Precise definition in this platform's context

> **Augment (this platform).** Every consequential decision the agent reaches inside an objective run is **surfaced before it acts, graded against a pre-chosen trust posture, and recorded with transparent provenance** — so the accountable human decides better and faster, with the agent's reasoning inputs and outputs fully legible. The unit removed is **decision cost**: the time, risk, and opacity of judging whether the agent's chosen path is the right one.

Augment is the brief's §3e/§3f made into a value axis. It is _not_ "the agent helps you write things." It is the **governance-and-transparency layer** that converts an opaque autonomous run into a series of legible, interveneable decision points. Critically (research 05, §2): because most knowledge work lacks a compiler, **this layer is load-bearing for correctness, not just UX** — it is the substitute for the missing ground-truth verifier.

### 2.2 The concrete mechanism — surfaced decisions + posture-graded approval + transparent provenance

Three sub-mechanisms, all grounded in shipped ecosystem code (research 08, §3.4):

**(a) Surfaced decisions.** When the agent decides to (e.g.) spin up three sub-agents for the report, that decision is "surfaced on screen, recorded" (brief §3e). The mechanism exists: PACT's `_PlatformHeldCallback.__call__` "creates an `AgenticDecision` record and **returns `False` to block the action until a human approves**" (research 08, §3.4). The decision is not a log line after the fact — it is a _gate before_ the act.

**(b) Posture-graded approval.** The human chooses the posture **beforehand**, per objective (brief §3e):

| Posture             | Brief wording       | What it means for the buyer (research 09, §2.1 mapping)        |
| ------------------- | ------------------- | -------------------------------------------------------------- |
| **L5 Autonomous**   | agent goes ahead    | The agent runs the whole objective; you read the trace after.  |
| **L4 Supervised**   | asks one permission | The agent pauses once, at the consequential step, for your OK. |
| **L3 Step-by-step** | pauses each step    | The agent pauses at each step; you walk it through.            |

This is a shipped state machine, not an aspiration: `TrustPosture` defines five levels (AUTONOMOUS=5 … PSEUDO=1) (research 08, §3.4; research 05, §3.5 notes the same ladder converges across three independent ecosystem implementations — COC, envoy, aegis). The platform does **not** invent the posture model; it "lifts it from a per-repo CLI guardrail into a per-objective user-facing control" (research 05, §3.5).

**(c) Transparent provenance.** "Every activity and output is traced… input and output are transparent; the only thing not transparent is how the model thinks" (brief §3f). The mechanism is the append-only, signed work ledger: envoy's two-phase signing records **intent before the action and outcome after** (research 05, §3.3), and PACT persists the full work graph (`AgenticObjective`, `AgenticRequest`, `AgenticWorkSession`, `AgenticDecision`, `Run`) as the "every activity traced" data model (research 05, §3.3; research 08, §3.4). The keystone enabling rule is "**tools are dumb data endpoints; the LLM does all reasoning**" (research 05, §5.2) — because reasoning lives in the LLM (logged) and tools only move data (logged), _everything except the model's internal cognition is transparent_ (research 05, §5.2). This is the structural reason the brief's §3f transparency claim is achievable rather than marketing.

**Retrace-and-intervene.** The brief's §3e — "retrace any previous step and intervene; downstream outputs change accordingly; old outputs are versioned" — is the hardest sub-mechanism and is **net-new engineering, not inherited**: research 05, §6.2 flags "intervenable replay with downstream re-derivation" as "a dataflow-graph re-execution problem… the ledger records it; re-running from a mid-graph intervention point and re-deriving cascades is non-trivial." This is flagged honestly: Augment's surface-and-approve half is inherited; its retrace-and-recascade half is the genuine build.

### 2.3 Worked example — Augment on "I want the 3Q financial report"

Continuing the Part 1 run. The analyst stated the objective; the agent assembled the draft across five systems. Now Augment:

- **Posture chosen beforehand.** Because a financial report is consequential, the analyst pre-selects **L4 Supervised** — "the agent prepares the whole report but pauses once, before anything is finalized, for my approval." (Contrast: a routine internal summary might run **L5**.)
- **Decision surfaced.** The agent's choice to recognize revenue on shipment (per the company artifact) vs. delivery is surfaced as an `AgenticDecision` record — visible, with its reason, _before_ it hardens into the report. The analyst sees _why_ the agent chose what it chose (transparent provenance), not just _what_ it chose.
- **Intervene + recascade.** The analyst notices the agent pulled bookings from a stale CRM view. They retrace to the data-gathering step, point the agent at the correct view, and the downstream draft **recomputes** — while the prior draft is **versioned**, not overwritten (brief §3e). _(This is the net-new replay engine flagged in §2.2.)_

The decision cost removed: the analyst is not re-auditing an opaque output by reverse-engineering it; the report arrives **with its reasoning attached and its risky decisions pre-flagged**, so sign-off is a graded approval, not a forensic exercise.

**The comms-wedge instance (Decision A).** The wedge already proves Augment's _surface-and-approve_ half convincingly: confidence-graduated HITL routing — >90% auto-send (≈L5), 60–90% escalate-with-AI-draft (≈L4), <60% escalate-without-draft (≈L3) (research 09, §2.1) — plus D/T/R audit rows on every transition (research 09, §2.3), under the binding principle "sending wrong information is worse than sending none" (research 09, §3; research 08, §4.3(4)). What the wedge does **not** prove (research 09, §6.2): step-level retrace/intervene with versioned cascades — "Comms' 'intervention' is binary (approve/edit/compose one response), not a graph-replay." So the wedge validates posture+provenance; the platform must add the recascade engine.

### 2.4 The buyer's cost-reduction logic for Augment

- **The cost line attacked is decision risk and decision latency.** The expensive part of high-stakes knowledge work is not the doing — it is the _deciding under uncertainty_ and the _time spent verifying_ an output you cannot see inside. Augment converts an opaque output into a graded, provenanced one.
- **Qualitative logic.** Without Augment, the buyer's only options for an autonomous agent are "trust it blindly" or "re-check everything" — the false binary research 05, §3.3 contrasts against the brief's intent-staged postures. Augment gives a _middle_: choose the posture that matches the objective's stakes, see the reasoning, intervene where it matters. The decision-cost reduction is **verification time falling because provenance is attached, and decision risk falling because consequential choices are gated before they act** — not after they have already shipped a wrong number to the CFO.
- **The buyer-legible sentence.** "For routine work, let the agent run and read the trace later. For the work that matters, the agent pauses exactly where a wrong call is expensive — and shows you _why_ it chose what it chose, so approving it takes a glance, not an audit."

---

## Part 3 — AMPLIFY: collapsing expertise cost (and scaling it)

### 3.1 Precise definition in this platform's context

> **Amplify (this platform).** A scarce expert's procedure is **encoded once as a reusable artifact** (skill / rule / command) so that a **non-expert can wield the expert's procedure** without becoming the expert — and that artifact can be **shared, with governed provenance, across teams and organizations**, scaling one expert's knowledge far beyond the people they could personally train. The unit removed is **expertise cost**: the scarcity, the onboarding time, and the non-transferability of institutional know-how locked in people's heads.

Amplify is the brief's §3g ("artifacts easily created, modified, stored, and shared across organizations and teams") elevated to a value axis. It is the answer to a structural fact from research 08, §2.4: **company-specific process is "structurally un-ownable by a vertical vendor"** — so today it lives in employees' heads, applied inconsistently (the "convention drift" failure mode). Amplify makes that process _a versioned, shareable object_.

### 3.2 The concrete mechanism — artifacts encode expertise; cross-org sharing scales it

**(a) Artifacts encode expertise → a non-expert wields an expert's procedure.** Process-as-artifact is "the only representation of P that is simultaneously institutional, reusable, versioned, and shareable — which is exactly why it beats P-lives-in-a-human" (research 08, §3.3). The five-layer artifact model (agents/skills/rules/commands/hooks) is fully domain-agnostic (research 05, §1.2): a `security-reviewer` agent becomes a `contract-reviewer`; SDK cheatsheets become company SOPs; `/analyze→/implement` becomes `/close-the-books` (research 05, §2 capability table). The expert authors the artifact once; thereafter any non-expert who states the objective gets the _expert's procedure applied for them_ — they wield it without holding it.

This directly addresses the market's dominant failure signal (per the strategic spine / research 07): MIT NANDA found ~95% of GenAI pilots fail because generic tools "don't learn from / adapt to workflows." Amplify is the structural counter — the platform captures the company-specific workflow _as an adaptable artifact_, which is exactly what generic tools cannot do.

**(b) Cross-org sharing scales expertise across orgs.** The loom platform is "literally already built" as the artifact splitter/distributor (research 05, §1.2): Gate-1 global-vs-variant classification, `/sync` distribution to 30+ downstream repos, variant overlays (research 08, §3.3). The strategic spine names this M4 — "governed, versioned, provenance-tracked cross-org artifact exchange" — as the **primary network-effects engine**, and identifies the genuinely-new part as the **untrusted-publisher trust model** (a trust/provenance layer atop the commoditizing skills/MCP marketplace).

**What is net-new (honest flag, research 09 §6.3).** The _isolation_ half of cross-org boundaries is proven (comms' schema-per-tenant passes Singapore PDPA — research 09, §2.4). The _controlled-permeability_ half — deliberate artifact sharing across the org boundary with provenance — is "not exercised by comms"; loom demonstrates it for coding artifacts, and the platform must generalize it to business artifacts under a trust model for untrusted publishers. Amplify's encode-once half is inherited; its cross-untrusted-org-exchange half is the genuine build.

### 3.3 Worked example — Amplify on "I want the 3Q financial report"

- **Encode once.** The company's best controller authors a `quarterly-close` command + a `revenue-recognition` rule + a `house-report-template` skill — the _exact_ procedure that made the 3Q run in Parts 1–2 right-for-here. This is a one-time authoring cost.
- **Non-expert wields it.** Next quarter, a **junior** analyst states "I want the Q3 report." The agent applies the controller's encoded procedure. The junior produces a controller-grade report **without being a controller** — the expertise was amplified, not cloned into a second human via months of training.
- **Scale across orgs.** A fractional-CFO firm authors a hardened `quarterly-close` artifact and shares it — with provenance, versioning, and recall if a defect is found — to twenty client companies. One expert's procedure now runs in twenty organizations. _(The cross-untrusted-org trust model is the net-new build; the encode-and-share-within-org mechanism is inherited from loom.)_

**The comms-wedge instance (Decision A).** The wedge proves Amplify's _capture_ primitive at the data layer: learning-from-human-answers turns every human escalation reply into a durable knowledge chunk, lifting coverage "from 0% (day 0) to 60–70% (month 6) purely through usage" (research 09, §1.3, §2.2). That is amplification of one human's answer into a reusable asset. But the wedge captures _data-level_ knowledge (Q→A pairs), not _process-level_ artifacts, and its tenants are "sealed silos" with no cross-org artifact sharing (research 09, §2.2, §6.3). So the wedge validates capture-from-intervention; the platform must add process-artifact capture and governed cross-org exchange.

### 3.4 The buyer's cost-reduction logic for Amplify

- **The cost line attacked is the scarcity and non-transferability of expertise.** Expertise today is a person; people are finite, slow to train, and walk out the door. Amplify converts expertise into an asset that does not leave, does not need re-training, and runs everywhere the artifact is shared.
- **Qualitative logic.** This is the axis with **compounding** returns: each authored artifact serves every future objective that matches it; each shared artifact serves every org that pulls it. Research 09 places artifacts squarely in the **80% agnostic reusable core** with company processes in the **15% client-configurable** layer (research 09, §5) — i.e., Amplify is structurally the high-leverage axis, because "knowledge compounding (zero onboarding)" is itself a throughput multiplier (research 09, §2.6, citing autonomous-execution.md).
- **The buyer-legible sentence.** "Your best person's way of doing the work becomes a tool everyone can run — and a tool you can share with partners or clients. You stop losing the procedure when the expert is busy, on leave, or gone."

---

## Part 4 — How AAA maps onto the competition's gap

The strategic spine's market read: **suite vendors (ServiceNow, Salesforce, SAP, Microsoft) are vertical by business model** — research 08, §2.4 explains _why this is structural, not a temporary state_: "integration across competitors is adversarial to each vendor," and "the process slice is structurally un-ownable by a vertical vendor." The AAA frame makes the gap precise on each axis.

| Axis         | What a suite vendor delivers                                    | The structural ceiling (research-grounded)                                                                                                                                   | Where the platform's AAA goes further                                                                                     |
| ------------ | --------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------- |
| **Automate** | Automation _within its own silo_ (workflows inside the CRM/ERP) | Cannot remove the _cross-system_ seam — "composition across competitors' systems is against each vendor's interest" (research 08, §2.4). Per-tool macros are brittle (§2.4). | Agnostic agent integrates _across_ silos via MCP; removes the seam itself, not just intra-silo steps.                     |
| **Augment**  | Bolt-on observability / approval inside one product             | Governance is per-product and binary; the brief's intent-staged, posture-graded, five-dimensional envelope (research 08, §3.4) is richer than tool-level allow/deny.         | Execution-time-native posture + provenance across the _whole_ objective, not one vendor's slice (strategic spine M2).     |
| **Amplify**  | Marketplace of templates/apps _for its own platform_            | Templates are locked to the vendor's product and process model; company-specific process is un-ownable by the vendor (research 08, §2.4).                                    | Process-as-artifact is _yours_, agnostic, and shareable cross-org with governed provenance (research 08, §3.3; spine M4). |

**The one-line gap.** _Suite vendors automate within their silo only._ The platform's AAA is differentiated on all three axes precisely because it sits **agnostic in the middle** rather than vertical at a node — and the strategic spine identifies agnosticism-via-business-model as the suite vendors' permanent whitespace.

**The honest threat (strategic spine).** The sharpest competitor is **not** a suite vendor — it is **Claude Cowork (GA Apr 2026)**, which embodies the _surface_ thesis ("an agent does your work in one interface"). Cowork plausibly delivers a strong **Automate** surface. The platform must **not** compete on that surface; it competes on the **substrate** Cowork has not productized — versioned/interveneable execution (M1), execution-time posture-graded governance (M2), multi-human shared work (M3), governed cross-org artifact exchange (M4). In AAA terms: **Automate is the contested surface; Augment and Amplify are the uncontested substrate.** This directly informs the recommendation below.

**Role-map — reconciling the four framings (so a reader does not perceive a contradiction).** The strategy uses four different "lead" words across these analysis docs; each answers a _different_ question, and they are consistent, not competing:

| Framing                          | Answers                                  | Lead anchor                                       |
| -------------------------------- | ---------------------------------------- | ------------------------------------------------- |
| Lead **USP** (the story)         | What is the strongest differentiator?    | **M1** — versioned, interveneable execution       |
| **Ship-first** (the foundation)  | What gets built/demonstrated first?      | **M2** — execution-time posture-graded governance |
| Primary **platform transaction** | What compounds into a network engine?    | **M4** — governed cross-org artifact exchange     |
| Lead **wedge value** (AAA)       | Which axis leads the go-to-market wedge? | **Augment** — the decision layer (maps to M2)     |

The reconciliation: M1 is the _story you tell_ (hardest, highest-moat), M2 is the _thing you ship first_ (inherited, demonstrable now), M4 is the _engine that compounds_ (slowest to proof), and **Augment** is the AAA axis that carries the wedge — and Augment _is_ M2 expressed in AAA terms. No contradiction: different questions, aligned answers.

---

## Part 5 — Recommendation: which A is the sharpest wedge

Per `.claude/rules/recommendation-quality.md`: a single pick, its implications, and symmetric pros/cons in plain language.

### 5.1 The recommendation

> **Lead the wedge with AUGMENT. Use Automate as the necessary table-stakes demonstration beneath it, and position Amplify as the compounding moat that Augment unlocks over time.**

The logic in one paragraph: **Automate is the most visible axis but the most contested** — it is the exact surface Claude Cowork and every "agent does your work" entrant will fight on, and on a pure-Automate demo the platform competes head-on with the biggest-funded threat (Part 4, honest-threat clause). **Amplify is the strongest long-run moat** (network effects, M4) but has the slowest time-to-proof — its differentiating half (cross-untrusted-org exchange) is net-new and its value compounds over _quarters of usage_, not in a first demo (research 09, §6.3). **Augment is the axis where the platform is simultaneously differentiated AND demonstrable now**: the posture+provenance half is _inherited and shipping_ (research 08, §3.4; proven narrowly in the comms wedge per research 09, §2.1/§2.3), it is the substrate Cowork has not productized (strategic spine M2), and — decisively — research 05, §2 establishes that **Augment is load-bearing for correctness** in a world without a compiler, so it is not optional polish a competitor can skip. Leading with Augment lets the platform demonstrate Automate (you cannot show governance over nothing) while _winning on the part of the demo the competition cannot match_.

### 5.2 Implications of leading with Augment

- **What it changes for the build sequence.** The first proof targets research 08, §5.2 properties 4 and 5 (traced, interveneable) as the _headline_, with property 3 (≥2 systems) as the _substrate_ — i.e., the demo is "watch the agent run the 3Q report across five systems, **and watch yourself govern every consequential decision with full provenance and retrace**." The net-new replay engine (research 05, §6.2) moves onto the critical path, because retrace-and-recascade is the part of Augment that is not inherited.
- **What it changes for positioning.** The platform is sold as **"governed autonomous work,"** not "an agent that does your work." Connectivity is commodity (strategic spine: "only governed connectivity differentiates"); Augment is the framing that makes governance the headline.
- **Reversibility.** Low. Leading with Augment does not foreclose Automate or Amplify — it _orders_ them. If the market rewards raw Automate more than expected, the same demo already shows Automate underneath. The pick is a sequencing decision, not an architectural commitment (consistent with Decision B, capability-first/GTM-deferred).

### 5.3 Symmetric pros and cons

**Pros of leading with Augment:**

- **Differentiated against the biggest threat.** Avoids a head-on Automate-surface fight with Claude Cowork; competes on the substrate Cowork has not productized (strategic spine M2).
- **Demonstrable now.** The posture+provenance half is inherited and already proven narrowly in the comms wedge (research 09, §2.1, §2.3) — low first-demo risk for _that half_.
- **Load-bearing for correctness, not just trust.** Research 05, §2: without a compiler, the surfaced human judgment _is_ the verifier — so Augment is structurally necessary, not a feature a buyer can dismiss.
- **Bridges to Amplify.** Every interveneable decision and human correction is a capture point — Augment's provenance trail is the raw material Amplify codifies into artifacts (research 09, §2.2 learning-loop mapping). Augment first makes Amplify's compounding inevitable.

**Cons of leading with Augment (real, not glossed):**

- **The headline differentiator (retrace-and-recascade) is the hardest net-new build.** Research 05, §6.2 flags intervenable replay with downstream re-derivation as non-trivial and unspecced. Leading with Augment puts the _hardest_ piece on the critical path — the strategic spine names M1 as "best moat AND hardest build," and this is exactly that risk surfaced at demo time.
- **Governance is a less visceral first impression than "it did my work."** A buyer's gut reaction to Automate ("it did the whole report!") is stronger than to Augment ("I could see and steer every decision"). The Augment pitch requires the buyer to value _control_, which lands harder with risk-conscious / regulated buyers than with speed-first ones.
- **The governance category (TRiSM — Trust, Risk, and Security Management for AI) is filling with funded vendors** (strategic spine HONEST CAUTIONS). Leading with Augment enters a contested-and-funding category; the edge is "execution-time-native vs. bolt-on," which is real but must be demonstrated, not asserted.
- **Non-coder UX at the decision boundary is unsolved.** Surfacing "pick a posture; here is the agent's reasoning" in plain language a non-coder can act on is flagged as a hard 20–30% problem (research 05, §6.2(4)). Leading with Augment makes that UX the front door, raising the bar on the part of the build the no-code world historically fails (strategic spine: "non-coder DEPTH is where no-code dies at the last 20%").

### 5.4 The alternative, stated honestly

If the buyer evidence (deferred per Decision B) shows the early market rewards **raw speed over control** — e.g., a beachhead of speed-first SMEs rather than risk-conscious enterprises — then **lead with Automate** and treat Augment as the trust-enabler that _unlocks_ higher postures over time. The cost of that alternative is competing on the contested surface (Part 4 honest-threat); its benefit is a more visceral first demo and a lower first-build bar (no retrace engine on the critical path initially). The decision between these is exactly the GTM/beachhead choice the brief defers (Decision B), so this document **recommends Augment-led on capability grounds** while flagging that the buyer-evidence gate can legitimately re-order it.

---

## Part 6 — Synthesis: AAA in five load-bearing claims

1. **The three axes attack three distinct cost lines.** Automate → operational cost (the doing), Augment → decision cost (the judging), Amplify → expertise cost (the scaling). They are peers, not synonyms. (Part 0)
2. **Automate is the integration-layer inversion.** The agent becomes the integration layer the human used to be, crossing ≥2 systems with the human never swivel-chairing — distinct from brittle per-tool automation because the agent finds the path at run time. (Part 1; research 08 §2.4, §3.1, §5.2)
3. **Augment is the governance-and-transparency layer, and it is load-bearing for correctness.** Surfaced decisions + posture-graded approval + transparent provenance — inherited from PACT/EATP for the surface-and-approve half; net-new for the retrace-and-recascade half — and it substitutes for the compiler that knowledge work lacks. (Part 2; research 08 §3.4, research 05 §2, §3.3, §6.2)
4. **Amplify is process-as-artifact plus governed cross-org exchange.** A non-expert wields an expert's encoded procedure; sharing it across orgs (with an untrusted-publisher trust model) is the primary network-effects engine — the high-leverage, slowest-to-proof axis. (Part 3; research 08 §3.3, research 09 §5, §6.3)
5. **AAA exposes the suite-vendor gap and the Cowork threat.** Suite vendors automate within their silo only (structural, per research 08 §2.4); the platform differentiates on all three axes by sitting agnostic in the middle. The sharpest wedge is **Augment** — differentiated, demonstrable, and load-bearing — with Automate as the table-stakes substrate beneath it and Amplify as the compounding moat it unlocks. (Parts 4–5)

If these five hold, the AAA frame is not a marketing triptych — it is a cost-surface decomposition where each axis maps to a shipped-or-flagged mechanism in the platform's DNA, and the recommendation (Augment-led) is grounded in the conjunction of differentiation, demonstrability, and the compiler-substitute argument rather than in which axis sounds best.

---

## Appendix A — Source ledger

**Authoritative brief**

- `workspaces/future-of-work/briefs/01-vision.md` — the trinity (§2a/b/c), disruption thesis (§1), enabling shift (§2), future-of-work target state (§3a–g, esp. §3e posture + retrace, §3f transparency, §3g artifact sharing), Decisions A & B (§4).

**Research files (this analysis)**

- `01-research/08-work-disruption-thesis.md` — trinity & swivel-chair definition (§1.2, §1.3); seam-cost critique (§2.1–2.3); why vertical vendors can't fix it (§2.4); the inversion (§3.1); trinity→artifact mapping (§3.2, §3.3); inherited governance substrate (§3.4); honest seams (§3.5); capability-proof acceptance test (§5.2); empirical fragmentation figures (§2.2).
- `01-research/05-cli-harness-universal-interface.md` — harness anatomy & domain-agnostic capability table (§1, §2); the compiler-substitute argument (§2, §6.2); object/record-model gap (§3.2); intervenable-replay gap (§3.3, §6.2); posture ladder convergence (§3.5); business-MCP swap (§3.4, §5); "tools are dumb endpoints" keystone (§5.2); governance-between-agent-and-connector (§5.3); reusable-70-80% vs hard-20-30% (§6).
- `01-research/09-comms-wedge-mapping.md` — wedge as instance of platform primitives (§2); posture/HITL in comms (§2.1); learning-loop = feedback/capture (§2.2); D/T/R transparency (§2.3); tenant isolation (§2.4); process-as-config (§2.5); knowledge-compounding flywheel (§2.6); 80/15/5 split (§5); the three gaps comms does NOT exercise (§6.1 cross-system, §6.2 retrace/recascade, §6.3 cross-org sharing).

**Strategic spine (Phase A — aligned, not re-derived)**

- Moat conjunction M1–M4; Claude Cowork (GA Apr 2026) honest threat; suite-vendor verticality whitespace; "only governed connectivity differentiates"; TRiSM category-filling caution; non-coder-depth/last-20% caution; Decisions A (comms as wedge) & B (capability-first, GTM deferred); market read (research 07 — Gartner, MIT NANDA ~95% pilot failure).

## Appendix B — Flagged uncertainties (no fabrication)

1. **Retrace-and-recascade is the net-new core of Augment.** The surface-and-approve half is inherited and shipping (research 08 §3.4); the downstream-re-derivation engine is unspecced and non-trivial (research 05 §6.2). The Augment-led recommendation depends on this being buildable — it is the strategic spine's M1, named "best moat AND hardest build." Treated as the critical-path risk, not as done.
2. **Cross-untrusted-org artifact exchange (Amplify's differentiating half) is net-new.** Within-org / coding-artifact sharing is proven in loom (research 05 §1.2); the untrusted-publisher trust model for business artifacts across orgs is the genuine build (research 09 §6.3; spine M4). Amplify's _encode-once_ half is inherited; its _cross-org_ half is not.
3. **The comms wedge proves the AAA _shapes_ narrowly, not the AAA _breadth_.** Per research 09 §6: comms proves Augment's posture+provenance and Amplify's data-capture, but does NOT exercise cross-system Automate, retrace/recascade Augment, or cross-org Amplify. The wedge de-risks the spine; it is not a full AAA demonstration.
4. **The Augment-vs-Automate lead is a sequencing recommendation, re-orderable by buyer evidence (Decision B).** The capability-grounds pick is Augment; the GTM/beachhead choice that could re-order it to Automate-led is explicitly deferred per the brief. Stated as a recommendation with a named re-order condition (§5.4), not a locked decision.
5. **Empirical fragmentation figures are directional.** The context-switching and SaaS-count figures (research 08 §2.2) come substantially from vendor-adjacent sources; the AAA cost-reduction logic rests on the _structural_ claim (the seam is human-staffed), not on the precision of any single figure.
