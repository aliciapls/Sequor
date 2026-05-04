# PII Encryption at Rest -- Implementation Plan

## Executive Summary

Sequor stores email addresses and phone numbers in plaintext across three models (Contact, BackupContact, Account). This plan adds AES-256 column-level encryption to all PII fields so that a database breach or snapshot leak does not expose personal data. The approach uses a custom SQLAlchemy column type that transparently encrypts on write and decrypts on read, with a searchable HMAC-SHA256 blind index for equality lookups. Tenant-specific keys are stored in a `tenant_encryption_keys` table, encrypted under a single master key from `.env`.

Complexity: Moderate (12-18 autonomous execution cycles across 3 shards).

---

## 1. PII Field Inventory

### Confirmed PII fields across all models

| Model             | Field           | Type        | Nullable | Has Index                       | Queried By Equality                                      |
| ----------------- | --------------- | ----------- | -------- | ------------------------------- | -------------------------------------------------------- |
| **Contact**       | `email`         | String(320) | Yes      | Yes (`ix_contacts_email`)       | **Yes** -- inbound email lookup by `tenant_id` + `email` |
| **Contact**       | `phone`         | String(20)  | Yes      | Yes (`ix_contacts_phone`)       | Not currently, but indexed                               |
| **Contact**       | `name`          | String(255) | No       | No                              | No                                                       |
| **Contact**       | `company`       | String(255) | Yes      | No                              | No                                                       |
| **BackupContact** | `email`         | String(320) | No       | No                              | **Yes** -- escalation emails read `backup["email"]`      |
| **BackupContact** | `phone`         | String(20)  | Yes      | No                              | Not currently                                            |
| **Account**       | `owner_email`   | String(320) | No       | Yes (`ix_accounts_owner_email`) | **Yes** -- inbound account resolution                    |
| **Account**       | `email_address` | String(320) | Yes      | No                              | **Yes** -- inbound account resolution                    |

### Fields excluded from encryption

| Model       | Field                              | Reason                                                                                                                                                  |
| ----------- | ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tenant**  | `email_domain`                     | Organization domain, not personal PII. Used for tenant lookup.                                                                                          |
| **Message** | `body_text`, `body_raw`, `subject` | These contain PII in free text but full-text encryption is a separate concern (field-level encryption of message bodies is out of scope for this plan). |

### Fields that are PII but not email/phone

The `compliance.py` module at `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/compliance.py` defines `PII_FIELDS = {"email", "phone", "name", "company"}`. The `name` and `company` fields on Contact are PII but the requirement explicitly asks for email and phone fields. This plan encrypts email and phone. Name and company can be added in a follow-up if desired (same mechanism, lower urgency since they are not used for login or routing).

---

## 2. Encryption Approach

### Column-level encryption via custom SQLAlchemy type

**Library**: `cryptography` (Fernet is built on AES-128-CBC; for AES-256-GCM we use the lower-level `Cipher` API).

**Why not Fernet**: Fernet uses AES-128-CBC with HMAC-SHA256 for authentication. The requirement specifies AES-256. We will use AES-256-GCM via `cryptography.hazmat.primitives.ciphers.aead.AESGCM`, which provides both confidentiality and integrity in a single operation.

### Custom SQLAlchemy type: `EncryptedString`

```python
# New file: src/sequor/db/encrypted_column.py

class EncryptedString(TypeDecorator):
    """SQLAlchemy column type that transparently encrypts/decrypts values.

    Stores ciphertext as base64-encoded TEXT in the database.
    Supports a companion blind index column for equality searches.
    """
    impl = Text
    cache_ok = True
```

**How it works**:

- On **write** (`process_bind_param`): plaintext -> AES-256-GCM encrypt -> base64 -> stored as TEXT
- On **read** (`process_result_value`): base64 -> AES-256-GCM decrypt -> plaintext returned to Python
- Random 12-byte nonce per encryption, prepended to ciphertext (no IV reuse)
- The encryption key is derived from `tenant_id + field_name + tenant_key`, giving per-tenant per-field key separation

### Blind index for searchable fields

For fields that are queried by equality (`Contact.email`, `Account.owner_email`, `Account.email_address`, `Contact.phone`), we need a deterministic hash so lookups still work.

