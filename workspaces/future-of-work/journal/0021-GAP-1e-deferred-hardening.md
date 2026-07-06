# 0021 — GAP: shard 1e deferred hardening (3 items, non-blocking)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: redteam close-out (shard 1e).
Relates to: 0020 (1e convergence). Non-blocking for 1e; tracked for a "1e-tail" sweep.

## The deferrals

1. **`operator_count` dashboard metric label drift** (R2-reviewer MINOR — pre-existing,
   exposed by 1e).
   `portal_api_dashboard` (~`app.py:1791`) computes a metric labelled `operator_count` as
   `count(BackupContact.id) WHERE account_id = X`. Post-1e, "operators" (login identities)
   = the account owner (1 per account); `BackupContact` rows are escalation recipients,
   not operators. The numeric value is correct for "backup contact count" but the label is
   now semantically misleading in the UX. Fix: rename to `backup_contact_count` (or
   `primary_backup_count` for tier-1 only) + update the response key + the frontend
   consumer (`templates/*`). Not introduced by 1e (predates the shard) but exposed by it.

2. **`verify_password` / `hash_password` duplicated across modules** (R1-reviewer LOW —
   pre-existing, deepened by 1e).
   `onboarding/service.py:23-28` and `sequor/auth.py:32-33` each define the bcrypt
   verify contract. 1e added a new caller (`app.py` imports `verify_password` from
   `sequor.auth`). Two implementations of the same credential contract can drift. Fix:
   have `onboarding/service.py` import `verify_password` from `sequor.auth`; keep
   `hash_password` co-located with signup (its only caller) or also move to `auth.py`.

3. **Populated-deploy backfill caveat** (migration CAVEAT — not exercised, this repo is
   greenfield).
   Migration `e1d2c3b4a506` is schema-only: it ADDs `accounts.password_hash`, DROPs
   `backup_contacts.password_hash`, swaps the resolver. Correct for this repo (PR #7
   unmerged, undeployed, no production data). For a POPULATED deploy, existing operators'
   password hashes live on `backup_contacts.password_hash`; the migration must be preceded
   by a data backfill `UPDATE accounts SET password_hash = bc.password_hash FROM
backup_contacts bc WHERE bc.account_id = accounts.id` (plain VARCHAR — no master key
   needed at migrate time), else existing operators cannot log in. Belongs in a dedicated
   data migration, not the schema migration (per the 1f precedent).

## Non-deferrals (fixed in-session, recorded for the audit trail)

- `portal_api_me` owner-email regression (R1 HIGH) → reads Account.owner_email + Tier-2
  user-flow walk (`342ceb7`).
- `op_tier` dead role branch (R1 LOW) → inlined `role="admin"` (`342ceb7`).
- DEVIATIONS §R7-01 spec staleness (R2 IMPORTANT) → amended to RESOLVED same-shard.

## Why these are deferrable

Items 1–2 are LABEL/DEDUP polish on pre-existing surfaces (not 1e-introduced, no
correctness/security impact); item 3 is a deploy-time caveat for a state this repo does
not hold (greenfield). None block prod: the shipped split is correct, the xfail tripwire
is cleared, and the login + escalation + /portal/me paths are verified end-to-end.
