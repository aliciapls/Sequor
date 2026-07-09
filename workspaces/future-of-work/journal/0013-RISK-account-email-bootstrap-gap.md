# 0013 — RISK: Account inbound lookup-by-encrypted-email bootstrap gap (pre-existing)

Date 2026-07-05 · Branch `feat/data-layer-security` · Phase: redteam (shard 1b, round 1).
Surfaced by: reviewer + security-reviewer parallel pass over `814c15b..HEAD`.

## The gap

`email/inbound._resolve_account` and `whatsapp/inbound._resolve_account` resolve the
tenant BY READING `Account.owner_email` / `email_address` — both `EncryptedString`
since the initial schema (`5ab03308b1f3`, predates this session). Two compounding
failure modes, both fire in production (`app_env != "development"` + master key set):

1. **Equality-lookup can never match.** AES-GCM uses a random 12-byte nonce per
   write, so two encryptions of the same plaintext produce different ciphertext.
   `WHERE owner_email = 'plaintext'` cannot match a stored ciphertext row. The
   `ix_accounts_owner_email` index is dead weight (indexes non-deterministic
   ciphertext).
2. **Result-decryption fail-closes.** Even if a row matched, `process_result_value`
   fires on the encrypted email columns during ORM construction with no tenant key
   set (the tenant is not known yet — this lookup IS the tenant resolution) →
   `RuntimeError("EncryptedString requires a tenant key…")`.

Net: every inbound email/WhatsApp webhook returns 500 in production because no
Account can be resolved. The dev/test loop never sees it (no master key → plaintext
storage → equality + read both work).

## Why this is NOT a shard-1b regression (and not fixed in 1b)

- `Account.owner_email` / `email_address` were encrypted in the **initial schema**,
  before the build wave. The break has been latent since Account encryption landed.
- Shard 1b wrapped **9 other columns** (Message/Response/LearnedAnswer/
  Classification/Escalation/Contact.name) and wired `bind_tenant` at their access
  sites. The Account resolver is a **different fix class**: you cannot `bind_tenant`
  because no tenant is known yet — the fix is a **blind index** (the
  `BackupContact.email_blind_index` + `compute_email_blind_index` pattern already in
  tree), not a bind. Different shape, different scope.
- The repo is fresh-substrate (PR #7 unmerged, undeployed, no production data), so
  the latent break has bitten no one yet.

## Recommended fix (same data-layer-security wave, separate shard)

1. Add `Account.owner_email_blind_index` (and `email_address_blind_index` if the
   inbound resolver uses it) mirroring `BackupContact.email_blind_index`.
2. Populate in `onboarding/service.signup` (already computes
   `compute_email_blind_index(request.owner_email)` for the duplicate check at
   `service.py:135` — store it on the Account row).
3. Rewrite `_resolve_account` (both channels) to look up by blind index via a
   raw-`text()` projection selecting only non-encrypted columns (the
   `onboarding/app.py:auth_login` blind-index lookup is the reference pattern).
4. Drop or repurpose `ix_accounts_owner_email`.
5. Tier-2 test: inbound webhook resolves an Account under the master key.

## Disposition

Logged as RISK, escalated to the user. It is a production-blocker for the FIRST
deploy of the data-layer wave, but it is pre-existing and a distinct shard from 1b.
Shard 1b's own scope (9 columns + bind wiring) is converged; this entry prevents
the gap from being silently carried.

## For Discussion

- Counterfactual: if the inbound resolver is intended to key off a channel address
  that is NOT the owner email (e.g. a dedicated `Account.inbox_address`), the blind
  index should be on THAT field — confirm which field the inbound route actually
  matches against before building the index.
- Should this be shard 1f (fold into Wave 1 before the inter-wave gate), or land
  alongside A2 (RLS, shard 1c) since both touch the account-resolution boundary?
