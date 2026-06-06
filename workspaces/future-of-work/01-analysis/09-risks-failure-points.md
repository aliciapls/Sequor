# 09 — Risks & Failure-Points: The Skeptic's Document

> **Purpose.** This is the document that keeps the vision honest. Analyst discipline: failure-point
> analysis, risk assessment, first-principles. Every other document in this analysis argues for the
> platform; this one argues against it, as hard as the evidence allows, so the decisions that survive
> are decisions that earned it.
>
> **Method.** For each risk: a plain-language description (no jargon survives its first appearance
> untranslated, per `.claude/rules/communication.md`), a **likelihood** (Low / Medium / High /
> Near-certain), a **blast radius** (what breaks and how far it spreads if the risk fires), a
> **leading indicator** (the early signal that tells you it is firing _before_ it is too late to
> respond), and a **recommended mitigation** with symmetric pros and cons (per
> `.claude/rules/recommendation-quality.md` MUST-3 — the cons of the recommended path are stated, not
> glossed). Effort is in **autonomous execution cycles/sessions**, never human-days
> (per `.claude/rules/autonomous-execution.md`).
>
> **Grounding.** Cites the research stream directly: `01-research/05-cli-harness-universal-interface.md`
> (§6 risks), `01-research/06-transparency-intervention-versioning.md` (§8 risks),
> `01-research/07-competitive-landscape.md` (§10 threats), `01-research/08-work-disruption-thesis.md`
> (the agent-comms steelman/stress-test), and the strategic spine (Phase A synthesis). Where a claim
> rests on a single source or is genuinely uncertain, it is flagged. Named competitors appear as
> factual landscape grounding only; the platform (Sequor) is never positioned as a derivative of any
> of them (per `.claude/rules/independence.md`).
>
> **Naming.** "The platform" / "Sequor" = the product. "The moat conjunction" = M1+M2+M3+M4 (defined
> in the spine). "Cowork" = Claude Cowork, the closest horizontal competitor (GA April 2026), named
> factually per the competitive research.

---

## 0. Executive summary — the shape of the danger

The platform's strategy is a **bet on a conjunction**: that the combination of versioned-cascade
transparency (M1), execution-time posture governance (M2), multi-human coordination (M3), and
governed cross-org artifact exchange (M4) — none individually unique, all together unoccupied — is
defensible, and that proving the disrupted-work _capability_ first (Decision B) and deferring
go-to-market (the beachhead) is the right sequence.

A conjunction is strong when it holds and catastrophic when one term collapses. The skeptic's job is
to find the terms most likely to collapse. They are, in rank order:

| # | Existential risk | Likelihood | Blast radius | The one-line failure |
| - | ---------------- | ---------- | ------------ | -------------------- |
| **1** | **PMF: the horizontal platform "lands nowhere"** | **High** | Total — no revenue, no reference customer, capability proven but unsold | Capability-first becomes capability-only; >40% agentic-project cancellation rate (Gartner, per research 07 §1) catches a product with no beachhead to anchor it |
| **2** | **M1 (versioned cascade) is too hard to ship for non-coders** | **High** | The strongest moat term collapses; product degrades to "Cowork with audit logs" | Non-deterministic LLM steps + unsolved non-coder versioning UX = the moat that was supposed to be the lead USP never reaches a usable state |
| **3** | **The agent-comms hypothesis (brief 3d) is wrong or culturally rejected** | **Medium-High** | M3 loses its rationale; team-oriented positioning collapses to single-player | Builds team-comms disruption on an unproven, contrarian premise; users reject the loss of human judgment/ambiguity/accountability |
| **4** | **Trust/security: the centered agent concentrates blast radius** | **Medium** (any single incident) / **Near-certain** (some incident over time) | One incident on one tenant becomes a category-defining headline; enterprise sales freeze | One agent touching ERP+CRM+bank, prompt-injected via an untrusted cross-org artifact, does something irreversible at L5 — and the liability question has no clean answer |
| **5** | **Competitive window closes: a hyperscaler ships M1/M3** | **Medium** | The conjunction stops being unoccupied; the moat evaporates before it is built | Cowork (or a suite vendor) productizes versioned cascade or multi-human coordination before the platform reaches GA |

The remaining risks (execution depth, adoption/change-management, dependency on harnesses you don't
control) are serious but **bounded** — they degrade outcomes rather than ending the company. They are
covered in full below and folded into the ranked sequence in §10.

**The single most important framing:** Decision B (capability-first, GTM deferred) is **both a
mitigation and a risk**, and the document treats it as both. It mitigates risk 5 (you build the
hard moat before competitors notice) and risk 2 (you prove the hard thing before you sell it). It
_creates_ risk 1 (a horizontal capability with no beachhead is the textbook "lands nowhere" failure).
The two pull against each other, and the resolution (§1) is the most consequential recommendation in
this document.

---

## 1. PRODUCT-MARKET-FIT risk — "the everything platform lands nowhere"

### 1.1 Description (plain language)

A **horizontal platform** is one built to do many kinds of work for many kinds of users, rather than
one specific job for one specific buyer. The danger, well-documented across software history, is that
a product good at everything is the obvious choice for no one: the finance buyer wants a finance
tool, not a "work platform that can also do finance," and picks the finance tool. The platform wins
the architecture argument and loses every individual purchase.

The market data makes this acute right now. Per `01-research/07-competitive-landscape.md` §1:
**Gartner predicts >40% of agentic-AI projects will be cancelled by end-2027**, and the MIT NANDA
study found **~95% of generative-AI pilots fail to deliver measurable financial impact**, with the
root cause being that "generic tools don't learn from or adapt to workflows." A horizontal platform
is, by construction, the most generic-looking thing on the buyer's desk. It walks into a market that
is actively killing generic agentic projects.

Decision B sharpens the question. By deferring the beachhead — the first specific vertical and buyer
to win — the platform deliberately spends its early cycles proving a capability that names no
customer. The research is explicit that this is a real cost: `08-work-disruption-thesis.md` §5.1
defines the capability as "deliberately beachhead-free," and §5.4 names the per-vertical connector
economics as "where the beachhead decision (deferred) will eventually bite."

### 1.2 Is deferring GTM a mitigation or a risk?

**Both, and the resolution is not "pick one."** Deferring GTM is a mitigation against building the
wrong thing fast (you don't pour cycles into a finance vertical before you know the horizontal
capability even works) and against tipping off competitors (risk 5). It is a risk because a
capability with no buyer is unfalsifiable as a _business_ — you can prove it _runs_ (the §5.2
acceptance test in the disruption thesis) without proving anyone will _pay_, and "it runs" is exactly
what the 40%-cancelled projects also achieved before they were cancelled.

The honest distinction the spine already draws is the resolution: prove the **capability** first
(technically), but do not confuse "capability proven" with "product-market fit found." They are
different gates. Capability-first defers the _beachhead build_, not the _beachhead hypothesis_.

### 1.3 Likelihood, blast radius, leading indicator

- **Likelihood: High.** The base rate is against horizontal platforms; the market is actively
  cancelling generic agentic projects; and Decision B structurally postpones the buyer conversation.
- **Blast radius: Total.** This is the failure that ends the company quietly: the capability demo
  works, the engineering is admired, and no one writes a cheque. There is no partial version of this
  — you either have a buyer who renews or you don't.
- **Leading indicator:** the **capability proof completes and the immediate next question is "now
  which vertical?" with no evidence-backed answer.** If the §5.2 acceptance test passes and the team
  cannot point to a specific design-partner who watched it and said "I would pay for that against
  _this_ workflow," the risk is firing. A second indicator: every customer conversation requires the
  buyer to imagine their own use-case rather than recognize it — that is the "generic tool" tell from
  the MIT NANDA finding.

### 1.4 Recommended mitigation

**Recommendation: run capability-first and beachhead-discovery in parallel, not in sequence — pick
ONE concrete "lighthouse" workflow to prove the capability _against_, chosen for evidence value, not
revenue commitment.**

Concretely: keep the architecture horizontal (Decision B holds), but the §5.2 acceptance test
(`08-work-disruption-thesis.md`) MUST be run against a _named, real, painful_ cross-system workflow
with a _real design partner watching_ — not a synthetic demo. The Sequor comms wedge (Decision A) is
the natural first lighthouse because it already ships and already proves four of the six acceptance
properties (`08` §5.3). The lighthouse is not the beachhead commitment; it is the falsifiability
instrument for the business hypothesis, run concurrently with the capability proof.

**Implications:** the team carries one real customer relationship through the capability-proving phase
instead of zero. The capability demo becomes a capability _trial_. The beachhead decision, when it
arrives, is informed by a real buyer's reaction rather than a whiteboard.

**Pros:**
- Converts an unfalsifiable business bet into a falsifiable one at near-zero added cost (the
  lighthouse workflow is also the acceptance-test fixture you needed anyway).
