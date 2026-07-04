# 13 — Sequor Pitch: The Control Layer for Agentic Work

> The repositioned pitch, grounded in `12-saas-2.0-thesis.md` (evidence + citations) and
> `briefs/02-repivot-to-saas-2.0.md` (the seven value principles). Written for a skeptical buyer/investor:
> every claim ties to evidence; risks are stated, not hidden.

## The one-liner

**Sequor is the control layer that lets a non-technical manager safely put AI agents to work across the
systems their company already uses — and prove, to an auditor, exactly what every agent did and who
approved it.**

Category: **governed agentic orchestration + oversight** — the layer _between_ the humans who are
accountable and the agents that do the work, sitting _on top of_ the systems of record a company already
owns.

## 1. The problem (why agents are stuck)

Every enterprise is being told to deploy AI agents. Almost none can. The blocker is **not** agent
capability — it's **deployable control**:

- **Risk/governance is the #1 cited barrier** to scaling agents; only ~**30%** of organizations call
  themselves governance-ready (McKinsey).
- **Gartner predicts >40% of agentic-AI projects will be cancelled by 2027** — mostly for cost, unclear
  value, and inadequate risk controls.
- And the deadline is real and dated: **EU AI Act Article 14** legally requires _effective human oversight_
  of high-risk AI, with high-risk obligations in force **from 2 August 2026**.

So the market has a growing pile of agent pilots that can't go to production because **no one can safely
let them act, and no one can prove to a regulator/auditor what they did.** That gap — between "an agent
_can_ do this" and "we're _allowed_ to let it" — is the whole opportunity.

## 2. The insight (what actually changed — "SaaS 2.0")

"SaaS is dead" is a misread. What's happening is a **re-tiering**:

- **Systems of record survive and harden** — agents need trusted, governed data _more_ than humans did
  (Deloitte: no wholesale replacement "for at least five years"; every incumbent is _layering agents on
  top_ of its data, rebranding "systems of action").
- **The workflow/app tier dissolves** into an agent orchestration layer, and pricing shifts from
  per-seat to per-outcome.
- **The interface inverts** — from _entering data_ to _overseeing agents that act._
- And **workers do not become builders** — building stays a thin specialist skill (the no-code last-mile
  plateau survived AI; METR measured AI making expert devs _slower_). What democratized is **consumption**:
  the many become **directors** who approve, inspect, steer, and correct.

**Value moved out of "UI + workflow lock-in + seats" and into: trusted data · orchestration · governance/
trust/evals · governed distribution · outcomes.** Sequor targets the orchestration + governance + oversight
slice — the part that makes agents _deployable_ on top of the systems that survive.

## 3. What Sequor is (the product)

A control layer that does four things, for a **director** (a manager, not a coder):

1. **Connect** — reads/writes _through_ the systems the company already uses (CRM, ERP, ticketing, mail,
   docs) via standard connectors. We don't replace them; we orchestrate across them.
2. **Govern** — the director sets, _before_ work runs, how much autonomy each kind of job gets
   (pause-and-approve / ask-once / supervise-by-exception), with budgets, clearances, and hard limits.
