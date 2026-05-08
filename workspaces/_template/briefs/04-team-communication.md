# Team Communication Feature Spec

**Date:** 2026-05-08
**Status:** Draft — for team review
**Scope:** Operator-side collaboration + customer-facing AI reply quality

---

## Overview

Sequor serves two audiences simultaneously: the **operators** (the business's team using the portal to manage coverage) and the **customers** (the end clients sending messages via WhatsApp and email). Strong team communication features make the operator's job efficient and clear. High-quality AI replies make the customer's experience feel responsive, not robotic. Both sides need to be designed together.

---

## PART 1 — OPERATOR-SIDE: TEAM COLLABORATION

### Why This Matters for GTM

The GTM strategy targets 3–10 person professional services teams. In a 5-person accounting firm, coverage is handled by a practice manager, a senior secretary, and maybe one partner. These teams already have tool overload. If Sequor adds complexity instead of removing it, they churn. The portal must make collaboration feel effortless — not like a second job.

---

### 1.1 Operator Identity & Presence

**What:**
Each team member gets an operator account tied to their email. Operators are invited by the account owner (the first user who set up the account).

**Fields per operator:**

- Name, email, role (Owner / Admin / Operator)
- Notification preferences (email / in-portal / both)
- "Last seen" timestamp (visible to other operators on the same account)

**Access levels:**
| Role | Can do |
|------|--------|
| Owner | Everything + billing + delete account |
| Admin | Everything except billing |
| Operator | View assigned escalations, resolve threads, add notes, adjust own notification settings |

**Presence indicator:**

- Green dot = online (any portal action in last 5 min)
- Yellow = idle (no action in 30 min)
- Gray = offline
- Visible on escalation cards: "Assigned to: Jane (Online)"

---

### 1.2 Escalation Assignment & Reassignment

**What:**
When a message escalates, it is assigned to the configured backup contact (an operator on the account). Operators can reassign escalations to another operator.

**Assignment rules:**

1. **Default**: Assigned to the configured backup contact for the contact tier (VIP → senior operator, standard → any available operator)
2. **Manual**: Any operator can reassign to any other operator on the account
3. **Auto-balance** (future): SLA-breach-risk escalations auto-reassign to the least-loaded available operator

**Reassignment UX:**

- On the escalation detail page: dropdown showing all operators on the account
- Reassignment logs the reassignor's name, timestamp, and reason (optional free-text)
- Notification sent to the new assignee: "Escalation #1234 reassigned to you by [Name]"

**UI placement:**

- Escalation card: "Assigned to: [Name] [Reassign ↓]"
- Escalation detail page: prominent operator selector at the top

---

### 1.3 SLA Countdown & Timers

**What:**
Every escalation has a visible SLA countdown. Operators know at a glance how much time is left before a breach.

**SLA configuration (per account):**

- Default SLA window: configurable (e.g., 4 hours for standard, 1 hour for VIP)
- VIP contacts get a shorter SLA by default
- Custom SLA rules per contact tier

**SLA states:**
| State | Visual | Behavior |
|-------|--------|----------|
| Healthy | Green timer | > 50% of SLA window remaining |
| Warning | Amber timer | 25–50% remaining — notification to assignee |
| Critical | Red timer | < 25% remaining — notification to all operators |
| Breached | Red + "SLA BREACHED" | Timer turns red, escalation marked breached |

**Breach notification:**

- At 25%: in-portal notification to assigned operator + email if enabled
- At breach: all operators on the account notified

---

### 1.4 Thread Notes (Internal Collaboration)

**What:**
Operators can add internal notes to any escalation thread. These notes are visible only to operators on the same account — never to the customer.

**Use cases:**

- "Jane already called this client about the same issue — do not escalate further"
- "Customer is the managing partner's sister — treat as VIP"
- "Confirmed verbally: this invoice has been paid, draft response accordingly"

**UX:**

- "Add note" button on the escalation detail page
- Notes appear in a collapsible thread below the customer messages
- Each note shows: operator name, timestamp, content
- Notes are permanent (not deleted) and logged in the audit trail

**Why permanent + logged:**
If the same escalation is used in a dispute or PDPA audit, the internal notes provide context for why a decision was made.

---

### 1.5 Escalation Status Workflow

**Status states:**
| Status | Meaning | Who can set |
|--------|---------|-------------|
| Open | New escalation, assigned, awaiting resolution | Any operator |
| In Progress | Operator is actively working it | Assigned operator |
| Waiting on Customer | Operator sent a reply, waiting for customer response | Assigned operator |
| Resolved | Customer issue handled, thread closed | Assigned operator |
| Closed | Thread archived (no further action needed) | Any operator |

**Transitions:**

- Resolved → can be reopened by any operator within 48 hours
- Closed → permanent (only Owner can reopen)

**Bulk actions (escalations list):**

- Select multiple escalations → Mark as Resolved / Reassign / Add Tag
- Filter by: status, operator, SLA state, contact tier, date range

---

### 1.6 Operator Notifications

**What:**
Operators get notified when something needs their attention.

**Notification channels:**

- In-portal: bell icon in topbar, red badge with unread count
- Email: digest (every 30 min) or real-time, per operator preference

**Notification triggers:**
| Event | Recipients |
|-------|-----------|
| New escalation assigned | Assigned operator |
| SLA warning (25% remaining) | Assigned operator |
| SLA breach | All operators on account |
| Escalation reassigned | New assignee |
| New customer reply (Waiting on Customer) | Assigned operator |
| AI draft ready for review (medium confidence) | Assigned operator |
| Document quality degraded | Account Owner |

**Notification preferences (per operator):**

- Real-time email for SLA breaches only
- Digest email for all other events
- In-portal notifications: all events

---

### 1.7 Message Status & Read Tracking

**What:**
Operators can see which escalations are unread, which have been read by whom.

**Message states on escalation list:**
| State | Badge |
|--------|-------|
| Unread (new escalation) | Bold text + blue dot |
| Unread by assigned operator | Bold assigned operator name |
| Read by all operators | Normal text |
| Resolved | Muted text |

**Read receipts (internal, not shown to customer):**

- Each operator's "last read" timestamp shown on the escalation detail page
- "Jane read this 3 min ago" visible to other operators

---

## PART 2 — CUSTOMER-FACING: AI REPLY QUALITY

### Why This Matters

The customer's experience is the product. If the AI reply sounds like a robot wrote it, the customer feels they're being handled by a machine — which breaks trust. If it sounds natural, warm, and helpful, the customer doesn't think about the AI at all. That's the goal.

---

### 2.1 RAG-Grounded Answers with Citations

**What:**
Every AI-drafted reply must be grounded in a specific document chunk from the business's Document Hub. The customer should feel the reply is accurate and specific to the business — not a generic AI hallucination.

**UX for the customer:**

- Reply reads as a natural response ("Hi! Yes, our workshop on Saturday is confirmed — here's the schedule...")
- No mention of "RAG", "AI", or "confidence" in the customer-facing reply

**Citation display (operator view only):**

- On the AI draft preview: "Grounded in: Fee Schedule 2026.pdf — Section 3, line 12"
- Operator can click to expand and see the full source chunk

**Fallback behavior:**

- If no chunks are retrieved (low retrieval score): draft is not auto-generated
- Instead: escalation is triggered with reason "No document match — routing to operator"
- Customer receives a human response within the SLA window

---

### 2.2 Confidence Badges (Operator-Facing)

**What:**
Each AI draft carries a confidence badge — visible only to operators, not customers.

**Confidence bands:**
| Badge | Score | Meaning | Behavior |
|-------|-------|---------|----------|
| 🟢 High | > 90% | RAG retrieval + drafting both strong | Auto-send enabled |
| 🟡 Medium | 60–90% | Retrieval or drafting uncertain | Operator must approve before send |
| 🔴 Low | < 60% | Retrieval failed or drafting uncertain | Never auto-sent. Escalate. |

**Why visible to operators only:**
Customers don't need to know the AI's confidence. If a customer sees "🤖 AI confidence: 67% — please review", they feel like they're testing a beta product. The operator reviews, edits if needed, and sends — the customer just sees a good reply.

---

### 2.3 Reply Tone & Language

**What:**
AI drafts must match the business's voice — not generic corporate speak.

**Tone configuration (per account):**

- **Formal**: "Dear [Name], Thank you for your inquiry. We will respond within..."
- **Friendly**: "Hi [Name]! Got your message — here's what I found..."
- **Professional but warm** (default): "Hi [Name], Thanks for reaching out. Here's what I can confirm..."

**How it works:**
The business's tone preference is set in Settings. This is passed to the LLM as a system prompt preamble. The tone applies to: auto-sent replies, AI drafts for review, escalation context summaries.

**Language:**

- Default: English (for Singapore market)
- Future: Bahasa, Thai, Vietnamese — configurable per contact

---

### 2.4 WhatsApp Template Messages (OOO Windows)

**What:**
When a primary operator is OOO and the AI can't auto-resolve, a pre-approved WhatsApp template message is sent to the customer within the 24-hour WhatsApp window.

**Pre-approved templates (configured at onboarding):**

1. **Acknowledgement**: "Hi! We've received your message and our team is looking into it. We'll respond fully within [timeframe]."
2. **OOO Notice**: "[Name] is currently out of office. Your message has been noted and our team will follow up by [date]."
3. **Escalation Notice**: "Your message has been forwarded to [Backup Name]. They'll respond within [timeframe]."

**Why pre-approved:**
WhatsApp requires template message strings to be pre-approved by Meta before they can be sent outside the 24-hour session window. This is a Meta policy requirement. Template approval takes 24–48 hours per template and is a one-time onboarding cost.

---

### 2.5 Customer Escalation Notification

**What:**
When an escalation is created and assigned, the customer receives a notification — so they know their message has been received and is being handled.

**WhatsApp:**

- If within 24-hour window: direct reply via WhatsApp API
- If outside window: escalation notification template sent

**Email:**

- Auto-reply email triggered at escalation creation:
  Subject: "We've received your message — [#XXXX]"
  Body: "[Name] has been notified and will respond within [SLA window]."

---

### 2.6 Branded Reply Footer

**What:**
Every auto-sent reply includes a consistent footer that maintains brand presence without being intrusive.

**Default footer:**

```
Sent by [Business Name] via Sequor
[Business Address] | [Phone Number]
This message was sent by our AI assistant. If you'd prefer to speak with a human, reply to this message.
```

**Customisation:**

- Footer text configurable in Settings
- Business name, address, phone pulled from account settings
- "Sent by our AI assistant" note is optional — recommended for transparency

---

### 2.7 Customer Feedback on AI Replies

**What:**
Customers can flag AI replies that were incorrect or unhelpful. This feeds the learning loop directly.

**How it works:**

- On WhatsApp/email: after the AI reply, a follow-up message asks: "Was this helpful? Reply YES or NO"
- If NO: the thread is flagged for operator review + the correction is logged to the learning loop
- Operators see a "Customer feedback: negative" badge on the thread

**Why this matters:**
Currently the learning loop only captures operator corrections. Customer feedback adds a second signal — the customer's perception of quality, not just the operator's correction of it.

---

## PART 3 — OPEN QUESTIONS FOR DISCOVERY

- [ ] What is the realistic number of operators per Starter account? (3–5 seats — do all 5 actively use it, or 1–2 power users + rest passive?)
- [ ] Do accounting firms want internal thread notes, or is that too "ticketing system-y" for their culture?
- [ ] What percentage of customers will respond to "Reply YES/NO" feedback prompts? (Industry average: 5–15%)
- [ ] Do customers in Singapore prefer WhatsApp notifications for escalations, or email?
- [ ] Should AI reply tone be configurable per contact (VIP gets formal, standard gets friendly)?