- The Sequor wedge already exists, so the first lighthouse is a sunk asset, not new spend.
- Surfaces the "lands nowhere" signal early — while there is still time to pivot the horizontal
  emphasis — rather than after the capability is "done."

**Cons (real, not glossed):**
- A single lighthouse risks **anchoring** the horizontal product to one vertical's idiosyncrasies —
  the exact re-verticalization trap the spine warns against ("defensible IF the platform stays
  disciplined about not re-verticalizing," research 07 §9a). Discipline is required to treat the
  lighthouse as evidence, not as the product's gravity well.
- Carrying a design-partner relationship costs coordination cycles that a pure capability sprint
  would not, slightly slowing the technical proof.
- If the chosen lighthouse is unrepresentative (comms is "easier" than ERP/CRM — `08` §5.3 flags
  this), a clean lighthouse result can give false confidence about the hard heterogeneous-systems
  case (the genuine net-new risk per `08` Appendix B item 1).

**Alternative considered and rejected:** pure sequential capability-first (prove it fully, _then_ go
find a buyer). Rejected because it maximizes risk 1 — you discover "lands nowhere" at the most
expensive possible moment, after the build, with no design-partner feedback to have redirected it.

---

## 2. EXECUTION risk — M1 versioned cascade, and the no-code "last 20%" death

### 2.1 Description (plain language)

**M1** is the platform's strongest moat and, by the spine's own admission, its highest execution
risk. M1 is the promise that a non-coder can **retrace to any earlier step of a piece of work,
change something there, and have everything downstream automatically re-do itself — while the old
versions are kept.** Think "undo and redo, but for a whole multi-step job done by agents, and a
non-programmer drives it."

Two things make this genuinely hard, both documented in `06-transparency-intervention-versioning.md`
§8 and the spine:

1. **LLM steps are non-deterministic.** When you re-run a step that calls a language model, you do
   not get the same answer twice. So "re-run from step 4" is semantically slippery: did the user want
   the _recorded_ old answer reused (deterministic, cheap, but maybe stale), or a _fresh_ answer
   (honest to the edit, but the whole downstream may legitimately diverge in ways the user didn't ask
   for)? Research 06 §8 flags this as a genuine open _product_ decision, not just an engineering one:
   "should a retrace re-run the LLM or reuse the recorded one? likely user-selectable per step." A
   feature whose correct behavior is itself undecided is a feature at risk.

2. **Non-coder versioning UX is unsolved.** Programmers have git, and git is famously hard even for
   programmers. Asking a non-coder to reason about branches, forks, and "which version of the output
   am I looking at" is asking them to do the thing that defeats most _engineers_. Research 06 §2.2
   proposes git-like branching over the provenance graph as the technical model — which is exactly
   the cognitive surface that has no non-coder precedent.

This collides directly with the **no-code "last 20%" failure** (research 07 §6): the industry
consensus is that no-code tools "get you ~40% of the way; the remaining 60% — integrations,
compliance, edge cases, production hardening — requires engineering," and that the depth (conditional
logic, error handling, branching) is exactly where visual builders break. M1 _is_ depth. If depth
without code is where no-code historically dies, M1 is the platform planting its flag on the hill
where competitors are buried.

### 2.2 Why the spine's escape hatch is plausible but unproven

The spine's answer (research 07 §6, §9d) is structurally sound: don't make the non-coder _author_ the
depth (the visual-builder trap); let the **LLM be the depth engine** and make the depth **legible**
through M1's transparency, so the human _supervises_ depth rather than _building_ it. This is a real
distinction and it is the platform's actual edge. But it is a bet, not a result: "differentiable but
the riskiest claim — must be proven, not asserted; pair tightly with (b)" (research 07 §9d). The
legibility claim — that transparency makes agent-generated depth comprehensible to a non-coder — is
itself unvalidated. Transparency can equally produce _overwhelming_ legibility: a 40-step traced DAG
is transparent and also incomprehensible to a non-coder.

### 2.3 Likelihood, blast radius, leading indicator

- **Likelihood: High** that the _full_ M1 vision (arbitrary retrace + cascade + non-coder branching)
  is not shippable in usable form in the first build horizon. **Medium** that a _reduced_ M1
  (linear retrace, reuse-recorded-output default, no user-facing branching) ships and is enough.
- **Blast radius: the lead USP.** If M1 collapses to "audit log + manual re-run," the platform's
  headline differentiator becomes a feature Cowork can match, and the moat conjunction loses its
  strongest term. The product does not die, but it loses its reason to be chosen over the horizontal
  incumbent.
- **Leading indicator:** **the cascade cost-preview is the canary.** Research 06 §8 flags "cascade
  cost explosion" — a change near the root of a wide work-graph legitimately invalidates everything
  downstream. If early prototypes cannot show a non-coder a comprehensible "this change will re-run N
  steps and cost roughly $X" preview _before_ committing, the non-coder will not trust the feature,
  and the legibility bet has failed. A second indicator: usability tests where non-coders cannot
  answer "which version of this output is the current one?" within seconds.

### 2.4 Recommended mitigation

**Recommendation: ship M1 in a deliberately reduced first form — linear retrace with
reuse-recorded-output as the default, an explicit per-step "regenerate" opt-in, and NO user-facing
branching in v1 — and treat the cascade cost-preview as a hard acceptance gate, not a nice-to-have.**

This sequences the moat by tractability. The reactive-cascade engine (research 06 §7) has a live
feedback loop (each cascade is testable against a fixture work-graph), so per
`.claude/rules/autonomous-execution.md` it can run at higher per-session budget — but the
_non-coder-facing_ surface should expose the minimum that is comprehensible, and grow only as
usability evidence justifies. Estimated ~4–6 autonomous cycles for end-to-end retrace over the
comms-wedge graph (research 06 §7), with branching explicitly deferred.

**Implications:** v1 proves "retrace + cascade + versioning" on a narrow, linear work-graph (the
comms wedge's 4-step graph: Message → Classification → Retrieval → Response, per research 06 §6.2),
where a non-coder _can_ hold the whole picture. Branching and wide-graph retrace are earned later,
gated on usability evidence.

**Pros:**
- De-risks the hardest moat term by shipping its tractable core first and proving legibility on a
  graph small enough that legibility is achievable.
- The reduced form still beats the field — no competitor productizes _any_ non-coder versioned
  cascade (research 07 §9b), so even linear-retrace is differentiated.
- Cost-preview-as-gate forces the legibility question to be answered with evidence early, not
  discovered late.

**Cons (real, not glossed):**
- A reduced M1 is **less differentiated** than the full vision. Marketing the moat on its strongest
  claim while shipping its weakest form risks an expectation gap that itself erodes trust — the
  recommendation must be paired with honest messaging about what v1 does and does not do.
- Deferring branching means the "explore an alternative timeline without destroying the original"
  use-case (research 06 §2.2) — genuinely valuable for analytical work — is absent at launch, and a
  competitor could claim that ground.
- "Reuse recorded output by default" is the safe choice but can silently present stale results as
  current if the versioning UX is not crystal-clear — the very legibility risk this whole section is
  about, reappearing inside the mitigation.

**Alternative considered and rejected:** build full M1 (arbitrary retrace + branching) before any
launch. Rejected because it maximizes the chance of the "last 20%" death — pouring cycles into the
hardest non-coder UX surface in the product before validating that non-coders can use even the
simple version.

---

## 3. The UNPROVEN agent-comms hypothesis (brief §3d)

### 3.1 Description (plain language)

Brief §3d makes the platform's most contrarian claim: that **communication between agents is more
complete, efficient, and less error-prone than communication between humans**, because agents carry
full context and durable memory while humans send lossy sentences and rely on fallible recall. This
claim is the justification for extending the platform from individual work into **team** work — it
is why M3 (multi-human + multi-agent shared substrate) is in scope at all.

Research 08 (Part 4) does the honest work of both steelmanning and stress-testing it. The steelman is
strong _for one specific layer_ of communication: **handoffs and coordination** — "pull the Q3
numbers" carries a sentence across the wire while the executable context stays in the sender's head.
Agent-mediated handoff transfers the whole record, not a lossy summary (research 08 §4.1). For that
layer, the claim is internally consistent with the entire disruption thesis: if integration loss is
the disease, communication loss is the same disease, and the same cure applies.

But research 08 §4.2 names four ways the claim is **dangerous or false** when over-extended:

1. **Loss of human judgment.** CARE's Mirror Thesis says what remains valuable when AI does the
   measurable work is the human's non-measurable contribution — judgment, relationships, wisdom — and
   communication is the richest carrier of exactly those. The "inefficient" hallway conversation is
   often where relationship capital and tacit context are actually built. Optimizing the channel for
   information density can strip out the bandwidth that carried the judgment.
2. **Accountability cannot be delegated to the channel.** If agent↔agent comms become primary,
   accountability risks migrating from "a named person decided and is answerable" to "the agents
   worked it out" — the precise governance failure CARE was built to prevent.
3. **The value of ambiguity.** Human communication's incompleteness is sometimes a feature:
   ambiguity preserves optionality, enables negotiation and face-saving, and lets parties defer
   commitment. "Let's see how Q3 goes" is _deliberately_ unspecified. Forcing it into a complete,
   recorded objective can force premature commitment, destroy political flexibility, and create a
   discoverable record where deniability was the point — a real legal-discovery and privacy hazard.
4. **Misconstrual moves, it does not vanish.** Agent channels carry more context but introduce a new
   failure: the agent misreads the human's intent at the human↔agent boundary, then propagates that
   misreading with high-fidelity confidence across the network — a _confident, fast, well-recorded_
   error. Human telephone-game loses information; agent telephone-game can _amplify a wrong premise_.

### 3.2 What if the hypothesis is simply wrong, or culturally rejected?

The defensible position (research 08 §4.3) is that the hypothesis is true for the executable,
coordination-bearing layer and false (even harmful) for the relational, judgment-bearing, and
deliberately-ambiguous layers. If that nuance is _right_, M3 still has a foundation — but a narrower
one than the brief's verbatim claim. If the nuance is _wrong_ — if it turns out that even
coordination handoffs lose something essential when mediated, or that users simply refuse to let
agents talk to each other about their work — then M3 loses its rationale and the team-oriented
positioning collapses to single-player.

Cultural rejection is a distinct and underrated failure mode. Even if the hypothesis is _technically_
true, knowledge workers may reject agent-mediated team comms on grounds that have nothing to do with
efficiency: a felt loss of agency, discomfort with a permanent record of every handoff, resistance to
a manager's coordination being automated, or simple distrust. The platform can be _right_ and still
_rejected_.

### 3.3 Likelihood, blast radius, leading indicator

- **Likelihood: Medium-High** that the verbatim brief §3d claim ("agent comms beat human comms") is
  over-broad; **Medium** that even the narrowed coordination-layer claim meets cultural resistance.
- **Blast radius: M3's rationale.** The multi-human coordination substrate is real DNA (research 07
  §9c: signed coordination log, claims/leases, distinct-person gates) and differentiates on the human
  side where A2A commoditizes the agent side. But if the comms hypothesis is rejected, M3 is a
  beautifully-built answer to a question users didn't ask. The substrate survives as
  coordination plumbing; the _team-comms-disruption_ story does not.
