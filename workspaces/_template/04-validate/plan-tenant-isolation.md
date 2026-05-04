# Plan: Per-Tenant PostgreSQL Schema Isolation

## Executive Summary

Sequor currently stores all tenant data in shared tables, separated by a `tenant_id` column on every model except `Tenant` itself. This plan migrates to per-tenant PostgreSQL schemas where each tenant gets its own schema (e.g., `tenant_abc123`) containing private copies of all tenant-scoped tables. The `tenants` table remains in the `public` schema as the shared registry.

Complexity: **Complex** (cross-cutting, ~14 files, ~1200-1500 LOC of load-bearing changes, migration strategy with dual-read period).

---

## 1. Current State Analysis

### 1.1 Data Model Summary

**Shared table (public schema, no `tenant_id`):**

- `tenants` -- the tenant registry itself

**Tenant-scoped tables (all have `tenant_id` FK to `tenants.id`):**

- `accounts` -- tenant's accounts
- `backup_contacts` -- backup contacts per account
- `contacts` -- external contacts
- `channel_consents` -- consent records
- `messages` -- inbound/outbound messages
- `classifications` -- AI classification results
- `rag_retrievals` -- RAG retrieval records
- `documents` -- uploaded documents
- `document_chunks` -- chunked document text with embeddings
- `learned_answers` -- AI-learned responses
- `responses` -- AI/human responses
- `escalations` -- escalation records
- `audit_entries` -- audit log
- `routing_outcomes` -- routing decision records

### 1.2 Two Access Patterns

The codebase uses **two distinct database access patterns**:

**Pattern A: SQLAlchemy AsyncSession (direct ORM)**
Used by `onboarding/service.py` and `billing/service.py`. These use `session.execute(select(...))`, `session.get()`, `session.add()`, `session.flush()`, `session.commit()`.

**Pattern B: DataFlow db.express (CRUD abstraction)**
Used by `escalation/service.py`, `email/inbound.py`, `digest/service.py`, `escalation/scheduler.py`. These use `db.read()`, `db.list()`, `db.create()`, `db.update()` -- the DataFlow express API from `kailash-dataflow`.

### 1.3 Schema Name Strategy

Tenant schema names will use the format `tenant_{uuid_hex}` where the hex is derived from the tenant's UUID. For example, tenant `550e8400-e29b-41d4-a716-446655440000` maps to schema `tenant_550e8400e29b41d4a716446655440000`. The 32-char hex is safe for PostgreSQL identifier rules (letters+digits, starts with letter via `tenant_` prefix).

---

## 2. Change Impact Map

### 2.1 Files That Must Change

| #   | File                                 | Lines   | Access Pattern | What Changes                                                                                                                                                         |
| --- | ------------------------------------ | ------- | -------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 1   | `src/sequor/db/database.py`          | 82      | Engine         | Add schema-per-session middleware; provide `get_tenant_engine()` or `set_search_path()` helper                                                                       |
| 2   | `src/sequor/db/models.py`            | 698     | ORM            | Split into `public_models.py` (Tenant) and `tenant_models.py` (everything else); remove `tenant_id` FK columns from tenant-scoped models; remove `tenant_id` indexes |
| 3   | `src/sequor/db/base.py`              | 10      | ORM            | Add `TenantBase` with schema-overriding metadata for tenant-scoped models                                                                                            |
| 4   | `src/sequor/db/schema_manager.py`    | **NEW** | DDL            | Schema creation/deletion service: `create_tenant_schema()`, `drop_tenant_schema()`, `migrate_tenant_schema()`                                                        |
| 5   | `src/sequor/onboarding/service.py`   | 193     | AsyncSession   | After creating the Tenant, call `create_tenant_schema()`; remove `tenant_id` from Account/BackupContact creation; set search_path before inserts                     |
| 6   | `src/sequor/onboarding/api.py`       | 49      | AsyncSession   | Pass tenant context to session so search_path is set                                                                                                                 |
| 7   | `src/sequor/billing/service.py`      | 226     | AsyncSession   | No structural change needed (operates on Tenant in public schema), but verify no cross-schema queries                                                                |
| 8   | `src/sequor/escalation/service.py`   | 656     | db.express     | All db.express calls must go through tenant-scoped session; remove `tenant_id` from filter dicts                                                                     |
| 9   | `src/sequor/escalation/scheduler.py` | 113     | db.express     | Tenant enumeration stays on public schema; per-tenant calls must switch search_path                                                                                  |
| 10  | `src/sequor/email/inbound.py`        | 211     | db.express     | `_resolve_account()` must search across tenant schemas (or keep accounts in public); remove `tenant_id` from Message/Contact creation                                |
| 11  | `src/sequor/digest/service.py`       | 239     | db.express     | All db.express calls need tenant-scoped search_path; remove `tenant_id` from filter dicts                                                                            |
| 12  | `src/sequor/db/migrations/env.py`    | 49      | Alembic        | Must handle per-schema migrations; add `--schema` option or iterate all tenant schemas                                                                               |
| 13  | `src/sequor/db/migrations/versions/` | N/A     | Alembic        | New migration: create `tenant_schema_template()` SQL function; add `schema_name` column to `tenants` table                                                           |
| 14  | `tests/`                             | N/A     | Tests          | All integration tests need tenant context setup                                                                                                                      |

