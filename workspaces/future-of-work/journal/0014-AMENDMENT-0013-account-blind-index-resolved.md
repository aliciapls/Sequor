# 0014 — AMENDMENT: 0013 Account inbound-lookup gap RESOLVED by shard 1f

Date 2026-07-05 · Branch `feat/data-layer-security` · Phase: redteam (shard 1f, converged).
Relates to: 0013 (RISK: Account inbound lookup-by-encrypted-email bootstrap gap).

## Closure

The pre-existing RISK logged in 0013 — that every inbound email/WhatsApp
webhook 500'd in production because `_resolve_account` filtered on
`EncryptedString` columns (ciphertext equality never matches + ORM load
fail-closes before the tenant key is known) — is **resolved** by shard 1f
(commits `aca5672` + `578fd9f` + `4faba46`).

## What landed

- `Account.owner_email_blind_index` + `Account.email_address_blind_index`
  (HMAC-SHA256 under the global master-key-derived lookup key, mirroring
  `BackupContact.email_blind_index`); both UNIQUE. Migration
  `c3a9e1d4b702_add_account_email_blind_index` (chain
  `5ab03308b1f3 → a1f4c82d6e90 → c3a9e1d4b702`); drops the dead
  `ix_accounts_owner_email`.
- `onboarding/service.signup` populates both indexes (reusing the `email_index`
  already computed for BackupContact).
- `email/inbound._resolve_account` + `whatsapp/inbound._resolve_account` look
  up by blind index / plain `whatsapp_phone` via a raw `text()` projection of
  non-encrypted columns (`SessionCrud.raw_execute`, SELECT-only guard), so no
  encrypted column materializes before the tenant is bound. Mirrors
  `onboarding.app.auth_login`. Dev (no master key) falls back to the plaintext
  ORM path, matching `bind_tenant`'s no-op-in-dev split.

## Convergence

Redteam converged in 4 rounds (R1: security-reviewer + reviewer → 5 LOW, 3
fixed; R2: adversarial reviewer → 1 MED, fixed; R3: inline closure-parity
clean; R4: final reviewer CONVERGENCE CONFIRMED — 1 pre-existing dev-only LOW
re-surfaced, documented in 0015). Unit 438/1-xfailed (hermetic in both env
regimes); Tier-2 51/1-xfailed (5 new incl. a UNIQUE regression + a test that
proves the naive ORM load still fail-closes while the resolver succeeds).
Spec assertion table: `04-validate/.spec-coverage-v2.md` § "shard 1f".

## Blocks-first-prod-deploy

This was the CRITICAL pre-existing gap that blocked the FIRST production deploy
of the data-layer wave. It is now closed. (PR #7 merge +
`/whoami --enroll-genesis` remain owner actions before the next `/release`.)
