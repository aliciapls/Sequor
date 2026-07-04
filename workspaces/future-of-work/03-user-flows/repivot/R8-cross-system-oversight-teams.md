# R8 — One control surface across many systems (cross-vendor neutrality; teams)

> Value principles embodied: P5 (cross-vendor neutrality — one surface across many systems of record), P3 (governance is the product, priced as compliance), P4 (meaningful oversight at scale), P1 (integrate-and-govern, never replace). Wedge: enterprise (multi-system, multi-manager).

This is the thing single-suite incumbents structurally cannot offer. Salesforce governs Salesforce; ServiceNow governs ServiceNow; SAP governs SAP. None of them govern the _others_. When agents act across Salesforce **and** the ERP **and** ticketing **and** mail, a company that relies on each vendor's native governance gets four separate oversight silos, four approval inboxes, four audit trails — and no single place to see, approve, and prove what the agents did across all of them. Sequor is that single place: one approval surface, one audit surface, one control surface, spanning every system of record, with multiple managers overseeing it together and every decision attributed to the human who made it.

## The walk (from the directors' shared screen)

Meet **Priya** (revenue-operations director) and **Sam** (finance director). Their company runs agents that do real cross-system work: an agent handling a customer renewal reads the account in **Salesforce**, checks the invoice in the **ERP**, closes the support case in **ticketing**, and emails the customer through **mail** — one job, four systems. Priya and Sam co-oversee this work.

1. **Priya opens one unified oversight surface — not four.** Her screen shows held actions from _all four systems in a single queue_. A renewal agent's held action reads:

   > **Renew Globex — apply 12% loyalty discount and issue invoice.**
   > _This one job touches four of your systems:_ read the account (**Salesforce**), apply the discount + issue the invoice (**ERP**), close the renewal case (**ticketing**), send confirmation (**mail**).
   > _Held because:_ a 12% discount is above your **10% auto-approve limit** on renewals.
   > _Confidence:_ medium (74%).
   > **[ Approve ] [ Edit ] [ Reject ]**

   Priya sees the _whole_ cross-system action as one thing to approve — not a Salesforce approval, then separately an ERP approval, then a ticketing action. One decision governs the job across all four systems.

2. **Approvals route to the right manager automatically.** The discount is Priya's call (revenue), so it landed in her queue. But the same job also proposes writing off a $900 aged balance in the ERP — and _that_ is Sam's call (finance). Sequor split the job's two consequential actions to the two accountable humans: the discount to Priya, the write-off to Sam. Neither can approve the other's piece. The job proceeds only when both have approved their part. This is **multi-human coordination** — the right human approves the right action, and the accountability is attributed, not shared into a blur.

3. **Priya and Sam each see who approved what — attributed.** On the job's timeline, Priya sees: _"Discount 12% — approved by Priya K. 09:14. Write-off $900 — approved by Sam T. 09:31."_ Every action carries the named human who authorized it. If a fourth manager later asks "who signed off on the write-off?", the answer is on the record: Sam, at 09:31, with his reason. No action is anonymous; no approval is untraceable to a person.

4. **High-stakes actions can require two managers.** For the largest write-offs (over $10,000), the company set a rule that _two_ finance managers must both approve — a four-eyes gate. Sequor holds the action until two distinct, named, senior-enough humans have each approved; one manager cannot approve twice or approve their own request. The gate is structural, not a convention.

5. **One control surface, not just one queue.** Beyond approvals, Priya and Sam share one place to set the rules across all systems: "renewal agents can auto-apply discounts up to 10% in the ERP, must never touch anything except renewal accounts in Salesforce, may email customers but never regulators, and may spend up to $5,000 per job." They set this once, in plain language, and it governs the agents' behavior in _every_ system simultaneously. They do not configure Salesforce's guardrails, then the ERP's, then mail's — they set one posture and one envelope that spans the four.

6. **When something needs more room, the break-glass is unified too.** A major customer escalation needs an agent to act faster than the normal rules allow across three systems at once. Sam requests an **emergency override** — time-limited (4 hours), scoped, and it cannot grant more than Sam himself holds. It applies across all four systems from one request, is logged once, and schedules its own 7-day review. There is no need to open four separate vendor consoles to widen four separate permissions.

7. **The audit is unified across every system.** When quarter-end comes, Priya generates one audit bundle (the R6 flow) that covers _all four systems in one export_ — every cross-system job, every action inside each system of record, every named approver, the rules in force, the data touched, the outcome. An auditor asks "show me everything the AI did across Salesforce, the ERP, ticketing, and mail, and who approved each piece." Priya hands over **one** bundle that answers it — not four vendor exports she'd have to stitch together and reconcile.

