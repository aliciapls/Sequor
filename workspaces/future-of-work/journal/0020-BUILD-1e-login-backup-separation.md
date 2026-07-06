# 0020 — BUILD: shard 1e R7-01 login/backup separation (redteam-CONVERGED)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: implement → redteam (shard 1e).
Value-anchor: `specs/DEVIATIONS.md` §R7-01 (the backup-contact feature was silently
non-functional — escalations routed to the owner, not the designated backup person).
User-ratified wave plan 2026-07-05. Closes R7-01; clears the xfail tripwire.

## What shipped

`backup_contacts` no longer conflates the owner-login identity with the escalation backup
contact. The split:

- **Account** owns the owner-login identity: + `password_hash` (moved off BackupContact);
  `owner_email` + `owner_email_blind_index` were already there (1f). Login resolves the
  Account via the new `resolve_account_login_by_email_blind_index` SECURITY DEFINER fn
  (`WHERE owner_email_blind_index = p_idx AND status = 'active'`, returns id/tenant_id/
  password_hash/name — least-privilege: only login gets the hash).
- **BackupContact** owns the backup person: `email`/`name`/`tier` are the BACKUP PERSON's
  (`email = request.backup_email` at signup, was the owner's). `escalation/service.py`
  `to=backup["email"]` now routes to the designated backup person.

Re-points: signup (Account.password_hash = owner's; BackupContact.email = backup_email;
dedup on Account.owner_email_blind_index); `auth_login` (resolves Account, reloads Account,
role=admin owner-only); `portal_api_me` (reads owner email from Account — round-1 caught
it still reading BackupContact by the new Account.id operator_id → blank email);
`admin/backfill-blind-indexes` (repointed to Account blind indexes).

Dead code removed (security): the legacy `resolve_backup_contact_by_email_blind_index`
SECURITY DEFINER fn (RLS-bypassing, returned password_hash) is DROPped in `rls.py` +
the migration; `backup_contacts.password_hash` is DROPped. A lingering RLS-bypassing fn
returning password_hash + a dead password column are security debt that don't survive the
split.

Migration `e1d2c3b4a506` (schema-only, mirrors the 1f greenfield precedent — no prod data;
CAVEAT documents the populated-deploy backfill); `init_db` self-heals `accounts.password_hash`
for the create_all test loop.

## Tier-2 evidence (real sequor-test-pg, NO mocking)

`tests/integration/test_onboarding_integration.py`: the xfail-strict tripwire cleared
(`test_signup_creates_backup_contact` now passes) + 4 new tests — resolver finds account
by owner_email; backup person's email is NOT a login identity; wrong password rejected;
**user-flow walk** signup → `/auth/login` → `/portal/me` → assert owner_email (httpx
ASGITransport; the test the suite was missing). Full suite **489 passed, 1 xfailed** (the
1 xfail is F8 — unrelated landing-page-fields issue).

## Redteam convergence (2 rounds → CONVERGED)

- **R1** (reviewer + security-reviewer, both `ran:true`): security CLEAN; reviewer BLOCKED
  on 1 HIGH + 2 LOW — (1) `portal_api_me` returned blank email post-login (read
  BackupContact by the new Account.id operator_id — same R7-01 bug class at a sibling
  call-site the resolver tests couldn't see); (2) `op_tier` hardcoded → dead `"operator"`
  role branch. Fixed in `342ceb7`: portal_api_me reads Account.owner_email + a Tier-2
  user-flow walk test; dead role branch inlined to `role="admin"`.
- **R2** (reviewer + security-reviewer, both `ran:true`): both **CONVERGED**. Round-1
  fixes CONFIRMED-FIXED with regression coverage. Fresh-eyes sweep: no other sibling
  BackupContact-by-operator_id call-sites (`portal_api_me` was the only one); migration
  symmetric; resolver swap zero surviving references; escalation routes to the backup
  person. 1 IMPORTANT (spec staleness — DEVIATIONS §R7-01 still said "recommend BUILD":
  amended to RESOLVED same-shard) + 1 MINOR (`operator_count` dashboard label drift —
  pre-existing, deferred to 1e-tail → 0021).

## Receipts

- Build: `9333b8f` (feat). Round-1: `342ceb7`. Spec update: this closeout.
- Convergence receipt: commit `342ceb7` + both R2 verdicts "SHARD 1e REDTEAM-CONVERGED".
- Spec: `DEVIATIONS.md` §R7-01 amended to RESOLVED.

## Deploy note

Login is owner-only (role=admin). The login resolver is SECURITY DEFINER (bypasses RLS for
the cross-tenant lookup, then binds the tenant + reloads under RLS) — `password_hash` is
a bcrypt hash (work factor 12), returned only to login. The timing-attack mitigation (burn
bcrypt for absent email) is intact across all three failure paths. RLS is no-FORCE → the
app role must be non-owner for the policy to constrain direct `SELECT password_hash`
(the resolver is the sanctioned bypass).
