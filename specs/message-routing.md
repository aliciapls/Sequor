# Message Routing — Channel Contracts and Constraints

## Per-Account Channel Configuration

Each account configures its own channels independently:

- Email only
- WhatsApp only
- Both email and WhatsApp

A solo operator might start with email only. A department might use both channels. The company decides per account.

**Company WhatsApp number**: WhatsApp uses a company-owned Business API number (not individual employees' personal WhatsApp). Clients message the company number — the product handles it from there. Employees never need to connect their personal WhatsApp.

---

## WhatsApp Business API — Session Window

WhatsApp Business API enforces a 24-hour session window from the last contact message. After the window closes, the business cannot send free-form replies — only pre-approved template messages may be sent.

**This is manageable, not a roadblock**: The AI responds within minutes for queries it can answer from the knowledge base. For queries it cannot answer, an automated template message is sent within the 24-hour window acknowledging receipt and setting expectations. The human follows up when available — conversation traceability is maintained in the product's internal system regardless of the WhatsApp session state.

### Template Message Strategy

- A library of generic templates MUST be pre-approved at onboarding before the first OOO deployment
- Required templates: these 5 named templates are the mandatory minimum set — acknowledgement, OOO notice, escalation notice, urgent routing, "I don't have this information" notice. Onboarding pre-approves **8 templates total** (these 5 + a 3-template buffer for account-specific needs), per the onboarding checklist below. (Resolves the 5-vs-6-vs-8 drift 2026-07-05 per `DEVIATIONS.md` CS-5: 5 named-required ⊆ 8 pre-approved.)
- Template approval takes 24-48 hours per new template; this is a one-time onboarding cost
- Template pool is limited per business account; the system MUST track template usage and request new templates before the pool is exhausted

### Session Window Behavior by Day

| Day     | Contact Messages           | AI Response Capability                               |
| ------- | -------------------------- | ---------------------------------------------------- |
| Day 1   | New query                  | Full AI response — classify, RAG, auto-reply, route  |
| Day 2+  | Follow-up to same thread   | Session closed — only template message can re-engage |
| Any day | New query from new contact | Full AI response — fresh 24hr window starts          |

### Implication for Product Promise

The product MUST NOT promise multi-day continuous AI coverage on WhatsApp. The 24-hour window is a hard constraint. Coverage quality degrades on Day 2 and beyond for any contact with prior engagement.

Design implication: The product MUST surface this limitation to users at configuration time. Users who need true multi-day coverage must use email as the primary channel or configure a second-tier backup.

---

## WhatsApp Business API — Compliance Design

This section ensures the product does not violate WhatsApp's Business Messaging Policy. Items marked **[REQUIRES CONFIRMATION]** must be verified against the live Meta policy before launch.

### Permitted Use Cases (Known)

Under WhatsApp's published Business Messaging Policy:

- **Session messages**: AI-generated responses during an active 24-hour session are permitted — no human authorship required
- **Inbound-only**: Responding to inbound messages is permitted; unsolicited outbound messages to contacts who have not messaged first are not
- **Template messages**: Pre-approved templates sent after the session window closes are permitted
- **Automated routing**: Using AI to classify and route messages is permitted (not a prohibited use case)

### Hard Compliance Requirements

These are non-negotiable — violation results in API access revocation:

**1. Opt-in recording at first contact**

Every contact who sends a message to a covered business must receive a clear opt-in notice before or at the time of their first message. The notice must state:

- The business name using the WhatsApp channel
- That an AI system may process their message to route it correctly
- That they can reply "HUMAN" to have a human handle it

The opt-in is recorded as a `ChannelConsent` record (see data model). No message processing begins until consent is recorded.

**2. HUMAN rejection path**

When a contact replies "HUMAN" (case-insensitive, within the session window):

- All subsequent routing for this contact is forced to backup
- The contact receives a template message: "A team member will respond shortly."
- The `auto_response_rejected` flag is set in `RoutingOutcome`
- The contact's future messages are tagged `human_override = true` and never auto-responded

**IMPORTANT — False positive prevention**: The word "HUMAN" must be detected as an explicit rejection signal, not as part of natural language. The detection logic requires:

- Exact match "HUMAN" OR starts-with "HUMAN " — not substring match
- "human resources", "human form", etc. do NOT trigger rejection
- The detection window is only within the active 24-hour session

**3. Template message compliance**

All template messages sent after the session window closes must:

- Be pre-approved by Meta before first use
- Match the approved content exactly (no dynamic content except approved variables)
- Be relevant to the ongoing conversation context or a recent customer interaction
- Not be used for promotional or marketing purposes

Minimum required templates (pre-approved at onboarding):

1. `oo_acknowledgement` — "We've received your message. The team will respond within [timeframe]."
2. `oo_notice` — "The person you messaged is currently out of office. A team member will follow up."
3. `escalation_notice` — "Your query has been forwarded to our team."
4. `no_information` — "I don't have that information. A team member will get back to you shortly."
5. `human_override` — "A team member will respond shortly."
6. `urgent_routing` — "Your message has been flagged as urgent and forwarded immediately."

**4. No unsolicited outbound messages**

The product never initiates contact with a WhatsApp user who has not first messaged the business. This is a hard violation.

**5. No prohibited content**

AI-generated responses must not contain:

- Adult content
- Hate speech or discriminatory content
- Illegal goods or services
- Content that violates third-party rights

Classification filters must reject any message in these categories and force routing to backup without auto-response.

### Rate Limits (WhatsApp-Required)

| Limit Type        | Value                        | Consequence of Violation                                               |
| ----------------- | ---------------------------- | ---------------------------------------------------------------------- |
| Outbound messages | 250/minute/business account  | Error code 131056; temporary API block                                 |
| Session messages  | 1 per 6 seconds to same user | Error 131056                                                           |
| Template pool     | Limited per account          | Exhausting pool means no WhatsApp coverage until new template approved |

The system MUST track template usage and alert before the pool is exhausted.

### BSP Requirement

The product must operate through an approved WhatsApp Business Solution Provider (BSP). Approved BSPs include Twilio, MessageBird (Bird), Infobip, and others registered with Meta.

Using unofficial or scraped WhatsApp API access is a direct Terms of Service violation and results in permanent API revocation.

### Items Requiring Explicit Legal Confirmation [REQUIRES CONFIRMATION]

The following items require review of the live Meta Business Messaging Policy before the product launches:

1. **AI-authored session responses**: Does Meta permit fully AI-generated responses without any human authorship during the session window? Confirmation needed from BSP or legal review.

2. **"Coverage" use case classification**: Is using WhatsApp Business API for "OOO coverage" an permitted use case under Meta's policy, or does it fall into a restricted category?

3. **Opt-in notice format**: What constitutes a compliant opt-in notice? A brief inline message ("This inbox is covered by AI.") may or may not meet Meta's "clear and prominent" standard.

4. **HUMAN override**: Is routing all future messages to a human (bypassing AI entirely for that contact) a compliant approach under Meta's policy?

5. **Cross-border data**: If the AI processing happens on servers outside Singapore (e.g., OpenAI servers in the US), does this comply with WhatsApp's data processing requirements?

### WhatsApp Compliance Checklist

Before first deployment, verify:

- [ ] All template messages pre-approved by Meta
- [ ] `ChannelConsent` records exist for all contacts
- [ ] Opt-in notice displayed to all new WhatsApp contacts
- [ ] BSP relationship established (Twilio, Bird, or equivalent)
- [ ] HUMAN override path tested and confirmed working
- [ ] Rate limit monitoring in place
- [ ] No prohibited content filters in AI response path
- [ ] Legal review of items [REQUIRES CONFIRMATION] above completed

---

## Email — Async Channel

Email does not have a session window constraint. Messages can be responded to at any time within reasonable SLA windows.

### Threading Rules

- Use `Message-ID`, `In-Reply-To`, and `References` headers for thread reconstruction
- Forwarded emails may lose threading headers — fall back to subject-line similarity matching (subject unchanged + same sender within 72hr window, matching the deduplication window below)
- CC/BCC semantics: messages CC'd to the primary (who is OOO) are treated as addressed to the system; messages BCC'd require inference from context

### Email Parsing Requirements

- HTML email: strip formatting, extract plain text; handle inline images via CID references (ignore for routing purposes)
- Attachments: extract filename and MIME type; if body is empty and attachment name is meaningful (e.g., "Invoice.pdf"), route to backup for human review — do not auto-acknowledge
- HTML tables that look like plain text must be handled gracefully

### Email Deliverability

- SPF, DKIM, DMARC must be configured for the sending domain
- Outbound volume rate limiting: max 60 emails/minute per domain to avoid spam classification
- Domain reputation monitoring: if sender reputation degrades, alert user and queue outbound messages

---

## Multi-Channel Deduplication

When the same contact reaches out on WhatsApp and email about the same topic within a 48-hour window, the system MUST detect this and prevent duplicate escalations.

### Deduplication Key

- Contact identity resolution: match by email address (primary) + phone number (secondary) + name similarity (tertiary)
- Thread key (shipped mechanism, see `src/sequor/escalation/thread_key.py::derive_thread_key`): a stable `SHA256(normalized_email_or_phone + "|" + extract_topic(first 5 significant words))`. Two messages from the same contact about the same topic share a thread key and are treated as the same thread. (An earlier draft of this spec described an embedding/semantic-similarity match at >70%; that is NOT what ships — the shipped dedup is the deterministic SHA256 thread key. Resolved 2026-07-05 per `specs/DEVIATIONS.md` CS-2.)
- Deduplication window: 72 hours from first contact (matches `channel-coordination.md` and the shipped 72h thread-key window; resolved 2026-07-05 per `DEVIATIONS.md` CS-1)

### Unified Backup View

When a contact reaches out on both channels, the backup sees:

1. Both message threads linked under one escalation
2. Channel indicator (WhatsApp / Email) on each message
3. A summary: "Contact messaged on WhatsApp and email about the same issue — WhatsApp response sent; email escalation for context"

### Contradictory Response Prevention

If the AI auto-responds on WhatsApp before the backup replies on email:

- The escalation summary notes: "WhatsApp auto-replied [content summary]"
- The backup MUST NOT send an email response that contradicts the WhatsApp reply
- The system logs the WhatsApp response content so the backup can read it before composing an email reply

---

## Channel Priority

1. **Email**: Primary channel — no session window, no platform restrictions, works for all coverage scenarios
2. **WhatsApp**: Client-facing channel on company number — strong for Day-1 coverage, template-based after 24 hours
3. **Escalation**: Both channels route unresolved items to the account owner's email inbox

The system does not handle phone calls, in-person contact, or external social media. These fall outside the coverage guarantee.

---

## Rate Limits

| Channel            | Limit                                                   | Notes                                         |
| ------------------ | ------------------------------------------------------- | --------------------------------------------- |
| WhatsApp outbound  | 250/minute/business account                             | Business-initiated messages                   |
| WhatsApp templates | Pool per account; new templates require WhatsApp review | Pre-approve minimum 8 templates at onboarding |
| Email outbound     | 60/minute/domain                                        | To maintain sender reputation                 |
| Email inbound      | No limit                                                | —                                             |

---

## Backup Routing

When the AI routes to backup:

1. The escalation is logged with full message context, RAG retrieval results (if any), and classification confidence
2. The backup receives a notification via their preferred channel (configured at setup)
3. If the backup does not acknowledge within the configured SLA window (default: 4 hours), a second-tier backup is notified
4. If the backup is also OOO (detected via OOO status in the system), the escalation routes to the second-tier immediately

---

## Configuration Contract

Per-account configuration (set during onboarding):

1. **Account name and ownership**: individual or department
2. **Channels**: which channels (email, WhatsApp, or both) this account monitors
3. **Escalation chain**: primary backup + second-tier; escalation SLA timing
4. **Routing rules**: which message types escalate vs. auto-respond
5. **Template message set**: which pre-approved templates are active for WhatsApp (if WhatsApp enabled)

Coverage is always-on by default — not limited to OOO periods. The account monitors and handles messages continuously. OOO mode is an optional overlay that changes routing behavior (e.g., routes more aggressively to backup when the account owner is away).

The system validates that at least one backup contact is configured and reachable before activating the account.

---

## Routing Intelligence Flywheel — Compounding Moat

Every routing decision the system makes is stored as a learning event. This creates a compounding data advantage that deepens the moat over time — a competitor starting from zero cannot shortcut this.

### Feedback Loop Architecture

Every message routed produces a `RoutingOutcome` record:

```
routing_outcome_id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
classification_category: string
classification_confidence: float
routing_target: enum (backup_contact, escalation_queue, auto_respond, primary_user)
backup_contact_id: UUID (FK → BackupContact, nullable)
escalation_acknowledged: boolean
escalation_resolved: boolean
resolution_time_minutes: integer
auto_response_accepted: boolean (contact accepted AI response without escalation)
auto_response_rejected: boolean (contact replied HUMAN or escalated manually)
created_at: timestamp
resolved_at: timestamp (nullable)
```

### What gets learned

The aggregated `RoutingOutcome` data across all tenants feeds back into the classification engine:

1. **Routing accuracy by category**: Which categories most often route to backup? Which auto-responses get rejected? This adjusts the confidence thresholds per category.
2. **Backup workload patterns**: Which backup contacts handle which message types fastest? Routing to the right backup reduces resolution time by X%.
3. **Industry routing patterns**: Professional services firms route client billing queries differently from logistics firms. Cross-tenant learning (anonymized) sharpens defaults per industry template.
4. **Auto-response acceptance rates**: If a category has >90% acceptance on auto-response, the system auto-responds more aggressively. Below 70%, it routes to backup by default.

### Cross-Tenant Learning (Anonymized)

Individual tenant routing data is isolated. But aggregate patterns across similar businesses improve the default routing model:

- "Businesses in professional services with 3–5 seats auto-respond to 60% of inbound"
- "Consulting firms route client queries to backup 40% faster when routed to second_tier instead of primary"
- "FAQ-type queries have 95% auto-response acceptance; policy-type queries have 40%"

These aggregate patterns are used to set default routing confidence thresholds for new tenants. A new accounting firm gets pre-configured thresholds calibrated from aggregate accounting firm data — not starting from zero.

### Outcome Tracking Instrumentation

This is not a future feature. It is architected from day 1:

- Every routing decision logs a `RoutingOutcome` record at the time of routing
- The `resolved_at` and `auto_response_accepted/rejected` fields are updated when the outcome is known (contact responds, escalation acknowledged, etc.)
- A nightly aggregation job computes per-category acceptance rates and updates the routing model
- New tenant onboarding pre-loads industry-specific default thresholds from the aggregate model

A competitor replicating the product in 3-6 months gets a working UI. They do not get 2 years of routing outcome data. They cannot replicate the thresholds that were calibrated from real routing decisions across hundreds of businesses.