### 2.2 Files That Do NOT Change

| File                                  | Why                           |
| ------------------------------------- | ----------------------------- |
| `src/sequor/config.py`                | No database query logic       |
| `src/sequor/schemas.py`               | Pydantic validation only      |
| `src/sequor/protocols.py`             | Protocol interfaces only      |
| `src/sequor/compliance.py`            | No database logic             |
| `src/sequor/email/sender.py`          | No database logic (SMTP only) |
| `src/sequor/email/templates.py`       | Pure functions, no DB         |
| `src/sequor/email/rate_limiter.py`    | In-memory rate limiter        |
| `src/sequor/email/parser.py`          | Parsing only                  |
| `src/sequor/escalation/sla.py`        | Pure datetime math            |
| `src/sequor/escalation/thread_key.py` | Pure hashing                  |

### 2.3 Estimated LOC Impact

| Category                        | Files                     | LOC Changed/Added                                                |
| ------------------------------- | ------------------------- | ---------------------------------------------------------------- |
| New schema manager module       | 1 new file                | ~200 LOC                                                         |
| Model restructuring             | 2 files (models.py split) | ~300 LOC changed                                                 |
| Database engine/session helpers | 2 files                   | ~120 LOC added                                                   |
| Service layer changes           | 5 files                   | ~250 LOC changed (mostly removing `tenant_id` from filter dicts) |
| Migration scripts               | 2-3 new files             | ~150 LOC                                                         |
| Tests (new + modified)          | 5-8 files                 | ~300 LOC                                                         |
| **Total**                       | **~17-20 files**          | **~1320 LOC**                                                    |

---

## 3. Detailed Design

### 3.1 Schema Naming and Registry

Add a `schema_name` column to the `tenants` table in the public schema. This column is the canonical mapping from tenant to PostgreSQL schema.

```sql
ALTER TABLE public.tenants ADD COLUMN schema_name TEXT NOT NULL DEFAULT '';
-- For each existing tenant:
UPDATE public.tenants SET schema_name = 'tenant_' || REPLACE(id::text, '-', '');
```

The `schema_name` column is set during tenant creation and never changes. It is derived deterministically from the tenant UUID so it can be reconstructed if needed, but storing it explicitly avoids recomputation and allows the column to be indexed.

### 3.2 Model Split

Split `models.py` into two modules:

**`src/sequor/db/public_models.py`** -- stays in `public` schema:

- `Tenant` (with new `schema_name` column)

**`src/sequor/db/tenant_models.py`** -- deployed into each tenant schema:

- `Account` (no `tenant_id` FK, no `tenant_id` index)
- `BackupContact` (no `tenant_id` FK)
- `Contact` (no `tenant_id` FK)
- `ChannelConsent` (no `tenant_id` FK)
- `Message` (no `tenant_id` FK)
- `Classification` (no `tenant_id` FK)
- `RAGRetrieval` (no `tenant_id` FK)
- `Document` (no `tenant_id` FK)
- `DocumentChunk` (no `tenant_id` FK; remove `tenant_id` from UniqueConstraint)
- `LearnedAnswer` (no `tenant_id` FK)
- `Response` (no `tenant_id` FK)
- `Escalation` (no `tenant_id` FK)
- `AuditEntry` (no `tenant_id` FK)
- `RoutingOutcome` (no `tenant_id` FK)

