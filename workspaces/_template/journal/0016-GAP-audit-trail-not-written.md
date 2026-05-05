---
type: GAP
date: 2026-05-05
status: open
priority: high
---

# Audit Trail Never Written — AuditEntry Model Is an Orphan

The `AuditEntry` model exists in `models.py` with columns for `tenant_id`, `action`, `actor`, `details`, `timestamp`. But zero production code paths ever create an AuditEntry row.

**Impact:** We cannot answer "who did what, when" for any operation. This matters for:

- PDPA compliance — businesses must demonstrate they can trace data access
- Customer trust — "we can show you exactly what happened with your data" is a selling point
- Incident response — when something goes wrong, there's no forensic trail

**Key operations that should produce audit entries:**

- Message classified and auto-replied
- Escalation created, resolved, or SLA breached
- Document uploaded or deleted
- Contact PII accessed or erased
- Login/signup events
- Manual override of AI decision

**Fix:** Create an `audit()` helper function that writes AuditEntry rows. Call it from the key action points listed above. Start with the most sensitive operations (PII access, escalation resolution, data erasure).
