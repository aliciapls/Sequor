# R6 — Prove it: the audit / compliance export

> Value principles embodied: P3 (governance is the product, priced as compliance), P4 (meaningful oversight at scale), P7 (undo + trace = the trust surface), P1 (integrate-and-govern, never replace). Wedge: compliance-driven enterprise (the compliance-tier SKU).

This is the flow that turns everything the director does in R5 into something they can hand to a regulator. It is the compliance-tier SKU — the budget line carried by the EU AI Act deadline. The director (or their compliance owner) produces an **audit bundle**: for every agent action, the named human who approved it, the posture (rules) in force at the time, the data it touched, and the outcome — packaged as plain-language evidence that a human was meaningfully overseeing high-risk AI, the way Article 14 requires.

## The walk (from the director's / compliance owner's screen)

Meet **Omar**, the compliance owner. His company's board has asked him to prove, before an external audit next month, that the AI agents running in customer operations are under genuine human control. He is not technical. He opens Sequor.

1. **Omar clicks "Create audit bundle."** He is asked three plain questions, no jargon: _which time period?_ (he picks last quarter), _which systems and agents?_ (he picks "all customer-operations agents, all systems"), and _what's this for?_ (he picks "EU AI Act Article 14 — human oversight evidence" from a short list). He clicks **Generate.**

2. **Sequor assembles the bundle and shows him a plain-language summary first.** Before any document downloads, Omar sees a readable cover page:

   > **Audit bundle — Customer Operations agents — Q3**
   > 12,480 agent actions across Salesforce, the billing system, ticketing, and email.
   > Of these: **11,902 ran automatically** under rules a named director set beforehand; **578 were held and decided by a named human**; **0 ran with no rule in force.**
   > **41 refunds over $500** — every one approved by a named director, with a recorded reason.
   > **3 emergency overrides** — each granted by a named senior approver, time-limited, and auto-reviewed within 7 days.
   > Every action below traces to: the human accountable, the rule in force, the data touched, and the result.

   Omar can read this and understand it. That is the point — the export is legible to a compliance officer, not only to an engineer.

3. **He drills into one action to see the full lineage.** He clicks the $2,400 Acme refund from R5. Sequor shows the complete chain in plain language:

   > **Action:** Issue refund to Acme Corp.
   > **What the agent proposed:** refund $2,400 · **Confidence:** low (58%), contract terms flagged ambiguous.
   > **Rule in force at that moment:** "Step through with me" (pause-and-approve) for refunds; auto-approve limit $500 — set by Director Dana R. on 12 June, cryptographically recorded.
   > **Held because:** $2,400 exceeded the $500 limit.
   > **Decided by:** Director Dana R. (named, authenticated) — **Rejected**, reason: _"contract caps refunds at $1,000 — re-issue at that amount."_
   > **Re-planned action:** refund $1,000 — approved by Dana R.
   > **Data touched:** Acme account (Salesforce, read + write), billing system (credit issued), one email to the customer.
   > **Outcome:** $1,000 credit issued 14:22; customer notified 14:23.
   > **Tamper-evidence:** this record is part of a signed chain; altering it would break the chain and be detectable.

   This is one action → one named human → the posture in force → the data touched → the outcome. Multiply it by 12,480 and that is the bundle.