Priya and Sam oversee agents acting across four vendors' systems from one approval surface, one control surface, one audit surface — each of them accountable for their own decisions, all of it attributed and provable. No single-suite vendor can give them this, because no single-suite vendor governs its competitors' systems.

## Features exercised

- **Unified cross-system oversight queue** — held actions from Salesforce + ERP + ticketing + mail in ONE ranked queue, with each cross-system job shown as a single approvable object.
- **Approval routing by accountability** — each consequential action routed to the named human accountable for it (discount → revenue director; write-off → finance director), using the D/T/R accountability chain to compute who must be looped in.
- **Attributed multi-human decisions** — every approve/edit/reject tied to the named, authenticated human who made it; visible on a shared timeline.
- **Four-eyes / multi-approver gates** — high-stakes actions require two distinct, senior-enough humans; self-approval and double-approval structurally blocked.
- **One posture + one envelope spanning many systems** — a single plain-language rule set (scope, spend, data, channels) that governs agent behavior across all four systems of record at once.
- **Unified emergency override** — one time-limited, scoped, self-reviewing break-glass request that applies across systems, capped at the approver's own authority.
- **Cross-system connectors** — read/write _through_ the existing systems (never replacing them), via standard connectors.
- **Unified cross-system audit export** — one bundle covering every system, feeding the R6 compliance flow.

## Deliverables / artifacts produced

- **A unified cross-SoR control surface** — one place to set rules, approve actions, and oversee agents acting across many vendors' systems — the artifact incumbents structurally cannot produce.
- **Attributed multi-human approval decisions** — a record of which named manager approved which action, across which system, with reason and timestamp — accountability lineage that spans vendors.
- **A cross-system posture + envelope** — the single governing rule set, versioned and signed, that applied to the agents across all four systems.
- **A unified cross-SoR audit bundle** — one export covering every action in every system of record, with per-action lineage grouped so an auditor can inspect each system independently _and_ see the whole.
- **Four-eyes gate records** — proof that the highest-stakes actions carried two distinct named approvals, not one.

## Reuse → net-new

**Shipped substrate reused:** the **MCP connectors** that read/write _through_ Salesforce, ERP, ticketing, and mail (integrate-not-replace — the same connective tissue every incumbent has converged on). PACT's `ApprovalBridge` + `ApprovalConfig` + `MultiApproverService` already handle approval routing, per-operation approval policy, and multi-approver quorum with duplicate-vote prevention and per-decision locks. The **D/T/R accountability grammar** already computes, from an action's address, exactly which named humans are accountable — the substrate for routing the right action to the right manager. **aegis multi-tenant** isolates each customer org. EATP posture + envelopes already apply one rule set across arbitrary actions regardless of which system executes them. `EmergencyBypass` already delivers the scoped, time-limited, self-reviewing break-glass. loom's governed distribution is the pattern for a cross-org/cross-system bundle. **Net-new:** the **cross-SoR unified oversight/audit surface** — one queue, one control panel, one export spanning _multiple_ systems of record (the shipped pieces govern per-action; unifying them into a single multi-system director surface is the concentrated new work); the **cross-system job view** (one approvable object for a job that touches four systems); and the **multi-human director UX** (attributed approvals + four-eyes gates rendered for non-technical managers).

## Why it matters (grounded)

Incumbents each govern only their own silo — Salesforce governs Salesforce, ServiceNow governs ServiceNow, SAP governs SAP — and every one of them is racing to pull you _deeper_ into its own stack (all four converged on agents-on-top-of-their-own-system-of-record via MCP). The one thing they **structurally cannot offer** is a single oversight surface _across_ SAP + Salesforce + ticketing + mail — the exact unmet need this flow serves (**P5, cross-vendor neutrality**). That neutrality is one of the two things a single-suite vendor can never do (the other being genuine non-technical usability), and it is the defensible wedge the thesis identifies for the standalone-vs-absorbed risk. Combined with the #1-barrier finding (governance is the top blocker to deploying agents) and **EU AI Act Article 14** (a company running high-risk agents across four vendors' systems still needs _one_ coherent human-oversight record, not four fragmentary ones), a unified cross-system approval + audit + control surface is precisely the deployable control that lets a stalled, multi-vendor agent program actually ship.