**Key structural changes to each tenant-scoped model:**

1. Remove the `tenant_id: Mapped[uuid.UUID]` column definition
2. Remove `ForeignKey("tenants.id", ondelete="CASCADE")` -- no cross-schema FK
3. Remove `Index("ix_{table}_tenant_id", "tenant_id")` -- no tenant_id column
4. Remove `tenant_id` from any `UniqueConstraint` (e.g., `DocumentChunk`)
5. Remove `tenant = relationship("Tenant", ...)` relationships
6. Change `__table_args__` to use `schema` parameter or rely on search_path

**Cross-schema foreign keys:** PostgreSQL supports cross-schema FKs, but they are fragile for schema isolation (dropping a tenant schema can cascade unexpectedly). The plan removes FKs from `tenants.id` on tenant-scoped tables. The relationship is maintained at the application layer, not the database constraint layer. This is the standard trade-off for schema-based isolation.

### 3.3 Session/Search Path Management

#### For SQLAlchemy AsyncSession (Pattern A)

Create a helper in `database.py`:

```python
async def get_tenant_session(tenant_id: uuid.UUID) -> AsyncGenerator[AsyncSession, None]:
    """Yield a session with search_path set to the tenant's schema."""
    engine = get_engine()
    async with AsyncSession(engine) as session:
        # Look up schema_name from public.tenants
        from sequor.db.public_models import Tenant
        from sqlalchemy import select
        result = await session.execute(
            select(Tenant.schema_name).where(Tenant.id == tenant_id)
        )
        schema_name = result.scalar_one_or_none()
        if schema_name is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        await session.execute(text(f'SET search_path TO "{schema_name}", public'))
        yield session
```

#### For DataFlow db.express (Pattern B)

DataFlow express operates at a higher level. Two options:

**Option A (Recommended): Pass tenant context to express calls.**
DataFlow's express API would need a `tenant_id` parameter that sets `search_path` before executing queries. This requires checking whether `kailash-dataflow` supports a `search_path` hook or connection event listener. If not, we need a thin wrapper:

```python
class TenantScopedExpress:
    def __init__(self, db_express, tenant_id: uuid.UUID, schema_name: str):
        self._express = db_express
        self._schema = schema_name

    async def _with_schema(self, coro):
        """Set search_path, execute coroutine, reset."""
        # This requires the underlying connection pool to support
        # per-connection SET search_path. If db.express uses a
        # connection pool, we need to use connection events.
        ...
```

**Option B: Use connection pool events.**
Register a SQLAlchemy `PoolEvents.checkout` listener that sets `search_path` based on a thread-local or context variable. This is more transparent but requires careful lifecycle management.

**Decision:** Option A is preferred because it makes the tenant context explicit at every call site, preventing accidental cross-tenant queries. The implementation depends on whether DataFlow's express API exposes the underlying connection. If it does not, we need a minimal adapter. This is the primary technical risk (see Section 6).

### 3.4 Schema Creation (On Signup)

When a new tenant signs up via `onboarding/service.py`:

1. Create the `Tenant` record in `public.tenants` (including `schema_name`)
2. `CREATE SCHEMA "{schema_name}"`
3. Create all tenant-scoped tables in the new schema: `CREATE TABLE "{schema_name}".accounts (...)`, etc.
4. Continue with Account and BackupContact creation using the tenant-scoped session

The table creation DDL is templated from the SQLAlchemy metadata. The `schema_manager.py` module provides:

```python
async def create_tenant_schema(conn, schema_name: str) -> None:
    """Create a new schema and deploy all tenant-scoped tables."""
    await conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
    # Use metadata.create_all with schema= parameter
    tenant_metadata.create_all(conn, schema=schema_name)
```

### 3.5 Schema Deletion (On Tenant Deletion)

```python
async def drop_tenant_schema(conn, schema_name: str, *, force: bool = False) -> None:
    """Drop a tenant schema and all its data. Requires force=True."""
    if not force:
        raise RuntimeError("pass force=True to acknowledge data loss")
    _validate_identifier(schema_name)  # prevent injection
    await conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
```