- **Leading indicator:** in lighthouse usage, **do users route their actual handoffs through the
  agent channel, or do they keep using email/chat and treat the agent as a side-tool?** If the agent
  substrate is bypassed for real coordination, the hypothesis is failing in practice regardless of
  what benchmarks say. A second indicator: users asking for an "informal / off-the-record" mode —
  which signals the ambiguity-preservation need (§3.1 point 3) is real and currently unmet.

### 3.4 Recommended mitigation

**Recommendation: treat brief §3d as a research BET to validate cheaply, NOT a settled USP — and
build M3 to the narrowed §4.3 position (disrupt the handoff, not the relationship) with
ambiguity-preservation as a first-class, shipped feature from day one.**

The cheap validation: the lighthouse workflow (§1.4) already exercises a handoff (the Sequor wedge's
HITL escalation is a human↔agent handoff under a confidence gate). Instrument it. Measure whether
agent-mediated handoffs reduce the round-trips, the "I thought you were doing that" failures, and the
re-keying — the steelman's specific claims (research 08 §4.1). This costs near-zero incremental build:
the data falls out of the audit trail the platform records anyway.

**Implications:** M3 ships with an explicit "informal / not-an-objective" mode that is _not_
auto-structured, auto-recorded-as-decision, or auto-acted-upon (research 08 §4.3, commitment 3), and
every consequential decision keeps a _named human_ on it via the existing posture-gated HELD path
(research 08 §4.3, commitment 2). The team-comms story is marketed only as far as the evidence
reaches — handoffs and coordination — never as "agents communicate better than you do."

**Pros:**
- Converts the riskiest claim in the brief from a marketing liability into an instrumented experiment
  at the cost of one dashboard.
- The narrowed position is _more_ defensible, not less — it aligns with the CARE principles the whole
  ecosystem rests on, so the platform is not arguing against its own governance philosophy.
- Ambiguity-preservation-as-feature pre-empts the legal-discovery/privacy hazard and the cultural-
  rejection failure mode simultaneously.

**Cons (real, not glossed):**
- The narrowed claim is **less exciting** than the brief's bold version. A bet pitched as "we make
  handoffs lossless" is a smaller story than "we replace human-to-human inefficiency," and may
  under-sell the team-oriented vision to investors who liked the bold version.
- Building the "informal mode" adds surface area (a second comms path that is deliberately
  ungoverned) that complicates the otherwise-clean "everything is traced" story — and an ungoverned
  path is a place risk-4 (security) can hide.
- Instrumenting handoff-quality is only as good as the lighthouse's representativeness; comms handoffs
  may not generalize to ERP/CRM-class coordination, so a positive signal could be a false positive
  for the harder case.

**Alternative considered and rejected:** ship M3 on the verbatim §3d claim and let the market decide.
Rejected because it builds the team-comms product on a premise the platform's own governance
philosophy (CARE Mirror Thesis, Dual Plane) partly contradicts — an internal inconsistency a sharp
buyer will find.

---

## 4. TRUST / SECURITY — the centered agent concentrates blast radius

This is the largest cluster of risk and the one most likely to produce a _category-defining_
incident. Research 08 §3.5 names the root cause in one line: "A centered agent is a centered point of
failure and a centered point of authority. Putting the agent in the middle concentrates both
capability and risk." The whole inversion thesis — agent as integration layer — is also the whole
security problem: the thing that makes the platform valuable (one agent touching everything) is the
thing that makes a breach catastrophic.

Five distinct sub-risks, each treated below.

### 4.1 Untrusted cross-org publishers (the genuinely-new trust model)

**Description.** M4 — governed cross-org artifact exchange — is the network-effects engine and
carries a genuinely-new problem (per the spine): the **untrusted-publisher trust model**. When
organization A publishes a process artifact (a skill, rule, command — the encoded know-how of how to
do some work) and organization B consumes it, B is running A's instructions inside B's agent, against
B's connected systems. A malicious or careless publisher can ship an artifact that does the wrong
thing — exfiltrate data, skip a compliance step, take an action B never intended — and B's agent
executes it with B's authority.

This is not the marketplace problem (which is "is this artifact good quality"); it is the supply-chain
problem (which is "can this artifact be trusted to run against my systems"). Research 07 §9e is
explicit that the moat is "the trust/provenance layer, not the marketplace itself," and that "the
genuinely-new part is the untrusted-publisher trust model." There is no productized precedent — the
8+ skill/MCP marketplaces (research 07 §9e) are "publish/consume directories" that lack exactly this.

- **Likelihood: Medium**, rising as the artifact network grows (the risk scales with adoption — the
  more valuable M4 becomes, the more attractive a target).
- **Blast radius: cross-tenant, cross-org.** A single poisoned popular artifact runs in every
  consuming org's agent against every consuming org's systems. This is the supply-chain attack shape
  (the npm/PyPI-poisoning pattern) applied to executable enterprise work.
- **Leading indicator:** the first artifact that requests broader tool/clearance scope than its
  stated purpose justifies. If intake review cannot _mechanically_ detect "this 'format a report'
  skill also wants write access to the payments system," the model is unenforced.

**Recommended mitigation: ship M4 with capability-scoped artifacts and a default-deny intake fence —
a consumed artifact runs only against the tool scopes it declared and the consumer pre-approved, and
the platform's existing disclosure-scrub + Gate-1/Gate-2 distribution discipline
(`.claude/rules/artifact-flow.md`) is the enforcement spine, not a new invention.**

The DNA exists: loom's intake disclosure-scrub (`artifact-flow.md` § Intake Disclosure Scrub) and the
Gate-1 human-classify step are precisely a supply-chain intake fence, currently used for COC
artifacts. Re-target it: every cross-org artifact declares its required tool/clearance envelope; the
consumer's posture (M2) gates whether that envelope is auto-granted (L5) or human-approved (L4/L3);
an artifact cannot escalate beyond its declared envelope at runtime.

