# Sequor — Feasibility Summary

**Date:** 29 April 2026 (updated)
**Original:** 20 April 2026
**Status:** Pre-build feasibility analysis — refined product design
**Viability:** 7/10 (up from initial assessment; dependent on market validation)

---

## 1. The Product

**[Product name TBD]** is the **coverage layer for every team**.

It reads incoming messages across WhatsApp and email, classifies them by type and urgency, resolves routine queries using a knowledge base that grows smarter over time, and routes everything else to the right person — without anyone having to be everywhere.

**Positioning:** "Your team handles more. Without hiring."

The product runs through the company's existing email inbox — no separate app required. Employees receive escalations as structured emails, reply to resolve, and the AI learns from every human answer.

---

## 2. Key Design Decisions (Refined)

The product design was refined through analysis and challenge sessions. Key changes from the original concept:

### Account-Based Model (Not Per-Seat)

The product is organized around **accounts** — communication points the company wants covered. A solo operator has one account. A firm might have three (secretary, HR, operations). Each account independently configures its channels, routing rules, and escalation chain.

### Email-First, No App

The entire product interface is email. No separate app, no dashboard, no new platform to toggle between. Employees interact with the product through their existing inbox:

- Unresolved items arrive as structured emails
- Replying to the email sends the response to the client
- Ignoring the email triggers auto-escalation to the backup contact
- Daily digest and weekly recap emails summarize activity

### Company WhatsApp Number (Not Personal)

WhatsApp uses a company-owned Business API number, not individual employees' personal phones. Clients message the company number. Employees never connect their personal WhatsApp. This keeps personal phones personal and gives the company a professional client-facing presence.

### Flexible Channel Choice

Each account chooses its channels: email only, WhatsApp only, or both. A solo consultant can start with email only and add WhatsApp later. No channel is mandatory.

### Learning from Human Answers

The AI doesn't depend on pre-uploaded documents. Every time a human resolves an escalation, that answer is captured and added to the knowledge base. The product gets smarter with every interaction — no upfront document preparation required.

### 24-Hour WhatsApp Window Is Manageable

The WhatsApp 24-hour session window is not a roadblock. The AI responds within minutes for queries it can answer. For queries it cannot answer, an automated template message acknowledges receipt within the window. The human follows up when available. Traceability is maintained in the product's internal system regardless of WhatsApp session state.

---

## 3. The Target Market

**First beachhead: Professional services firms**

Accountants, consultants, freelance professionals, and small advisory practices across Southeast Asia.

Why they are the ideal first users:

- They bill by the hour — every minute not spent on inbox admin is directly billable time. ROI is measurable in dollars.
- They run lean teams of 3–10 people — no spare capacity to absorb inbound volume.
- Client communication is the product — missed follow-ups are directly revenue-adjacent.
- They already use WhatsApp and email as primary client channels — no workflow change required.
- Email-first design fits their existing habits — no new tool adoption required.

**Horizontal expansion** follows: customer service, HR, operations, sales — same problem, new departments.

**Pricing:**

| Tier         | Price            | Accounts  | Channels          | RAG                          | Retention |
| ------------ | ---------------- | --------- | ----------------- | ---------------------------- | --------- |
| Free         | S$0              | 1         | Email only        | None                         | 7 days    |
| Starter      | S$20/acct/month  | 1         | Email OR WhatsApp | Auto-reply + learning loop   | 90 days   |
| Professional | S$60/acct/month  | Up to 5   | Both              | Full RAG + confidence badges | 12 months |
| Enterprise   | S$200/acct/month | Unlimited | Both              | Priority RAG + PDPA report   | 24 months |

Document cleanup service: S$300–500 one-time (optional accelerator; not required).

---

## 4. Differentiation from Competitors

No existing product provides complete coverage. The product differentiates on three levels:

### vs. General Automation Tools (OpenClaw, etc.)

OpenClaw automates personal WhatsApp — it's a tool for power users. This product is a company's communication coverage layer:

- Company-owned accounts (not individual WhatsApp)
- Multi-channel with flexible choice per account
- Email-first — no new app to learn
- Learning loop that gets smarter with every human answer
- Escalation routing with auto-escalation
- PDPA compliance and audit trails
- Purpose-built for coverage, not general automation

