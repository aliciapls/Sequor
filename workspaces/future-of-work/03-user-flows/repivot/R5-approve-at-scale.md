# R5 — Approve consequential actions at scale (meaningful oversight, not rubber-stamp)

> Value principles embodied: P4 (meaningful oversight at scale, not rubber-stamp), P3 (governance is the product, priced as compliance), P7 (undo + trace = the trust surface). Wedge: mid-market → enterprise.

This flow answers the single strongest counter-argument to any oversight product: _"at volume, approval degrades to one-click bulk-accept — the human stops actually steering."_ The design's whole job is to keep the director's attention on the few actions that genuinely need a human, and to let the safe majority flow through under a pre-agreed rule — without ever presenting a "select all → approve" button that lets the director wave through 500 things they never read.

## The walk (from the director's screen)

Meet **Dana**, a customer-operations director. Overnight, eight agents worked across the company's systems on hundreds of small jobs — answering customer emails, updating records, issuing refunds, scheduling follow-ups. Dana did not watch any of it happen. She set the rules beforehand. Now she opens Sequor to do her real job: oversee.

1. **Dana opens her Oversight Queue.** The screen does NOT show hundreds of items. It shows a short, ranked list of the things that _stopped and asked for her_ — because she set those kinds of jobs to "Step through with me" (pause-and-approve) beforehand. Everything the agents did under "Go ahead" or "Ask me once" already ran and is recorded; it is not in her approval queue, it is in her trace. The queue header reads: _"14 actions are waiting for you. 486 ran under your rules overnight and are logged."_ She sees, plainly, that she is being asked to look at 14 things, not 500.

2. **Each waiting item is a plain-language card, ranked by risk — not by time.** The riskiest, least-confident actions sit at the top. A card reads:

   > **Refund $2,400 to Acme Corp** — held for your approval.
   > _Why this stopped:_ the amount is above your **$500 auto-approve limit** for refunds (you set this).
   > _Agent's confidence:_ **Low (58%)** — the customer's contract terms are ambiguous; the agent flagged that it is not sure this refund is owed.
   > _What it would touch:_ Salesforce (the Acme account), the billing system (issue the credit), and one email to the customer.
   > **[ Approve ] [ Edit ] [ Reject ]**

   Dana reads it, checks the contract note the agent surfaced, and clicks **Reject** with a one-line reason: _"contract caps refunds at $1,000 — re-issue at that amount."_ The agent re-plans and comes back with the corrected action.

3. **The high-risk items are one-at-a-time by design.** For anything Dana tagged high-risk beforehand (refunds over a threshold, anything touching a VIP account, anything sending externally to a regulator), Sequor holds each action individually — **pause-and-approve, human-in-the-loop.** There is no batch button on these. The friction is deliberate: these are the actions an auditor will later ask "who approved this, and did they actually look?"

4. **The safe majority is supervised _by exception_, not one-by-one.** Below the high-risk cards, Dana sees a second section: _"212 low-risk record updates ran under 'Ask me once'. 3 look unusual."_ This is **human-on-the-loop** — the agents proceeded, and Sequor only surfaces the **exceptions**: the 3 out of 212 where the agent's confidence dipped, or the action fell just inside a boundary, or the pattern differed from the other 209. Dana reviews the 3. The other 209 she does not need to touch — but she can open them anytime in the trace.

5. **When Dana _does_ want to clear a batch, she must sample it — she cannot blind-accept it.** For a genuinely repetitive, low-stakes batch (say, 40 near-identical "order shipped" confirmations the agent drafted), Sequor offers **Batch review with sampling**: it shows her a representative handful (e.g. 5 of the 40, chosen to include the least-confident ones), and requires her to actually open and disposition _those_ before the batch clears. The button is not "Approve 40." It is "Review 5 samples → then release the batch." If any sampled item is wrong, the whole batch is held for full review. This is the structural defense against rubber-stamping: **the system will not let her approve what she has not, in some real sense, looked at.**

6. **Confidence scores steer her attention, honestly.** Every held or exception item carries the agent's own confidence and _why_ it is unsure — not a decorative number. Low-confidence items are surfaced louder and sampled more heavily. Sequor also watches Dana's own behavior: if her approval rate on high-risk items climbs toward "approve everything in under two seconds," the system flags it back to her — _"you've approved 18 high-risk actions in 40 seconds; oversight may be degrading"_ — because a rubber-stamp that _looks_ like oversight is the exact failure this product exists to prevent.

