# Sequor — Product Feasibility Analysis

**Date:** 2026-04-19
**Source:** Three independent analysis agents (Problem/Market, Technical Feasibility, Business Model) + red team audit + brief traceability review

---

## Verdict: Proceed to Validation, Not Yet to Build

The Sequor has a coherent concept and at least one genuine market gap. However, three agents working independently identified the same structural problem: **the product concept conflates "a gap exists" with "a business can be built on that gap."** These are different questions requiring different evidence.

The product has five hard constraints that cannot be resolved in implementation — they must be resolved in discovery first.

---

## Part 1: Problem & Market Analysis

### 1.1 Problem Validation

**The core analogy: an AI secretary. The pain: not having one.**

Every knowledge worker has a shared experience: a 3-minute message arrives that requires looking something up, switching between three platforms, and composing a reply. By the time it's done, 45 minutes of focused work is gone. This happens 5–10 times a day. The day is gone before it started.

The problem is not new. The reason most knowledge workers don't have a solution is simple: a human secretary costs $2,000–5,000/month and is out of reach for lean teams, SMEs, nonprofits, and even individuals inside larger orgs. The pain is universal but the solution has been accessible only to large enterprises.

**What this product is:** An AI secretary — not an assistant that surfaces information, drafts replies, or organizes your inbox. A secretary that handles the work. It reads messages, answers what's answerable from internal records, logs what's not, tracks tasks to completion, and routes everything else to the right person.

**The OOO angle is one scenario.** When someone is on leave, their inbox goes dark. But the same dynamic applies every day — in meetings, in deep focus, on calls. The inbox fills up, the small stuff waits, and nothing gets resolved until the person is free. A secretary handles this continuously. So does this product.

**Five-Why root cause diagnosis:**

- Why does focus fragmentation happen? → Because every incoming message is a potential interruption, and knowledge workers can't tell which ones matter without reading them
- Why do minor messages consume disproportionate time? → Because even a 3-minute reply requires switching platforms, looking something up, and composing — breaking deep focus for much longer than the task takes
- Why is the assessment work left to the human? → Because existing tools notify, capture, or draft — but none handle the work autonomously
- Why do messages accumulate? → Because there's no system that resolves the routine ones and only surfaces what actually needs human attention
- Why does the problem persist? → Because the alternative — a human secretary — is out of reach for most knowledge workers

**The core job-to-be-done:** "Be my secretary. Handle what's handleable. Only interrupt me when it actually matters."

### 1.2 Market Analysis

**The 99% / 4% framing is accurate but does not apply to the OOO coverage category.**

"SEA SMEs make up ~99% of businesses. Only 4% have adopted AI tools." This statistic covers AI tools broadly — helpdesks, CRMs, email assistants, internal IT tools. It does **not** cover the OOO coverage category, because **no product in this category has been built and marketed yet.** The 4% adoption rate is irrelevant to this product's market prospects because it measures something else entirely.

The existing AI tool landscape is fragmented into silos:

- **Notification tools**: "You have unread messages," "This person messaged while you were away — follow up?" (WhatsApp Business, AutoResponder.ai, shared inbox tools)
- **Task trackers**: Trello, Asana, Notion — "here's what you need to do when you get back"
- **Email AI assistants**: Superhuman, SaneBox — help you reply faster when you're at your desk
- **Phone answering services**: Smith.ai, Frontdesk — handle inbound calls, not cross-channel messaging

Each addresses one narrow slice of the problem. None addresses the **full gap**: the primary goes away, messages pile up, tasks go untracked, and nothing gets resolved or completed until they return.

**Sequor is not competing in an existing category.** It is creating a new category — "autonomous OOO coverage" — that doesn't yet exist in buyers' minds or in vendors' product roadmaps. The challenge is not breaking through existing skepticism; it is category creation: making SME and nonprofit buyers aware that "AI that covers for me completely while I'm away" is a thing they should be evaluating.

**The three constraint conflicts (accuracy, no setup, low cost) address real product design tensions** — but they are not responses to market rejection. They are responses to the actual product requirements: the target buyer cannot afford setup friction, cannot tolerate wrong answers sent to their customers/volunteers, and cannot pay enterprise prices.

**Three distinct buyer personas with very different purchase triggers:**