Identifier validation uses the `^[a-zA-Z_][a-zA-Z0-9_]*$` regex per `rules/dataflow-identifier-safety.md`.

### 3.6 Migration Strategy

#### New Tenants

New tenants get their schema created with the latest migration applied (via `metadata.create_all`). No migration history tracking needed for new tenants -- they start at the current schema version.

#### Existing Tenants

Alembic migrations need to run against every tenant schema. The approach:

1. Add a `schema_name` column to `public.tenants` (single migration on public schema)
2. Create a migration runner that:
   a. Reads all `schema_name` values from `public.tenants`
   b. For each schema, sets `search_path` to that schema
   c. Runs the tenant-scoped migration
   d. Tracks per-schema migration state in `public.tenant_schema_versions` table

```python
# New table in public schema:
class TenantSchemaVersion(Base):
    __tablename__ = "tenant_schema_versions"
    tenant_id: Mapped[uuid.UUID] = mapped_column(Uuid, ForeignKey("tenants.id"), primary_key=True)
    current_version: Mapped[str] = mapped_column(String(100), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
```

#### Migration `env.py` Changes

The Alembic `env.py` at `src/sequor/db/migrations/env.py` needs to support two modes:

1. **Public schema mode** -- runs migrations against the public schema (for `tenants` table changes)
2. **Tenant schema mode** -- iterates all tenant schemas and runs migrations against each

This can be controlled via an environment variable or Alembic command-line flag.

### 3.7 Cross-Schema Queries

Some operations need to query across tenant schemas:

| Operation                        | Current Approach                                 | Schema-Isolated Approach                                                  |
| -------------------------------- | ------------------------------------------------ | ------------------------------------------------------------------------- |
| SLA scheduler                    | Lists all tenants, then queries per tenant       | Same pattern -- list tenants from public, then set search_path per tenant |
| Digest send_all_tenants          | Lists all tenants                                | Same pattern                                                              |
| Inbound email `_resolve_account` | Queries `Account` by email with no tenant filter | **Problem**: which schema contains this email?                            |
| Billing webhook                  | Looks up Tenant by metadata                      | Stays on public schema                                                    |

**The critical cross-schema query is `_resolve_account` in `email/inbound.py`.** When an inbound email arrives, the system needs to find which account (and therefore which tenant schema) owns the target email address. Two solutions:

**Solution A: Keep a shallow `public.account_email_index` table.**
A denormalized index table in the public schema containing only `(email, tenant_id, account_id)`. Maintained via triggers or application-level writes on account creation/update. The inbound processor queries this index, gets the tenant_id, then switches to that tenant's schema for the full operation.

**Solution B: Full scan across schemas.**
Query each tenant schema's `accounts` table. This is O(n_tenants) and not viable at scale.

**Decision: Solution A.** The denormalized index is small (one row per account email), easy to maintain, and keeps the inbound processing path O(1).

### 3.8 What Stays in Public Schema

| Table                    | Why                                                           |
| ------------------------ | ------------------------------------------------------------- |
| `tenants`                | Registry of all tenants, needed before search_path can be set |
| `tenant_schema_versions` | Migration tracking per tenant                                 |
| `account_email_index`    | Cross-tenant email lookup for inbound routing                 |

---

## 4. Implementation Phases

### Phase 1: Infrastructure (Shard 1, ~200 LOC, 2-3 invariants)

**Files created/modified:**

- `src/sequor/db/schema_manager.py` (NEW) -- schema create/drop/migrate
- `src/sequor/db/database.py` -- add `get_tenant_session()` helper
- `src/sequor/db/base.py` -- add `TenantBase` with schema-aware metadata

**Invariants:** tenant schema creation creates all 14 tables, identifier validation rejects injection payloads, search_path is set correctly.

### Phase 2: Model Restructuring (Shard 2, ~300 LOC, 3 invariants)

**Files modified:**

- `src/sequor/db/models.py` -- split into `public_models.py` and `tenant_models.py`
- Remove `tenant_id` columns, FKs, and indexes from all tenant-scoped models
- Add `schema_name` to Tenant model
- Update `database.py` `init_db()` to create both public and tenant tables
- Update all imports across the codebase