- **Pros:** reuses shipped governance DNA rather than inventing; the capability-scope declaration is
  also the thing that makes artifacts _comprehensible_ to a non-coder buyer ("this skill needs access
  to X and Y"); default-deny is the correct posture for executable supply-chain content.
- **Cons:** default-deny + per-envelope approval adds friction to the consume path, which directly
  taxes the network-effects engine M4 depends on — every approval gate is a place adoption leaks; and
  capability-scoping is only as good as the granularity of the tool/clearance model, which for
  heterogeneous enterprise systems (ERP, CRM) may be coarse, leaving large-grained "access the ERP"
  envelopes that are technically scoped but practically broad.
- **Rejected alternative:** trust-by-reputation (let popular artifacts run with fewer gates).
  Rejected because reputation is gameable and the first high-reputation poisoned artifact is the
  category-defining incident.

### 4.2 Prompt injection across connected enterprise systems

**Description.** Prompt injection is when an attacker hides instructions inside data the agent reads —
a malicious email, a poisoned CRM note, a crafted document — and the agent, unable to reliably
distinguish "data to process" from "instructions to follow," obeys them. In a single-app chatbot this
is bounded. In an agent that is the integration layer across ERP + CRM + email + bank, an injection
in _any_ connected system can drive actions in _every_ connected system. The attack surface is the
union of all connected data sources; the action surface is the union of all connected tools.

This is made worse by the platform's own keystone design rule. The spine and research 05 §5.2 make
"tools are dumb data endpoints; the LLM does all reasoning" a core conviction — correctly, because it
is what makes the work _transparent_ (all reasoning is in the logged LLM I/O). But the same rule means
**there is no deterministic business-logic layer between the injected instruction and the action** —
the LLM is the only thing deciding, and the LLM is the thing being injected. Transparency and
injection-vulnerability are two faces of the same design choice.

- **Likelihood: Near-certain that injection attempts occur; Medium that one succeeds destructively**
  before defenses mature. Prompt injection is an unsolved problem industry-wide, not a platform-
  specific gap.
- **Blast radius: the full connected-system union.** An injection that reaches an L5-autonomous agent
  with write access to a system of record can cause irreversible action (a payment, a deletion, a
  sent communication) before any human sees it.
- **Leading indicator:** the first red-team exercise that gets the agent to take an out-of-policy
  action via data-borne instruction. If the platform's own red-teaming (per
  `.claude/rules/zero-tolerance.md` and the `/redteam` discipline) cannot _yet_ produce this, it is
  because it has not tried hard enough, not because the risk is absent.

**Recommended mitigation: make the posture/envelope layer (M2) the structural containment — write
actions to systems of record require an explicitly higher posture or a human gate by default, so an
injected instruction cannot reach an irreversible action at L5 without the human having pre-authorized
exactly that class of action in advance.**

The five-dimensional constraint envelope (research 08 §3.4:
`{financial, operational, temporal, data_access, communication}`) is richer than tool-level
allow/deny and is the right granularity: an injection might get the agent to _want_ to send a payment,
but the financial dimension of the envelope caps what can execute without a HELD gate
(research 06 §4.2). The defense is not "prevent injection" (unsolvable) but "bound what a successful
injection can do" (tractable, and the platform's existing DNA).

- **Pros:** containment is achievable where prevention is not; reuses the shipped PACT HELD-gate and
  EATP envelope; aligns the security model with the transparency model (every gated action is also a
  traced decision).
- **Cons:** aggressive gating of write actions directly undercuts the L5-autonomous value
  proposition — "the agent does your work end-to-end" is weakened by "except every consequential
  write needs approval," which is the HITL-bottleneck failure mode research 07 §7 explicitly names
  ("naive HITL creates bottlenecks — every action queued for approval"); calibrating which actions
  need gates is an ongoing, never-finished tuning problem, and every mis-calibration is either a
  security hole (gated too little) or a UX death (gated too much).
- **Rejected alternative:** rely on input sanitization / injection detection as the primary defense.
  Rejected because injection detection is an arms race the defender loses; containment via the
  envelope is the durable layer.

### 4.3 The agent-as-integration-layer concentrating blast radius (one agent, ERP+CRM+bank)

**Description.** This is the structural core of the security cluster, stated plainly: the single most
valuable thing the platform does — put one agent in the middle touching all systems — is the single
most dangerous thing it does. A compromised, injected, or simply mistaken agent with simultaneous
access to the ERP, the CRM, and the bank has a blast radius no single-app tool can have. Research 08
§3.5 names this as the honest seam in the inversion: "concentrates both capability and risk."

- **Likelihood: High that the concentration exists by design; the question is whether a triggering
  event (4.1, 4.2, or a model error) reaches it.**
- **Blast radius: maximal by construction.** This is the amplifier on every other security risk.
- **Leading indicator:** the breadth of the _default_ connected-tool set per objective. If an agent
  running a "quarterly report" objective is connected to the bank's _write_ API when the objective
  only needs the ledger's _read_ API, the blast radius is over-provisioned and the indicator is
  flashing.

**Recommended mitigation: least-privilege per objective — the agent for a given objective is granted
the minimum tool/clearance envelope that objective requires, not the union of everything the org has
connected, with the envelope derived from the objective and the process artifacts in scope.**

The envelope is _per-AgenticRequest_ already in the data model (research 06 §1.1:
`AgenticRequest.envelope_id`). The mitigation is to make the default _narrow_ and earned, not broad
and assumed: a report objective gets read-ledger + write-document, never write-bank, unless the
process artifact for that objective explicitly declares and the human explicitly grants the wider
scope.

- **Pros:** directly bounds the blast radius that amplifies 4.1 and 4.2; per-objective scoping is
  already modeled (envelope_id), so this is configuration discipline, not new architecture; narrow
  envelopes are also more legible (the human sees exactly what this run can touch).
- **Cons:** per-objective envelope derivation is hard to automate well — too narrow and the agent
  hits a wall mid-objective and has to escalate (friction, the HITL-bottleneck again); too broad and
  the mitigation is theater; and the derivation logic itself, if it lives in tools, violates the
  "tools are dumb" rule (research 05 §6.2 names this exact tension: "governance-at-connector
  enforcement that doesn't become decision-logic-in-tools").
- **Rejected alternative:** broad standing connections with audit-after-the-fact. Rejected because
  audit catches the irreversible action after it is irreversible.

### 4.4 Tenant isolation

**Description.** In a multi-tenant platform (many customer organizations on shared infrastructure),
tenant isolation is the guarantee that organization A can never see or affect organization B's data.
A cross-tenant leak — A's data surfacing in B's results — is the incident that ends enterprise trust
permanently. The platform compounds the normal multi-tenant risk with two specifics: the provenance
ledger (M1) creates a _shared content-addressed namespace_ (research 06 §7.1 flags "a shared
content-address namespace across tenants is a cross-tenant leak"), and the cross-org artifact exchange
(M4) is, by design, a channel _across_ org boundaries — the one place isolation is intentionally
crossed, which makes it the place isolation is most likely to be crossed wrongly.

- **Likelihood: Low per-incident with disciplined engineering, but the consequence asymmetry makes
  even Low unacceptable; the M1 content-address namespace is a specific, named, easy-to-get-wrong
  vector.**
- **Blast radius: permanent enterprise-trust loss** + regulatory exposure. One cross-tenant leak is a
  headline.
- **Leading indicator:** any cache key, content-hash, or ledger query that does not carry a tenant
  dimension. The ecosystem already has a mechanical audit for exactly this
  (`.claude/rules/tenant-isolation.md` audit protocol: grep for cache-key construction without
  tenant_id). If that audit is not run on the provenance ledger, the indicator is unmonitored.

**Recommended mitigation: every content-hash, cache key, ledger query, and artifact-scope check
carries an enforced tenant dimension, with multi-tenant strict mode (missing tenant_id raises a typed
error, never silently defaults), reusing the shipped tenant-isolation discipline as a hard gate on the
M1 ledger and the M4 exchange.**

This is the most directly reusable mitigation in this document — `.claude/rules/tenant-isolation.md`
is a complete, mechanically-audited contract. Research 06 §7.1 already lists tenant isolation as a
hard invariant for the cascade engine. The mitigation is to enforce it _on the new surfaces_ (the
content-addressed ledger, the cross-org channel), not to invent it.

- **Pros:** reuses a complete, audited discipline; strict-mode-fail-loud converts a silent leak into
  a loud error at write time (per `tenant-isolation.md` Rule 2); the audit is mechanical and can run
  in CI.
- **Cons:** the M4 cross-org channel _intentionally_ crosses tenant boundaries, so "every query
  carries tenant_id" is necessary but insufficient there — M4 needs an additional explicit
  cross-tenant-grant model that tenant-isolation.md does not cover, which is net-new design; and
  content-addressing's main benefit (deduping identical bytes across versions, research 06 §8) is in
  tension with strict per-tenant namespacing (you cannot dedupe across tenants without crossing the
  boundary), forcing a per-tenant content-address space that loses some storage efficiency.
- **Rejected alternative:** shared content-address namespace with access-control on read. Rejected
  because access-control-on-read is exactly the layer that fails open under a bug; namespace
  separation fails closed.

### 4.5 The "agent did something wrong autonomously at L5" liability question

**Description.** When a human approves an action (L3/L4), accountability is clear: the human decided.
When the agent acts autonomously (L5) and does something wrong — sends the wrong payment, deletes the
wrong record, emails the wrong customer — _who is accountable?_ The user who chose L5 in advance? The
organization that deployed the platform? The platform vendor? The publisher of the artifact that drove
the behavior (4.1)? This is not primarily a technical question; it is a legal and trust question that
the technical design can _inform_ but not _answer_.

Research 08 §4.3 commitment 2 and §3.4 give the design's partial answer: a human is named on every
consequential decision, and L5 is recorded as having run "under an explicitly chosen autonomous
posture that a named human chose in advance." The posture-at-time is recorded per step (research 06
§7.1). So the platform can always answer "who chose L5 for this class of action, and when" — which is
the _accountability anchor_. But "who chose the posture" is not the same as "who is liable for the
outcome," and the gap between them is where the lawsuits live.

- **Likelihood: Near-certain that the question is asked (by every enterprise legal team in
  procurement); Medium that an actual incident forces a real answer.**
- **Blast radius: the enterprise sales motion itself.** Enterprise legal review can block adoption on
  this question alone, before any incident. It is a _sales_ blocker as much as an incident risk.
- **Leading indicator:** the question appears in the first enterprise security/legal questionnaire and
  the platform has no crisp, documented answer. If the answer is improvised per-deal, the indicator is
  red.

**Recommended mitigation: make the posture choice an explicit, recorded, attributable
pre-authorization with a clear accountability anchor — "named human X authorized autonomous action of
class Y within envelope Z at time T" — and pair it with conservative L5 defaults (L5 is opt-in
per-action-class, never the global default) so the human's pre-authorization is always specific enough
to anchor accountability.**

