# 0016 — BUILD: shard 1c A2 Row-Level Security tenant isolation (CONVERGED, 3 rounds)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: redteam (shard 1c).
Relates to: DEVIATIONS §A2; closes the A2 build item from the wave plan.
Receipts: commits `d8bab0a` (foundation) + `a34525f` (R2 fixes) + `64fc842` (R3 sweep).

## What landed

DB-enforced tenant isolation via PostgreSQL Row-Level Security on the shared
schema — the defense-in-depth `data-model.md` wanted, at a layer an app bug
cannot bypass. `db.rls.apply_rls_and_policies` + alembic `b7d2a9e5f401`
(production mirror) enable RLS + a `tenant_isolation` policy
(`USING` + `WITH CHECK`: `tenant_id = current_setting('app.current_tenant',
true)::uuid`) on all 15 tenant-scoped tables. `current_setting(..., true)` is
`missing_ok` → an unbound session sees NO tenant rows (fail-closed, no error).

Pieces:

- **`bind_tenant` always sets the GUC** (dev no-master-key used to no-op the
  whole bind, which under RLS would have hidden every row). Encryption stays
  fail-open in dev; RLS does not.
- **`tenant_encryption_keys` EXEMPT** — `KeyManager` reads the key row before
  the GUC is set (chicken-and-egg).
- **3 SECURITY DEFINER lookup functions** (`resolve_account_by_email_blind_index`,
  `resolve_account_by_phone`, `resolve_backup_contact_by_email_blind_index`)
  bypass RLS — they are the cross-tenant _discovery_ path (inbound resolution +
  login), not forgotten-WHERE bugs. `SET search_path = public` (no `pg_temp`),
  bound params, constant-SQL bodies.
- **`SLAScheduler` per-tenant commit boundary** — the GUC is `SET LOCAL`, so
  each tenant gets its own commit/rollback (one session serves the whole tick).
- **Removed the dead schema-per-tenant machinery** — `schema_manager.py`,
  `get_tenant_session`, signup schema provisioning, their tests.

## Convergence trajectory (3 rounds)

- **R1**: security HIGH — `auth_login` set only the encryption key, not the
  GUC, before the BackupContact reload → fail-closed under non-owner deploy
  (operator=None → JWT email fell back to user input). Fixed round 2
  (`bind_tenant`).
- **R2**: reviewer CLEAN; security BLOCK-MERGE — same-class sweep gap: ~10
  portal endpoints + the startup task + admin backfill ran tenant-scoped
  queries with no bind → fail-closed under non-owner. Per Multi-Site Kwarg
  Plumbing, fixed in the SAME PR (round 3): `bind_tenant` at every portal site;
  startup + backfill refactored to per-tenant iteration (scheduler pattern);
  `delete_document` (raw conn) gets `_set_rls_guc` + a pre-existing table-name
  typo fix (`keyphrase_mappings` → `key_phrase_mappings`).
- **R3**: reviewer CLEAN + security CLEAN → **shard CONVERGED**.
  - JWT trust chain VERIFIED: `jwt.decode(algorithms=["HS256"])` closes
    alg-confusion/none; `_signing_secret` fail-closed outside dev; `app_env`
    defaults to production → `operator["tenant_id"]` (consumed by `bind_tenant`
    at ~10 sites) cannot be tampered.
  - Per-tenant loops cannot leak the GUC (fresh session + `SET LOCAL` clears on
    commit/rollback).
  - SECURITY DEFINER functions SQLi-free + search_path-hardened.

Tests: unit 421/1-xfailed; integration 55/1-xfailed (4 new RLS Tier-2 tests:
filter-less isolation, fail-closed, WITH CHECK write-block, SECURITY DEFINER
bypass + the auth_login regression). The leak test `SET ROLE`s to a
non-superuser role (postgres bypasses RLS, so the test must drop privileges to
genuinely exercise the policy).

## Deploy note (RLS effectiveness)

RLS is enabled **without `FORCE`**, so the table owner bypasses the policy —
which is what lets the SECURITY DEFINER discovery functions operate. For RLS
to actually constrain the application at runtime, the deploy MUST connect as a
non-owner, non-`BYPASSRLS` role (the owner is the migrator/deploy role). This
is a deploy-time responsibility, like connection-pool sizing. The schema
declares the isolation contract; the deploy enforces the role separation that
makes it effective. Sequor is undeployed today (PR #7 unmerged).

## Spec action

Amended `specs/data-model.md` (the §A2 "spec + code land together" commitment):
"separate schema per tenant" → the RLS mechanism above.

Deferred items → journal 0017.