**Approach**: A companion column `{field_name}_hash` storing `HMAC-SHA256(key=tenant_key, msg=normalize(plaintext))`. The hash column is indexed. Lookups become: `WHERE email_hash = HMAC(key, 'user@example.com')`.

**Normalization before hashing**:

- Email: lowercase + strip whitespace (matching `normalize_email()` in `thread_key.py`)
- Phone: digits only (matching `normalize_phone()` in `thread_key.py`)

### New columns per model

| Model         | Existing Column                   | New Hash Column                                  | Index Change                                                          |
| ------------- | --------------------------------- | ------------------------------------------------ | --------------------------------------------------------------------- |
| Contact       | `email` (TEXT, encrypted)         | `email_hash` (CHAR(64), HMAC-SHA256 hex)         | Replace `ix_contacts_email` with `ix_contacts_email_hash`             |
| Contact       | `phone` (TEXT, encrypted)         | `phone_hash` (CHAR(64), HMAC-SHA256 hex)         | Replace `ix_contacts_phone` with `ix_contacts_phone_hash`             |
| BackupContact | `email` (TEXT, encrypted)         | `email_hash` (CHAR(64), HMAC-SHA256 hex)         | No index needed (not queried by email)                                |
| BackupContact | `phone` (TEXT, encrypted)         | --                                               | No index, no hash needed (not queried)                                |
| Account       | `owner_email` (TEXT, encrypted)   | `owner_email_hash` (CHAR(64), HMAC-SHA256 hex)   | Replace `ix_accounts_owner_email` with `ix_accounts_owner_email_hash` |
| Account       | `email_address` (TEXT, encrypted) | `email_address_hash` (CHAR(64), HMAC-SHA256 hex) | New index `ix_accounts_email_address_hash`                            |

---

## 3. Key Management

### Architecture: Two-tier key hierarchy

```
Master Key (.env: ENCRYPTION_MASTER_KEY)
  |
  +-- tenant_key_1 (stored encrypted in DB, decrypted at runtime)
  |     |
  |     +-- HMAC key for blind indexes (derived: HKDF(tenant_key, "blind-index"))
  |     +-- AES key for field encryption (derived: HKDF(tenant_key, "encrypt:" + field_name))
  |
  +-- tenant_key_2 (stored encrypted in DB, decrypted at runtime)
  |     ...
```

### Master key

- Stored in `.env` as `ENCRYPTION_MASTER_KEY` (base64-encoded 32-byte random key)
- Generated once via `python -c "import base64, os; print(base64.urlsafe_b64encode(os.urandom(32)).decode())"`
- **Rotation**: changing the master key requires re-encrypting all tenant keys (rare, planned operation)

### Tenant keys

- Stored in a new `tenant_encryption_keys` table:

```python
class TenantEncryptionKey(Base):
    __tablename__ = "tenant_encryption_keys"

    tenant_id: Mapped[uuid.UUID] = mapped_column(
        Uuid, ForeignKey("tenants.id", ondelete="CASCADE"), primary_key=True
    )
    encrypted_key: Mapped[str] = mapped_column(Text, nullable=False)
    key_version: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, default=_now)
    rotated_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
```

- `encrypted_key` = AES-256-GCM encrypt(tenant_key, master_key)
- Tenant key is a random 32-byte key, generated on tenant creation
- Decrypted once at runtime and cached in-process (with a TTL or invalidation on rotation)
- **Key loss consequence**: If the master key is lost, all encrypted PII is unrecoverable. If a tenant key is lost (but master key exists), it can be re-derived or the tenant's data re-encrypted.

### Key derivation per field

```python
def derive_field_key(tenant_key: bytes, field_name: str) -> bytes:
    """Derive a per-field encryption key using HKDF-SHA256."""
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=f"sequor:encrypt:{field_name}".encode(),
    )
    return hkdf.derive(tenant_key)

def derive_blind_index_key(tenant_key: bytes) -> bytes:
    """Derive the HMAC key for blind indexes."""
    from cryptography.hazmat.primitives.kdf.hkdf import HKDF
    from cryptography.hazmat.primitives import hashes
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"sequor:blind-index",
    )
    return hkdf.derive(tenant_key)
```

### Key provisioning

- On tenant creation: generate 32 random bytes, encrypt with master key, store in `tenant_encryption_keys`
- For existing tenants: a migration script generates and stores tenant keys
- Key access: decrypt tenant key from DB using master key, cache in a `dict[tenant_id, bytes]` with LRU eviction