The technical substrate exists (posture-at-time recording, the five-dimensional envelope, the signed
decision records). The mitigation is to make the _accountability anchor_ a first-class, contractually-
referenceable artifact: every L5 action traces to a specific, narrow, human-made, time-stamped
pre-authorization, not a blanket "trust the agent" toggle.

- **Pros:** gives enterprise legal a crisp answer ("your named user pre-authorized exactly this class
  of action within exactly this envelope"); conservative L5 defaults reduce the incident rate; the
  anchor is reusable as the audit artifact for compliance (EU AI Act Article 14 human-oversight,
  enforceable Aug 2026 per research 07 §7).
- **Cons:** conservative L5 defaults and per-action-class authorization push the product back toward
  supervised operation, undercutting the "fully autonomous" value proposition — the same L5-vs-HITL
  tension as 4.2/4.3; and a crisp accountability anchor that says "the customer's user authorized it"
  may be _legally_ clean but _commercially_ toxic if customers read it as "the vendor disclaims all
  responsibility," which can itself block deals.
- **Rejected alternative:** vendor-assumes-liability for autonomous actions. Rejected as commercially
  unviable for an early platform — but flagged because at scale, _some_ vendor liability stance may be
  required to close large deals, and that is a business decision outside this analysis's scope (open
  question, §11).

---

## 5. COMPETITIVE risk — convergence, the window, and the hyperscaler

### 5.1 Description (plain language)

The closest competitor, Cowork (Claude Cowork, GA April 2026), embodies the platform's _surface_
thesis — "re-interface the agent harness for all knowledge work, for non-coders" — and ships
fast: research 07 §10 records "12 features in ~12 weeks; Computer Use; enterprise SCIM/groups." The
spine's central competitive discipline follows directly: the platform **MUST NOT compete on "agent
finishes a deliverable in one interface"** — Cowork already does that and iterates every ~2 weeks. The
platform competes only on the substrate Cowork has not productized: M1 (versioned cascade), M2
(pre-set posture gates), M3 (multi-human coordination), M4 (governed cross-org artifacts).

The competitive risk has three faces:

1. **Surface convergence.** Cowork keeps adding surface features. Each one narrows the visible gap
   between "Cowork plus some governance" and the platform, even if the substrate differs.
2. **The window.** The moat conjunction is unoccupied _now_. The platform is racing to build it
   before the gap is noticed. Decision B (capability-first, GTM deferred) widens this window
   deliberately — building the hard substrate quietly while competitors ship surface.
3. **The hyperscaler ships M1 or M3 first.** The mechanisms underlying M1 (durable execution /
   time-travel / checkpoint replay — research 07 §2, LangGraph 1.2) and M3 (A2A multi-agent
   coordination) already exist as developer primitives. A well-resourced incumbent could productize
   the non-coder form of either before the platform reaches GA. This is the existential version of the
   competitive risk: not "they match the surface" but "they take the moat term."

### 5.2 Likelihood, blast radius, leading indicator

- **Likelihood: Medium** that a hyperscaler ships a productized M1 (versioned cascade for non-coders)
  in the platform's build horizon — the _mechanism_ is OSS-proven but the _non-coder product_ is
  genuinely hard (it is risk 2, for the platform _and_ for them); **Medium-High** that surface
  convergence continues regardless.
- **Blast radius: the conjunction's uniqueness.** If a competitor takes M1, the platform's strongest
  moat term is no longer unoccupied and the lead USP must shift to M2/M3/M4. If a competitor takes
  M3, the team story weakens. The conjunction is robust to losing _one_ term (three remain); it is not
  robust to losing M1, the lead.
- **Leading indicator:** any competitor shipping _any_ non-coder-facing "retrace a step and re-run
  downstream" feature, or any non-coder "multiple people on one shared agentic workspace" feature.
  Monitor competitor release notes for these two specific capabilities — they are the canaries for the
  two moat terms most at risk. The durable-execution / time-travel developer primitives moving "up"
  toward a non-coder surface (research 07 §2 calls this "the gap to productize, not invent") is the
  early signal that the window is closing.

### 5.3 Recommended mitigation

**Recommendation: race on the conjunction, not on any single term — build M2 (governance) first
because it is the most defensible and most-shipped DNA, while M1 (the contested term) builds in
parallel — so that even if a competitor takes M1, the platform still owns a unique M2+M3+M4 combination
no suite vendor and no horizontal harness can match.**

The competitive logic: M1 is the highest-value, highest-risk, most-contested term. M2 (execution-time
posture governance) is the platform's home-field advantage (research 07 §7: "the platform's home-field
advantage," file-verified DNA across PACT/EATP/loom/aegis) and is the _hardest for a horizontal
harness to retrofit_ because it must be _native to the execution substrate_, not bolted on
(research 05 §7.2). Leading with M2 means the platform's defensibility does not rest entirely on
winning the M1 race. Suite vendors cannot be agnostic (research 07 §3: "vertical by construction");
horizontal harnesses have not productized native governance (research 07 §3, Cowork gaps). The
agnosticism + native-governance combination is the part of the conjunction least exposed to the
competitive race.

**Implications:** the build sequence is governance-and-agnosticism-led (M2 + the MCP/A2A foundation),
with M1 in parallel as the differentiator-when-it-lands and M3/M4 as the network/team layers. If the
M1 race is lost, the platform's positioning shifts from "transparent versioned work" to "the agnostic,
natively-governed work platform" — still unoccupied.

**Pros:**
- Hedges the single most contested term: the platform survives losing the M1 race.
- Leads with the most-shipped DNA (M2), so the first defensible thing is also the cheapest to build.
- Native governance + agnosticism is structurally hard for _both_ competitor classes (suite vendors
  can't be agnostic; harnesses haven't gone native on governance), so it is the most durable ground.

**Cons (real, not glossed):**
- Leading with M2 means the platform's _first_ public story is "governance," and the governance
  category (TRiSM) is filling with funded observability vendors (research 07 §10 point 6) — the
  platform risks reading as "yet another governance tool" unless the execution-time-native distinction
  is made legible to buyers, which is itself hard.
- De-emphasizing M1 in the early sequence cedes the _narrative_ high ground (versioned cascade is the
  most exciting story) to whoever ships it first, even if the platform's version is better — first-
  mover owns the category name.
- Racing on a conjunction means no single term gets the full force of the build, so _every_ term
  ships a bit later than a focused single-term sprint would deliver it — a real cost if the window is
  shorter than estimated.

**Rejected alternative:** all-in on M1 as the lead, race to ship it first. Rejected because it stakes
the entire competitive position on winning a race for the hardest-to-build term against better-
resourced competitors — if the platform loses that race, it has nothing else far enough along to fall
back on.

---

## 6. ADOPTION / CHANGE-MANAGEMENT risk

### 6.1 Enterprises distrust autonomous agents touching systems of record

**Description.** Even when the platform is technically sound, the buyer is a human (or a committee)
who must approve letting an autonomous agent write to the ERP, the CRM, the bank — the systems of
record that the business _is_. Distrust of autonomous action on systems of record is rational, deep,
and slow to overcome. It is reinforced by the market reality (research 07 §1: >40% of agentic projects
cancelled, ~95% of pilots failing) — every buyer has heard the horror stories. This is not a security
risk (covered in §4); it is a _trust-adoption_ risk: the agent could be perfectly safe and still not
be _trusted enough to be allowed to act_.