### vs. Email/AI Tools (Superhuman, Spark, Gmail AI)

These tools help individuals process email faster. They still require the person to be at their inbox. This product handles communication when the person isn't available — that's a fundamentally different value proposition.

### vs. Auto-Reply Tools (WhatsApp Business auto-replies)

Auto-replies acknowledge. They don't resolve. This product reads the message, classifies it, attempts to answer from the knowledge base, and only escalates what it can't handle. The client gets a real answer, not a "we'll get back to you."

---

## 5. Feasibility Scores (Updated)

| Dimension             | Score       | Key Driver                                                        | Change                      |
| --------------------- | ----------- | ----------------------------------------------------------------- | --------------------------- |
| Problem urgency       | 9/10        | Coverage gap — structural, not personal                           | Unchanged                   |
| Market size           | 8/10        | Professional services as defined beachhead                        | Unchanged                   |
| Competitive moat      | 7/10        | Learning loop + account model — defensible but not unassailable   | Down from 8 (honesty)       |
| Technical feasibility | 8/10        | Email-first reduces platform risk; learning loop reduces doc risk | Unchanged                   |
| Unit economics        | 7/10        | Per-account model works; email-only free tier is low-cost         | Down from 8 (honesty)       |
| GTM clarity           | 8/10        | "Coverage in your inbox" — simple, no new app to explain          | Down from 9 (honesty)       |
| Regulatory complexity | 8/10        | PDPA designed in; WhatsApp compliance spec'd                      | Unchanged                   |
| **Overall**           | **~7.5/10** |                                                                   | **Down from 8.5 (honesty)** |

The overall score reflects a structurally sound concept with genuine differentiation, but the core commercial question — will people pay for this? — remains unvalidated by real market data.

---

## 6. Resolved Roadblocks

The following were initially flagged as roadblocks and resolved through analysis:

| Roadblock                      | Resolution                                                                                    |
| ------------------------------ | --------------------------------------------------------------------------------------------- |
| WhatsApp 24-hour window        | Not a roadblock — AI responds fast, template messages cover the gap, traceability is internal |
| No differentiation vs OpenClaw | Different product category — company coverage layer vs individual automation tool             |
| Low AI adoption (4%)           | Market creation through sales/government support; email-first removes AI adoption barrier     |
| Internal documents assumption  | Learning loop removes dependency — AI learns from human answers, no upfront docs required     |

---

## 7. Remaining Risks

| Risk                              | Severity | Mitigation                                                                |
| --------------------------------- | -------- | ------------------------------------------------------------------------- |
| Market validation incomplete      | High     | Talk to 10 firms; validate pain and willingness to pay                    |
| AI accuracy on real queries       | High     | RAG validation gate with real documents before build                      |
| Learning loop quality             | Medium   | Human answers need review; weekly digest flags low-quality                |
| Big tech embedding AI in email    | Medium   | Gmail/Outlook AI helps respond faster, but doesn't cover when you're away |
| Channel partner model unvalidated | Medium   | Need committed partnership before scaling                                 |

---

## 8. Open Items

1. **Market validation**: Talk to 10 professional services firms. Not "would you buy?" — ask them to show yesterday's inbox and point to messages that could have been handled without them.
2. **RAG validation gate**: Test AI on real SME documents (not clean test data). 2–3 weeks, 5–10 firms.
3. **WhatsApp legal review**: Five compliance items require confirmation with BSP or legal counsel.
4. **Channel partner**: No committed partnership yet. Need to validate GTM path.
5. **Learning loop validation**: Test whether human answers produce usable knowledge base entries in practice.

---

## 9. Recommended Next Steps

1. **Market validation interviews** — 10 firms, show the email-first flow, validate pain
2. **WhatsApp legal review** — Confirm compliance items with BSP
3. **RAG validation gate** — 2–3 weeks with real documents; go/no-go on build
4. **Channel partner conversation** — Capital and GTM validation

---

_This document was updated on 29 April 2026 to reflect refined product design. The concept is structurally sound (~7.5/10) with genuine differentiation. The next required step is market validation before any build decision is made._