---

## 4. File-by-File Change Inventory

### New files

| File                                                                   | Purpose                                                                                                  | Est. LOC |
| ---------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------- | -------- |
| `src/sequor/db/encrypted_column.py`                                    | `EncryptedString` SQLAlchemy type, `encrypt_value()`, `decrypt_value()`, `compute_blind_index()` helpers | ~120     |
| `src/sequor/db/encryption_keys.py`                                     | `TenantEncryptionKey` model, `KeyManager` class (cache, derive, rotate)                                  | ~100     |
| `src/sequor/db/migrations/versions/XXXX_add_pii_encryption.py`         | Alembic migration: add hash columns, alter column types, add/remove indexes                              | ~80      |
| `src/sequor/db/migrations/versions/XXXX_encrypt_existing_plaintext.py` | Data migration: read plaintext, encrypt, write back, drop old indexes                                    | ~60      |
| `tests/unit/test_encrypted_column.py`                                  | Unit tests for encrypt/decrypt/blind-index                                                               | ~80      |
| `tests/unit/test_encryption_keys.py`                                   | Unit tests for KeyManager, key derivation, rotation                                                      | ~70      |
| `tests/regression/test_pii_encryption_regression.py`                   | Regression: plaintext in DB is gone, blind index lookup works                                            | ~50      |

### Modified files

| File                                  | Changes                                                                                                                                                                                                                                                                                                                                                                                                                                    | Est. LOC Changed  |
| ------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ----------------- |
| `src/sequor/db/models.py`             | (1) Change `Contact.email` and `Contact.phone` column types to `EncryptedString`. (2) Add `email_hash`, `phone_hash` columns. (3) Change `BackupContact.email` and `BackupContact.phone` to `EncryptedString`. Add `email_hash`. (4) Change `Account.owner_email` and `Account.email_address` to `EncryptedString`. Add `owner_email_hash`, `email_address_hash`. (5) Update indexes: drop old plaintext indexes, add hash-column indexes. | ~40               |
| `src/sequor/compliance.py`            | Update `ERASURE_NULL_FIELDS` to also clear `email_hash`, `phone_hash` when erasing a contact.                                                                                                                                                                                                                                                                                                                                              | ~5                |
| `src/sequor/email/inbound.py`         | `InboundEmailProcessor._resolve_or_create_contact()`: pass `email_hash` when creating a Contact. `_resolve_account()`: query by `email_address_hash` and `owner_email_hash` instead of plaintext columns.                                                                                                                                                                                                                                  | ~15               |
| `src/sequor/escalation/service.py`    | `EscalationService.create_escalation()`: reads `backup["email"]` -- this now auto-decrypts via the SQLAlchemy type, **no change needed** in the service layer. However, the `_mask_email()` bug at lines 175 and 302 passes masked email as `to` address (sending to `j***@example.com`). This is a pre-existing bug to fix separately.                                                                                                    | ~0 (auto-decrypt) |
| `src/sequor/escalation/thread_key.py` | `derive_thread_key()` reads `contact_email` and `contact_phone` -- these now auto-decrypt, **no change needed**. The `normalize_email()` and `normalize_phone()` functions continue to work on decrypted values.                                                                                                                                                                                                                           | ~0                |
| `src/sequor/config.py`                | Add `encryption_master_key: str = ""` setting.                                                                                                                                                                                                                                                                                                                                                                                             | ~2                |
| `pyproject.toml`                      | Add `cryptography>=43.0` to dependencies.                                                                                                                                                                                                                                                                                                                                                                                                  | ~1                |
| `.env.example`                        | Add `ENCRYPTION_MASTER_KEY=` placeholder with instructions.                                                                                                                                                                                                                                                                                                                                                                                | ~3                |
| `alembic.ini`                         | No changes (already configured).                                                                                                                                                                                                                                                                                                                                                                                                           | ~0                |

### Files that require NO changes (auto-decrypted by SQLAlchemy type)

These files read PII from model instances returned by SQLAlchemy queries. Because the `EncryptedString` type handles decryption transparently in `process_result_value`, these files see plaintext values as before:

