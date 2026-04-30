# Product Brief

## Product

**What is an interruption costing your team right now?**

You were in a client call for 90 minutes. During that time, 11 messages arrived. When you came out, your inbox was full, three colleagues were covering for you, and two of them were also in meetings. Nobody was fully present anywhere. Your team is already stretched. Hiring isn't happening this quarter.

This is not a people problem. It is a **coverage gap**.

Every lean team has the same problem: too much inbound, not enough bandwidth to handle it without losing focus on what actually matters. Customer inquiries pile up. HR questions go unanswered. Sales follow-ups slip. Operations runs on borrowed attention from people who should be doing something else.

The solution isn't more headcount. It's better coverage.

**[Product name TBD]** is the coverage layer for every team. It reads incoming messages across WhatsApp and email, classifies them by type and urgency, resolves routine queries by retrieving answers from your internal documents (FAQs, rosters, price lists), answers factual questions from your records, tracks and completes tasks autonomously, and routes everything else to the right person — without anyone having to be everywhere.

**What this means for your team:**

- Customer service handles everything — without needing someone glued to the inbox
- HR answers policy and onboarding questions — without the constant interruption
- Sales never misses a follow-up — even when the whole team is in back-to-back meetings
- Operations stays on top of suppliers, incidents, and status updates — without the morning inbox scramble
- Managers stop worrying about coverage — because it's handled

**Your team handles more. Without hiring.**

Research on interruption recovery suggests that after being diverted from a task, it takes significant time to restore full focus — commonly cited as 20–25 minutes (Gloria Mark, _Interruptions in Knowledge Work_, 2004, though recovery time varies significantly by task complexity and individual). For a knowledge worker receiving 10–15 interruptions across a working day, even 5 minutes of reduced focus per interruption represents 50–75 minutes of lost productive capacity daily. At S$80/hour fully-loaded cost, that is **S$400–600 in recovered capacity per week** — or **S$1,600–2,400 per month** — against which S$60/month per seat for complete coverage is not a cost. It is a recovery of capacity the team is already paying for and not using.

_Note: The interruption frequency and recovery time figures above are cited from published research and are directionally correct. The precise figures for the target market should be validated in discovery interviews._

The backlog compounds. Every message not handled creates two follow-up messages. Every week of inaction deepens the hole. Coverage fixes that — permanently.

## Objectives

- Eliminate repetitive/minor inbound tasks that break focus and waste time
- Resolve routine queries automatically using internal document retrieval — without context-switching
- Protect deep work sessions by handling interruptions autonomously
- Ensure nothing is missed — whether the user is OOO or in a meeting
- Route complex or sensitive items to the correct person (backup, colleague, or escalation queue)
- Provide complete visibility into what was handled vs. what needs attention

## Tech Stack

- Backend: Kailash Core SDK + DataFlow + Nexus
- Frontend: Flutter (WhatsApp-native mobile app) or React/Next.js (web)
- Database: PostgreSQL (structured data: logs, tasks, routing rules)
- AI: Kaizen agents for intent detection and action routing; RAG from internal docs (FAQs, rosters, price lists) for query resolution

## Constraints

- Must work across WhatsApp and email as primary channels
- Must be low-cost enough for nonprofits, lean SMEs, and lean teams within larger orgs
- Must not require technical setup or training to operate
- All internal documents used for RAG must be kept confidential and tenant-isolated
- Responses must be accurate — sending wrong information is worse than sending none

## Users

- **Absent/Primary User**: The person who is away or busy; configures coverage rules, doc sources, and backup contacts before going OOO. Applies across all team sizes — solo operators, small SMEs, and individuals within lean teams at larger organisations.
- **Backup Contact**: The designated person who receives escalated items they need to handle manually
- **Internal Admins** (future): Manage team-wide settings, billing, and usage reports
- **End Users** (external): Clients, partners, volunteers, colleagues — the people sending messages that need coverage

## Target Market

**First beachhead: Professional services firms** — accountants, consultants, freelance professionals, and small advisory practices across SEA. They are the ideal first users because:

- They bill by the hour — every minute not spent on inbox admin is directly billable time. The ROI is measurable in dollars, not estimates.
- They run lean teams of 3–10 people. Coverage gaps are felt immediately — there is no spare capacity to absorb inbound volume.
- Client communication is the product. Missing a client follow-up, giving a slow response, or letting a proposal slip is directly revenue-adjacent.
- They already use WhatsApp and email as primary client channels — no workflow change required.

**Horizontal expansion:** After professional services, the product expands to other departments — customer service, HR, operations, marketing, sales — within the same organisations. Each department is a new entry point with the same coverage problem.

**Later expansion:** Nonprofits, then lean teams within larger organisations, then cross-industry.

Entry point is low-cost ($40/seat/month) with a natural upsell path to enterprise tier ($100/seat/month) within the same accounts.

## Competitor Gap

Existing tools help your team work faster. None of them provide coverage:

- **Email/notification tools** (Superhuman, Spark) — help you process faster. You still process everything.
- **AI writing assistants** (ChatGPT, Claude) — draft replies. You copy, paste, review, and send. You're still the bottleneck.
- **Auto-reply tools** (WhatsApp Business, AutoResponder.ai) — acknowledge. Don't resolve anything.
- **Task trackers** (Trello, Asana, Notion) — capture tasks. Don't complete them.
- **OOO auto-reply tools** — notify senders you'll respond later. Nothing gets handled.
- **Hiring more people** — solves capacity but at enormous cost, onboarding time, and management overhead.

No existing product provides complete coverage — reading messages, resolving what's resolvable, routing what's not, and tracking everything to completion — without requiring more headcount.

## Why This Is Harder to Copy Than It Looks

A competitor can build the product in 3-6 months. Building the compounding advantages takes years. Here's what we're building that can't be shortcut:

**Routing intelligence that improves with every customer**

Every message classified, every routing decision made, every escalation outcome tracked — all of it feeds back into the system. The more businesses use the tool, the better the routing engine gets at predicting what needs to route where, across contexts and industries. A competitor starting from zero cannot replicate this. They can replicate the UI. They cannot replicate 2 years of routing decisions.

**Document library as operational lock-in**

The document cleanup service does more than answer queries — it structures a business's institutional knowledge. Once structured, it becomes the reference point for every coverage decision. Switching means re-building that knowledge structure from scratch. The longer a business uses the tool, the costlier it is to leave.

**System of record depth**

The tool becomes where all coverage decisions live — not just messages handled, but every escalation, every resolution, every follow-up tracked. Switching means losing that institutional memory. Staying means the coverage history stays intact, searchable, and useful.

**Certifications as time gates**

SOC 2 Type II and ISO 27001 take 6-12 months to obtain. Building these in from month 1 means a competitor cannot claim equivalent compliance for at least half a year — a real purchasing criterion for any team with a security review.

## Document Cleanup Service (Optional Onboarding)

The AI secretary relies on internal documents (FAQs, price lists, rosters) to answer routine queries. Most businesses don't have these organized — they're scattered across WhatsApp chats, email threads, spreadsheets, and verbal knowledge.

For teams that want the full AI secretary capability, we offer a document cleanup service:

- We review, organize, and structure your existing documents into RAG-ready format
- One-time engagement — typically $300–500 depending on volume
- The deliverable is independently valuable: clean, organized, searchable documents — whether or not you continue the subscription
- After cleanup, the AI secretary can answer routine queries directly from your documents

This is optional. Teams can self-serve document preparation, but the full RAG capability requires documents to be clean enough to retrieve accurately.

## Pricing

| Tier             | Price               | Users     | Channels         | RAG                               | Audit Retention |
| ---------------- | ------------------- | --------- | ---------------- | --------------------------------- | --------------- |
| **Starter**      | **$40/seat/month**  | 1         | WhatsApp + Email | Auto-reply from cleaned documents | 90 days         |
| **Professional** | **$60/seat/month**  | Up to 5   | Both             | Full RAG with confidence badges   | 12 months       |
| **Enterprise**   | **$100/seat/month** | Unlimited | Both             | Priority RAG + PDPA audit report  | 24 months       |

Minimum 1 seat. Document cleanup service: $300–500 one-time (optional, required for RAG to work).
