---
type: RISK
date: 2026-05-05
status: open
priority: critical
---

# PII Stored in Plaintext — Encryption Not Wired Into Models

The encryption library is complete (`sequor.db.encrypted_column` with AES-256-GCM, per-field key derivation via HKDF, HMAC blind indexes, tenant context variable). Unit tests pass. But no model column actually uses it.

**Affected columns (all plaintext today):**

- `Contact.email`, `Contact.phone`
- `BackupContact.email`, `BackupContact.phone`
- `Account.owner_email`, `Account.email_address`

The `KeyManager` and `provision_tenant_key()` also exist but onboarding never provisions keys during signup, so there would be no tenant key to encrypt with even if the columns were switched.

**Risk:** A database breach or backup leak exposes every customer's PII in readable form. PDPA requires reasonable security measures — plaintext PII in 2026 is indefensible. This is also the most common finding in Singapore PDPA enforcement actions.

**Fix:** Change the six columns above to `EncryptedString(field_name="...")`. Wire `provision_tenant_key()` into the onboarding signup flow. Ensure `set_tenant_key()` is called at request boundaries so the encryption column can access the current tenant's key.