**Invariants:** All 14 tenant-scoped models have no `tenant_id` column, Tenant model has `schema_name`, imports resolve correctly.

### Phase 3: Service Layer Migration (Shard 3-5, ~250 LOC, 3 shards)

**Shard 3: Onboarding + Billing** (~80 LOC changed)

- `src/sequor/onboarding/service.py` -- call `create_tenant_schema()`, remove `tenant_id` from Account/BackupContact, use tenant-scoped session
- `src/sequor/onboarding/api.py` -- adapt session creation
- `src/sequor/billing/service.py` -- verify public-schema-only access

**Shard 4: Escalation + Digest + Scheduler** (~100 LOC changed)

- `src/sequor/escalation/service.py` -- remove `tenant_id` from all filter dicts, accept `schema_name` parameter
- `src/sequor/escalation/scheduler.py` -- look up schema_name per tenant, set search_path per tick
- `src/sequor/digest/service.py` -- remove `tenant_id` from filter dicts, set search_path per tenant

**Shard 5: Inbound Email** (~70 LOC changed)

- `src/sequor/email/inbound.py` -- use `account_email_index` for routing, set search_path for message creation
- Create `account_email_index` maintenance logic

### Phase 4: Migration Framework (Shard 6, ~150 LOC)

**Files modified:**

- `src/sequor/db/migrations/env.py` -- dual-mode (public + tenant schemas)
- New Alembic migration: add `schema_name` to `tenants`, create `account_email_index`
- Migration script to migrate existing data from shared tables to per-tenant schemas

### Phase 5: Data Migration Script (~200 LOC)

**New file:** `scripts/migrate_to_schema_isolation.py`

This script:

1. Creates a schema for each existing tenant
2. Copies data from public tables into tenant schemas (filtered by `tenant_id`)
3. Validates row counts match
4. Drops `tenant_id` columns from tenant-scoped tables in public schema (after verification)

### Phase 6: Tests (~300 LOC)

- New integration tests for schema creation/deletion
- New tests for cross-schema queries (account_email_index)
- Modified existing tests to include tenant context
- Regression tests for migration script

---

## 5. The `account_email_index` Denormalized Index

### Schema

```sql
CREATE TABLE public.account_email_index (
    email TEXT NOT NULL PRIMARY KEY,
    tenant_id UUID NOT NULL REFERENCES public.tenants(id),
    account_id UUID NOT NULL,
    schema_name TEXT NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_aei_tenant_id ON public.account_email_index(tenant_id);
```

### Maintenance Points

| Event                        | Action                          |
| ---------------------------- | ------------------------------- |
| Account created (onboarding) | INSERT into account_email_index |
| Account email updated        | UPDATE account_email_index      |
| Account deleted              | DELETE from account_email_index |
| Tenant deleted               | CASCADE deletes via FK          |

---

## 6. Risk Register

| #   | Risk                                                                                             | Likelihood | Impact       | Mitigation                                                                                                                          |
| --- | ------------------------------------------------------------------------------------------------ | ---------- | ------------ | ----------------------------------------------------------------------------------------------------------------------------------- |
| 1   | DataFlow db.express does not expose connection-level `search_path` control                       | Medium     | **Critical** | Pre-implementation spike: verify DataFlow's connection lifecycle. If blocked, fall back to raw SQLAlchemy sessions for all queries. |
| 2   | Cross-schema foreign keys from `public.tenants` to tenant tables silently break                  | Low        | Major        | Do not use cross-schema FKs. Application-layer enforcement only. Add integration test that verifies no cross-schema FKs exist.      |
| 3   | Data migration script loses rows during copy from shared to per-tenant tables                    | Low        | **Critical** | Migration script runs in a transaction; validates row counts per table per tenant before committing. Rollback on mismatch.          |
| 4   | Performance regression from `SET search_path` per query                                          | Low        | Significant  | PostgreSQL caches search_path per session. Use connection pool with per-connection tenant affinity (set once, reuse).               |
| 5   | Alembic migration runner fails mid-tenant, leaving some schemas at old version                   | Medium     | Major        | Per-schema version tracking in `tenant_schema_versions`. Runner is idempotent -- re-run picks up where it left off.                 |
| 6   | `account_email_index` drifts from actual account data                                            | Medium     | Major        | Application-level writes are co-transactional with account creation. Add periodic reconciliation job.                               |
| 7   | Schema count grows beyond PostgreSQL limits                                                      | Low        | Minor        | PostgreSQL handles thousands of schemas well. Monitor via `pg_namespace` count. Add schema archival for deleted tenants.            |
| 8   | pgvector indexes in per-schema `document_chunks` tables cause high memory usage during migration | Medium     | Significant  | Create indexes after data migration, not during schema creation. Add `CONCURRENTLY` flag.                                           |