- `src/sequor/escalation/service.py` -- reads `backup["email"]` (auto-decrypted)
- `src/sequor/escalation/thread_key.py` -- receives already-decrypted values
- `src/sequor/email/sender.py` -- receives email addresses as strings (already decrypted)
- `src/sequor/email/templates.py` -- receives contact names (not encrypted in this phase)
- `src/sequor/ai/learning.py` -- no PII fields touched
- `src/sequor/ai/response.py` -- no PII fields touched
- `src/sequor/ai/classifier.py` -- no PII fields touched

### Critical caveat: DataFlow express API

The inbound email processor uses `self._db.list("Contact", {"tenant_id": ..., "email": ...})` and `self._db.list("Account", {"email_address": ...})`. If this `db` is a Kailash DataFlow `db.express` instance, DataFlow's query engine constructs SQL `WHERE` clauses from the filter dict. When the column type is `EncryptedString`, a filter like `{"email": "user@example.com"}` will encrypt the value and compare it to encrypted column values -- which will fail because encryption is non-deterministic (random nonce).

**This is the most important design decision**: the blind index columns exist precisely to solve this. The query pattern must change to:

```python
# Before (plaintext query):
await self._db.list("Contact", {"tenant_id": tenant_id, "email": email})

# After (blind index query):
email_hash = compute_blind_index(tenant_key, email, field="email")
await self._db.list("Contact", {"tenant_id": tenant_id, "email_hash": email_hash})
```

This means `InboundEmailProcessor` needs access to the `KeyManager` to compute blind indexes before querying. Alternatively, a thin wrapper around `db.express.list()` can intercept PII field filters and redirect them to hash columns automatically.

**Recommended approach**: Create a `PIIAwareDB` wrapper that intercepts queries on encrypted fields:

```python
class PIIAwareDB:
    """Wraps db.express to automatically redirect PII field queries to hash columns."""

    def __init__(self, db_express, key_manager):
        self._db = db_express
        self._keys = key_manager

    async def list(self, model_name: str, filters: dict) -> list[dict]:
        enhanced = self._redirect_pii_filters(model_name, filters)
        return await self._db.list(model_name, enhanced)
```

This adds ~50 LOC to `src/sequor/db/encrypted_column.py` and requires the inbound processor and any other caller to use `PIIAwareDB` instead of raw `db.express` when querying by PII fields.

---

## 5. Migration Strategy

### Phase 1: Schema migration (add columns, keep plaintext)

1. Add `email_hash`, `phone_hash`, `owner_email_hash`, `email_address_hash` columns (nullable initially)
2. Add `tenant_encryption_keys` table
3. **Do not** alter existing email/phone columns yet

### Phase 2: Backfill (encrypt existing data)

1. Generate a tenant encryption key for each existing tenant
2. For each row with PII:
   a. Compute blind index hash from plaintext value
   b. Store hash in the new `*_hash` column
3. Create new indexes on hash columns
4. Backfill all tenant keys into `tenant_encryption_keys`

### Phase 3: Encrypt columns (in-place)

1. Alter column types from `String` to `EncryptedString` (stored as `TEXT`)
2. For each row:
   a. Read plaintext value
   b. Encrypt with tenant's derived field key
   c. Write encrypted value back
3. Drop old plaintext indexes (`ix_contacts_email`, `ix_contacts_phone`, `ix_accounts_owner_email`)
4. Verify: run a check query that no row has a plaintext-looking value in the encrypted columns

### Phase 4: Enforce not-null on hash columns

1. After all rows have hash values, add `NOT NULL` constraint to hash columns
2. Update the ORM model to mark hash columns as `nullable=False`

### Rollback plan

Each Alembic migration has a `downgrade()`:

- Phase 3 downgrade: decrypt all values back to plaintext, restore original column types
- Phase 2 downgrade: drop hash columns
- Phase 1 downgrade: drop `tenant_encryption_keys` table

**Downtime**: The schema change (Phase 1) is non-blocking (adding nullable columns). The backfill and encryption (Phases 2-3) can run with the application online if queries use the hash columns for new writes while the migration processes old rows. For safety, recommend a brief maintenance window during Phase 3.

---

## 6. Search Compatibility

### Equality lookups (the common case)

All current PII queries are equality lookups (`WHERE email = '...'`). These are handled by blind index columns.

