# 04 — The Platform Model: Producers, Consumers, Partners, and the Artifact Exchange

> Product-analysis output for the agentic-work-platform (`/analyze`, Phase 01). Addresses
> the platform-business question: who PRODUCES value, who CONSUMES it, who PARTNERS to
> extend it, what the CORE TRANSACTION is, and how the marketplace's network effects start
> from a cold start.
>
> Grounds in: `01-research/01-coc-artifact-system.md` (the artifact machinery that already
> runs), `01-research/02-multi-operator-coordination.md` (the coordination + provenance
> substrate), `01-research/09-comms-wedge-mapping.md` (the deployed wedge as a working
> producer/consumer loop), and the Phase-A strategic spine (M1–M4 moat). Every claim cites
> a research file or the brief; genuine uncertainty is flagged **[UNCERTAIN]**.
> Effort is framed in autonomous-execution cycles (sessions), never human-days, per
> `rules/autonomous-execution.md`.

---

## 0. Executive summary — read this first

**A platform business is one where the operator does not produce all the value itself —
it builds the marketplace where others produce value and consumers find it, and it takes a
cut (monetary or otherwise) of every seamless transaction in between.** The classic examples
are an app store (developers produce apps, users consume them, the store governs the
exchange) or a ride marketplace (drivers produce rides, riders consume them, the platform
governs trust + payment). The question this document answers: **what is Sequor's equivalent
of "an app" — the unit that one party produces, another consumes, and the platform makes the
exchange seamless and trustworthy?**

The answer, recommended and justified in §2, is **the governed, versioned, provenance-tracked
work-artifact** — the reusable unit of "how a company does a piece of work" (a skill, a rule,
a process command, an agent, a connector). This is the **PRIMARY transaction**. A **secondary,
faster-cycling transaction** rides on top of it: the **knowledge contribution** — a human
answering something an agent could not, which the platform captures and turns into a learned
artifact (the comms wedge already runs this loop end-to-end, `09-comms-wedge-mapping.md` §1.3).
The first is the durable good being exchanged; the second is the mechanism by which the goods
keep improving without anyone writing them by hand.

**Why this is the right pick and not the obvious alternatives** (the full argument is §2):
an _executed work objective_ (the agent finishing a task) is real value but it is a SERVICE
the platform renders, not a TRANSACTION BETWEEN TWO PARTIES — there is no second party
producing it. A _posture-governed delegation_ (handing work to an agent under chosen
autonomy + budget) is a control surface, not a tradeable good. Only the **artifact** is a
thing one party creates, another party reuses, and the platform's trust layer makes safe to
exchange across an organizational boundary — which is exactly the network-effects engine the
strategic spine names **M4** ("the primary network-effects engine").

**The recommended shape (§7): a governed two-sided artifact exchange — a curated marketplace,
NOT an open free-for-all.** Producers publish work-artifacts; consumers (workers, teams,
whole organizations) install and run them; partners (connector vendors, system integrators,
compliance auditors, CLI-harness providers) extend the supply side and the trust side. The
exchange itself — the part Sequor owns and nobody else does — is **the trust/provenance/recall
layer** that makes it safe to run a stranger's process-artifact inside your company. That
layer already exists in skeleton form for one organization's code artifacts
(`01-coc-artifact-system.md` §0: "runs in production"); generalizing it to untrusted
cross-organization publishers is the genuinely-new 5% (`01-coc-artifact-system.md` §7c).

The honest counterweight, carried throughout: **the strongest network effects are also the
slowest to ignite and the hardest to govern.** A marketplace with ten artifacts is worthless;
the cold-start problem (§6) is existential. And an untrusted-publisher trust model that is
too strict kills supply, while one that is too loose ships a malicious process-artifact into
a customer's payroll run. Both failure modes are real and both are addressed, not waved away.

---

## 1. What "platform" means here, in plain language

Before naming the transaction, fix the vocabulary — because "platform" is overloaded and the
non-technical reader needs the business meaning, not the engineering one.

**A product** sells you a finished thing. You buy it, you use it, the seller made all of it.

**A platform** sells you _access to a marketplace_. The platform operator builds the rails;
other people (producers) put goods on the rails; you (a consumer) pick goods off the rails;
the operator makes sure the exchange is fast, trustworthy, and — critically — that nobody has
to negotiate the exchange by hand each time. That last property is what "seamless direct
transactions" means: a rider does not haggle with a driver over trust and payment; the
platform pre-solved both, so the transaction _just happens_.