- **Likelihood: High.** This is the default state of every enterprise buyer in 2026.
- **Blast radius: adoption velocity.** It does not kill the product; it slows every deal and pushes
  every customer toward the most-supervised (least-autonomous) postures, which undercuts the value
  proposition that justified the purchase. A platform used only at L3 (step-by-step approval) is a
  very expensive way to do what a macro could do.
- **Leading indicator:** customers deploy and then never raise the posture above L3/L4. If, six
  months in, no customer trusts any objective to L5, the autonomy value is unrealized and renewal is
  at risk.

**Recommended mitigation: make the platform's transparency and posture model the _trust-building
instrument_ — let customers start fully supervised (L3), watch the traced execution prove itself, and
earn their way to higher autonomy per-objective-class on evidence, with the posture upgrade always
human-gated and instantly reversible (the EATP "upgrades earned, downgrades instant" model,
research 06 §4.3).**

This turns the platform's own moat (M1 transparency + M2 posture) into the change-management tool: the
buyer does not have to trust the agent on day one; they trust the _trace_, and grant autonomy as the
trace accumulates evidence. This is the EATP posture philosophy (research 06 §4.3) applied as a sales
and adoption strategy, not just a security control.

- **Pros:** aligns the adoption path with the product's actual strengths (transparency, graduated
  posture); the conservative default (L3) is also the safest default (§4); "earn autonomy on
  evidence" is a story enterprise buyers find credible because it matches how they trust human
  employees.
- **Cons:** a product that defaults to fully-supervised and grows autonomy slowly takes _longer_ to
  demonstrate ROI, lengthening the sales cycle and delaying the "wow" that drives expansion; and if
  the trace itself is not legible (risk 2), "watch it prove itself" fails because the customer cannot
  read the proof — this mitigation depends on M1's legibility working, coupling it to risk 2.
- **Rejected alternative:** lead with autonomous demos to show the wow. Rejected because it front-
  loads exactly the trust the buyer doesn't have yet, and one bad autonomous demo confirms the
  distrust.

### 6.2 The non-coder authoring paradox — who writes the org's process artifacts?

**Description.** The entire thesis rests on process being captured as artifacts (skills/rules/commands
— research 08 §3.2). The platform is _for non-coders_. But artifacts are, today, authored by people
who understand the COC artifact model — a developer-adjacent skill. **Who writes the organization's
process artifacts if not coders?** If the answer is "the org must hire someone technical to encode its
processes," the platform has reintroduced the very technical-gatekeeper dependency it promised to
remove, and the cold-start cost per customer (research 08 §3.5: "a real cold-start cost for each new
customer") becomes a hiring requirement. This is the no-code authoring problem wearing a process-
artifact hat: the depth (good process artifacts) may still need an engineer, which is the "last 20%"
death (risk 2) relocated to the authoring side.

- **Likelihood: High** that early customers cannot self-author good process artifacts without help.
- **Blast radius: the cold-start economics and the non-coder promise.** If every customer needs
  expert artifact-authoring help, the platform's per-customer onboarding cost balloons and the
  "for non-coders" positioning is compromised.
- **Leading indicator:** the first customer onboarding requires the platform team to write the
  customer's artifacts _for_ them. If self-serve artifact authoring is never achieved, the indicator
  is permanent.

**Recommended mitigation: make the agent author the first draft of the process artifacts from
observed work and natural-language description — the non-coder _describes_ and _corrects_ the process,
the agent _encodes_ it, and M1's transparency lets the non-coder verify the encoding by watching it
run.** The platform's own keystone (LLM does the reasoning, including the reasoning about how to
encode a process) is the escape hatch: artifact authoring becomes a supervised generative task, not a
manual coding task.