| Query Site                                        | Current Pattern                                     | New Pattern                                               |
| ------------------------------------------------- | --------------------------------------------------- | --------------------------------------------------------- |
| InboundEmailProcessor.\_resolve_or_create_contact | `list("Contact", {"tenant_id": ..., "email": ...})` | `list("Contact", {"tenant_id": ..., "email_hash": hash})` |
| InboundEmailProcessor.\_resolve_account           | `list("Account", {"email_address": ...})`           | `list("Account", {"email_address_hash": hash})`           |
| InboundEmailProcessor.\_resolve_account           | `list("Account", {"owner_email": ...})`             | `list("Account", {"owner_email_hash": hash})`             |

### Partial / LIKE queries (not currently used)

No code currently does `LIKE '%@gmail.com'` or similar. If this is needed in the future, options are:

1. Maintain a separate `email_domain` column (extracted at write time, not encrypted) for domain-level filtering
2. Use a server-side encryption proxy (e.g., pgcrypto with deterministic encryption for specific use cases)
3. Accept that partial matching is not possible on encrypted data and filter in application code after decryption

### Sorting

No code sorts by email or phone. Sorting by encrypted values produces meaningless order. If sorting is needed in the future, sort by `name` instead or decrypt in application code.

---

## 7. Risk Register

| Risk                                                                      | Likelihood | Impact                                  | Mitigation                                                                                                                                                              |
| ------------------------------------------------------------------------- | ---------- | --------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Master key loss** -- all encrypted data unrecoverable                   | Low        | **Critical** (permanent data loss)      | (1) Store master key in multiple secure locations (secrets manager, offline backup). (2) Document key recovery procedure. (3) Consider HSM or cloud KMS for production. |
| **Migration fails mid-encryption** -- some rows encrypted, some plaintext | Medium     | **Major** (inconsistent state)          | (1) Run in a transaction per tenant. (2) Track migration progress per tenant. (3) Migration is idempotent: can re-run safely.                                           |
| **Performance regression** -- encryption/decryption per row               | Medium     | **Significant**                         | (1) Key caching avoids per-query key derivation. (2) Benchmark before/after. (3) Batch decrypt is fast with cached keys (~1us per value).                               |
| **Tenant key not found** -- new tenant created without key                | Low        | **Major** (cannot encrypt/decrypt)      | (1) Key generation is part of tenant creation flow. (2) Runtime guard: raise typed error if key missing. (3) Health check includes key existence verification.          |
| **DataFlow incompatibility** -- `db.express` filter on encrypted column   | Medium     | **Major** (query returns no results)    | (1) `PIIAwareDB` wrapper intercepts PII filters. (2) Unit tests for every query path. (3) Fallback: raw SQL query via session if wrapper insufficient.                  |
| **Blind index collision** -- two values produce same hash                 | Very Low   | **Significant** (wrong record returned) | (1) SHA-256 collision probability is negligible (~2^-128). (2) Application code already handles multiple results (takes first).                                         |
| **Nonce reuse** -- same key+nonce encrypts two values                     | Very Low   | **Critical** (cryptographic break)      | (1) Random 12-byte nonce per encryption call. (2) Nonce is generated inside `AESGCM.encrypt()` which uses `os.urandom(12)`. No manual nonce management.                 |
| **Key rotation downtime** -- re-encrypting all tenant data                | Low        | **Significant** (service degraded)      | (1) Dual-key support: old key decrypts, new key encrypts. (2) Background rotation process. (3) Track key version per tenant.                                            |

---

## 8. Performance Considerations

### Encryption overhead

- AES-256-GCM encryption/decryption: ~1us per 100 bytes on modern hardware
- Key derivation (HKDF): ~10us per derivation, cached after first use
- Blind index computation (HMAC-SHA256): ~1us per value
- Expected throughput impact: < 5% on read-heavy workloads, < 10% on write-heavy workloads

### Index performance

- Blind index columns are fixed-length CHAR(64) (hex-encoded SHA-256)
- B-tree index on CHAR(64) is efficient for equality lookups
- No performance regression vs current VARCHAR(320) email indexes

### Memory

- Key cache: 32 bytes per tenant. At 10,000 tenants: ~320 KB. Negligible.
- No ciphertext expansion concern: encrypted values are ~50% larger than plaintext (base64 + nonce + tag), but still fits in TEXT columns

---

## 9. Implementation Roadmap

### Shard 1: Foundation (schema + encryption primitives)