| Buyer                                          | Why they buy                                    | Why they don't                                                              |
| ---------------------------------------------- | ----------------------------------------------- | --------------------------------------------------------------------------- |
| Absent individual (sales rep, account manager) | Fear of falling behind, peer pressure           | "I'll deal with it when I'm back" — no personal cost                        |
| SME owner/manager                              | Customer retention, competitive differentiation | Low visible cost of missed inquiries; believes relationships survive delays |
| Nonprofit director                             | Volunteer coordination, donor stewardship       | No budget; no perceived accountability for response time                    |

**The nonprofit segment is the most plausible early adopter** but also the least able to pay. The brief's "low-cost enough for nonprofits" conflicts with building a sustainable SaaS business unless nonprofits are a loss leader for social proof.

### 1.3 Competitor Gap Critique

| Competitor                           | Brief's Assessment                  | Reality                                                                                                                                                                                                                                                                                     |
| ------------------------------------ | ----------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| WhatsApp Business / AutoResponder.ai | Rule-based; can't classify or route | Accurate. But a sophisticated WhatsApp Business setup (shared inbox + canned responses + routing rules) covers 80% of the SME use case at near-zero cost. The marginal value of "AI classifies and RAG-retrieves" over "keyword-triggered canned response" may not justify the price delta. |
| SleekFlow                            | "For sales teams"                   | SleekFlow's actual positioning is mid-market WhatsApp/SMS automation with CRM integration. Their AI features (AI Compose, Smart Inbox) directly compete with the described RAG + classification capability. The brief dismisses SleekFlow as positioning, not capability gap.               |
| Smith.ai / Phone answering services  | Phone-focused                       | A direct substitute exists: "forward your phone to Smith.ai when you're OOO." If SEA SME owners are comfortable forwarding their phone, this category is a stronger competitor than the brief suggests.                                                                                     |
| Moveworks / Salesforce               | Enterprise/expensive                | Valid for internal IT helpdesk. Not positioned for external customer inquiry coverage. Microsoft Copilot Studio and Google Workspace AI are the more relevant platform risk — OOO coverage may arrive as a feature of tools SMEs already pay for.                                           |

**Is there a real gap?** Yes. The existing competitive landscape is a collection of silos — no single product does what this product does:

- **Notification tools** (WhatsApp Business, AutoResponder.ai, shared inbox tools) tell the user _what happened_ but don't resolve anything
- **Task trackers** (Trello, Asana, Notion) capture _what needs to be done_ but don't主动 get it done
- **AI email tools** (Superhuman, SaneBox) help the user reply _faster when present_ but don't cover when absent
- **Phone answering services** (Smith.ai) handle voice but not the cross-channel WhatsApp/email problem

The Sequor is the only product that:

1. **Reads** incoming messages across WhatsApp and email
2. **Resolves** routine queries autonomously by retrieving from internal records (not just "here's a notification")
3. **Tracks and completes tasks** while the primary is away (not just "here's a follow-up reminder")
4. **Answers factual questions** from internal documents — "Did I sign up for the event tomorrow?" — by pulling records, not by forwarding the question to the backup

This is not a feature improvement on an existing category. It is a category that has not been built.

---

## Part 2: Technical Feasibility

### 2.1 WhatsApp 24-Hour Session Window — Revised Assessment

**The initial framing of this as a "Critical" blocking constraint was overstated.** The 24-hour window only affects follow-up messages within an active conversation thread. New messages from the same contact start a fresh window. The window is irrelevant for simple queries that resolve in 1–2 messages.

**The product design principle resolves this naturally:**

- Simple query (1–2 messages): AI handles it → resolved → no follow-up needed
- Complex query becoming a conversation (3+ messages): AI recognizes the pattern → escalates to backup → backup takes over → window is irrelevant
- Follow-up within 24 hours on a simple query: rare; if it happens, template message acknowledges it and contact knows the primary will respond on return

**Practical impact**: The window only affects the rare case where a simple query generates a follow-up before the AI can resolve it, and before the AI recognizes it needs escalation. This is manageable, not blocking.

**Template messages (still required)**: Pre-approve 4–6 generic templates at onboarding: acknowledgement, OOO notice, escalation notice, "I don't have this info." WhatsApp review takes 24–48 hours per new template — a one-time onboarding cost.

**Revised severity: Low.** This is a manageable edge case with a clear solution, not a fundamental constraint on the product concept.

### 2.2 Content Moderation and Rate Limits

WhatsApp Business API applies non-deterministic content moderation — URLs, keywords, attachment types can trigger message blocking with no appeal process and no API to check moderation status before sending. Rate limits: 250 business-initiated messages/minute/business account.