7. **Every decision Dana makes is recorded against her name.** When she approves, edits, or rejects, Sequor writes down: which named human decided, when, what the action was, what rule held it, what data it touched, and what she typed as her reason. She does not do anything extra to make this happen — the act of clicking **Approve** _is_ the audit record. This is what makes R6 (the audit export) possible.

At the end, Dana has spent fifteen focused minutes on the 14 + 3 + 5-sampled actions that actually needed a human — and the other ~480 ran safely under rules she set, fully logged. She steered; she did not rubber-stamp.

## Features exercised

- **Risk-tiered posture per objective** — "Step through with me" (HITL / pause-and-approve) for high-risk job types; "Ask me once" and "Go ahead" (HOTL / supervise-by-exception) for the rest.
- **The Oversight Queue** — a ranked queue of HELD actions (risk-first, not time-first), separated from the already-run supervise-by-exception stream.
- **Plain-language approval cards** — the verdict→prose renderer turning `constraint_dimension=financial, requires_approval_above_usd=500` into "$2,400 is above your $500 auto-approve limit," with **Approve / Edit / Reject**.
- **Confidence scoring + reason-for-hold** — the agent's own uncertainty surfaced as the primary attention-ranking signal.
- **Exception surfacing** — HOTL actions surfaced only when they deviate (low confidence, near a boundary, off-pattern); the rest run silently and land in the trace.
- **Batch-with-sampling** — representative-sample review (weighted toward least-confident items) as the ONLY path to clear a repetitive batch; no blind "approve all."
- **Rubber-stamp detection** — a meta-watch on the director's own approval velocity that flags when oversight is degrading.
- **Accountability capture on every decision** — named human + timestamp + reason + rule-in-force + data-touched, written automatically at the moment of Approve/Edit/Reject.
- **Auto-downgrade safety floor** — if an agent misbehaves mid-run, its autonomy drops instantly (operative posture = min(what Dana chose, what the system now trusts)), pushing more of its actions into Dana's held queue.

## Deliverables / artifacts produced

- **Approval decisions with accountability lineage** — for every held action: the named approver, the decision (approve/edit/reject), the reason, the rule that held it, the data touched, and the outcome — the raw material R6 exports.
- **A supervise-by-exception log** — the full record of HOTL actions that ran, with the exceptions Dana reviewed marked distinctly from the ones that flowed through.
- **Sampling receipts** — for each cleared batch: which items were sampled, that a named human opened them, and that the batch was released (or held) on that basis — provable evidence the batch was not blind-accepted.
- **An oversight-quality signal** — a record of the director's attention pattern (how many held items, how long spent, rubber-stamp flags raised) that itself becomes audit evidence of _meaningful_ (not nominal) human oversight.

## Reuse → net-new

**Shipped substrate reused:** PACT's surface-and-approve pipeline — `SupervisorOrchestrator` (the HOLD-creates-approval-record-and-blocks loop), `ApprovalBridge` (each HOLD → a durable, human-resolvable decision row with who/when/why), and `EventBridge` (live plan/hold/cost stream to screen). The four-level verdict gradient (`AUTO_APPROVED / FLAGGED / HELD / BLOCKED`) already routes actions to the right lane. EATP posture (the L1–L5 ladder + the min(user, floor) safety floor + auto-downgrade) sets which actions land in the queue. PACT's `ApprovalConfig` / `MultiApproverService` handles multi-approver quorum for the highest-stakes items. aegis multi-tenant keeps each customer's queue isolated. **Net-new:** the director's **Oversight Queue UX** (risk-ranked, plain-language, HELD-vs-exception-separated); the **batch-with-sampling** control (there is no shipped "sample-before-release" primitive — this is the anti-rubber-stamp construct); **exception surfacing** as a ranking over the HOTL stream; and the **rubber-stamp-velocity meta-watch** on the director's own behavior.

## Why it matters (grounded)

Governance is the **#1 cited barrier** to deploying agents (McKinsey: ~2/3 name risk as the top blocker; only ~30% call themselves governance-ready), and **EU AI Act Article 14** makes _effective_ human oversight a dated legal requirement for high-risk AI (in force 2 Aug 2026). The word that matters in Art. 14 is _effective_ — a rubber-stamp is not oversight, and an auditor (or a regulator) will not accept "the director clicked approve on all 500" as evidence a human was meaningfully in control. Batch-with-sampling, exception-surfacing, confidence-ranked queues, and the rubber-stamp meta-watch are the structural answer to the strongest attack on the entire oversight thesis: they keep the human genuinely steering as agent volume scales, which is the one thing that turns "we deployed agents" into "we deployed agents _we can defend_."
