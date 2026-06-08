---
title: "Sequor — The Agentic Work Platform"
subtitle: "Vision Brief & Analysis Walkthrough"
date: "June 2026"
---

> **What this document is.** A plain-language walkthrough of the Sequor platform
> vision and the strategic analysis behind it. It is written for a decision: _is
> this the right direction to build a plan on?_ It is **not** a build spec, a
> budget, or a go-to-market plan — those come later and stay your call.

---

## 1. The idea, in one sentence

**Turn the AI agent — the kind that today lives in a coder's terminal — into a single
work surface where any employee, not just coders, gets their whole job done by
stating what they want, while every step stays visible, controllable, and undoable.**

---

## 2. The problem we're attacking

Today a staff member is the **human glue** between disconnected tools. To produce one
quarterly report they hop ERP → CRM → spreadsheet → Word → an internal portal, copying
data between each, holding all the context in their head.

Every task is really three things:

- an **objective** — what they want done,
- a **process** — how _this_ company does it (varies company to company), and
- **data** — spread across all those tools.

The real cost isn't one slow task. It's that **the human is the integration layer** —
and that doesn't scale, makes mistakes, and can't be audited.

---

## 3. The bet

**Flip it: make the agent the integration layer, and the human the director.**

The person says _"I want the Q3 financial report."_ The agent reaches into the ERP, the
CRM, and the spreadsheet, does the work, and hands back the result — without the person
ever leaving one screen. The company's **process** becomes reusable building blocks; the
**data** comes through connectors; the **objective** is just what you type.

---

## 4. Why it can win (and won't get crushed)

This is the most important section, because there is a serious competitor.

**The threat.** Anthropic's "Claude Cowork" (launched around April 2026) already does the
_surface_ version of this — _"an agent does your office work in one place"_ — and it ships
fast. If our entire pitch were "an agent does your work," **we would already be late.**

**So we don't compete there. We win on four things underneath the surface that nobody —
including Cowork — has actually delivered for non-coders:**

| Pillar                                               | What it means for the user                                                                                                                                                                                    |
| ---------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Undo anything, see everything**                    | Every step the agent took is recorded. You can rewind to _any_ earlier step, change it, and only the affected downstream work re-runs — old versions are kept. A glass box with an undo button.               |
| **You choose the leash, up front**                   | Before the agent runs, you pick: _Go ahead_ (full autonomy), _Ask me once_, or _Step through with me_. Spending limits and approvals are built in, not bolted on.                                             |
| **Teams of humans _and_ agents, one shared space**   | Several people and several agents work the same job, with everyone's steps attributed and auditable. (Agent-to-agent teamwork is common; multiple _humans_ on one shared, governed surface is the rare part.) |
| **Share know-how safely across teams and companies** | A company's processes become reusable "recipes" you can publish, govern, and recall. This is the engine that makes the platform more valuable as more people use it.                                          |

**Why competitors can't easily copy this.** The big suite vendors (Salesforce, ServiceNow,
SAP, Microsoft) are locked to their own systems by business model — they can't credibly be
"works with everything." That neutrality is open ground.

---

## 5. The honest risks (not sugar-coated)

Three things this rests on are **not proven yet**. They are flagged everywhere in the
analysis so nobody sells them as fact:

1. **The "agents communicate better than humans" idea is a genuine bet.** It's likely true
   for clean _handoffs_, but risky for judgment, nuance, and accountability. We treat it as
   something to **test cheaply**, not assume.
2. **"Undo anything" is the strongest advantage _and_ the hardest thing to build** — AI isn't
   perfectly repeatable, so "re-run from step 4" is genuinely tricky, and making it legible to
   a non-coder is unsolved design work. Version 1 is deliberately scaled back (simple rewind,
   no branching).
3. **Non-coder depth is where simple "no-code" tools historically die** at the last 20%. Our
   bet is that the "see everything" transparency is what makes the depth usable — but it must
   be _proven_, not asserted.

---

## 6. The good news — most of it already exists

About **80%** of the hard machinery — the governance, the trust/permission levels, the
team-coordination, and the artifact-sharing engine — is **already built and shipping** across
the Kailash / Terrene ecosystem. The genuinely _new_ work concentrates in just three places:

- the **non-coder interface**,
- the **"undo" engine**, and
- the **safe cross-company sharing** model.

_Caveat that stays attached to that 80%: existing pieces are not a finished product — it's a
head start, not a shortcut._

---

## 7. Where the current product fits

The existing **email / WhatsApp communication product becomes the first proving ground**, not
a throwaway. It already quietly demonstrates several of the pillars:

- confidence-based human escalation = the _"choose the leash"_ idea in miniature,
- learning from human answers = the _sharing / know-how_ engine, and
- per-customer data isolation = the multi-company boundary.

It is the **lighthouse** that lets us test the risky bets on real users before betting big.

---

## 8. What we deliberately did _not_ decide

Per your steer, we **did not pick a target market or first customer.** The analysis stays
horizontal and proves the **capability** first; the "who do we sell to first" decision is left
open, on purpose, for later.

---

## 9. Two things that need _your_ decision

1. **A small correction to confirm.** Your brief defined "D/T/R" as _Decision / Task / Review_.
   In the governance system it actually means **Department / Team / Role** (who is accountable).
   The analysis uses the correct one — please confirm that matches your intent.
2. **A premise we down-weighted.** One of your premises — _agents communicate better than
   humans_ — is treated as a **bet to validate**, not a settled selling point. If you firmly
   believe it is already true, say so; it changes how hard the plans lean on it.

---

## 10. So what does "approve" actually mean?

**Approving says:** the problem, the strategy, the four pillars, the honest risks, and the
"comms-as-first-proving-ground" framing are right — turn this into a build plan.

**It does _not_ commit you to:** a budget, a timeline, building everything, or a market. Those
come at the next step and remain entirely your call.

---

## 11. What's next

The next step is **planning** (`/todos`): turn this analysis into a sharded, sequenced build
plan. The first inputs are already identified — the cheapest, most decisive experiments first
(prove the "undo" engine and the cross-system reach on the comms lighthouse) before any heavy
build.

---

## Appendix — What backs this analysis

This walkthrough is a summary. The full analysis package (≈19,000 lines, red-teamed) lives in
the repository under `workspaces/future-of-work/` and `specs/`:

- **Research (9 docs)** — the COC artifact system, multi-operator coordination, PACT governance,
  the EATP trust/posture model, the CLI-harness-as-universal-interface thesis, the
  transparency/versioning architecture, the competitive landscape, the work-disruption thesis,
  and the comms-wedge mapping.
- **Analysis (8 docs + executive summary)** — value propositions, unique selling points, the
  platform model, the AAA framework (Automate / Augment / Amplify), network effects, the
  transparency-and-undo architecture, the 80/15/5 reuse split, and a risks/failure-point audit.
- **Plans (5)** — architecture, capability roadmap, the "undo" engine design, the
  trust/permission model, and the comms-wedge integration.
- **User flows (5)** — objective-to-output, rewind-and-intervene, team collaboration,
  recipe authoring/sharing, and the comms wedge end-to-end.
- **Specs (7 target-state platform specs)** — the authoritative description of what the platform
  is and does, alongside the preserved specs for the shipped comms product.
- **Red team** — independent adversarial review across four dimensions; all blocking and
  high-priority findings resolved. Brief coverage: 22 of 24 requirements fully addressed, 1
  partially (deferred by design), 0 missing, no scope creep.

_Start with `workspaces/future-of-work/01-analysis/00-EXECUTIVE-SUMMARY.md` for the deeper read._
