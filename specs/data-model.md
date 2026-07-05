# Data Model — Entities and Relationships

## Multi-Tenancy Requirement

All data is tenant-isolated. Each organization (or individual user) is a separate tenant. No tenant can access another tenant's data under any circumstances. This is a PDPA (Singapore) hard requirement and applies to all jurisdictions with similar data protection laws.

Database architecture: separate PostgreSQL schemas per tenant, OR separate database instances for high-security tenants. Namespace separation (shared schema with tenant_id) is NOT sufficient for Singapore PDPA compliance.

---

## Core Entities

### Tenant

```
id: UUID (PK)
name: string
email_domain: string (for email routing)
created_at: timestamp
plan: enum (free, starter, professional, enterprise)
settings: JSONB (flexible key-value store)
whatsapp_bsp_account_id: string (optional)
pdpa_consent_recorded_at: timestamp
```

### Account (communication point the company wants covered)

An account is a communication point — it can belong to an individual (e.g., a secretary) or a department (e.g., HR, Operations). The company decides how many accounts they need and who owns each one.

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
name: string (e.g., "Acme Front Desk", "HR Department")
ownership_type: enum (individual, department)
owner_email: string — the email address that receives escalations for this account
channels: enum[] (email, whatsapp) — which channels this account monitors
email_address: string (nullable) — the inbox this account monitors (e.g., hello@company.com)
whatsapp_phone: string (nullable, E.164 format) — the company WhatsApp number for this account
backup_contact_ids: UUID[] — people who receive escalations if primary doesn't respond
routing_rules: JSONB (category → routing_target mappings)
confidence_threshold: float — minimum confidence for auto-reply (default: 0.90)
escalation_sla_hours: integer — hours before auto-escalation to next tier (default: 4)
status: enum (active, inactive)
created_at: timestamp
```

**Design rationale**: The account model replaces per-user OOO configuration. Instead of each employee setting up their own coverage, the company creates accounts for the communication points they want covered. A solo operator has one account. A firm might have 3 (secretary, HR, operations). Each account independently configures its channels, routing rules, and escalation chain.

**No separate app required**: The `owner_email` is the primary interface. Escalations arrive as structured emails. The employee replies to the email to resolve. No dashboard login needed.

### BackupContact

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
account_id: UUID (FK → Account) — the account this backup serves
name: string
email: string
phone: string (E.164 format, nullable)
tier: enum (primary, second_tier)
active: boolean
```

### Contact (external — client, partner, volunteer)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
email: string (nullable)
phone: string (nullable, E.164 format)
name: string
company: string (nullable)
tags: string[] (e.g., ["volunteer", "donor", "client"])
last_seen: timestamp
channel_preference: enum (whatsapp, email, either)
human_override: boolean — if true, all messages from this contact route to backup, never auto-responded
```

### ChannelConsent (WhatsApp opt-in record)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
contact_id: UUID (FK → Contact)
channel: enum (whatsapp, email)
opt_in_at: timestamp
opt_in_method: enum (first_contact_notice, explicit_checkbox, verbal)
opt_in_notice_version: string — version of the notice text shown at opt-in
opt_out_at: timestamp (nullable) — if contact exercised right to withdraw
withdrawal_method: enum (replied_human, replied_stop, settings_change)
```

**Design rationale**: Opt-in records must be stored separately from Contact to support PDPA access requests ("show me what consent you have for my data"). The `opt_in_notice_version` field proves which notice text was displayed at the time of consent.

**PII constraint**: This entity contains no PII beyond contact_id and channel. The notice text itself is not PII.

### Message

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
contact_id: UUID (FK → Contact)
direction: enum (inbound, outbound)
channel: enum (whatsapp, email)
external_message_id: string (WhatsApp/email message ID)
in_reply_to: UUID (FK → Message, nullable) — for threading
subject: string (email only)
body_text: text — plain text extracted from content
body_raw: text — original raw content
attachments: JSONB (list of {filename, mime_type, size, url})
whatsapp_session_expired: boolean — true if sent after 24hr window
received_at: timestamp
processed_at: timestamp (nullable)
```

### Classification

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
classifier: string (Kaizen agent name/version)
category: enum (routine, semi_routine, complex, high_stakes)
urgency: enum (low, medium, high, critical)
confidence: float (0.0–1.0)
reasoning: text — LLM reasoning for the classification
classified_at: timestamp
```

### RAGRetrieval

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
document_ids: UUID[] (FK → Document)
passages: JSONB (list of {doc_id, chunk_text, similarity_score, citation})
retrieval_confidence: float (0.0–1.0)
synthesis_confidence: float (0.0–1.0) — after cross-check prompt
retrieved_at: timestamp
```

### Document (uploaded internal doc for RAG)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
name: string
type: enum (faq, roster, price_list, policy, other)
file_url: string (storage reference)
file_hash: string (SHA-256 for cache invalidation)
chunk_count: integer
indexed_at: timestamp
last_indexed_at: timestamp — for staleness detection
status: enum (pending, indexing, ready, stale, error)
```