BSP (Business Solution Provider) costs: $0.05-$0.15 per message. At 50 contacts/day with 3 message exchanges each over a 3-day OOO, BSP fees alone reach ~$225/month — before AI inference, hosting, and RAG infrastructure costs. This is structural and cannot be optimized away.

### 2.3 Internal Documents Don't Exist — Solved as a Service

The RAG value proposition assumes structured, text-searchable internal documents. The target market largely does not have these. Rather than engineering an AI to handle messy documents (which is unsolved and high-risk), this is solved as a service:

**Document Cleanup Service (one-time, $300–500):**

- We review the customer's existing documents — however messy
- We organize, clean, and structure them into RAG-ready format
- The deliverable is independently valuable — clean, organized documents — whether or not they continue the subscription
- After cleanup, RAG works reliably because the input is controlled

**Self-serve path (for teams that prefer it):**

- Customers can prepare their own documents
- The product warns them if documents are below RAG-readiness threshold
- They can still use the routing/escalation features without RAG

**What this removes:** The hardest unsolved engineering challenge — making AI handle unstructured SME documents — is converted to a business operations problem. Engineering builds a scalable cleanup playbook, not a custom AI document parser.

**Remaining technical risk:** Building the scalable cleanup playbook and ensuring consistent quality across customers. This is a process risk, not a technical research risk.

### 2.4 Accuracy vs. Automation — Direct Conflict (Critical)

The brief states: "sending wrong information is worse than sending none" AND wants the AI to auto-resolve routine queries. These cannot both be satisfied without human-in-the-loop.

**Three architectural options:**

| Option                                      | Auto-respond when                           | Result                                                     | Risk                              |
| ------------------------------------------- | ------------------------------------------- | ---------------------------------------------------------- | --------------------------------- |
| A: High precision                           | RAG + classifier both >95%                  | ~30-40% auto-resolved; 60-70% routed to humans             | Users feel the AI doesn't do much |
| B: High recall                              | Either >70%                                 | ~70-80% auto-resolved; wrong answers sent                  | Hallucination damages trust       |
| C: Human-in-the-loop with confidence badges | Auto-send >90%; review 60-90%; compose <60% | Contact approves before sending; automation reduces burden | Contact may not respond promptly  |

**Option C is the only design consistent with the brief's stated constraint.** Every AI-generated response must carry a confidence badge. For confidence 60-90%, the contact reviews and approves before the response is sent. The product must route to backup for anything uncertain rather than risk a wrong answer.

### 2.5 Email as a Channel (High)

Email is harder to parse reliably than WhatsApp:

- **Threading**: Breaks on forward; In-Reply-To/Reference headers must be used; fall back to subject-line similarity
- **CC/BCC**: Messages CC'd to the OOO primary are addressed to the system; BCC semantics require inference
- **Attachments**: Filename + MIME type but no semantic relationship to body; ambiguous cases route to backup
- **HTML email**: Strip formatting, extract plain text, handle inline images via CID references
- **Deliverability**: SPF, DKIM, DMARC required; domain reputation management required

### 2.6 Multi-Channel Coordination (High)

If the same contact messages on WhatsApp AND email about the same topic within 48 hours, the system must detect this and prevent duplicate escalations. This requires:

- Contact identity resolution (email + phone + name similarity)
- A deduplication key (SHA256 of normalized contact identity + topic)
- A unified backup view showing both channels linked under one escalation
- Contradictory response prevention (if AI auto-replied on WhatsApp, the backup must see this before composing an email reply)

This is not a simple feature. Contact identity resolution is its own complex subsystem.

---

## Part 3: Business Model Analysis

### 3.1 Pricing Tiers

| Tier         | Price   | Users     | Messages  | Channels         | RAG                          | Audit Retention |
| ------------ | ------- | --------- | --------- | ---------------- | ---------------------------- | --------------- |
| Free         | $0      | 1         | 50/mo     | Email only       | None (all to backup)         | 7 days          |
| Starter      | $20/mo  | 1         | 200/mo    | Email + WhatsApp | Auto-reply (>90% confidence) | 90 days         |
| Professional | $60/mo  | 5         | 1,000/mo  | Both             | Auto-reply (>80% confidence) | 12 months       |
| Enterprise   | $200/mo | Unlimited | Unlimited | Both             | Dedicated RAG pipeline       | 24 months       |

Per-message overages above quota: $0.05 (Starter), $0.03 (Professional).

### 3.2 The Two-Part Pricing Problem

