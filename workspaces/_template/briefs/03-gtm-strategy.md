# GTM Strategy Brief

**Date:** 2026-05-08
**Status:** Draft — for team review

---

## 1. ICP (Ideal Customer Profile)

### Primary ICP: Small Professional Services Firms

**Definition:** 3–10 person firms in Singapore / SEA that bill by the hour, use WhatsApp + email as primary client channels, and have at least one person in a client-facing role who spends meaningful time in meetings.

**Firmographic criteria:**

- Headcount: 3–10 operators
- Industry: Accounting firms, management consultants, legal practices, financial advisors, HR consultancies, marketing agencies
- Channels: WhatsApp Business + email as client-facing channels (non-negotiable)
- Tech maturity: Uses Google Workspace or Microsoft 365, has at least one shared inbox or team email
- PDPA-aware: Already handling or considering PDPA compliance (or will need to before scale)
- Existing tools: WhatsApp personal or Business, Gmail/Outlook, potentially a CRM (HubSpot, Zoho, Salesforce)

**Who NOT to sell to:**

- Startups with < 3 people (TOFU is too wide, support cost is too high)
- Companies with < 50 WhatsApp messages/week (no felt pain, churn risk)
- Regulated verticals without SOC 2 (medical, legal during active matters) — avoid until certification
- Enterprises (> 50 seats) — product is not ready for enterprise complexity

**Why this ICP:**
Every hour not spent on inbox admin is directly billable time. The ROI story is quantifiable in dollars, not estimates. They feel the pain immediately. And they have a known decision-maker (the partner / director) who can say yes without a committee.

---

## 2. Beachhead Segment

**Go narrow before wide.** The first beachhead within professional services:

### Phase 1 (Months 1–6): Accounting Practices in Singapore

**Why accounting?**

- High message volume — clients send statements, queries, deadline reminders daily
- Clear compliance obligation (PDPA + ACRA) — audit trail is a selling point, not a nice-to-have
- Seasonal spikes (tax season) that expose coverage gaps most acutely
- Existing use of practice management software means they understand digital tools
- Referrals within the industry are fast — one partner tells three others

**Profile of first lighthouse customer:**

- 5–8 person firm in Singapore (CBD or Ubi area)
- Uses WhatsApp for client communication
- Has a practice manager or senior secretary who triages messages
- Has documents: fee schedules, ACRA deadline calendars, engagement letters, FAQ documents
- Willing to be a reference customer in exchange for discount

**Phase 2 (Months 6–12): Management Consultants and Legal Practices**

- Similar pain profile, same channels
- Legal adds urgency around confidentiality (PDPA + legal privilege) — doubles as a compliance story
- Referrals to related professional services are fast

**Phase 3 (Months 12+): Financial Advisors, HR Consultancies, Marketing Agencies**

---

## 3. Pricing & Packaging for Launch

### Launch Pricing (Q2–Q3 2026)

| Tier        | Price    | Seats | Messages  | Channels | RAG               | Audit     | Notes                                          |
| ----------- | -------- | ----- | --------- | -------- | ----------------- | --------- | ---------------------------------------------- |
| **Free**    | $0       | 1     | 50/mo     | Both     | Yes               | 30 days   | No credit card. Converges curious users.       |
| **Solo**    | $15/mo   | 1     | 200/mo    | Both     | Yes               | 30 days   | Default landing for inbound inquiries.         |
| **Starter** | $35/seat | 3–5   | Unlimited | Both     | Yes               | 90 days   | **Core launch tier.** Default for small firms. |
| **Pro**     | $55/seat | 5+    | Unlimited | Both     | Yes + custom maps | 12 months | Upsell when team grows.                        |

### Launch Offer

**3 months free on Starter** for the first 20 paying customers, in exchange for:

1. A 15-minute monthly feedback call (usability, product, pricing)
2. Permission to use as a case study / reference
3. A LinkedIn testimonial (if satisfied)

This is not a discount — it is a structured discovery program disguised as a launch offer. Every conversation generates learning. The customers feel they got a good deal. We get validation data.

### Document Cleanup as a Service

One-time $300 engagement at onboarding. Mandatory for Starter/Pro if documents are not RAG-ready. This is a revenue line and a product quality gate — it ensures RAG quality is high from day 1, which drives the learning loop.

---

## 4. Channel Strategy

### Tier 1: Direct Sales (Primary — Months 1–12)

**What:** One-to-one outreach to decision-makers at target firms.
**Who does it:** Founder-led sales initially (credibility, no headcount cost).
**Tactics:**

- LinkedIn outreach to partners / directors at accounting and consulting firms in Singapore
- Subject line: specific to their industry ("Accounting practice coverage gap" vs generic "AI tool")
- Body: 3–4 sentences. Problem statement. Ask for 15-min call. No deck unless asked.
- Follow up twice over 3 weeks. Then stop.
- Target: 3 outreach threads per day → 1 qualified call per week

**Why founder-led:** At this stage, the product story is the founder's story. A rep reading a script loses the nuance that makes this compelling. The lighthouse customer conversation is a product discovery conversation as much as a sales conversation.

### Tier 2: Channel Partners (Starting Month 6)