### Response

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
rag_retrieval_id: UUID (FK → RAGRetrieval, nullable)
content: text — the actual response content
confidence_badge: enum (high, moderate, low, uncertain)
confidence_score: float
was_auto_sent: boolean
sent_at: timestamp (nullable)
approved_by_backup_at: timestamp (nullable)
backup_approver_id: UUID (FK → BackupContact, nullable)
```

### Escalation

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
response_id: UUID (FK → Response, nullable)
backup_contact_id: UUID (FK → BackupContact)
tier: integer (1 = primary, 2 = second_tier)
status: enum (pending, acknowledged, resolved, expired, notification_pending)
priority: enum (low, medium, high, critical)
assigned_at: timestamp
acknowledged_at: timestamp (nullable)
resolved_at: timestamp (nullable)
resolution_summary: text (nullable)
```

### AuditEntry (D/T/R accountability log)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
doer_type: enum (ai_agent, backup_contact, user, system)
doer_id: UUID — varies by type (agent name, backup contact ID, user ID)
action_type: string (e.g., "message_classified", "rag_retrieved", "response_auto_sent")
recipient_type: enum (contact, backup_contact, user, system)
recipient_id: UUID
message_id: UUID (FK → Message, nullable)
metadata: JSONB (flexible context — confidence scores, doc citations, routing reasons)
occurred_at: timestamp — immutable; not updated on edit
```

### RoutingOutcome (Routing Intelligence Flywheel)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
message_id: UUID (FK → Message)
classification_category: string
classification_confidence: float
routing_target: enum (backup_contact, escalation_queue, auto_respond, primary_user)
backup_contact_id: UUID (FK → BackupContact, nullable)
escalation_acknowledged: boolean
escalation_resolved: boolean
resolution_time_minutes: integer
auto_response_accepted: boolean — contact accepted AI response without escalation
auto_response_rejected: boolean — contact replied HUMAN or escalated manually
created_at: timestamp
resolved_at: timestamp (nullable)
```

**Indexes:**

- `routing_outcome(tenant_id, created_at)` — for per-tenant trend analysis
- `routing_outcome(tenant_id, classification_category, auto_response_accepted)` — for category-level acceptance rate

**Note:** This entity is the foundation of the routing intelligence flywheel. Every routing decision produces a record. The aggregate data across all tenants feeds back into default routing confidence thresholds per industry and message category. No PII is stored in this entity.

### RoutingThresholdConfig (Per-Tenant Live Thresholds)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
industry_template: string (e.g., "professional_services_accounting") — null for custom
category: string (e.g., "faq_billing", "client_inquiry")
auto_respond_threshold: float (0.0–1.0) — confidence above this → auto-respond
escalate_to_backup_threshold: float (0.0–1.0) — confidence below this → route to backup
high_stakes_escalate: boolean — always route to backup regardless of confidence
model_version: string — which routing model version produced these thresholds
updated_at: timestamp — when these thresholds were last updated from aggregate data
updated_by: enum (aggregate_job, manual_override)
```

**Design rationale**: These thresholds are the output of the flywheel's aggregation job. Each tenant has per-category thresholds that are continuously updated from their own routing outcome data. New tenants (without history) receive defaults from the cross-tenant aggregate model.

### RoutingOutcomeAggregate (Nightly Aggregation)

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
industry_template: string (nullable) — null = tenant's own data
category: string
period_start: timestamp
period_end: timestamp
total_routing_count: integer
auto_respond_count: integer
auto_respond_accepted_count: integer
auto_respond_rejected_count: integer
escalation_count: integer
escalation_acknowledged_count: integer
escalation_resolved_count: integer
avg_resolution_time_minutes: float
computed_at: timestamp
```

**Indexes**: `(tenant_id, category, period_start)` — for threshold update queries

**Design rationale**: This is a materialized aggregation — not raw RoutingOutcome data. It is computed nightly from RoutingOutcome records and used to update RoutingThresholdConfig. Raw RoutingOutcome records are purged after 90 days (retention limit). The aggregate survives.

**The flywheel loop mechanical path**:

1. `RoutingOutcome` records accumulate per routing decision
2. Nightly job → computes `RoutingOutcomeAggregate` from RoutingOutcome
3. `RoutingOutcomeAggregate` → updates `RoutingThresholdConfig` per category
4. `RoutingThresholdConfig` → Kaizen classifier uses thresholds for next routing decision
5. New `RoutingOutcome` records are generated with the updated thresholds
6. Loop repeats