The "low-cost for nonprofits" constraint conflicts with viable unit economics in two separable ways:

**COGS problem:** WhatsApp BSP fees ($0.05-0.15/message) mean that at moderate volume (50 contacts/day × 3 exchanges × 30 days = 4,500 messages/month), BSP costs reach $225-675/month — exceeding any reasonable subscription price. The Starter tier at $20/month cannot cover BSP costs at moderate volume without overage revenue.

**CAC problem:** Acquiring a nonprofit customer at $30/month ACV never recoups sales-assisted CAC ($1,500-3,000). Even self-serve CAC ($150-400) requires 24+ month customer life to work at nonprofit pricing.

**Resolution:** Channel Partner model (accountants, HR firms, SME advisors) reduces CAC to $50-100 and converts faster because trust already exists. Partner receives 20% recurring revenue share.

### 3.3 Unit Economics Reality Check

| Metric                    | Optimistic     | Pessimistic                     |
| ------------------------- | -------------- | ------------------------------- |
| CAC (self-serve)          | $150           | $400                            |
| CAC (channel partner)     | $50-100        | —                               |
| ACV (Starter)             | $240/year      | $240/year                       |
| LTV (3yr, 70% GM)         | $504           | $504                            |
| LTV:CAC (self-serve)      | 1.3:1 to 3.4:1 | Barely viable at optimistic end |
| LTV:CAC (channel partner) | 5:1 to 10:1    | Viable                          |

**Critical dependency:** Customer life must exceed 24 months for self-serve to work at Starter ACV. If median churn is 12 months (common for SMB tools), self-serve is not viable at any price point below $100/month.

### 3.4 Competitive Moat

**Primary threat:** SleekFlow / Twilio adding "OOO coverage" as a feature. This is the most credible near-term risk. They have WhatsApp Business API access, SME customer relationships, and engineering capacity to add this in 1-2 quarters.

**Medium-term threat:** Meta/WhatsApp building this natively into WhatsApp Business. Probability: medium (2-5 years). Defense: none at scale. Mitigation: vertical specialization (medical practice OOO with patient triage, legal OOO with matter escalation) — deep vertical workflows take 18+ months to replicate.

**The one genuine moat:** RAG quality on messy SME documents (WhatsApp chat exports, informal notes, inconsistent spreadsheets) that takes 18+ months for a competitor to match. If the product builds a RAG pipeline that reliably handles this mess — without requiring users to restructure their documents — that is a switching cost. Everything else (WhatsApp integration, AI classification, routing logic) is a feature replicable in one quarter.

---

## Part 4: Red Team Findings

### 4.1 The Three Constraint Conflicts Are Correct (With Amendments)

| Conflict                                                      | Assessment                                                                                                    |
| ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------- |
| "Low-cost for nonprofits/SMEs" vs. viable SaaS unit economics | **Correct** — two separable problems: CAC/LTV and COGS/BSP fees. Both must be addressed independently.        |
| "No technical setup required" vs. RAG pipeline quality        | **Correct** — target users have no structured documents. "Upload a PDF" fails on Day 1 for most target users. |
| "Accurate responses always" vs. autonomous query resolution   | **Correct** — Option C (human-in-the-loop with confidence badges) is the only viable architecture.            |

### 4.2 Three Additional Product Decisions Required Before Build

1. **WhatsApp Day 2 recovery strategy:** Templates-only (accept 2-4 hour delay on Day 2), or route-all-Day-2-to-backup (no AI response, all human)?
2. **Document preparation approach:** Build an onboarding flow that creates structured docs from unstructured inputs (WhatsApp exports, chat histories), or accept RAG is DOA for most target users without this?
3. **Backup OOO detection timing:** At configuration time (warn primary if backup is also OOO during the same window), at escalation time (dynamic check), or continuously (pre-route before escalations fire)?

### 4.3 Kaizen Classifier Accuracy Is Unvalidated

The 90%/60% confidence thresholds in the response accuracy spec are placeholders. The Kaizen classifier accuracy on real SEA SME query corpus is unknown. If overall accuracy is 60% but accuracy at the routine/complex boundary is 40%, the thresholds are meaningless.

**Required before build:** Gather 200+ real queries from target users. Run Kaizen classifier. Measure precision/recall/F1 per category. Adjust thresholds based on actual performance.

### 4.4 PDPA PII Handling Gap

Contact messages may contain PII (NRIC, passport numbers, phone numbers). Classification and RAGRetrieval records store raw message text. When a contact exercises their right to erasure, the system must be able to delete their PII from these records — but AuditEntry is immutable and cannot be deleted.