The strategic spine has already decided Sequor is **both**: it is a product (the agentic work
interface a non-coder uses to get work done, brief §3) AND, layered on top, a platform (the
cross-organization artifact exchange, brief §3g: "artifacts are easily created, modified,
stored, and shared across organizations and teams"). This document is about the _platform_
half — the marketplace, its participants, and its core transaction. The product half (the
interface itself) is the consumer-side client of the marketplace.

> **One sentence to anchor the rest:** the platform's job is to make it as safe and as
> frictionless to run _another company's way of doing a piece of work_ as it is to install an
> app — and to make every such installation traceable, revocable, and improvable.

---

## 2. The core transaction — candidates, pick, and justification

The brief offers four candidate transactions; the strategic spine adds the constraint that
the transaction must be the thing that drives **M4 network effects** ("primary network-effects
engine"). Below, each candidate is assessed on one test: **is it a transaction BETWEEN TWO
PARTIES that the platform makes seamless, and does reusing it across parties get more valuable
as more parties join?** That two-part test is what separates a platform transaction from a
mere product feature.

### 2.1 The four candidates, assessed

| Candidate transaction                                                                                                        | What it is, plainly                                         | Two-party?                                                                                                                 | Network effect?                                                                                                                        | Verdict                                                                                              |
| ---------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------- |
| **(A) An executed work objective** — the agent finishes "produce the 3Q report"                                              | The platform renders a service for one user                 | **No** — one party (user) consumes a service the _platform_ produces; no second producing party                            | Weak — my finished report does not make your report easier                                                                             | **Not the primary** — it is the product's core _value_, but it is a service, not an exchange         |
| **(B) A published/consumed work-artifact** — org A's "invoice-reconciliation skill" installed and run by org B               | A reusable unit of _how to do work_ crosses an org boundary | **Yes** — A produces, B consumes, platform governs the exchange                                                            | **Strong** — every new artifact raises the value of the catalog for every consumer; every new consumer raises the payoff of publishing | **PRIMARY**                                                                                          |
| **(C) A posture-governed delegation** — handing an objective to an agent at a chosen autonomy level (L3/L4/L5) with a budget | A control + trust act between a human and their own agent   | **No** — it is a _governance_ act within one party, not an exchange between two                                            | None — my delegation choice is private to my run                                                                                       | **Not a transaction** — it is the _control surface_ (moat M2) that makes the other transactions safe |
| **(D) A knowledge contribution** — a human answers what the agent could not; the platform learns it into a reusable policy   | An intervention residue captured as durable knowledge       | **Yes, asymmetrically** — human produces the answer, the platform (and future runs, and potentially other orgs) consume it | **Strong but slower-burning** — each captured answer improves the artifact that produced the gap                                       | **SECONDARY / FEEDER**                                                                               |

The decisive column is "Two-party?". A platform transaction needs a _producer_ and a _consumer_
who are different parties; (A) and (C) fail that test — they are things the platform does FOR
one party, not exchanges BETWEEN parties. (B) and (D) pass.

### 2.2 The recommendation: B is primary, D is its feeder

**Recommended primary transaction: (B) the published/consumed work-artifact.** Recommended
secondary transaction: **(D) the knowledge contribution**, which feeds B by generating new and
improved artifacts from real work.

**Why B is primary, in business terms.** The artifact is the only candidate that is a _durable
good_ one party creates and another party reuses across an organizational boundary. That is
precisely the definition of the marketplace good. And it is the one the strategic spine already
named as the **primary network-effects engine (M4)** — the more orgs publish their ways of
working, the richer the catalog; the richer the catalog, the more orgs want in. The machinery
to make this exchange real _already exists and runs in production for one organization_
(`01-coc-artifact-system.md` §0: the COC artifact system "does this for one organization's
codegen artifacts across ~6 distribution targets and 30+ downstream consumers"). The platform's
build is to generalize it from one-org-code-artifacts to many-orgs-work-artifacts — the
80/15/5 split in `01-coc-artifact-system.md` §7 (80% reusable, 15% adapt, 5% genuinely new).

**Why D is the feeder, not the primary.** A marketplace whose only supply is hand-written
artifacts grows at the speed of expert authors — slow, and it dies at "the last 20%" of
domain depth (the strategic spine's honest caution about where no-code dies). The knowledge
contribution loop (D) is what makes the supply self-replenishing: every time a worker corrects
or completes something the agent could not do, the platform captures that correction and turns
it into an improved artifact, _without anyone authoring it by hand_. The comms wedge proves
this loop end-to-end _today_: a human resolves an escalation by replying to an email, and the
reply becomes a durable knowledge chunk that answers future matching queries
(`09-comms-wedge-mapping.md` §1.3, §2.2). That is transaction D running in production — and it
is "the captured residue of a human intervention" becoming "durable institutional knowledge"
(`09-comms-wedge-mapping.md` §2.2). Generalizing D from "learns _answers_" to "learns
_artifacts_ (procedures, rules, skills)" is the stated gap (`09-comms-wedge-mapping.md` §2.2
[INFERENCE], §6.1): comms captures data-level knowledge; the platform must capture
process-level knowledge.

**The two transactions compose into one flywheel** — this is the load-bearing insight:

```
   (D) human answers what the agent couldn't        the comms wedge runs this loop NOW
        │   captured as durable knowledge            (09-comms-wedge-mapping §1.3)
        ▼
   improved / new work-artifact                      generalize "answer" → "artifact"
        │                                            (the platform's real build, §6.1 gap)
        ▼
   (B) artifact published to the exchange            the M4 marketplace
        │   installed + run by other consumers
        ▼
   more usage → more gaps surfaced → more (D)        the flywheel closes
```

**Implications of choosing B+D over A or C:**

- The platform's defensibility lives in the _exchange_, not the _execution_. Cowork (GA Apr 2026) executes work in one interface (the strategic spine's "biggest threat") — that is
  transaction A's surface. Choosing B as primary means Sequor does NOT compete on "agent does
  your work" (a commoditizing surface); it competes on "your way of working is a tradeable,
  trustworthy, improvable asset" (a surface no competitor has productized for non-coders).
- A and C are not abandoned — they are _repositioned_. A (executed objective) is the product's
  value to the individual user; it is what makes someone _use_ the platform daily, which is the
  precondition for D (you only generate knowledge contributions while doing real work). C
  (posture-governed delegation) is moat **M2**, the governance that makes running a stranger's
  artifact safe enough to be a transaction at all. They are the _engine_ and the _brakes_; B
  is the _goods_ and D is the _refinery_.

**Symmetric cons of this pick (stated honestly):**

- B has the strongest network effects AND the worst cold-start (§6). A marketplace good is
  worthless until there is both supply and demand; A (execute a work objective) has value from
  the very first user with zero network. Betting the platform thesis on B means accepting a
  longer runway to the network-effect payoff.
- D depends on an unproven generalization. Comms proves D for _answers_ (data-level); the leap
  to D for _artifacts_ (process-level) is explicitly flagged as not-yet-built
  (`09-comms-wedge-mapping.md` §6.1). If process-level capture turns out to be much harder than
  answer-level capture, the flywheel's refinery stalls and supply reverts to hand-authoring
  speed.
- The whole pick rests on the contrarian bet that "a company's way of working" is a thing
  worth trading across org boundaries at all. MIT NANDA's finding that ~95% of GenAI pilots
  fail because generic tools "don't learn from / adapt to workflows" (market research 07, cited
  in the strategic spine) _supports_ the bet — but it is still a bet, not a proven market.

---

## 3. PRODUCERS — who creates the goods

A producer is anyone who puts a reusable work-artifact (or a knowledge contribution that
becomes one) onto the exchange. The platform's supply side has five distinct producer types,
in rough order from highest-skill/lowest-volume to lowest-skill/highest-volume.

### 3.1 The five producer types

| Producer type                               | What they publish                                                                                             | Skill required                                  | Volume      | Grounding                                                                                                                                   |
| ------------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ----------------------------------------------- | ----------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| **Expert teams / domain authors**           | Hand-crafted high-value artifacts (a finance team's close-process skill, a legal team's contract-review rule) | High (domain + authoring discipline)            | Low         | The three authoring meta-skills + the layer taxonomy (`01-coc-artifact-system.md` §1, §4)                                                   |
| **Process owners**                          | Their company's specific procedure encoded as a configurable artifact                                         | Medium (knows the process, not the code)        | Medium      | "company-specific process as configurable artifact" — comms' per-account routing config proves it (`09-comms-wedge-mapping.md` §2.5)        |
| **Connector / integration builders**        | Adapters that make a system (ERP, CRM, a niche SaaS) reachable as a tool                                      | High (technical)                                | Low–medium  | The MCP connector layer; comms' email/WhatsApp adapters are instances (`09-comms-wedge-mapping.md` §3, §5.1 "Connectors")                   |
| **Workers (as incidental producers via D)** | Knowledge contributions — answers/corrections captured into artifacts                                         | None (they just do their work)                  | **High**    | The learning-from-human-answers loop (`09-comms-wedge-mapping.md` §1.3, §2.2)                                                               |
| **Agents (as producers)**                   | Artifacts proposed from observed work via the codify loop                                                     | None human (the agent drafts; a human approves) | Medium–high | `/codify` originates proposals from observed sessions (`01-coc-artifact-system.md` §3a); the codify loop is the agent-as-producer mechanism |

### 3.2 The producer hierarchy is the supply-side answer to cold-start

The critical design insight: **the producer types are ordered so that the low-skill/high-volume
producers (workers + agents) generate most of the supply once the platform is in use, while the
high-skill/low-volume producers (expert teams) seed the initial catalog.** This is the
self-replenishing supply the flywheel (§2.2) requires.

- **Workers produce without knowing they are producing.** A worker resolving an escalation in
  comms is producing a knowledge contribution (transaction D) as a _byproduct_ of doing their
  job (`09-comms-wedge-mapping.md` §4.2: "intervention residue can be captured at the moment of
  resolution with no separate training step — the human just replies, and the system learns").
  This is the single most important supply-side property: **the platform's largest producer
  cohort produces for free, as exhaust from work they were doing anyway.**
- **Agents produce drafts; humans gate them.** The codify loop has an agent observe a work
  session, draft a candidate artifact, and route it for human approval before it enters the
  catalog (`01-coc-artifact-system.md` §3a). This keeps agents as _producers_ (they generate
  supply) without making them _authorities_ (a human always classifies and approves, per the
  Gate-1 human-classify discipline, `01-coc-artifact-system.md` §2b). The agent-as-producer is
  governed, never autonomous-into-the-catalog.

### 3.3 Producer-side identity and attribution

For the marketplace to work, _every published artifact must be attributable to its producer_ —
both for trust (who vouches for this?) and for the recall primitive (if it is bad, whose other
artifacts are suspect?). The multi-operator substrate already makes attribution cryptographic,
not nominal: every record is signed by a `verified_id` that resolves to exactly one `person_id`
(one human) (`02-multi-operator-coordination.md` §4.3, §4 synthesis takeaway #4). The net-new
piece for the marketplace is **two-level attribution**: an agent-produced artifact must be
attributable to _both_ the producing agent AND the human accountable for it
(`02-multi-operator-coordination.md` §4.3: "giving agents their own enrolled signing identity
… so an agent's autonomous output is attributable to the agent AND to the human accountable
for it").

> **Implication for the founder:** the producer side is not a "build it and they will come"
> bet on expert authors. It is a _byproduct-capture_ engine — the platform's biggest supply
> source is ordinary work, captured automatically. The expert-author tier seeds; the
> worker+agent tier scales. This inverts the usual marketplace cold-start risk on the supply
> side (it does NOT solve the demand side — see §6).

---

## 4. CONSUMERS — who uses the goods

A consumer is anyone who installs and runs a work-artifact to get their own work done. Three
nested scopes, from individual to organization.

### 4.1 The three consumer scopes

| Consumer scope               | What they consume                                                                   | What "seamless" means for them                                                   | Grounding                                                                                              |
| ---------------------------- | ----------------------------------------------------------------------------------- | -------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------ |
| **Individual workers**       | A single artifact to do a single objective (install "expense-report skill", run it) | One interface, state intent, govern; no crossing 5 vertical tools                | Brief §1, §3; comms collapses 4 interfaces into 1 (`09-comms-wedge-mapping.md` §3)                     |
| **Teams**                    | A shared set of artifacts + a shared coordination substrate for co-working          | Humans + agents co-work on one objective with claims/leases preventing collision | The multi-operator team-work substrate (`02-multi-operator-coordination.md` §0, §3, §10) — moat **M3** |
| **Downstream organizations** | A whole org adopts another org's process library (or a vendor's)                    | Install once, distribute to all the org's teams, govern centrally                | The two-gate `/sync` distribution to "30+ downstream consumers" (`01-coc-artifact-system.md` §2c, §7)  |

### 4.2 Consumption is governed at install AND at run

The consumer does not just download an artifact — they _run someone else's process inside
their own company_, against their own data, with their own agents. That is the moment trust
matters most. Two governance gates protect the consumer:

- **At install:** the artifact's provenance is checked (who produced it, is it signed, has it
  been recalled). The recall primitive — a single declarative entry purges a bad artifact from
  every consumer on next sync (`01-coc-artifact-system.md` §2d: "the ONLY mechanism by which
  30+ downstream repos can purge stale orphan directories"; "the cross-org 'recall a bad
  artifact' primitive the marketplace will need") — is the consumer's protection against a
  producer who turns malicious or buggy after the fact.
- **At run:** the consumer chooses the _posture_ (transaction C, moat M2) under which the
  artifact executes — L3 step-by-step, L4 one-permission, L5 autonomous — plus budgets and
  clearance (brief §3e). A consumer running an unfamiliar artifact runs it at L3 (pause at every
  step) until they trust it; a consumer running a battle-tested one runs it at L5. **The posture
  choice is the consumer's brake on the producer's artifact** — this is why C is the control
  surface that makes B safe (§2.1).

### 4.3 The consumer is also (via D) a producer

The defining feature of this marketplace, distinguishing it from an app store: **consuming
generates supply.** Every time a consumer runs an artifact and a human has to intervene to fix
a gap, that intervention is captured (transaction D) and feeds back as an improved artifact
(§2.2 flywheel). In an app store the consumer is a pure sink; here the consumer is a sink that
emits refinements. This is what makes the network effect compounding rather than merely additive
(`09-comms-wedge-mapping.md` §2.6: the routing flywheel is "the data-layer instance of the
platform's knowledge-compounding primitive").

> **Implication for the founder:** demand-side adoption is the hard half of cold-start (§6).
> But every consumer who adopts is not just demand — they are future supply (via D) and future
> word-of-mouth (a team that co-works successfully on the platform pulls in adjacent teams). The
> consumer scopes nest: an individual's success pulls in their team; a team's success pulls in
> their org; an org becomes a downstream-distribution consumer pulling its own sub-teams. The
> team scope (M3) is the inflection point — single-user value is real but bounded; team value is
> where the platform stops being a tool and becomes the substrate.

---

## 5. PARTNERS — who extends the rails

A partner is a third party who does not produce work-artifacts for end-consumers directly, but
extends the platform's _supply capacity_ or _trust capacity_. Partners are the multi-sided
dimension: a two-sided market is producers↔consumers; partners make it multi-sided.

### 5.1 The four partner types

| Partner type                    | What they provide                                                                               | Which side they extend                                                   | Grounding                                                                                                                                                                                                                                    |
| ------------------------------- | ----------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Connector / MCP vendors**     | Pre-built, maintained adapters to systems (the long tail of enterprise SaaS, ERPs, niche tools) | Supply (more systems reachable = more objectives addressable)            | The MCP connector layer is the agnosticism foundation (strategic spine FOUNDATION; brief §2); "connectivity is commodity, only GOVERNED connectivity differentiates" (strategic spine caution)                                               |
| **System integrators (SIs)**    | Per-customer deployment, the bespoke 5%, change management for non-coder rollout                | Demand (lower the adoption cost for large orgs)                          | The 5% true-custom layer is genuinely external/one-off (`09-comms-wedge-mapping.md` §5.3) — SIs own it                                                                                                                                       |
| **Compliance / audit partners** | Independent attestation that an artifact (or a deployment) meets a regulatory bar               | Trust (third-party vouching raises catalog trust)                        | D/T/R audit trail is PDPA-clean and built to a real regulator's bar (`09-comms-wedge-mapping.md` §4.3, §4.4); the signed coordination log is "auditable in a way human↔human comms can never be" (`02-multi-operator-coordination.md` §10.2) |
| **Harness providers**           | The agent CLI runtimes themselves (Claude Code, Codex, Gemini)                                  | Supply + reach (the platform runs ON these; multi-harness = wider reach) | Multi-CLI parity via the emitter (`01-coc-artifact-system.md` §6); the platform is "harness-agnostic" (brief §3e); envoy proves the same artifact across three harnesses                                                                     |

### 5.2 The partner relationship is asymmetric — and that is the design

The connector/MCP and harness layers are explicitly _commoditizing_ (the strategic spine:
"agnosticism via MCP/A2A + multi-CLI parity" is FOUNDATION, table-stakes, not headline; A2A
commoditizes agent-to-agent). Sequor's relationship to those partners is therefore deliberately
_thin_: it consumes their commodity (connectivity, runtimes) and adds the one thing they do not
— **governance and provenance over the exchange**. The platform does not try to own connectors
(a losing race against the whole MCP ecosystem); it owns the _governed_ layer on top
(`01-coc-artifact-system.md` §7c: "the trust/provenance layer atop the commoditizing
skills/MCP marketplace" = moat M4).

The compliance/audit partner is the inverse — a _thick_, high-value relationship. An
independent auditor attesting "this payroll-process artifact meets SOC-2 / PDPA / [regime]" is
a trust multiplier the platform cannot self-provide credibly (a marketplace cannot be its own
auditor). The D/T/R audit substrate (`09-comms-wedge-mapping.md` §2.3, §4.3) gives auditors a
clean, append-only, PII-free trail to attest against — which makes Sequor an unusually
_auditable_ platform, a genuine selling point into regulated buyers.

> **Implication for the founder:** partners are not all equal. Connector + harness partners are
> commodity inputs — integrate broadly, depend on none, never try to own them. Compliance/audit
> partners are trust amplifiers — invest in making the platform the _easiest to audit_, because
> third-party attestation is the lever that lets a consumer trust an artifact from a producer
> they have never met. SIs are the demand-side accelerant for the enterprise segment — but the
> 80/15/5 split means SIs should own only the 5%; if SIs are doing 30% of every deployment, the
> self-service layer (the 15%) is failing and the platform economics break.

---

## 6. The cold-start problem and how to avoid it

This is the existential risk for any platform thesis, stated plainly: **a marketplace with no
supply has no demand, and a marketplace with no demand attracts no supply.** The strongest
network effect (M4, transaction B) is also the slowest to ignite. Three avoidance strategies,
in priority order.

### 6.1 Seed the supply side with the ecosystem's existing 400+ artifacts

The platform does not start empty. The COC artifact system already contains a counted inventory
of **39 agents, 36 skills (405 total skill files), 70 rules, 30 hooks, 41 commands, and 499
variant-overlay files** (`01-coc-artifact-system.md` §1). These are _real, running, production_
artifacts — the layer taxonomy, the authoring discipline, the splitter, all of it
(`01-coc-artifact-system.md` §0). They are codegen-domain artifacts, so they are not directly
sellable to a finance team — but they prove the machinery works at scale and they are the seed
catalog for the _first_ vertical the platform generalizes into.

**The de-coupling work is mechanical, not novel:** generalizing the artifact taxonomy from
"codegen" to general work domains is "mechanically identical to adding a tier in
sync-manifest.yaml" (`01-coc-artifact-system.md` §7b.3), estimated at **~1 session** of
autonomous work (`01-coc-artifact-system.md` §7d: "generalizing tiers + adding org-axis variants
is ~1 session … high feedback loop"). The seed catalog is therefore not a year of hand-authoring;
it is an existing asset plus a small generalization.

**Symmetric con:** the 400+ seed artifacts are _codegen_ artifacts. They prove the _machinery_
but they do not seed _demand_ in any non-coding vertical. A finance buyer sees an empty finance
shelf. Seeding the machinery is necessary but not sufficient; the first vertical still needs its
own seed supply, which is where the wedge comes in.

### 6.2 Use the comms wedge as a working, single-vertical producer/consumer loop

The comms product is a **complete, deployed producer↔consumer loop in one vertical** — running
against real users and real data on Vercel + Neon (`09-comms-wedge-mapping.md` §0, §4). It runs
transaction D end-to-end _today_ (human answers → learned knowledge → better future answers,
`09-comms-wedge-mapping.md` §1.3) and it embodies the consumer experience (one interface
collapsing four tools, `09-comms-wedge-mapping.md` §3).

The wedge's role in cold-start avoidance is **proof, not scale**: it demonstrates that the
core loop _works against real users_ before the cross-org marketplace exists. It de-risks five
platform primitives (trust/posture, feedback, D/T/R transparency, multi-org isolation,
process-as-config — `09-comms-wedge-mapping.md` §2, §4) so that when the marketplace launches,
the rails underneath it are already battle-tested. A founder pitching the marketplace can point
to a _live system_ running the same loop, not a slide.

**Symmetric con:** the wedge proves the _spine_ (trust/feedback/transparency/isolation) but
NOT the _orchestration_ half the marketplace ultimately needs — it has no multi-step cross-system
objectives, no step-level retrace/intervene with versioned cascades, and crucially **no cross-org
artifact sharing** (`09-comms-wedge-mapping.md` §6.1–6.3). Comms tenants are "sealed silos by
design" (`09-comms-wedge-mapping.md` §6.3). So the wedge is a working single-vertical loop but
it is NOT a working marketplace — it proves the producer↔consumer loop _within_ a tenant, not
_across_ tenants. The cross-org leap (the actual M4 marketplace) is unproven by comms and is the
platform's real build.

### 6.3 Make the first producers also the first consumers (close the loop inside one org)

The third strategy follows from §3.2 + §4.3: **the same party can be producer and consumer**,
so the marketplace can bootstrap _inside a single organization_ before any cross-org exchange
exists. Org A's finance team publishes its close-process artifact; org A's _other_ teams consume
it; workers' interventions (D) improve it. This is a fully-functional artifact economy with a
network size of one organization — exactly what the COC system already does for one org's code
artifacts ("does this for one organization's codegen artifacts", `01-coc-artifact-system.md`
§0). Cross-org exchange is then an _expansion_ of a working intra-org economy, not a leap from
zero.

This sequencing matters for the cold-start math: intra-org, supply and demand are the _same_
customer, so there is no chicken-and-egg — the org that buys gets value from day one (its own
teams sharing its own processes), and cross-org network effects are pure upside layered on top.

> **Recommended cold-start sequence (single recommendation, not a menu):** (1) seed the
> machinery with the existing 400+ artifacts and generalize the taxonomy (~1 session); (2) run
> the comms wedge as the live proof-of-loop and first revenue-bearing vertical; (3) launch the
> marketplace as an _intra-org_ artifact economy first (supply = demand = same customer, no
> chicken-and-egg), and only then open the cross-org exchange once intra-org loops are running.
> **Implication:** this defers the highest-network-effect transaction (cross-org B) until the
> intra-org version has proven the loop with paying customers — slower to the big payoff, but it
> removes the existential cold-start risk by never requiring two unknown parties to both show up
> at once. **Con of this sequence:** a competitor who launches an open cross-org marketplace
> first could capture the network-effect lead while Sequor is still proving intra-org loops;
> the trade-off is cold-start safety vs first-mover-on-network-effects, and the recommendation
> takes safety because a cross-org marketplace that fails to ignite is worth zero while an
> intra-org economy that works is worth real revenue.

---

## 7. The recommended platform-model shape

**Recommendation: a governed, curated, two-sided-plus-partners artifact exchange — where the
defensible layer Sequor owns is the trust/provenance/recall machinery over the exchange, NOT
the artifacts themselves and NOT the connectivity.**

In one line: **Sequor is the trust layer of a work-artifact marketplace.** Producers make the
goods; consumers run the goods; partners extend supply and trust; Sequor governs the exchange
and takes its cut from being the party that makes a stranger's process safe to run.

### 7.1 What "curated, not open" means and why

The choice between an **open marketplace** (anyone publishes, caveat emptor — like a package
registry) and a **curated marketplace** (publishing is gated, provenance is enforced — like a
reviewed app store) is the single most consequential shape decision. The recommendation is
**curated, leaning toward graduated-openness**:

- **Why curated, not open:** the goods here are not apps that run in a sandbox — they are
  _processes that run inside a company against its real data, payroll, customers_. An open
  marketplace's failure mode is a malicious or buggy artifact executing in a consumer's
  production environment. The strategic spine names the "untrusted-publisher trust model" as the
  genuinely-new 5% precisely because this is unsolved (`01-coc-artifact-system.md` §7c.1: the
  existing threat model is _bounded-trust_ — "the adversary is a legitimate team member with
  repo write access" — and "signed-artifact provenance from an _external_ publisher … is not yet
  modeled"). You cannot run a stranger's payroll process on caveat-emptor.
- **Why graduated, not locked-down:** a fully locked-down marketplace (only Sequor-blessed
  artifacts) kills the supply-side network effect — the whole point of B is that _many parties_
  publish. The resolution is the **asymmetric publish/consume governance** that already exists as
  a baseline rule in the commercial fork (`01-coc-artifact-system.md` §7c.2): the canonical
  registry artifact stays generic; org-specific overrides are allowed; upstreaming
  generic-improvements is allowed but client-specific leakage downstream is blocked. Layered on
  top: posture-graded _consumption_ (§4.2) means even an unvetted artifact can be run safely at
  L3 (pause-every-step), so openness on the _publish_ side is balanced by caution on the _run_
  side.

### 7.2 The three layers Sequor owns vs the two it does not

| Layer                                                        | Sequor's stance                                                                                             | Grounding                                                                                                                                        |
| ------------------------------------------------------------ | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| **The artifacts**                                            | Sequor does NOT own these — producers do. Sequor seeds, never monopolizes.                                  | Producers §3; the 400+ seed is a starter, not a moat                                                                                             |
| **The connectivity**                                         | Sequor does NOT own this — MCP/connector vendors + harness providers do. Integrate broadly, depend on none. | "Connectivity is commodity" (strategic spine); MCP foundation (brief §2)                                                                         |
| **The exchange / trust / provenance / recall**               | Sequor OWNS this. It is moat M4 and the genuinely-new 5%.                                                   | `01-coc-artifact-system.md` §7c; the splitter + variant overlay + recall primitive + Gate-1 human-classify (`01-coc-artifact-system.md` §2, §7a) |
| **The coordination substrate (team co-work)**                | Sequor OWNS this. It is moat M3 (the human-multiplicity half A2A does not commoditize).                     | `02-multi-operator-coordination.md` §0, §10.3                                                                                                    |
| **The execution-time governance (posture/budget/clearance)** | Sequor OWNS this. It is moat M2, the brake that makes B safe.                                               | brief §3e; `09-comms-wedge-mapping.md` §2.1                                                                                                      |

The discipline this table encodes: **own the layers that get more defensible as the network
grows (exchange, coordination, governance); rent the layers that commoditize (artifacts,
connectivity).** Trying to own the commodity layers is the classic platform mistake — it burns
capital racing an entire ecosystem and adds no defensibility.

### 7.3 Pros and cons of the recommended shape (symmetric, honest)

**Pros:**

- **It maps onto machinery that already runs.** 80% of the exchange layer exists in production
  for one org's code artifacts (`01-coc-artifact-system.md` §7a); the recommendation is a
  generalization, not a greenfield build. Estimated: taxonomy generalization ~1 session;
  cross-org publish/subscribe surface ~3–5 sessions; the untrusted-publisher trust model is a
  novel-architecture decision to design _first_ (`01-coc-artifact-system.md` §7d).
- **The defensible layer is the one competitors haven't built.** Cowork does transaction A's
  surface; suite vendors are vertical by business model; nobody has productized governed cross-org
  artifact exchange for non-coders (strategic spine M4). Owning the exchange/trust layer is
  whitespace.
- **It is unusually auditable**, which is a real enterprise selling point — the D/T/R trail is
  PDPA-clean and built to a regulator's bar (`09-comms-wedge-mapping.md` §4.3, §4.4), and the
  coordination log is cryptographically attributable (`02-multi-operator-coordination.md` §10.2),
  giving compliance partners (§5) a clean surface to attest against.
- **Supply self-replenishes** via the worker+agent producer tiers (§3.2) feeding transaction D
  — the largest producer cohort produces for free as work exhaust.

**Cons (real, not glossed):**

- **The genuinely-new 5% is the load-bearing 5%.** The untrusted-publisher trust model
  (`01-coc-artifact-system.md` §7c.1) is unbuilt AND unmodeled AND it must be designed before
  the cross-org surface, because it constrains that surface (`01-coc-artifact-system.md` §7d). If
  this trust model is harder than estimated, the entire cross-org marketplace (the M4 payoff)
  slips. This is the highest-risk dependency in the whole platform thesis.
- **Cold-start on the cross-org B transaction is severe** (§6) — mitigated by the intra-org-first
  sequence, but mitigation means deferring the biggest network effect, which cedes potential
  first-mover-on-network-effects advantage.
- **Curation is a cost and a bottleneck.** The Gate-1 "human classifies every change" discipline
  (`01-coc-artifact-system.md` §2b) is a _human_ gate; at marketplace scale (thousands of
  publishers vs the current one-org-many-repos), a human-classify bottleneck does not obviously
  survive (`02-multi-operator-coordination.md` §11.1 flags the substrate is designed for "~12
  operators" and its scaling to "10K+ participants / 1M+ records" is unproven). The recommendation
  assumes curation can be partially automated (suggestion-automated, placement-human per the
  existing rule) but the scaling is an open question, not a solved one.
- **The posture-graded-consumption brake (M2) depends on consumers actually choosing
  conservative postures.** A consumer who runs every unvetted artifact at L5 (autonomous) to save
  time defeats the brake. The platform can default to L3 for unfamiliar artifacts, but defaults
  are not guarantees; a determined consumer can over-trust, and then a bad artifact runs
  autonomously. The brake is real but it is a _default_, not a _lock_.

### 7.4 What this is NOT — explicit non-goals

To keep the recommendation honest and bounded:

- It is **not** "agent does your work in one interface" (transaction A's surface — that is the
  product layer, and it is where Cowork competes; do not compete there).
- It is **not** an open package registry (caveat-emptor fails for process-that-runs-on-your-data).
- It is **not** a connector marketplace (connectivity commoditizes; owning it adds no
  defensibility).
- It is **not** proven at cross-org scale by anything currently running — the comms wedge proves
  the intra-tenant loop, not the cross-tenant exchange (`09-comms-wedge-mapping.md` §6.3).

---

## 8. The multi-sided dynamics, drawn together

The exchange (M4) is the core; producers, consumers, and partners arrange around it with the
flywheel running through the middle.

```
            PARTNERS (extend supply + trust)
   connector/MCP vendors · SIs · compliance/audit · harness providers
        │  supply capacity            trust capacity  │
        ▼                                             ▼
  ┌──────────────────────────────────────────────────────────┐
  │            THE GOVERNED ARTIFACT EXCHANGE (M4)            │
  │   provenance · versioning · recall · variant-overlay     │
  │   Gate-1 human-classify · disclosure-scrub · trust model │
  │   ── the layer Sequor OWNS; the 80%-exists + 5%-new ──   │
  └──────────────────────────────────────────────────────────┘
        ▲                                             │
        │ (B) publish artifact          install + run │ (B)
        │                                             ▼
   PRODUCERS                                     CONSUMERS
   expert teams · process owners ·    individual workers · teams (M3) ·
   connector builders · workers ·     downstream organizations
   agents (via /codify)                          │
        ▲                                         │ governed at install (recall)
        │                                         │ governed at run (posture M2)
        │       (D) knowledge contribution        │
        └─────────  human answers gap  ◄──────────┘
                    captured → improved artifact → re-published (B)
                    [the comms wedge runs this loop in one vertical NOW]
```

**The three sides and what each gets:**

- **Producers** get distribution (their way of working reaches consumers they never met) +
  attribution (cryptographic credit, `02-multi-operator-coordination.md` §4.3) + upstream
  improvement (consumers' D-contributions flow back as refinements).
- **Consumers** get a catalog of vetted ways-to-do-work + the safety to run a stranger's process
  (governed install + governed run) + the collapse of N vertical tools into one interface
  (brief §1).
- **Partners** get reach (connector/harness vendors' commodity becomes the substrate of every
  governed transaction) + a high-trust attestation surface (compliance partners) + the bespoke
  5% (SIs).
- **Sequor** gets the cut — the position of being the party that makes the exchange seamless and
  safe, which is the only position in the diagram that gets _more_ valuable as every other
  position fills.

---

## 9. Open questions / uncertainty flags

1. **[UNCERTAIN] The untrusted-publisher trust model.** This is the genuinely-new 5%
   (`01-coc-artifact-system.md` §7c.1) and the load-bearing dependency (§7.3). Its design —
   how an external publisher's signed provenance is established, vouched, and revoked when there
   is no shared enrollment authority — is not yet modeled. It must be designed before the cross-org
   surface. **This is the #1 thing to resolve before committing to the cross-org marketplace.**
2. **[UNCERTAIN] Curation at marketplace scale.** Gate-1 human-classify
   (`01-coc-artifact-system.md` §2b) works for one-org-many-repos; the coordination substrate is
   designed for ~12 operators (`02-multi-operator-coordination.md` §11.1). Whether
   human-in-the-loop curation survives thousands of publishers, or whether it must become
   reputation-weighted / partially-automated, is unresolved.
3. **[UNCERTAIN] Does D generalize from answers to artifacts?** The comms wedge proves D for
   _answers_ (data-level); the platform needs D for _process-artifacts_ (process-level)
   (`09-comms-wedge-mapping.md` §6.1 [INFERENCE]). The flywheel's refinery (§2.2) depends on this
   generalization holding; it is asserted, not yet demonstrated.
4. **[UNCERTAIN] The monetary model.** The brief says transactions "need not be monetary"; this
   document deliberately stays at the transaction-shape level and does NOT recommend a pricing
   model (per Decision B, GTM deferred). Whether the cut is subscription, per-install, per-run,
   revenue-share with producers, or a blend is a downstream GTM question — but the _shape_ (own
   the exchange, rent the commodity layers) constrains it: Sequor monetizes the exchange position,
   not the artifacts or the connectivity.
5. **Cross-org sharing vs hard tenant isolation.** Comms enforces hard PDPA schema-per-tenant
   isolation (`09-comms-wedge-mapping.md` §1.4, §2.4); the marketplace requires deliberate
   cross-tenant artifact permeability. How the strong-isolation default and the
   controlled-permeability exchange coexist is the boundary-policy question
   (`09-comms-wedge-mapping.md` §7.5) — loom's variant-overlay + Gate distribution is the
   candidate mechanism but its interaction with hard tenant isolation is undesigned.
6. **Substrate choice for the trust root.** The two existing implementations (loom git-native vs
   aegis runtime-keypair) have diverged (`02-multi-operator-coordination.md` §11.5); the
   marketplace likely wants "aegis-shape runtime records, with loom-shape external anchoring
   against the tenant's identity provider instead of GitHub" (`02-multi-operator-coordination.md`
   §10.3) — but this is a synthesis-to-be-built, not a chosen substrate.

---

## 10. Source index (files actually consulted)

- Brief: `~/repos/projects/Sequor/workspaces/future-of-work/briefs/01-vision.md`
- Artifact machinery: `01-analysis/01-research/01-coc-artifact-system.md` (§0 exec summary,
  §1 layer taxonomy + inventory counts, §2 splitter/variant/recall, §3 codify lifecycle,
  §4 authoring skills, §7 cross-org synthesis + 80/15/5, §7c genuinely-new + untrusted-publisher,
  §7d autonomous-execution sizing)
- Coordination + provenance + team-work: `01-analysis/01-research/02-multi-operator-coordination.md`
  (§0 exec summary, §1 unit-of-work + pact ontology, §2 coordination log, §3 claims/adjacency,
  §4 identity/attribution, §10 mapping + 80/15/5 read, §11 risks/scale)
- Comms wedge as working loop: `01-analysis/01-research/09-comms-wedge-mapping.md` (§0 exec
  summary, §1.3 learning loop = transaction D, §2 primitives, §3 objective/process/data triple,
  §4 de-risking, §5 80/15/5, §6 honest gaps incl. no cross-org sharing)
- Strategic spine (Phase A): provided inline in the analysis invocation (M1–M4 moat, biggest
  threat, honest cautions, market research 07, Decisions A + B)