**Cross-tenant defaults**: When `industry_template` is not null, the aggregate is computed across all tenants with that industry template. This data seeds `RoutingThresholdConfig` for new tenants onboarding with that industry template.

### OOOConfiguration

```
id: UUID (PK)
tenant_id: UUID (FK → Tenant)
account_id: UUID (FK → Account)
channels: enum[] (whatsapp, email) — subset of Account.channels
backup_contact_ids: UUID[] (must include at least one)
start_at: timestamp
end_at: timestamp
routing_rules: JSONB (category → routing_target mappings)
template_message_ids: string[] (WhatsApp template IDs active during this OOO)
status: enum (scheduled, active, completed, cancelled)
created_at: timestamp
```

**Note**: OOO configuration is per-account, not per-user. When an account goes into OOO mode, all messages to that account's channels are handled by the AI and escalated to backup contacts via email.

---

## Key Indexes

Every table: `tenant_id` + `id` as composite primary key where applicable.

Additional indexes:

- `message(tenant_id, contact_id, received_at)` — for contact history
- `message(tenant_id, external_message_id, channel)` — for deduplication
- `escalation(tenant_id, backup_contact_id, status)` — for backup workload
- `audit_entry(tenant_id, occurred_at)` — for audit log queries
- `document(tenant_id, status)` — for staleness monitoring
- `rag_retrieval(tenant_id, message_id)` — for retrieval audit

---

## Foreign Key Constraints

- All foreign keys use `ON DELETE RESTRICT` — a record cannot be deleted if other records reference it
- Tenant deletion requires all child records deleted first (cascade ordering enforced at application layer, not DB layer, to ensure audit trail integrity)
- AuditEntry records are IMMUTABLE — no UPDATE or DELETE allowed at application level; the DB may enforce this via rules

---

## PDPA-Specific Requirements

> PDPA (Personal Data Protection Act, Singapore) compliance is a **requirement**, not a competitive feature. All design decisions below are aimed at clean compliance with Singapore PDPA, with the framework extensible to Malaysia (PDPA 2010), Indonesia (GR 27/2022), and other SEA jurisdictions as the product scales.

---

### Personal Data Categories

| Data type                                    | Classification                  | Why collected                             | Retention                                                           |
| -------------------------------------------- | ------------------------------- | ----------------------------------------- | ------------------------------------------------------------------- |
| External contact name, email, phone          | PII — moderate sensitivity      | Route messages to correct recipient       | Until contact deleted or tenant deletes account                     |
| Message content (body, subject, attachments) | PII — high sensitivity          | Core service: classify, retrieve, respond | 90 days (Starter), 12 months (Professional), 24 months (Enterprise) |
| Internal document content (used for RAG)     | PII — variable (depends on doc) | Answer routine queries                    | Until user deletes document                                         |
| Backup contact details                       | PII — moderate sensitivity      | Route escalations                         | Until configuration updated                                         |
| Audit log (who did what, when)               | Non-PII but sensitive           | Accountability (D/T/R)                    | 90 days (Starter), 12 months (Professional), 24 months (Enterprise) |

---

### Consent and Collection

**Collection notice** must be displayed at the point of first contact (inbound message to a covered inbox):

- Brief notice: _"This inbox is managed by [Company]'s AI secretary. Your message will be processed to route it to the right person."_
- Link to full Privacy Policy
- This applies to **all inbound messages**, not just first contact

**Opt-out path**: If a sender does not want their message processed by AI, they can reply with "HUMAN" — the message is flagged for manual handling only and excluded from RAG processing.

**No secondary use**: Message content is never used for AI training, analytics, or shared with third parties. Contractually enforced in Terms of Service.

---

### Purpose Limitation

The system processes personal data for **three permitted purposes only**:

1. **Message routing**: classify the message type and urgency, route to the correct recipient (backup, escalation queue, or the primary user upon return)
2. **Query resolution**: retrieve factual answers from the tenant's internal documents (RAG), respond on behalf of the covered user
3. **Task tracking**: log follow-up items and mark them complete when resolved

No other use of personal data is permitted. The data model enforces this: message content is linked only to `Message`, `Classification`, `RAGRetrieval`, and `Response` entities. There is no export path to external systems.

---

### Individual Rights (Automated)

| Right                | How implemented                                                             | SLA                                                  |
| -------------------- | --------------------------------------------------------------------------- | ---------------------------------------------------- |
| **Access**           | User can view all data held about their contact/backup profile via Settings | Immediate (self-serve)                               |
| **Correction**       | User can edit name, email, phone in Settings                                | Immediate (self-serve)                               |
| **Erasure**          | User requests deletion via Settings → "Delete my data"                      | 30 days (PDPA requirement)                           |
| **Data portability** | User can export all messages + contacts as JSON                             | 30 days                                              |
| **Withdraw consent** | Contact can reply "STOP" to opt out of AI processing                        | Immediate — message flagged for manual handling only |

