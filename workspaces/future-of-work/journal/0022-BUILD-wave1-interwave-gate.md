# 0022 — BUILD: Wave-1 inter-wave gate (holistic redteam → CONVERGED)

Date 2026-07-06 · Branch `feat/data-layer-security` · Phase: wave-loop inter-wave gate (G1–G5).
Value-anchor: wave-loop MUST-2 — a plan shipped across ≥3 sharded waves MUST run ONE holistic
redteam across ALL merged shards before the wave is declared converged. Wave 1 shipped 6 shards
(1a/1b/1c/1d/1e/1f) → the gate is mandatory.

## The gate (G1 — 3 parallel reviewers on the UNION diff `c771c455597d..HEAD`)

Per `agents.md` "Holistic Post-Multi-Wave Redteam": reviewer + security-reviewer + closure-parity
verifier, scoped to the union (30 commits, 61 files, +5096/-648), NOT the latest shard.

- **reviewer (cross-shard correctness):** WAVE 1 CONVERGED. Found 2 IMPORTANT (test
  non-determinism; compliance.py bypasses `bind_tenant`) + 1 MEDIUM (BackupContact blind index
  non-UNIQUE — already the 1c-tail item) + 1 MINOR (deferrals genuinely non-blocking).
- **security-reviewer:** WAVE 1 SECURITY-CONVERGED. Found 1 MEDIUM (`_orm_to_dict` projected
  `Account.password_hash` into every crud Account dict) + 2 LOW (migration downgrade order;
  signup dedup no-op under prod role).
- **closure-parity verifier:** **BLOCKED** — the suite was NOT reproducibly green at HEAD (the
  journals' "489 passed" was lucky test-ordering). Root cause: the process-wide `KeyManager`
  singleton was reset by only ~5 of 12 integration files → a stale singleton leaked across tests
  → order-dependent flakes spanning 1b/1d/1e/1f tests. Per verify-resource-existence MUST-4, the
  convergence receipt was not reproducible.

## The fixes (`43d7c4b`) — all in-session, in-budget

1. **BLOCKING — suite determinism:** added an autouse `reset_key_manager()` to the integration
   conftest (alongside the existing `set_tenant_key` reset). The `KeyManager` singleton (LRU
   per-tenant key cache) was the contamination vector.
2. **IMPORTANT — compliance → bind_tenant:** `erase_contact_pii` now uses the 1a boundary
   (sets the RLS GUC in dev too, not just prod). Erasure unit-test stub updated (bind_tenant is
   the new side-effecting boundary).
3. **MEDIUM — `_orm_to_dict` credential surface:** added a `_SENSITIVE_COLUMNS` denylist so
   `password_hash` no longer bleeds into every `crud.read/list("Account")` dict; it stays scoped
   to the login resolver (its sole reader, via raw SQL).
4. **LOW — migration downgrade order:** restore `backup_contacts.password_hash` BEFORE
   recreating the legacy resolver that references it (PG14+ parses LANGUAGE sql bodies at
   CREATE time).
5. **LOW — signup dedup docstring:** documented that the friendly dedup is a no-op under the prod
   non-owner role (RLS fail-closes pre-bind); the UNIQUE index is the structural backstop.

The per-shard redteams could NOT see #1/#2 — they cross shard boundaries (the KeyManager +
the bind_tenant boundary). That is exactly what the holistic post-multi-wave gate exists to catch.

## Convergence receipt (reproducible — verify-resource-existence MUST-4)

`43d7c4b` (HEAD). 3 consecutive full-suite runs (unit + integration) under the Tier-2 env:

```
RUN 1: 489 passed, 1 xfailed
RUN 2: 489 passed, 1 xfailed
RUN 3: 489 passed, 1 xfailed
```

(5+ consecutive clean runs since the fix; the 1 xfail is F8 — an unrelated landing-page-fields
tripwire.) Both the reviewer + security-reviewer verdicts on the code were CONVERGED; the
closure-parity BLOCK is lifted by the reproducible receipt.

## Deferred to the Wave-1 tail (F7)

- BackupContact.email_blind_index non-UNIQUE (the 1c-tail item; a `LIMIT 1` ambiguity — self-DoS,
  not cross-tenant access). Migration to UNIQUE.
- Free-tier Contact (no `created_at`) + Document (RAG cascade) retention purge (1d-tail).
- `operator_count` dashboard label drift, `verify_password` dup, populated-deploy backfill caveat
  (1e-tail).
- Pre-existing pyright sweep (F7): the `str | int` `_valid_request` kwargs typing,
  `FakeEmailSender` protocol mismatch, `_FakeSession`/AsyncSession, the unused-import hints — all
  in untouched files, surfaced by pyright re-running on the package.

## Verdict

**WAVE 1 CONVERGED — inter-wave gate passed.** Proceed to Wave 2 (A3 auto-send gate unification)
when the operator authorizes it. Owner-gated items remain: PR #7 merge (F5) + `/whoami
--enroll-genesis` (F6) before the next `/release`.