**Files**: `encrypted_column.py`, `encryption_keys.py`, `models.py`, `config.py`, `pyproject.toml`, `.env.example`

1. Add `cryptography` to `pyproject.toml`
2. Add `ENCRYPTION_MASTER_KEY` to `Settings` in `config.py`
3. Create `src/sequor/db/encrypted_column.py` with `EncryptedString` type and `compute_blind_index()`
4. Create `src/sequor/db/encryption_keys.py` with `TenantEncryptionKey` model and `KeyManager`
5. Write unit tests for encrypt/decrypt/derive/blind-index (Tier 1)
6. Add Alembic migration for schema changes (new columns, new table)

**Load-bearing LOC**: ~220 logic + ~150 tests
**Invariants**: encrypt-then-decrypt = identity, blind index is deterministic, wrong key fails with typed error

### Shard 2: Query layer + inbound processor

**Files**: `encrypted_column.py` (add `PIIAwareDB`), `email/inbound.py`, `compliance.py`

1. Add `PIIAwareDB` wrapper to `encrypted_column.py`
2. Modify `InboundEmailProcessor` to use `PIIAwareDB` for account/contact resolution
3. Update `compliance.py` `ERASURE_NULL_FIELDS` to clear hash columns
4. Write unit tests for `PIIAwareDB` filter redirection (Tier 1)
5. Write integration test: create contact via encrypted path, resolve by email hash (Tier 2)

**Load-bearing LOC**: ~80 logic + ~100 tests
**Invariants**: PII filter redirects to hash column, blind index lookup returns correct record, erasure clears both value and hash

### Shard 3: Data migration + verification

**Files**: Alembic data migration, `test_pii_encryption_regression.py`

1. Write Alembic data migration: generate tenant keys, compute blind indexes, encrypt existing values
2. Write downgrade: decrypt back to plaintext, drop hash columns
3. Write regression test: verify no plaintext emails in DB after migration
4. Run migration against staging database
5. Verify all inbound email flows still work end-to-end

**Load-bearing LOC**: ~140 migration + ~50 tests
**Invariants**: migration is idempotent, downgrade restores plaintext, no data loss

---

## 10. Success Criteria

- [ ] All email and phone values in the database are stored as AES-256-GCM ciphertext
- [ ] No plaintext email/phone in any database column (verified by grep-like query)
- [ ] Contact lookup by email (inbound email flow) works via blind index
- [ ] Account resolution by `email_address` and `owner_email` works via blind index
- [ ] Escalation emails are delivered to the correct backup contact (auto-decrypt transparent)
- [ ] PDPA erasure clears both encrypted value and blind index hash
- [ ] Master key is not stored in the database or in git
- [ ] Tenant key rotation is possible without downtime (dual-key support)
- [ ] Performance impact < 10% on measured query latency
- [ ] Full downgrade path exists (Alembic `downgrade()` restores plaintext)

---

## 11. Pre-existing Bug Note

During this analysis, I found a bug at `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/escalation/service.py` lines 175 and 302:

```python
to=_mask_email(backup["email"]),
```

`_mask_email()` converts `john@example.com` to `j***@example.com`. This masked value is then passed as the `to` parameter to `send_escalation_email()`, meaning escalation emails are being sent to an invalid address. The masking should only be used for logging, not for the actual send. This is unrelated to encryption but will prevent escalation emails from working and should be fixed before the encryption work begins (or in the same PR, since it is in the same code path).

---

## 12. Estimated Effort

| Component                          | LOC (Logic) | LOC (Tests) | Autonomous Cycles             |
| ---------------------------------- | ----------- | ----------- | ----------------------------- |
| Encryption primitives (Shard 1)    | ~220        | ~150        | 2-3                           |
| Query layer + inbound (Shard 2)    | ~80         | ~100        | 2-3                           |
| Data migration (Shard 3)           | ~140        | ~50         | 2-3                           |
| Schema migration + models          | ~40         | --          | 1                             |
| Integration testing + verification | --          | ~100        | 2-3                           |
| **Total**                          | **~480**    | **~400**    | **~12 cycles (3-4 sessions)** |

The `name` and `company` fields on Contact are PII per `compliance.py` but are not included in this plan. Adding them follows the same pattern (encrypted column + optional blind index) and would add ~40 LOC to the models change and one migration step.