**Erasure implementation**:

> **Critical design rule**: `AuditEntry` contains **zero PII by design**. The `recipient_id` field is a UUID, not a name or email. The `metadata` JSONB field must never contain PII — only structured references (message_id, escalation_id, document_id). Because AuditEntry contains no PII, contact erasure does **not** require anonymizing audit rows.

Erasure of a Contact proceeds as:

1. **Contact record**: Hard delete — all PII (name, email, phone) permanently removed from `Contact` table
2. **ChannelConsent records**: Hard delete — opt-in record deleted; audit log of consent decisions also deleted
3. **Message records**: Hard delete — message content permanently removed from `Message` table
4. **Response records**: Hard delete — AI response content removed from `Response` table
5. **RoutingOutcome records**: Hard delete — routing outcome data removed; FK to Message breaks on cascade
6. **AuditEntry rows**: **No action required** — AuditEntry contains no PII. The `recipient_id` (UUID) and `message_id` (UUID) references are anonymized by the deletion of the Contact and Message records they reference; the audit trail of what actions occurred remains intact without PII.
7. **RAG index**: Document content purged from vector index and blob storage
8. **Encrypted backups**: Purge via key destruction — the backup encryption key for this contact's data is destroyed, making backup unreadable

**PDPA erasure ≠ Audit immutability**: The immutability of `AuditEntry.occurred_at` is preserved. The audit log is append-only. The erasure above removes PII without modifying any audit row. The accountability record survives; the personal data does not.

**What this means**: If a contact exercises their right to erasure, the system can fully comply — their PII is deleted everywhere it exists. The audit trail of what the system did with their data before erasure is preserved because it never contained PII.

---

### Security by Design

- All PII fields encrypted at rest (AES-256, tenant-specific keys)
- All data in transit: TLS 1.3 minimum
- Role-based access: only the covered user + designated backup contacts can see message content
- API access: authenticated via short-lived JWT tokens, not long-lived API keys
- No raw PII in application logs — contact IDs and message hashes used instead
- Tenant isolation enforced at the database schema level (separate schema per tenant, not just `tenant_id` column)

---

### Data Retention Schedule

| Data type          | Starter       | Professional  | Enterprise    |
| ------------------ | ------------- | ------------- | ------------- |
| Message content    | 90 days       | 12 months     | 24 months     |
| Contact profiles   | Until deleted | Until deleted | Until deleted |
| RAG documents      | Until deleted | Until deleted | Until deleted |
| Audit entries      | 90 days       | 12 months     | 24 months     |
| Escalation records | 90 days       | 12 months     | 24 months     |

Auto-deletion is enforced via a nightly batch job that purges records older than the retention period. Deletion is permanent and irreversible — this is logged in the audit entry.

---

### Data Breach Response

PDPA requires notification to the **Personal Data Protection Commission (PDPC)** within **3 calendar days** of a breach discovery.

**Breach classification**:

- **Tier 1 (major)**: Message content exposed to wrong tenant, or database schema isolation failure → notify PDPC within 72 hours + affected contacts within 3 days
- **Tier 2 (minor)**: Single contact record accessed by wrong user within same tenant → notify affected contact within 3 days, log internally

**Response workflow**:

1. **Detect**: automated alert on failed tenant isolation check, anomalous access patterns, or schema migration error
2. **Assess**: within 24 hours, determine breach scope and whether it meets the threshold for PDPC notification
3. **Notify**: if required, submit notification via PDPC's online portal within 72 hours of discovery
4. **Remediate**: close the breach, rotate keys if applicable, document root cause

---

### Immutability and Audit Integrity

- `AuditEntry.occurred_at` is **immutable** — no corrections allowed; new row added for any amendments
- Audit rows are **append-only** — the application layer enforces no UPDATE or DELETE
- Corrections to any record create a new audit row (e.g., if a classification is corrected, log it as `classification_corrected` with the reason)
- Audit log is **not subject to erasure** — it is the system's accountability record and is retained regardless of individual erasure requests

---

### Data Residency

- All data for Singapore tenants stored **exclusively on Singapore-based servers** (AWS ap-southeast-1 or equivalent)
- Future: cross-border data transfer only after Standard Contractual Clauses (SCCs) or equivalent legal mechanism are in place
- Documented in DPA (Data Protection Agreement) with each tenant

---

### Third-Party Data Processors

All third-party services that handle personal data (WhatsApp Business API, email delivery, AI model providers) must have:

- A Data Processing Agreement (DPA) in place before any data is sent
- Compliance certifications relevant to their handling of personal data (ISO 27001, SOC 2)
- Singapore PDPA added to their data protection obligations

No third-party processor may use personal data for their own purposes (including AI training).
