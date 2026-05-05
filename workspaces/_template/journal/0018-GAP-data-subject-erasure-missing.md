---
type: GAP
date: 2026-05-05
status: open
priority: medium
---

# Data Subject Erasure Function Missing

PDPA requires businesses to delete a customer's personal data upon request. Sequor has no function to do this.

**What exists:** A `compliance.py` module with consent tracking (`ChannelConsent` model) and consent checking. But no erasure capability.

**What's needed:** An `erase_contact_pii()` function that, given a contact identifier (email or phone):

1. Finds all records across all tables that reference that contact
2. Overwrites PII fields with `[ERASED]` or null (not just delete the row — audit trail must survive)
3. Deletes associated vector embeddings from pgvector
4. Writes an AuditEntry recording the erasure event
5. Returns a confirmation with a list of what was erased

**Affected tables:** contacts, messages, classifications, escalations, responses, channel_consents, documents (if the contact was a document owner).

**Fix:** Implement `erase_contact_pii()` in `compliance.py`. Wire it to a protected admin endpoint so the business owner can action erasure requests from their dashboard.