---

## 7. Migration Strategy: Incremental, Not All-or-Nothing

This change CAN be done incrementally. Here is the sequence:

### Step 1: Add infrastructure without breaking existing code

- Create `schema_manager.py` and `database.py` helpers
- Add `schema_name` column to `tenants` (nullable at first, backfill existing tenants)
- Create `tenant_schema_versions` and `account_email_index` tables
- **No existing code changes. System runs as before.**

### Step 2: Dual-write period

- Modify onboarding to create schemas AND write to both old (public) and new (per-tenant) tables
- Modify services to read from new schemas when present, fall back to public
- This is the most complex step but allows zero-downtime migration
- **Duration: 1-2 sessions**

### Step 3: Cut over reads

- Switch all read paths to tenant schemas
- Stop writing to public tables for tenant-scoped data
- **Verify data integrity with row count comparison**

### Step 4: Clean up

- Drop `tenant_id` columns from public tables
- Remove dual-write code
- Remove fallback code

### Step 5: Remove old tables from public schema

- After verification period (1 week in production), drop the tenant-scoped tables from public schema

### Rollback at Each Step

| Step | Rollback                                                                     |
| ---- | ---------------------------------------------------------------------------- |
| 1    | Drop new columns/tables, no code changes needed                              |
| 2    | Disable dual-write; all reads still go to public                             |
| 3    | Re-enable public reads; data is still in public tables                       |
| 4    | Re-enable public writes; data still exists in public                         |
| 5    | Cannot rollback -- data is gone from public. This is the point of no return. |

---

## 8. DataFlow Express Integration Risk (Detailed)

The primary technical uncertainty is whether `kailash-dataflow`'s `db.express` API supports setting `search_path` per operation or per connection. Three scenarios:

### Scenario A: DataFlow exposes connection events (best case)

Register a `set_search_path` listener on checkout. Tenant context is stored in a context variable. Zero service-layer changes needed beyond setting the context variable.

### Scenario B: DataFlow does not expose connections, but supports custom sessions

Wrap the session creation to inject `SET search_path`. Service layer passes `tenant_id` to the express constructor.

### Scenario C: DataFlow is opaque (worst case)

All services currently using `db.express` must be rewritten to use raw SQLAlchemy `AsyncSession` with explicit `search_path` management. This affects 4 service files (escalation/service.py, escalation/scheduler.py, email/inbound.py, digest/service.py) and adds ~150 LOC of query code.

**Recommendation:** Before starting Phase 3, spend 30 minutes verifying DataFlow's connection lifecycle. Read the `kailash-dataflow` source for `express.py` and the connection pool adapter. This determines whether Phase 3 is 100 LOC or 250 LOC.

---

## 9. Testing Strategy

### Tier 1 (Unit)

- Schema name validation (identifier safety)
- Model split correctness (no `tenant_id` on tenant-scoped models)
- `account_email_index` maintenance logic

### Tier 2 (Integration -- requires real PostgreSQL)

- Create tenant schema, verify all 14 tables exist
- Insert data via tenant-scoped session, read back from same schema
- Verify cross-schema isolation: tenant A cannot see tenant B's data
- Migration runner applies to all existing tenant schemas
- `account_email_index` returns correct tenant for inbound email lookup

### Tier 3 (E2E)

- Full onboarding flow creates tenant schema, Account, BackupContact
- Inbound email creates Message in correct tenant schema
- Escalation flow reads/writes within correct tenant schema
- Digest service iterates tenants correctly

---

## 10. Success Criteria