- **Pros:** keeps the non-coder promise intact (describe + correct, not author); reuses the LLM-as-
  depth-engine bet (the same bet as risk 2's mitigation, so they validate together); the agent-drafted
  artifact is itself a traced, interveneable work product — dogfooding M1 on the authoring path.
- **Cons:** an agent-drafted process artifact can encode the wrong process plausibly (the convention-
  drift / "plausible-but-wrong-for-here" failure mode, research 08 §1.1, §3.5) and a non-coder may
  not be able to tell — so the verification burden lands back on the non-coder's ability to read the
  trace, coupling this _again_ to risk 2's legibility bet; and bootstrapping (the agent needs _some_
  process knowledge to draft from, but the process is exactly what isn't encoded yet) is a chicken-
  and-egg the first few artifacts per customer must solve manually.
- **Rejected alternative:** a visual artifact-builder for non-coders. Rejected because it is the no-
  code visual-builder pattern that research 07 §6 documents dying at the 20% — and process depth is
  the 20%.

---

## 7. DEPENDENCY risk — building on harnesses and models you don't control

### 7.1 Description (plain language)

The platform can be built _on top of_ existing agent harnesses (Cowork / Claude Code / Codex / Gemini)
or it can _own its runtime_. Research 05 §4 lays out the three options and the decisive criterion: can
the brief's transparency + intervention + versioned-replay requirement (M1) be satisfied _without
owning the loop_? The evidence tilts toward "no" — the commercial harnesses' permission modes are
binary and per-call, not the intent-staged, posture-gated, replayable model M1 needs (research 05
§4.4) — and the sister project envoy chose to own its runtime for exactly this reason (research 05
§4.2). There is also a hard constraint: `.claude/rules/independence.md` forbids _depending on_ a
proprietary SDK, which rules out Option A's purest form (research 05 §6.4).

Two dependency sub-risks:

1. **Harness dependency.** If the platform sits on a harness it doesn't control, its core
   capabilities (transparency, intervention) are gated by that harness's introspection surface, its
   pricing, its availability, and its roadmap. A harness vendor that changes terms, deprecates an
   API, or simply ships M1 itself (risk 5) can pull the rug.
2. **Model black-box reliability.** The platform's entire value rests on the LLM reliably doing the
   reasoning (the "tools are dumb, LLM reasons" keystone). The model is a black box whose behavior can
   shift between versions, whose reliability is not contractually guaranteed, and whose failures are
   non-deterministic. Research 06 §3 names the determinism problem; research 08 §4.2 point 4 names the
   confident-fast-wrong amplification problem. The platform cannot make the model more reliable than
   it is; it can only contain the model's unreliability.

### 7.2 Likelihood, blast radius, leading indicator

- **Likelihood: Near-certain that the harness/runtime decision materially constrains M1; High that
  model-version drift causes behavior regressions over time.**
- **Blast radius: the core capability (for harness dependency) and output reliability (for model
  dependency).** Harness dependency is an existential-adjacent risk because it can gate the lead moat;
  model dependency is a chronic-degradation risk (it makes outputs unreliable, not impossible).
- **Leading indicator (harness):** any moment where M1's design is forced to compromise because the
  underlying harness "doesn't expose that." Research 05 §6.4 names the pivotal spike: "whether harness
  introspection can satisfy 5e/5f is the pivotal unknown that decides the runtime architecture; it
  should be the first thing a spike resolves." **If that spike has not been run, the indicator is that
  the most important architectural decision is being deferred on faith.**
- **Leading indicator (model):** output quality regressing across a model version bump with no code
  change — the signal that the platform's behavior is hostage to the model's.

### 7.3 Recommended mitigation

**Recommendation: own the governed core runtime (the envoy path, research 05 §4 Option C / the hybrid
in §4.3) so M1/M2's transparency, intervention, and posture-gating are _native_ — while continuing to
develop the product itself using the commercial harnesses (multi-CLI parity via the loom/envoy DNA),
and treat the model as a swappable, abstracted dependency behind a model-adapter layer.**

This is the hybrid research 05 §4.3 explicitly surfaces: "own the _product_ runtime (so
transparency/intervention/posture are native) while continuing to _develop the product_ using the
CC/Codex/Gemini harnesses." It satisfies the independence constraint (no proprietary dependency in the
product core), gives M1 the loop control it needs, and the model-adapter abstraction (research 05
§4.3, envoy's `model-adapter.md`) keeps the platform from being hostage to any single model vendor.
**Precondition: run the M1-introspection spike (research 05 §6.4) FIRST** — it is the cheap experiment
that confirms whether owning the loop is truly necessary, before committing to the highest-cost option.

**Implications:** the platform carries the cost of owning a runtime (reimplementing context
management, compaction, subagent orchestration the commercial SDKs give free — research 05 §4
Option C cons) in exchange for native M1/M2 and independence. Model-swappability is built in from the
start, so a model regression or a pricing change is a configuration change, not a rewrite.

**Pros:**
- Native M1/M2 (the loop is yours, so transparency/intervention/posture are first-class, not bolted
  on) — directly de-risks the lead moat against harness limitations.
- Satisfies the hard independence constraint, removing the proprietary-dependency rug-pull risk.
- Model-adapter abstraction hedges model-vendor risk (pricing, availability, version drift) — the
  platform is not married to one model.

**Cons (real, not glossed):**
- Owning a runtime is the **highest build cost** of the three options (research 05 §4 Option C) —
  reimplementing context management, compaction, and subagent orchestration that the commercial SDKs
  provide free — slowing time to first working demo, which directly worsens the competitive-window
  risk (5) and the PMF-falsifiability risk (1).
- Kaizen/Nexus maturity "at harness scale for this exact use case is unproven" (research 05 §6.4
  uncertainty flag) — owning the runtime on the in-ecosystem stack carries its own integration risk
  that the spike must also probe.
- The model-adapter abstraction is real ongoing engineering (research 05 §4 notes "envoy's
  model-adapter.md shows how large that is") — abstracting over models that differ in tool-calling,
  context windows, and reasoning surfaces is a perpetual tax, and a leaky abstraction can hide model-
  specific reliability problems until they surface in production.
- Multi-CLI parity for the _development_ side is itself a "perpetual tax" (research 05 §4.1: the
  drift audits, the codex-mcp-guard bridge) — choosing to develop across CC/Codex/Gemini buys vendor-
  risk hedging at the cost of ongoing parity maintenance.

**Rejected alternative:** build on a single commercial harness for speed. Rejected on two grounds: it
violates the independence constraint (`independence.md`), and it gates the lead moat (M1) on a loop the
platform doesn't control — the exact failure research 05 §4.4 warns produces "transparency/intervention
gated by each harness's introspection surface."

---

## 8. Cross-cutting failure mode — the legibility dependency

A pattern recurs across risks 2, 3, 6.1, and 6.2: **multiple mitigations depend on M1's transparency
being _legible to a non-coder_, and that legibility is itself unvalidated.** It is worth surfacing as a
distinct, named cross-cutting risk because it is a single point of failure for several otherwise-
independent mitigations.

- Risk 2's escape hatch (LLM-as-depth-engine, human supervises) requires the human to _read_ the
  depth via the trace.
- Risk 6.1's adoption path (start supervised, earn autonomy on evidence) requires the customer to
  _read_ the trace to gain confidence.
- Risk 6.2's authoring path (agent drafts artifacts, non-coder verifies) requires the non-coder to
  _read_ the trace to verify the encoding.

If transparency produces _data_ but not _understanding_ — a 40-step DAG is fully traced and fully
incomprehensible — then all three mitigations weaken together.

- **Likelihood: Medium-High** that naive transparency over-produces and under-explains.
- **Blast radius: three mitigations at once** — the depth bet, the adoption path, and the authoring
  path.
- **Leading indicator:** usability tests where non-coders, shown a complete trace, cannot answer "did
  the agent do the right thing here, and where would I intervene?" within a small number of seconds.

**Recommended mitigation: treat legibility as an explicit, separately-validated design goal — invest
in progressive disclosure and summarization of the trace (show the shape first, the detail on demand),
borrowing the platform's own progressive-disclosure DNA (the skill/artifact model already solves
context-bloat this way, research 07 §8), and gate any "watch it prove itself" claim on a usability
result, not an architectural one.**

- **Pros:** addresses three risks' shared dependency with one focused investment; reuses the
  progressive-disclosure pattern the ecosystem already runs; converts an implicit assumption into a
  measured, falsifiable design goal.
- **Cons:** summarization of a trace re-introduces the model's unreliability at the explanation layer
  (a summary is itself an LLM output that can mislead — the progressive-summarization trap, research
  05 §1.6: "$247.83 compressed to 'customer wants refund'"); and legibility-for-non-coders may
  genuinely cap how complex a work-graph the platform can expose, structurally limiting the depth M1
  can offer — the legible ceiling may be below the useful ceiling.
- **Rejected alternative:** assume transparency = legibility and ship the raw trace. Rejected because
  it is the assumption that, untested, sinks three mitigations silently.

---

## 9. Risk interaction map — how the failures compound

The risks are not independent. The most dangerous scenarios are _combinations_:

| Combination | Compounded failure |
| ----------- | ------------------ |
| **4.1 + 4.2 + 4.3** | An untrusted artifact (4.1) carries a prompt injection (4.2) that drives the centered agent (4.3) to an irreversible action — the category-defining incident. Each alone is survivable; together they are the headline. |
| **2 + 6.1 + 6.2 + 8** | The legibility dependency (8): if M1's transparency is not legible (risk 2), the adoption path (6.1) and the authoring path (6.2) both fail, because both rely on the non-coder reading the trace. One unvalidated assumption sinks three mitigations. |
| **1 + 5** | Decision B widens the competitive window (good for 5) but defers the buyer signal (bad for 1). If the window estimate is wrong (competitor moves faster than expected) _and_ the lighthouse signal is weak, the platform is both behind and unsold. |
| **2 + 5** | M1 is both the hardest to build (risk 2) and the most contested (risk 5). If the platform under-resources M1 to hedge (per §5's recommendation) and a competitor ships it anyway, the lead moat is lost on both fronts. |
| **4.5 + 6.1** | The liability question (4.5) and enterprise distrust (6.1) reinforce each other: the unanswered "who's accountable at L5" feeds the distrust that keeps everyone at L3, which prevents the autonomy that would prove the platform's value. |

The interaction map is itself an argument for the **conjunction-not-single-term** competitive posture
(§5) and the **legibility-as-explicit-goal** investment (§8): both are responses to the fact that the
moat terms and the mitigations are coupled.

---

## 10. The TOP 5 existential risks, ranked, with validation/mitigation sequence

The five risks that can _end_ the venture (as opposed to degrade it), ranked by likelihood × blast
radius, with the recommended validation/mitigation sequence. The sequence is designed so the
**cheapest, most-decisive falsifiers run first** — each step either de-risks the next or kills the
plan early enough to redirect.

### Rank 1 — PMF: the horizontal platform lands nowhere (§1)

**Why #1:** High likelihood (base rate + active market cancellation + Decision B's deferral) ×
total blast radius (no buyer = no company). It is the only risk that is _certain_ to be fatal if it
fires, and the market is actively producing the conditions for it.

**Validation/mitigation sequence:**
1. **Pick the lighthouse workflow now** (§1.4) — a real, painful, cross-system workflow with a real
   design partner watching. Cost: near-zero (the Sequor wedge is the first lighthouse).
2. **Run the §5.2 capability acceptance test against the lighthouse**, with the design partner — so
   "capability proven" and "someone would pay" are tested together, not sequentially.
3. **Gate the beachhead decision on the design partner's reaction**, not on a whiteboard.

**Implications / pros / cons:** Pro — converts the unfalsifiable business bet into a falsifiable one
at near-zero cost, and surfaces "lands nowhere" while there is still time to pivot. Con — risks
anchoring the horizontal product to one vertical (re-verticalization, research 07 §9a), requiring
active discipline to treat the lighthouse as evidence, not gravity.

### Rank 2 — M1 versioned cascade is too hard for non-coders (§2)

**Why #2:** High likelihood the _full_ vision isn't shippable soon × blast radius = the lead moat
collapses. It is the moat term most likely to fail on its own merits, independent of any competitor.

**Validation/mitigation sequence:**
1. **Run the M1-introspection spike** (research 05 §6.4) — does M1 require owning the loop? This
   decides the runtime architecture (risk 7) and must run before the runtime is committed.
2. **Prototype the reduced M1** (linear retrace, reuse-recorded-output default, no branching, §2.4)
   on the comms wedge's 4-step graph.
3. **Gate on the cascade cost-preview legibility test** (§2.3 leading indicator) — can a non-coder
   understand "this change re-runs N steps for ~$X" before committing?
4. **Validate legibility explicitly** (§8) before claiming M1 as the lead USP.

**Implications / pros / cons:** Pro — sequences the hardest moat by tractability, ships a
differentiated reduced form, and forces the legibility question early. Con — a reduced M1 is less
differentiated and risks an expectation gap if marketed on the full vision; deferring branching cedes
the alternative-timeline use-case at launch.

### Rank 3 — Trust/security: centered agent concentrates blast radius (§4)

**Why #3:** Medium per-incident but near-certain over time × category-defining blast radius (one
incident freezes enterprise sales). Ranked below PMF and M1 because it is _containable_ by reusing
shipped DNA (envelope, posture, tenant-isolation), whereas 1 and 2 are open problems.

**Validation/mitigation sequence:**
1. **Least-privilege per objective** (§4.3) — narrow default envelopes from day one.
2. **Posture/envelope as injection containment** (§4.2) — write-to-system-of-record requires higher
   posture or human gate by default.
3. **Enforce tenant isolation on the M1 ledger and M4 exchange** (§4.4) — reuse the mechanical audit.
4. **Capability-scoped artifacts + default-deny intake for M4** (§4.1).
5. **Document the L5 accountability anchor** (§4.5) — answer the legal questionnaire before it is
   asked.
6. **Red-team continuously** (`/redteam` discipline) — the leading indicator is "we can't yet get the
   agent to misbehave via injection," which means try harder.

**Implications / pros / cons:** Pro — most mitigations reuse complete, audited ecosystem DNA, so this
is discipline more than invention. Con — every containment gate undercuts the L5-autonomous value
proposition (the HITL-bottleneck tension), and calibrating gates is a never-finished tuning problem.

### Rank 4 — Agent-comms hypothesis wrong or rejected (§3)

**Why #4:** Medium-High likelihood the verbatim claim is over-broad × blast radius = M3's rationale
(but M3's substrate survives as plumbing). Ranked below security because the failure is _narrower_ —
it costs the team-comms _story_, not the company.

**Validation/mitigation sequence:**
1. **Instrument the lighthouse handoff** (§3.4) — measure round-trip reduction, "I thought you were
   doing that" failures, re-keying. Near-zero build (data falls out of the audit trail).
2. **Build M3 to the narrowed §4.3 position** (disrupt handoff, not relationship) with
   ambiguity-preservation as a shipped feature.
3. **Keep a named human on every consequential decision** (the existing HELD path).
4. **Watch the leading indicator:** do users route real handoffs through the agent, or bypass it?

**Implications / pros / cons:** Pro — converts the riskiest brief claim into an instrumented
experiment at the cost of a dashboard, and the narrowed position aligns with the platform's own
governance philosophy. Con — the narrowed claim is a smaller, less-exciting story that may under-sell
the team vision; the "informal mode" adds an ungoverned surface that complicates the
"everything-traced" story.

### Rank 5 — Competitive window closes; hyperscaler ships M1/M3 (§5)

**Why #5:** Medium likelihood × blast radius = the conjunction stops being unoccupied. Ranked #5 not
because it is unimportant but because it is the _least controllable_ (it depends on competitors) and
the most _hedgeable_ (the conjunction survives losing one term if the platform races on the
conjunction, not a single term).

**Validation/mitigation sequence:**
1. **Race on the conjunction, lead with M2** (§5.3) — the most-shipped, hardest-to-retrofit DNA.
2. **Monitor the two canary capabilities** (§5.2) — any competitor non-coder "retrace + re-run
   downstream" or "multiple humans on one agentic workspace."
3. **Hold agnosticism + native-governance as the un-raceable ground** (suite vendors can't be
   agnostic; harnesses haven't gone native on governance).
4. **Use Decision B's window deliberately** — build the hard substrate quietly while competitors ship
   surface, but treat the window as shorter than comfortable.

**Implications / pros / cons:** Pro — hedges the single most contested term; the platform survives
losing the M1 race because M2+M3+M4 remains unique. Con — leading with M2 risks reading as "yet
another governance tool" in a filling TRiSM category, and de-emphasizing M1 cedes the narrative high
ground to whoever ships versioned cascade first.

### The sequence in one picture

```
SPIKE FIRST (cheapest, most decisive):
  ├─ M1-introspection spike (research 05 §6.4)  → decides runtime ownership (risk 7) + M1 feasibility (risk 2)
  └─ Pick lighthouse workflow (§1.4)            → makes PMF (risk 1) + comms-hypothesis (risk 3) falsifiable

THEN BUILD (governance-led, conjunction-not-single-term):
  ├─ M2 governance + agnosticism foundation     → most-shipped DNA, hardest to retrofit (risk 5 hedge)
  ├─ Least-privilege + tenant-isolation + envelope containment (risk 4) — discipline on reused DNA
  └─ Reduced M1 on the lighthouse graph (risk 2) — linear retrace, legibility-gated

THEN VALIDATE (before claiming the moat):
  ├─ Legibility usability test (§8)             → gates risks 2, 6.1, 6.2 simultaneously
  ├─ Handoff instrumentation (risk 3)           → validates/narrows the comms bet
  └─ Design-partner pay-signal (risk 1)         → gates the beachhead decision

THROUGHOUT:
  └─ Continuous red-team (risk 4) + competitor canary-watch (risk 5)
```

The ordering principle: **spikes and the lighthouse run first because they are cheap and decisive** —
they can kill or redirect the plan before the expensive build. The build is **governance-led** because
M2 is the most-shipped, hardest-to-copy DNA and hedges the competitive race. Validation **gates the
moat claims** so the platform never markets a capability (M1 legibility, the comms bet, the business
case) it has not falsified.

---

## 11. Open questions (genuine uncertainty, flagged not resolved)

These are questions the analysis cannot resolve from the available evidence and that materially affect
the risk picture. They are surfaced for the decision-makers, not papered over.

1. **What is the actual size of the competitive window?** The §5 hedge assumes the window is "shorter
   than comfortable" but cannot quantify it. Whether a hyperscaler ships non-coder versioned cascade
   in 6 months or 24 months changes whether racing-on-the-conjunction is prudent or fatally slow. No
   evidence in the research stream sizes this.

2. **Can a non-coder genuinely read a multi-step agentic trace?** The legibility dependency (§8)
   underpins three mitigations and is _unvalidated_. The research proposes progressive disclosure as
   the answer (research 07 §8) but there is no usability evidence. This is the single most important
   thing to test cheaply.

3. **Where does vendor liability land at L5 (§4.5)?** The technical accountability anchor is clear
   ("named human pre-authorized"); the _legal/commercial_ liability stance is not, and at enterprise
   scale some vendor liability position may be required to close deals. This is a business/legal
   decision outside this analysis's scope, flagged because it can block sales independent of any
   technical mitigation.

4. **Is the comms-handoff signal from the Sequor wedge representative of ERP/CRM-class coordination?**
   The lighthouse-as-falsifier strategy (§1.4, §3.4) is only as good as the lighthouse's
   representativeness, and `08` §5.3 flags that comms may be "easier" than heterogeneous enterprise
   systems. A clean comms result could be a false positive for the hard case (research 08 Appendix B
   item 1: the heterogeneous-systems case is "the unproven net-new core").

5. **Does owning the runtime (risk 7 mitigation) cost more than the competitive window allows?** The
   recommended hybrid (own the governed core) is the highest-build-cost option and directly worsens
   time-to-demo (risks 1 and 5). The M1-introspection spike is meant to confirm it is _necessary_, but
   even if necessary, whether it is _affordable within the window_ is an open trade-off the spike does
   not resolve.

6. **At what point does conservative-by-default security (§4) cross from trust-building into value-
   destroying?** Risks 4.2/4.3/4.5/6.1 all push toward gating; the value proposition pushes toward
   autonomy. The "right" calibration is empirical and per-customer, and there is no evidence yet on
   where the line sits. Mis-calibration in either direction is a named failure (security hole vs UX
   death); the analysis cannot pre-locate the line.

---

## 12. Source ledger

**Research stream (read directly for this document):**
- `01-research/05-cli-harness-universal-interface.md` — §6 (feasibility risks, the hard 20–30%), §4
  (runtime-ownership options + decisive criterion), §6.4 (the M1-introspection spike), §1.6
  (progressive-summarization trap).
- `01-research/06-transparency-intervention-versioning.md` — §8 (risks: determinism, cascade cost
  explosion, storage growth, in-memory EventBus scaling, ledger-vs-spans), §7.1 (hard cascade
  invariants incl. tenant isolation), §2.2 (branching model), §4.2–4.3 (decision/posture mechanism).
- `01-research/07-competitive-landscape.md` — §10 (threats), §1 (market: Gartner 40%-cancelled, MIT
  NANDA 95%-fail), §3 (Cowork + suite vendors), §6 (no-code last-20% death), §7 (governance home-field
  advantage + TRiSM category filling), §9 (per-differentiator scrutiny), §11 (positioning).
- `01-research/08-work-disruption-thesis.md` — Part 4 (agent-comms steelman §4.1 + stress-test §4.2 +
  nuanced position §4.3), §3.5 (the honest seams in the inversion), §5 (capability-first / Decision B /
  the §5.2 acceptance test / Sequor wedge as partial proof), Appendix B (flagged uncertainties).

**Strategic spine:** Phase A competitive + research synthesis (M1–M4 moat conjunction, the Cowork
threat, Decisions A and B, the honest cautions) — provided in-session, aligned to, not re-derived.

**Ecosystem rule DNA referenced as mitigation substrate (cited, not re-read this session):**
- `.claude/rules/tenant-isolation.md` (the mechanical isolation audit, §4.4).
- `.claude/rules/artifact-flow.md` (Gate-1/Gate-2 + intake disclosure-scrub, §4.1 mitigation).
- `.claude/rules/communication.md`, `recommendation-quality.md` (writing discipline: plain language,
  symmetric pros/cons).
- `.claude/rules/autonomous-execution.md` (effort in cycles, not human-days).
- `.claude/rules/independence.md` (no proprietary-dependency constraint, §7).
