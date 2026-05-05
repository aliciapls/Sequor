---
type: GAP
date: 2026-05-05
status: open
priority: high
---

# Tenant Schema Isolation Not Activated During Onboarding

The schema manager is complete (`sequor.db.schema_manager` with `validate_identifier`, `tenant_id_to_schema`, `create_tenant_schema`, `drop_tenant_schema`). Unit tests pass. But the onboarding signup flow never calls any of it.

**What happens today:** All tenants share the same `public` schema tables. Tenant A's contacts sit in the same table as Tenant B's contacts, separated only by a `tenant_id` column. This works until someone forgets a WHERE clause — then it's a cross-tenant data leak.

**What should happen:** During signup, `create_tenant_schema()` creates a private PostgreSQL schema for the new tenant with copies of all 14 tables. `get_tenant_session()` then sets `search_path` to that schema for all subsequent queries, providing defense-in-depth isolation at the database level.

**Missing wiring:**

- Onboarding service never calls `create_tenant_schema()`
- Onboarding service never sets `tenant.schema_name` on the Tenant model
- No migration path for the existing shared-table data

**Fix:** Call `create_tenant_schema()` during signup (after account creation, before returning success). Store the schema name on the Tenant row. Verify `get_tenant_session()` is used by all query paths.