- [ ] Every tenant-scoped model has no `tenant_id` column
- [ ] Every query against tenant data goes through a session with `search_path` set
- [ ] Creating a new tenant creates a schema with all 14 tables in under 500ms
- [ ] No cross-tenant data leakage: tenant A's session cannot read tenant B's data
- [ ] Alembic migrations apply to all tenant schemas in a single command
- [ ] Existing data migrates with zero row count discrepancy
- [ ] `account_email_index` correctly routes all inbound emails
- [ ] All existing tests pass with the new schema structure
- [ ] Rollback is possible through Step 3 of the incremental migration

---

## Appendix A: SQL Reference for Key Operations

### Create a tenant schema

```sql
-- Derive schema name from tenant UUID
-- tenant 550e8400-e29b-41d4-a716-446655440000 -> tenant_550e8400e29b41d4a716446655440000

CREATE SCHEMA "tenant_550e8400e29b41d4a716446655440000";

-- Deploy all tables (generated from SQLAlchemy metadata)
CREATE TABLE "tenant_550e8400e29b41d4a716446655440000".accounts (...);
CREATE TABLE "tenant_550e8400e29b41d4a716446655440000".backup_contacts (...);
-- ... etc for all 14 tenant-scoped tables
```

### Set search path for a tenant session

```sql
SET search_path TO "tenant_550e8400e29b41d4a716446655440000", public;
-- Now SELECT * FROM accounts; resolves to tenant_550e8400...accounts
```

### Query across tenants (admin only)

```sql
-- List all accounts across all tenants
SELECT t.name AS tenant_name, a.name AS account_name
FROM public.tenants t
JOIN "tenant_550e8400e29b41d4a716446655440000".accounts a ON TRUE
WHERE t.schema_name = 'tenant_550e8400e29b41d4a716446655440000';
-- Note: dynamic SQL needed for arbitrary cross-tenant queries
```

### Drop a tenant schema

```sql
-- Requires force=True confirmation at application layer
DROP SCHEMA IF EXISTS "tenant_550e8400e29b41d4a716446655440000" CASCADE;
DELETE FROM public.tenants WHERE id = '550e8400-e29b-41d4-a716-446655440000';
DELETE FROM public.account_email_index WHERE tenant_id = '550e8400-e29b-41d4-a716-446655440000';
```

---

## Appendix B: Files Reference (Exact Paths)

Files that query the database (must be reviewed for schema-awareness):

| File Path                                                                      | Line Numbers                                                                                                                           | Query Pattern                                                                                           |
| ------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------- |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/onboarding/service.py`   | 120-176                                                                                                                                | AsyncSession: `session.execute(select(Tenant))`, `session.add()`, `session.flush()`, `session.commit()` |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/onboarding/api.py`       | 38-39                                                                                                                                  | Creates AsyncSession from engine                                                                        |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/billing/service.py`      | 131-152, 155-165, 167-195, 197-206                                                                                                     | AsyncSession: `session.get(Tenant, ...)`, `session.add()`, `session.commit()`                           |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/escalation/service.py`   | 101, 108, 114, 118, 132, 193-198, 218, 230, 233, 258, 268, 269, 312-320, 333-351, 364-377, 390-436, 456-550, 563-579, 590-598, 600-613 | db.express: `self._db.read()`, `self._db.list()`, `self._db.create()`, `self._db.update()`              |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/escalation/scheduler.py` | 66-82                                                                                                                                  | db.express: `self._db.list("Tenant", {})`                                                               |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/email/inbound.py`        | 99, 120-126, 134-137, 141-147, 161-166, 172-179                                                                                        | db.express: `self._db.create()`, `self._db.list()`                                                      |
| `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/digest/service.py`       | 44, 49, 67, 92-95, 111-125, 136-150, 216-224                                                                                           | db.express: `self._db.read()`, `self._db.list()`                                                        |

Model definition file:

- `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/db/models.py` (lines 1-698, all models)

Database infrastructure:

- `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/db/database.py` (lines 1-82, engine + init)
- `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/db/base.py` (lines 1-10, declarative base)
- `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/db/migrations/env.py` (lines 1-49, Alembic env)

Configuration:

- `/Users/aliciapang/Documents/GitHub/Sequor/src/sequor/config.py` (lines 1-61)
- `/Users/aliciapang/Documents/GitHub/Sequor/alembic.ini` (lines 1-149)