3. **Oversee** — every step (inputs, the agent's plan, tool calls, results, outputs) is surfaced live and
   recorded; the director approves the consequential moments, inspects the trace, and can **rewind any step,
   change it, and re-run only what's affected** — old versions kept.
4. **Prove** — every agent action carries an **accountability lineage back to a named human**, exportable
   as an audit bundle that satisfies EU AI Act-grade oversight requirements.

In one sentence: **Sequor turns "we can't deploy agents safely" into "we deploy agents with a director on
the loop and an auditor-ready record."**

## 4. Why now (the timing is not optional)

- **Regulation with a date:** EU AI Act Art. 14 human-oversight obligations bite Aug 2026 (high-risk),
  phasing through 2027; NIST AI RMF and Singapore's Agentic-AI governance framework reinforce globally.
- **The architecture just settled:** every incumbent (Microsoft, SAP, ServiceNow, Salesforce) has
  converged on _agents-on-top-of-systems-of-record via MCP_ — so the connect-and-govern-across layer is now
  a well-defined, buildable slot.
- **The cancellation wave is the demand:** the ~40% of agent projects that will be cancelled are cancelled
  for _lack of control_. Sequor is the thing that unblocks them.

## 5. Why us (this is ~80% already built, with a live wedge)

The hard substrate already ships across the Terrene/Kailash ecosystem **with paying enterprise customers**:
posture/trust machinery (EATP), governance/envelopes/audit (PACT), a governed multi-tenant runtime
(aegis), governed distribution (loom), a multi-model session engine (csq). Sequor is **composition + a
concentrated net-new surface** (the director's control/oversight UI + the cross-system cascade/undo engine),
not a from-scratch build. And the **comms product is a live proving ground** — a human already approves
AI-drafted responses and the system learns from corrections. **That human is a proto-director.** We
instrument that loop to validate the whole thesis cheaply.

## 6. The value principles — with rationale (the spine)

**P1 — Integrate-and-govern, never replace.**
_What:_ we sit on top of the customer's existing systems; those systems become our moat, not our target.
_Why:_ systems of record survive ≥5 years (Deloitte); **61% of CIOs buy AI from vendors they already
use**; Menlo (n=495) found build-vs-buy swung to **76% bought.** _Rejects:_ "rip out your SaaS suite" —
the framing that fights the single best-evidenced fact in the market (and the exact place a sibling
"replace-the-suite" thesis is most exposed).

**P2 — Director, not builder.**
_What:_ the user approves/inspects/steers/corrects; they never write code, flows, or harness config.
_Why:_ the no-code "last mile" plateau survived the AI transition; **METR measured AI making expert
developers 19% slower** (while they _felt_ faster); the FDE/AI-engineer boom proves durable building
stayed specialist. What scaled is **consumption.** _Rejects:_ "everyone becomes a builder" — the weakest
premise in the original vision, and the one the team correctly doubted.

**P3 — Governance is the product, priced as compliance.**
_What:_ audit trail + approval-routing + accountability lineage is the core deliverable, not a feature.
_Why:_ governance is the **#1 cited barrier** to agent deployment; **EU AI Act Art. 14** makes oversight a
dated legal requirement, not a nice-to-have; "Guardian Agents" is now a named analyst category (predicted
10–15% of the agentic market by 2030). _Rejects:_ selling governance as "convenience" — it's a budget line
with a deadline.

**P4 — Meaningful oversight at scale, not rubber-stamp.**
_What:_ risk-tiered control — pause-and-approve for high-risk actions, supervise-by-exception for the rest —
engineered so the director genuinely steers (confidence scoring, exception surfacing, batch-with-sampling).
_Why:_ the strongest counter-argument to any oversight product is "approval degrades to bulk-accept at
volume." Answering it _is_ the differentiation. _Rejects:_ one-click-approve-500 theater.

**P5 — Cross-vendor neutrality.**
_What:_ one approval + audit + control surface spanning _many_ systems of record.
_Why:_ incumbents each govern only their own silo (Salesforce governs Salesforce; ServiceNow governs
ServiceNow). The unmet need — a single oversight surface _across_ SAP + Salesforce + ticketing + mail —
is the one thing they structurally cannot offer. _Rejects:_ becoming a feature of any single suite.

**P6 — Outcomes over seats, honestly.**
_What:_ price on deployable value/work delivered, not per-login.
_Why:_ the shift from seat → outcome/consumption is real (Intercom Fin's $0.99/resolution is live proof;
Nadella's "seat erosion"). *But:* outcome-pricing is **not yet the winning model** (Harvey's $300M ARR is
still seat-based; attribution and margin-on-failures are unsolved; 11x's ARR fraud). _Rejects:_ betting the
company on outcome-attribution — we price first for **trust and deployability**, evolve toward outcomes as
attribution matures.

**P7 — Undo + trace = the trust surface.**
_What:_ rewind any step, see everything, keep versions.
_Why:_ a director consuming work they did **not** build cannot trust it without inspection and correction;
this is what makes P2 (director-not-builder) actually work. _Rejects:_ the opaque "agent did your work,
here's the result" surface (which Claude Cowork already owns and we will not win by copying).

## 7. Differentiation (who we are NOT)

- **vs. suite incumbents (Agentforce, Copilot, ServiceNow, Joule):** they govern _their own silo_ and want
  you deeper in their stack. We are **cross-vendor and neutral** — the oversight surface _across_ all of
  them. (They validate the layer exists; they can't be the neutral one.)
- **vs. "agent does your work" horizontal tools (Claude Cowork):** they own the **surface**; we own the
  **substrate for deploying it safely** — pre-set posture, versioned undo, cross-system audit, director
  oversight. We don't compete on "finish my deliverable"; we compete on "let me _deploy_ that safely at
  work."
- **vs. governance/observability point tools (Arize, Galileo, guardian-agent startups):** they sell to
  **technical** platform/security teams and observe/eval agents. We sell **deployable control to a
  non-technical director**, with the orchestration + undo built in — a product, not a dashboard.
- **vs. replace-the-suite bets:** we ride "SaaS won't die"; they fight it.

## 8. The wedge (where we land first)

Two grounded entry points, sequenced:

1. **The comms lighthouse (now, live):** the shipped product already runs the director loop (human approves
   AI drafts, system learns). Instrument it to prove the persona and the oversight value on real users at
   low stakes — the cheapest possible validation of the two speculative pillars.
2. **Governed cross-system objectives for the mid-market / SMB "departmental edge":** the evidence says
   "agent does real multi-system work" lands first where approval layers are thin and stakes are moderate
   (SMB/mid-market, departmental workflows) — _not_ the regulated enterprise core on day one. We expand
   _upward_ into compliance-driven enterprise oversight as the audit product matures against Art. 16.

## 9. Business model

- **Priced as deployable control / compliance**, not per-seat: a platform fee for the governed
  orchestration + oversight substrate, plus usage/consumption for agent work — and the **audit/oversight
  export as a compliance-tier SKU** carried by the EU AI Act deadline.
- **Land-and-expand from the audit surface:** enter as "the thing that lets your stalled agent project
  ship safely," expand across more systems and more objective-types as the director trusts it.
- **Deliberately not** an outcome-attribution bet (P6) until attribution is provable.

## 10. The honest risks (and how we retire them)

1. **The director persona is unproven as a _buyer_.** Today's oversight budget often sits with technical
   governance/security teams, not line-of-business directors. **Retire it:** instrument the comms wedge's
   proto-director loop; run a design partner where a real manager is the approver; measure whether they
   value (and would pay for) the control surface.
2. **Incumbents may ship "good-enough" native governance** on the data they own. **Retire it:** prove the
   _cross-vendor_ multi-SoR oversight need is real and unmet, and that non-technical usability is a genuine
   gap — win on the two things a single-suite vendor structurally can't do.
3. **"Agent-washing" credibility discount** (40% cancellations). **Retire it:** lead with provable ROI +
   reference audits + "control that lets you deploy," never with autonomy claims.

## 11. What building this proves

The single near-term proof: **a non-technical director puts an agent to work across two of their existing
systems, under a posture they chose beforehand, and walks away with the work done, a live trace they could
rewind, and an audit bundle they could hand to a regulator.** If that lands with a real manager who says
"I would pay for this against _this_ workflow," the thesis is validated and the persona is real.

---

_Grounding & citations: `01-analysis/12-saas-2.0-thesis.md`. Positioning principles: `briefs/02-repivot-to-saas-2.0.md`. Substrate & wedge: `01-analysis/01-research/09-comms-wedge-mapping.md`, `08-product-focus-80-15-5.md`._
