# Channel Coordination — Email-First, No App Required

## Purpose

This spec covers the coordination layer across WhatsApp and email channels — specifically how escalations are delivered, how duplicate detection works, and how contradictory responses are prevented. **The entire interface is email-based** — no separate app or dashboard is required.

---

## Email-First Escalation Interface

The backup contact and account owner interact with the product entirely through their email inbox. There is no dashboard to log into, no app to install.

### Unresolved Item Email Format

Every unresolved item arrives as a structured email to the account owner's inbox:

```
From: coverage@{account-name}.company.com
Subject: [UNRESOLVED] {one-line summary}

Client: {contact name} ({channel})
Received: {timestamp}
AI attempted: {what the AI tried — RAG lookup, classification result}
Confidence: {score} — {category}
Requested via: {channel}

{original message body}

---
→ Reply to this email to send your response to the client.
→ If unresolved by {escalation_deadline}, this will escalate to {backup name}.
→ AI suggested response (edit before sending or compose your own):
{AI-generated draft if confidence > 60%}
```

### Reply-to-Resolve Mechanism

- The account owner replies to the escalation email
- The product extracts the reply and sends it to the client on the original channel (WhatsApp or email)
- The escalation is marked as resolved
- The human answer is captured and added to the knowledge base for future AI learning

### Auto-Escalation

If the account owner does not reply within the configured SLA (default: 4 hours):

1. The original escalation email is updated with a "ESCALATED" marker
2. The backup contact receives the same structured email
3. If the backup also doesn't respond within SLA, second-tier backup is notified
4. If no one responds, the item is flagged as "breached" and included in the daily digest

---

## Daily Digest Email

Every morning, the account owner receives a digest email summarizing all activity:

```
Subject: [COVERAGE DIGEST] {date} — {account name}

AI handled automatically: {count} messages
 - Resolved by RAG: {count}
 - Resolved by learned answers: {count}

Pending your response: {count} items
 - Oldest unresolved: {hours} hours ago

Escalated to backup: {count} items
 - Breached SLA: {count} (need attention)

New knowledge learned: {count} answers added to knowledge base
  - "{topic 1}"
  - "{topic 2}"
```

---

## Weekly Recap Email (Professional+)

A weekly summary with trends:

```
Subject: [WEEKLY RECAP] {date range} — {account name}

Messages this week: {total}
 - AI auto-resolved: {count} ({percentage}%)
 - Human resolved: {count} ({percentage}%)
 - Pending: {count}

AI accuracy: {percentage}% (based on client acceptance/rejection)
Most common queries: {top 5 topics}
Knowledge base growth: {count} new answers learned this week ({total} total)
Average response time: {minutes} minutes (AI) / {hours} hours (human)
```

---

## Unified Escalation Record

Each escalation is tracked internally regardless of how it's delivered to the user:

```
Escalation {
  id: UUID
  thread_key: string — derived from contact identity + topic
  channel: enum (whatsapp, email, both)
  status: pending | acknowledged | resolved | expired
  created_at: timestamp
  contact: Contact
  messages: Message[] — all messages in the thread across channels
  ai_summary: string — one-sentence summary of what the contact wants
  routing_reason: string — why this escalated (low confidence, high-stakes, etc.)
  suggested_response: string (nullable) — AI-generated draft for backup
  assigned_backup: BackupContact
  resolution_summary: string (nullable)
  resolved_at: timestamp (nullable)
}
```

---

## Thread Key Construction

The thread key is the deduplication anchor. It must be stable across channels and time.

### Derivation

```
thread_key = SHA256(
  normalize_email(contact.email)
  OR normalize_phone(contact.phone)
  + "|" + extract_topic(message_body)  # first 5 significant words
)
```

Two messages from the same contact about the same topic within 72 hours belong to the same escalation.

---

## Contact Identity Resolution

### Identity Graph

A `Contact` has:

- `email` (nullable)
- `phone` (nullable)
- `name` (nullable)

Multiple contacts with different emails/phones may actually be the same person. Resolution rules:

1. Exact email match → same contact
2. Exact phone match → same contact
3. Same name + same domain in email → possible match; flag for manual merge review
4. No match → new contact

### Identity Confirmation

When a new channel appears for an existing contact (e.g., contact who previously emailed now messages on WhatsApp):

- System suggests: "We found this WhatsApp message is from [Name], who previously contacted you by email. Link to same thread?"
- User confirms → contacts are merged; thread is unified
- User rejects → new contact record created; no cross-channel deduplication for this contact

---

## Duplicate Detection Flow

### Scenario: Same contact, same topic, both channels

1. Contact emails about invoice #1234
2. AI receives, classifies, escalates to backup (email thread created)
3. Same contact sends WhatsApp message about invoice #1234 (within 72hr window)
4. System detects: same contact + same topic + within deduplication window
5. WhatsApp message is linked to existing escalation (not a new one)
6. Backup sees: escalation updated with WhatsApp message appended, with channel indicator

### Scenario: Same contact, different topic, both channels

1. Contact emails about invoice #1234
2. Contact sends WhatsApp about a new project inquiry
3. System detects: same contact, different topic (>5 significant words differ)
4. New escalation created for WhatsApp message
5. Backup sees two separate escalations

---

## Contradictory Response Prevention

### The Problem

Contact emails asking about invoice #1234 → AI escalates to backup → backup composes email reply. Meanwhile, the AI has already auto-responded on WhatsApp with different information.

### Prevention Mechanism

Every escalation record stores:

- `ai_auto_replies`: list of all AI-sent messages (WhatsApp and email) with content summary
- `human_replies`: list of all backup-composed responses

Before a backup sends a human reply:

1. System checks if an AI auto-reply on a different channel already addressed the same query
2. If conflict detected: warning shown to backup — "AI already replied on [channel] with: [summary]. Your reply may contradict this."
3. Backup must acknowledge the warning before sending
4. If backup sends anyway: both responses are logged; contact receives both (creates confusion but preserves audit trail)

### Undo Mechanism

If a backup realizes they sent a contradictory reply:

- Backup can mark escalation as "resolved with conflict"
- Contact receives a single clarifying message (composed by backup)
- Audit log records the contradiction for product improvement

---

## Backup Notification Priority

When an escalation is created:

1. **Primary backup** receives notification via preferred channel (email/SMS/WhatsApp)
2. If **primary backup does not acknowledge within 4 hours**: second-tier backup is notified
3. If **both backups are OOO** (detected via OOO configuration in the system): escalation is marked `pending_ooo_return`; primary receives notification on return with full summary
4. If **urgent** (urgency = critical): notification is sent immediately to primary AND second-tier simultaneously

### Notification Content

Backup notification includes:

- Contact name and channel
- One-line summary of what the contact wants
- Urgency level (low/medium/high/critical)
- Link to escalation detail view
- For high/critical: suggested response is pre-loaded

Backup can act on the escalation directly from the notification (approve AI draft, send response) without logging into the full dashboard.

---

## SLA Tracking

Each escalation has:

- `created_at`: when the escalation was created
- `sla_deadline`: `created_at` + configured SLA window (default 4 hours)
- `sla_acknowledged_at`: when backup opened/viewed the escalation

If SLA deadline passes without acknowledgement:

- Second-tier backup is notified
- Primary backup receives a reminder
- Escalation is flagged in the dashboard as "at risk"

If SLA deadline passes without resolution:

- Escalation is flagged as "breached"
- User (primary, on return) sees "breached escalations" prominently on their dashboard

---

## Return Summary (Primary User on Return from OOO)

When the primary user returns, they receive a single summary email:

```
Subject: [OOO COMPLETE] {date range} — {account name}

Messages received: {total}
 - Auto-resolved by AI: {count}
 - Resolved by backup: {count}
 - Still pending: {count}

Pending items requiring your attention:
{list of unresolved items with reply links}

AI learned {count} new answers from your team's responses this period.
```

This is the "nothing was missed" promise — delivered to the user's inbox, not a dashboard they need to remember to check.