4. **Omar chooses the export format for his audience.** Sequor offers: a **plain-language PDF report** (for the board and the auditor — the readable narrative above), a **structured data file** (for the auditor's own tooling to query), and a **cross-system view** that shows the same actions grouped by which system of record they touched (Salesforce vs billing vs ticketing vs email) — because his auditor will ask "what did the AI do inside _each_ of our systems?" He exports all three.

5. **He hands the bundle to the external auditor.** The auditor opens it and can independently check three things without Omar in the room: (a) every high-risk action names a real, authenticated human who approved it; (b) the rules those humans set were in force _before_ the actions ran, not written afterward (the signed timestamps prove ordering); and (c) the records have not been edited (the tamper-evident chain). The auditor is not asked to trust Sequor's word — the cryptographic chain lets them verify.

6. **Omar sees the honest boundary, stated plainly.** The bundle's cover page carries a truthful caveat Sequor does not hide: _"This bundle proves **traceability** — that every action is tied to a named human authority, the rule in force, and the data touched, in a tamper-evident record. It cannot prove a human fully **understood** each decision; that judgment remains the accountable human's. Article 14 obligations bind **high-risk** AI systems specifically — your compliance owner should confirm which of these workflows are classified high-risk."_ Omar would rather show the auditor this line than have the auditor find the gap themselves.

Omar walks into the audit with a bundle a non-technical board member can read, an auditor can independently verify, and a regulator's Article 14 checklist can be mapped against — without anyone writing a line of code.

## Features exercised

- **One-click audit bundle generation** — period + scope + purpose, in three plain questions.
- **Plain-language compliance summary** — a readable cover page (totals, held-vs-auto, high-value actions, overrides) before any raw data.
- **Per-action accountability lineage** — action → agent's proposal + confidence → rule in force → named human decision + reason → data touched → outcome, rendered in plain language.
- **Posture-in-force provenance** — the signed record that the governing rule was set _before_ the action ran, by a named human, with ordering provable by timestamp.
- **Tamper-evident signed chain** — hash-linked, signed records the auditor can independently verify were not altered.
- **Emergency-override audit trail** — every "break glass" expansion: who, which tier, time-limited, with a forced 7-day review.
- **Multiple export formats** — plain-language PDF (board/auditor), structured data (auditor tooling), cross-system view (per system of record).
- **The honesty caveat** — traceability-not-accountability + the Art. 14-binds-high-risk-specifically flag, stated on the bundle, not buried.

## Deliverables / artifacts produced

- **The exportable audit bundle itself** — the compliance-tier deliverable: a self-contained, plain-language + structured package covering every agent action in scope with full accountability lineage.
- **An EU AI Act Article 14 evidence mapping** — the bundle organized so each Art. 14 human-oversight requirement (a named human can understand, oversee, intervene, and override) maps to concrete records in the bundle.
- **A per-action lineage record** — reusable outside the bundle (e.g., to answer a single "who approved this?" question in a dispute).
- **A cross-system audit view** — the same evidence sliced by system of record, so an auditor can inspect "what the AI did inside Salesforce / billing / ticketing / email" independently.
- **A verifiable-integrity certificate** — the signed-chain summary that lets a third party confirm the records were not edited after the fact.

## Reuse → net-new

**Shipped substrate reused:** every governance record already exists as PACT DataFlow models — `AgenticObjective`, `AgenticDecision` (the human-judgment point, with `reason_held`, `constraint_dimension`, `envelope_version`, approver fields), `ApprovalRecord` (one approver's vote), `AgenticWorkSession` (cost + provider + verdicts), `AgenticArtifact` (versioned outputs). The `TieredAuditDispatcher` already routes actions to durable storage; `EmergencyBypass` already leaves a fail-closed, mandatory-review audit trail. The **aegis signed posture-transition anchors** (SHA-256 `record_hash` + Ed25519 `signature` + `parent_anchor_id` hash-chain) are the tamper-evidence — every posture change is already attributable, ordered, and tamper-evident. EATP's signing primitives (`generate_keypair` / `sign` / `verify_signature`) produce the verifiable chain. loom's governed distribution is the pattern for packaging a bundle to cross an org boundary safely. **Net-new:** the **EU AI Act Art. 14 export mapping** (assembling the shipped records into a regulator-shaped evidence bundle); the **plain-language compliance renderer** (turning `constraint_dimension=financial, envelope_version=…` into a board-readable narrative + the honest traceability caveat); the **cross-system audit view** that unifies records by system of record; and the **one-click bundle-generation UX** for a non-technical compliance owner.

## Why it matters (grounded)

**EU AI Act Article 14** legally requires _effective human oversight_ of high-risk AI, with high-risk obligations in force from **2 August 2026** — a hard, dated tailwind, not a nice-to-have. The whole market gap is that agents "can" act but no one "can prove to a regulator/auditor what they did and who approved it" (the #1-barrier finding: ~2/3 of enterprises cite risk/governance as the top blocker to scaling agents). This flow is the product's answer priced as **compliance (P3)** — the audit/oversight export as its own SKU carried by the deadline. It ships **traceability** honestly (the caveat is stated, per the spec's load-bearing traceability-not-accountability boundary) and flags that Art. 14 binds high-risk systems specifically — because over-claiming compliance is legally hazardous, and honesty is the differentiation against "agent-washing" vendors in a market where Gartner expects >40% of agentic projects cancelled by 2027, mostly for inadequate control.