**Required:** A PII detection layer at ingestion. NRIC, passport, credit card numbers are redacted from stored message text before Classification/RAGRetrieval persistence. AuditEntry retains full content for accountability but Classification/RAGRetrieval stores only PII-scrubbed text.

---

## Part 5: Spec Coverage Audit

### Brief Traceability Summary

| Brief Section                          | Coverage                                                        |
| -------------------------------------- | --------------------------------------------------------------- |
| Product: WhatsApp + email channels     | `message-routing.md` — both channel sections                    |
| Product: classify by type/urgency      | `response-accuracy.md` + `data-model.md`                        |
| Product: RAG from internal docs        | `rag-pipeline.md`                                               |
| Product: route complex to backup       | `message-routing.md` + `response-accuracy.md`                   |
| Product: auto-log everything           | `data-model.md` + `response-accuracy.md`                        |
| Product: visibility dashboard          | `response-accuracy.md` (Return Dashboard)                       |
| Objectives: reduce missed inquiries    | `message-routing.md` + `channel-coordination.md` (SLA tracking) |
| Tech stack: Kaizen agents              | `response-accuracy.md` (Classification + escalation)            |
| Tech stack: RAG                        | `rag-pipeline.md`                                               |
| Constraints: no technical setup        | `onboarding.md` (7-step wizard)                                 |
| Constraints: tenant-isolated docs      | `data-model.md` (separate schemas per tenant)                   |
| Constraints: accurate responses always | `response-accuracy.md` (Option C human-in-the-loop)             |
| Users: absent/primary configures       | `onboarding.md` + `message-routing.md`                          |
| Users: backup receives escalations     | `message-routing.md` + `channel-coordination.md`                |
| Users: internal admins (future)        | Not covered — explicitly future work                            |
| Users: end users (external contacts)   | `data-model.md` (Contact entity)                                |

**Two minor gaps:** Internal admin/billing (explicitly "future" in brief) and UI/frontend spec (implementation detail, not domain logic). All core requirements are covered.

---

## Part 6: Feasibility Scoring

