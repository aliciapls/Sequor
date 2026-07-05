# 0017 — GAP: shard 1c deferred hardening (6 items, non-blocking)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: redteam (shard 1c).
Relates to: 0016 (1c convergence). All items are non-blocking for 1c; tracked
for a follow-up hardening sweep (wave-plan follow-up "1c-tail").

## The deferrals

1. **BackupContact.email_blind_index is non-UNIQUE** (R3-security MEDIUM-1).
   `resolve_backup_contact_by_email_blind_index` returns `LIMIT 1` with no
   `ORDER BY`; two backup contacts across tenants sharing an email (contractor
   working for two tenants, or an attacker registers a victim's email at
   attacker-tenant) → login-tenant ambiguity. NOT exploitable for privilege
   escalation: the attacker can only verify their OWN password hash; the worst
   case is the victim's own login fails (self-DoS, not cross-tenant access).
   The sibling Account blind indexes ARE unique (`ix_accounts_*_blind_index`,
   unique=True). Fix: migrate `ix_backup_contacts_email_blind_index` to UNIQUE
   (NULLs distinct under PG UNIQUE, so pre-backfill rows coexist). Needs a
   design call (global UNIQUE vs per-tenant) if multi-tenant contractors are
   real. Pre-existing column (predates 1c); 1c inherits the LIMIT-1 ambiguity
   in the function it authored.

2. **Account.whatsapp_phone non-UNIQUE** (R3-security LOW-1).
   `resolve_account_by_phone` `LIMIT 1` ambiguity if two accounts share a
   number. Acknowledged in `whatsapp/inbound.py` ("row order unspecified in the
   implausible case…"). Inbound mis-routing, not cross-tenant data leak (RLS
   still constrains each tenant's rows). Pre-existing.

3. **Dev-mode ORM fallback in the inbound resolvers** (R1-reviewer LOW).
   The `if not settings.encryption_master_key:` branch in `_resolve_account`
   does a plaintext ORM `list("Account", …)` before any tenant bind. Under a
   non-owner app role it would fail-closed. Not a real scenario — production
   always has a master key (the resolver takes the blind-index/function path);
   dev real-DB runs as the postgres superuser (bypasses RLS); dev unit tests
   use fakes. Route the dev branch through the same discovery function only if
   dev-mode-non-superuser ever becomes a real config.

4. **Portal endpoints not E2E-tested under a non-superuser role** (R3-reviewer
   observation). Portal integration tests run as postgres (BYPASSRLS) so they
   don't catch a future regression where someone removes a `bind_tenant` call.
   The bind→select mechanism IS proven under non-superuser by
   `test_rls_filterless_select_isolates_tenants` + the auth_login regression in
   `test_lookup_function_bypasses_rls_for_tenant_discovery`. A dedicated
   portal-under-RLS E2E test (drive `/api/v1/portal/*` against a non-owner
   connection) would catch per-endpoint regressions; fold into a "portal
   hardening" pass.

5. **Codebase-wide pyright type-warning sweep**. The 1c edits surfaced many
   PRE-EXISTING pyright advisories across untouched files (FakeEmailSender
   protocol mismatches, `_FakeSession` vs `AsyncSession`, UploadFile typing,
   `Result.id` access, unused imports). None are runtime failures or
   introduced by 1c; they're accumulated type-checker noise. A dedicated
   `pyright --verifytypes` cleanup pass is its own shard.

6. **Deploy: non-owner app role + FORCE-row-security decision** (deploy
   follow-up). 1c enables RLS without `FORCE`; the deploy must connect as a
   non-owner role for RLS to constrain the app. Owner-action (F5 class): pick
   the prod DB role topology (owner/migrator vs app role), grant the app role
   DML-but-not-BYPASSRLS, document in the deploy config. Reconsider `FORCE`
   (which would make the discovery functions need a different bypass) only if
   the deploy can't separate roles.

## Pre-existing typo fixed in-shard

`portal_api_delete_document` raw-SQL `DELETE FROM keyphrase_mappings` →
`key_phrase_mappings` (the model's `__tablename__`). The DELETE hit a
non-existent table → endpoint 500'd. Found during the R3 sweep of the same
endpoint; fixed in `64fc842` (zero-tolerance: I found it in an endpoint I was
modifying).
