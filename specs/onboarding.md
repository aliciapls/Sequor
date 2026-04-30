# Onboarding — Non-Technical User Setup

## Design Principle

The target user has no technical background and zero tolerance for setup friction. Every step that requires user effort must justify itself. The goal is: first account active in under 10 minutes, with no external support required. **No separate app is needed** — the user's existing email inbox is the primary interface for receiving escalations and resolving items.

---

## Onboarding Flow (5 Steps)

### Step 1: Account Creation

- Email + password OR magic link (no password to forget)
- Organization name
- Accept terms of service and PDPA consent (Singapore requirement)
- No phone number required at signup

### Step 2: Create Account (Communication Point)

- User names the account (e.g., "Acme Front Desk", "HR Department")
- User selects ownership type: Individual or Department
- User enters the email address that receives escalations for this account (their existing email)
- User chooses channels: Email only, WhatsApp only, or Both
  - If Email: enter the inbox to monitor (e.g., hello@company.com); system generates DNS records
  - If WhatsApp: enter business phone number; system initiates WhatsApp Business API verification via BSP
  - WhatsApp setup is optional — user can start with email only and add WhatsApp later

### Step 3: Upload Documents (Optional)

- User is offered a document upload wizard
- Document types offered: FAQ, Roster, Price List, Policy, Other
- For each type: upload → preview parsed chunks → confirm
- **No documents? No problem.** The AI learns from human answers over time. Every time the account owner replies to an unresolved escalation, that answer is captured and added to the knowledge base. The product gets smarter with every interaction — no upfront document preparation required.
- Document cleanup service available as optional paid add-on for firms that want to accelerate the learning curve

### Step 4: Configure Escalation Chain

- User adds primary backup contact: name, email
- User optionally adds second-tier backup
- System sends a test email to each backup contact to verify reachability
- Escalation timing is configured: how long before auto-escalating to next tier (default: 4 hours)

### Step 5: Routing Rules

- User selects from pre-defined routing rule templates:
  - **Template A: All to backup** — all messages go to backup via email; no auto-reply
  - **Template B: FAQ-only** — messages matching documents are auto-replied; others sent as escalation emails
  - **Template C: Full AI** — messages above confidence threshold are auto-replied; others escalated via email
- High-stakes categories (medical, legal, financial) are pre-configured to always escalate; user cannot override
- **Completion**: account is live. Messages start being processed immediately.

---

## No Dashboard Required

There is no separate app or dashboard. The user interacts with the product entirely through their existing email inbox:

- **Unresolved items** arrive as structured emails with full context
- **Replying to the email** sends the response to the client
- **Ignoring the email** triggers auto-escalation to the backup contact after the configured SLA
- **Daily digest** (Starter+) summarizes all activity: what was auto-resolved, what's pending, what was escalated
- **Weekly recap** (Professional+) provides trends: AI accuracy, response times, common query patterns

---

## Progressive Disclosure

The onboarding wizard shows only the minimum required fields at each step. Advanced options (custom routing rules, document staleness thresholds, confidence score adjustments) are hidden behind an "Advanced" toggle, visible only to users who ask for them.

---

## Document Preparation Tool (v1.5 or later)

For users who don't have structured documents, the product offers a document preparation wizard:

- **Chat export parser**: user exports their WhatsApp chat and uploads the file; the system parses common FAQ patterns ("Q: ... A: ...") and suggests FAQ entries for the user to confirm
- **Spreadsheet template**: downloadable XLSX template for rosters with required columns; user fills in and uploads
- **Price list import**: user pastes text or uploads a file; system parses line items and shows a preview table for confirmation

This feature is optional at v1 launch — the core product works without it because the AI learns from human answers. Users with messy documents can start immediately and let the knowledge base grow organically.

---

## Error Handling at Onboarding

| Error                         | User Message                                                                                                          | Action                                                              |
| ----------------------------- | --------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------- |
| DNS verification failed       | "We couldn't verify your domain. Check that you copied the record exactly as shown."                                  | Show exact record values; offer manual retry                        |
| WhatsApp verification timeout | "Verification is taking longer than expected. Email is ready to use — WhatsApp setup can complete in the background." | Offer email-only mode; continue WhatsApp async                      |
| Document parsing fails        | "We couldn't read this file. Try a plain text file or PDF with selectable text (not a scan)."                         | Offer to re-upload; show supported formats                          |
| Backup contact unreachable    | "We couldn't reach [backup email]. Please check the address."                                                         | Allow retry; allow skip with warning that escalations won't deliver |

---

## Configuration Complexity Budget

Onboarding must not require the user to understand:

- Vector databases, embeddings, or RAG
- WhatsApp Business API or BSPs
- DNS records beyond simple copy-paste
- Confidence thresholds (shown as "High / Medium / Low" sliders, not numbers)

If a step requires explanation, the explanation must fit in one sentence. If it requires more, the step is too complex and must be redesigned.