| Dimension                 | Score (1–10) | Why                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 | What Would Improve It                                                                                                                                              |
| ------------------------- | :----------: | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Problem urgency**       |    **9**     | Universal knowledge worker pain, reframed as structural support gap — not personal failure. The "coverage + capacity" framing removes blame and positions this as infrastructure: every team needs coverage, now anyone can have it. Research on interruption recovery (Gloria Mark, 2004 — directionally: 20–25 min recovery per interruption) combined with 10–15 interruptions/day produces a credible cost of inaction. The "why now" is strong: AI is finally trustworthy enough. **Note**: The interruption frequency and recovery cost figures are from published research and are directionally validated, but should be confirmed against actual target user data in discovery interviews. | Evidence: 20 discovery interviews quantifying actual interruption frequency and cost per interruption would validate the figures and move this to 10/10            |
| **Market size**           |    **8**     | Narrowing to professional services (accountants, consultants, freelance professionals) as the first beachhead makes the TAM credible and actionable. They bill by the hour — clear ROI (every minute not spent on inbox admin is billable). They have exactly the coverage problem: client queries, meeting conflicts, follow-ups that slip. Lean teams of 3–10 people in professional services across SEA is a well-defined initial segment. Horizontal expansion to other departments and industries follows after.                                                                                                                                                                               | Validate willingness-to-pay via 10 discovery interviews with professional services firms; confirm pricing sensitivity at $40–60/seat/month before scaling          |
| **Competitive moat**      |    **8**     | Routing intelligence flywheel architected in specs from day 1 (RoutingOutcome entity, cross-tenant learning, industry-specific default thresholds). Document library as operational lock-in (document cleanup + ongoing maintenance). System of record depth (coverage history, escalation tracking, task completion). SOC 2 + ISO 27001 as time-gated compliance moat. A competitor replicating the UI in 3-6 months does not get the routing feedback data that sharpens classification thresholds across 2 years of real routing decisions. Moat deepens further with vertical specialization in professional services.                                                                          | Moat reaches 9 once flywheel produces measurable cross-customer routing insights (est. Month 3-4); vertical specialization adds compounding domain expertise layer |
| **Technical feasibility** |    **8**     | Pre-build validation gate documented in specs: 2–3 week RAG benchmark on real SME documents (5–10 professional services firms) with explicit pass/fail thresholds (>70% answerability, <10% hallucination, <15% false positive). Routing intelligence flywheel architected from day 1 (RoutingOutcome entity, feedback loop, cross-tenant learning). Document cleanup as ops removes the hardest build risk. WhatsApp window is a manageable edge case, not a blocker.                                                                                                                                                                                                                              | Validation gate must be run and passed before build is confirmed; routing intelligence feedback loop must be instrumented from day 1, not retrofitted              |
| **Unit economics**        |    **8**     | Per-seat model at $40–100/seat/month with professional services firms (3–10 seat teams = $120–1,000/month ACV) gives a credible ACV for sales-assisted motion. Document cleanup service ($300–500 one-time) lowers CAC by reducing onboarding cost. Enterprise tier at $100+/seat with unlimited seats targets larger teams within the same accounts. Multi-seat expansion within accounts is the primary expansion lever.                                                                                                                                                                                                                                                                          | Enterprise tier at $100+/user/month; ensure multi-seat adoption within accounts                                                                                    |
| **Go-to-market clarity**  |    **9**     | "Coverage + Capacity" positioning is department-agnostic, immediately resonant, and shifts the conversation from "AI replacing jobs" to "team equipped to do more." The pain (coverage gap, no headcount) is instantly recognizable to every manager in every department. "Your team handles more. Without hiring." is a complete sentence that sells itself.                                                                                                                                                                                                                                                                                                                                       | Lighthouse customers who say it in their own words; case studies with quantified ROI; first enterprise reference customer in a recognizable vertical               |
| **Regulatory complexity** |    **8**     | PDPA compliance thoroughly designed in data model spec: consent at collection, purpose limitation, individual rights (access/correction/erasure/data portability), breach notification workflow (72-hour PDPC), SOC 2 Type II and ISO 27001 certification path documented, third-party DPA requirements specified. WhatsApp API compliance addressed with template strategy. Singapore-first gives time to learn landscape before expanding.                                                                                                                                                                                                                                                        | Execute SOC 2 Type II certification path in parallel with product build; avoid regulated verticals (medical, legal) until certification is complete                |
| **Overall**               | **~8.5/10**  | Significantly improved across seven dimensions: problem urgency (structural support gap, 9), market size (professional services beachhead, 8), competitive moat (routing intelligence flywheel architected from day 1, 8), technical feasibility (pre-build RAG validation gate + flywheel specs, 8), unit economics (per-seat + enterprise tier, 8), GTM clarity (coverage + capacity positioning, 9), regulatory complexity (PDPA spec complete, SOC 2 path documented, 8). Product is viable for first build decision. Remaining real risks: RAG quality on real docs must be validated at pre-build gate; moat deepens to 9 once flywheel produces cross-customer insights.                     |                                                                                                                                                                    |

**Revised assessment:** From ~6 to ~8.5. All three dimensions in Path C delivered (moat 6→8, technical 7→8, regulatory 7→8) plus moat upgrade from architectural commitment (routing intelligence flywheel in specs). "Coverage + capacity" is the strongest GTM decision. Professional services as the first beachhead makes TAM credible. Routing intelligence flywheel is the compounding moat that competitors cannot shortcut. Document cleanup as ops removes the hardest technical risk. Pre-build RAG validation gate is the critical go/no-go decision before building.

---

## Summary: What Must Be Validated Before Building

1. **Discovery interviews (20+):** Knowledge workers and lean team leads. Ask: How many hours do you lose to inbox interruptions per week? What happens when you're in a meeting and a quick message comes in? Would you pay to fix this?
2. **Document audit (5–10 target orgs):** Audit the actual state of internal docs. Are there retrievable documents, or is the RAG pipeline DOA for your target users?
3. **Pricing validation (10+ prospective buyers):** What will they actually pay? Is $60/month acceptable for a tool that protects their focus? Does "it handles my inbox" feel worth more than "it reminds me to follow up"?
4. **RAG quality test:** On a sample of real SME documents (messy, unstructured), does RAG retrieval produce accurate answers more often than not?
5. **Focus loss quantification:** Can buyers quantify how many hours/week they lose to inbox fragmentation? The more specific the number, the stronger the ROI story.

---

## Recommended Next Step

Run 20 discovery interviews before any build — but lead with the focus/productivity angle, not the OOO angle. "How many hours a week do you lose to inbox interruption?" is a more powerful opening than "what happens when you're on leave?"

The product concept is plausible and significantly strengthened. The build must be preceded by validation, not followed by it.