**What:** Accountants, business consultants, and SME advisors sell Sequor alongside their existing services.
**Why:** These partners already have the trust relationship with the buyer. CAC drops to $50–100 vs $500–1,500 for direct sales. They are recommending a solution to a problem they already understand.
**Revenue share:** 20% recurring for the life of the customer.
**Who specifically:**

- SME business consultants (Singapore has ~3,000 registered business advisory firms)
- Accounting firms that offer IT/advisory services as a sideline
- HR consultancy firms targeting SMEs

### Tier 3: Product-Led Growth (Starting Month 9)

**What:** Free tier converts to paid through in-product prompts.
**Tactics:**

- In-portal prompt at 40 messages/month: "You've used 40 of 50 free messages. Upgrade to Solo for $15/month to keep the AI running uninterrupted."
- At 150 messages: "Your team is growing. Starter at $35/seat gives unlimited messages and smart escalations."
- Document Hub prompts: "RAG quality is low — 5 of your 20 docs need cleaning. Add document cleanup for $300 and improve auto-reply accuracy by ~30%."
- Trial prompts: "Upgrade to Starter free for 30 days. No credit card."

### Tier 4: Content / SEO (Ongoing)

**What:** Write about the problem Sequor solves.
**Topics:**

- "How accounting firms in Singapore handle OOO coverage"
- "The PDPA audit trail every WhatsApp Business account needs"
- "Why your consultant is missing client messages during tax season"
- "The real cost of coverage gaps in professional services"
  **Goal:** Own the search term "WhatsApp coverage for professional services Singapore" and similar long-tail queries.

---

## 5. Lighthouse Customer Plan

### Target Profile (First 5 Customers)

1. **5–8 person firm**, Singapore-based, professional services
2. **High WhatsApp volume**: > 30 client messages per day across the team
3. **Clear coverage gap**: Someone triages messages manually, or messages fall through when the primary is in meetings
4. **Documents exist**: At least a FAQ or fee schedule in digital form (PDF, Google Doc, Notion)
5. **Willing to be a reference**: Recognizes the problem is real and wants to help solve it
6. **PDPA-aware**: Already thinks about data handling

### Acquisition Steps

1. **Identify**: Use LinkedIn Sales Navigator to find 5–8 person accounting/consulting firms in Singapore with active WhatsApp Business presence (publicly visible WhatsApp Business number on their website = indicator of high-volume usage).

2. **Research**: Before outreach, spend 10 minutes on their website. Note: what services they offer, whether they mention PDPA compliance, what their client communication style looks like (formal/informal), whether they have a blog (shows they invest in client communication).

3. **Outreach**: Personalized. Not "I noticed your firm." Something specific to what you found. E.g., "I saw you handle tax deadline season for clients — how do you manage client queries when the whole team is working OOO?" This is a real question, not a pitch. 80% response rate if the problem resonates.

4. **Discovery call (30 min)**:
   - Q1: "Walk me through what happens when a client sends you a message and you're in a meeting."
   - Q2: "How many messages do you get on a busy day? Who triages them?"
   - Q3: "When a message slips through and a client follows up — what does that cost you?"
   - Q4: "If I told you that in 3 weeks you could have the AI reading those messages and drafting responses for your review — what would that be worth to you?"
   - Close: "Would you be open to trying it with your team for 30 days, free, if I could show you it working on your actual WhatsApp?"

5. **Onboarding (1 week)**:
   - Day 1: Connect WhatsApp (15 min)
   - Day 2: Connect email + upload documents
   - Day 3: Configure escalation rules
   - Day 4–5: Run first real messages through
   - Day 6: Review first AI drafts. Get operator feedback.
   - Day 7: Retune thresholds based on real corrections.

6. **Week 2: First checkpoint call** — What worked? What didn't? What does the AI still get wrong? Retune.

7. **Week 4: Review call** — Quantify: how many messages auto-replied? How many escalations? Time saved? Ask for a LinkedIn testimonial and referral.

---

## 6. First 90 Days Execution Plan

| Week  | Focus                                                                   |
| ----- | ----------------------------------------------------------------------- |
| 1–2   | LinkedIn outreach: 3 threads/day → 5 discovery calls booked             |
| 3–4   | 3 discovery calls → 2 lighthouse customers onboarded                    |
| 5–6   | Lighthouse customers live. First feedback calls.                        |
| 7–8   | Document learning loop: what corrections are happening? Retune.         |
| 9–10  | 2 more lighthouse customers. Refine messaging based on real objections. |
| 11–12 | First case study written. Partner referral program launched.            |
| 13+   | Channel partner outreach begins. PLG flow built in-product.             |

---

## 7. Open Questions (Need Discovery to Answer)

- [ ] What is the realistic CAC for direct outreach in professional services? ($500? $1,000?)
- [ ] What is the conversion rate from discovery call to trial? (10%? 30%?)
- [ ] Do accounting firms in Singapore already have documents in digital form, or is the cleanup service a hard requirement before onboarding?
- [ ] What is the minimum message volume that predicts a paying customer? (< 30/day = low urgency = churn risk)
- [ ] At what seat count does the "Starter" tier feel too small?
