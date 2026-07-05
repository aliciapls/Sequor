# 0015 — GAP: shard 1f deferred hardening (5 LOW/informational, non-blocking)

Date 2026-07-05 · Branch `feat/data-layer-security` · Phase: redteam (shard 1f).
Relates to: 0014 (1f closure).

## The deferrals

Shard 1f redteam surfaced 5 LOW/informational items that are genuinely
non-actionable now but worth tracking for a future hardening sweep.

1. **Dev-fallback casing asymmetry** (R2 quality-L2, re-surfaced R4-LOW). The
   email resolver's dev path lowercases `to_email` before the plaintext lookup,
   but signup stores `email_address`/`owner_email` verbatim (EmailStr does not
   normalize case). Dev-only (the prod blind-index path normalizes via
   `.lower().strip()`); unreachable via the real signup flow in pure-dev
   (signup's `compute_email_blind_index` raises without a master key before the
   Account insert). Fix when a non-signup dev Account-creation path exists.
2. **Cross-column blind-index collision** (R2-NEW2). UNIQUE is per-column; a
   future non-signup Account-creation path could set `owner_email_blind_index`
   on one row equal to `email_address_blind_index` on another → `LIMIT 1`
   ambiguity. signup can't cause it (BackupContact dup-check + both columns set
   equal per row). Enforce a cross-column invariant IF a non-signup creation
   path lands.
3. **Unicode NFKC normalization** (R2-NEW3). `compute_email_blind_index` does
   `.lower().strip()` (ASCII). IDN/Unicode local parts could miss. ASCII
   inboxes are the production norm; revisit if IDN support is needed.
4. **Unit-conftest fixture scope** (R2-NEW4). The autouse fixture zeros
   `encryption_master_key` only, not `app_env`. Exporting `APP_ENV=production`
   alongside a master key still breaks ~11 unit tests (signature-required
   branch). The 1f hermeticism claim is accurately scoped to
   `ENCRYPTION_MASTER_KEY`; extend to pin `app_env` if that shell combo becomes
   the dev norm.
5. **Constant-time burn on absent-account branch** (R1 security-LOW2). Inbound
   is a signed-webhook inbox-resolution path (not a credential path); a
   timing-based enumeration would require provider credentials to probe.
   Deferred — wrong tradeoff to add latency to every inbound webhook for
   negligible gain.

## For Discussion

- Which of these (if any) should gate the first prod deploy? (Current answer:
  none — all are dev-only, forward-looking, or wrong-tradeoff.)
- Should #2 (cross-column invariant) be a CHECK constraint now, or deferred
  until a non-signup creation path is actually planned? (Current answer:
  deferred — speculative now; the CHECK could over-constrain a future
  "separate inbox email" feature.)

## Disposition

All 5 deferred with rationale; documented in commit bodies (`578fd9f` +
`4faba46`) and this entry. None block 1f's convergence or the first prod
deploy. Consolidated here so a future test-hygiene / hardening sweep can pick
them up as a batch.
