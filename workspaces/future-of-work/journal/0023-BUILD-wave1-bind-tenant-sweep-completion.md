# 0023 — BUILD: Wave-1 bind_tenant sweep completion (fresh-session redteam → CONVERGED)

Date 2026-07-07 · Branch `feat/data-layer-security` · Phase: /redteam fresh-session re-validation.
Value-anchor: `autonomous-execution.md` Rule 4 — a gate-level review surfaced a same-class
gap (bind_tenant coverage, Wave-1 invariant #1) within one shard budget; filing a follow-up
instead of fixing in-session is BLOCKED.

## The discovery (fresh-session holistic redteam, Round 1)

A `/clear` made the prior inter-wave-gate receipt (journal 0022) a context-boundary
reconstruction — presumed false per `zero-tolerance.md` Rule 1c until re-verified. So this
session re-ran `/redteam`: re-verified the receipt (3× full-suite `489→560` green; the count
rose because bare `pytest` also collects the eval-harness probe accretion), then dispatched
reviewer + security-reviewer on the Wave-1 union diff (`c771c45..HEAD`).

Both converged on Wave-1's **own** diff (the 7 enumerated invariants held) — but the
fresh-eyes pass caught a **cross-cutting gap the union-diff-scoped 0022 gate could not see**:
Wave-1's shard-1c "application-tier bind_tenant sweep" (commit `64fc842`) was scoped to
`onboarding/app.py` ONLY. Four pre-existing tenant-scoped writers were never swept, and
Wave-1's own RLS-enablement makes them **fail under the production non-owner role the wave
mandates**:

| Site                                       | Table           | Failure under non-owner role                                               |
| ------------------------------------------ | --------------- | -------------------------------------------------------------------------- |
| `ai/vector_store.py::store_chunks`         | document_chunks | INSERT violates `WITH CHECK`                                               |
| `ai/vector_store.py::search`               | document_chunks | SELECT returns 0 rows (silent RAG retrieval death)                         |
| `ai/ingestion.py::_create_document_record` | documents       | INSERT violates `WITH CHECK`                                               |
| `ai/ingestion.py::_update_document_status` | documents       | UPDATE affects 0 rows (silent no-op)                                       |
| `ai/learning.py::delete_learned_answer`    | learned_answers | DELETE affects 0 rows → returns False (also an orphan: 0 callers, 0 tests) |

Net prod impact: after Wave-1 deploys + prod connects as the non-owner role, **document
upload (RAG ingestion) and retrieval silently break**. The dev/test suite never saw it
because it runs as `postgres` (superuser, RLS bypassed).

## The fix (in-session, in-budget — `+51/-4` across 4 files + 1 test file)

- Added `await bind_tenant(session, tenant_id)` to all 4 methods, placed after the session
  opens and before the tenant-scoped SQL, mirroring the sibling `_store_learned_answer` /
  `search_learned_answers` exactly.
- Plumbed a new `tenant_id` param into `_update_document_status` and updated ALL 5 callers
  (ingestion.py ×2 internal; onboarding/app.py ×3 portal-upload — `tenant_id=UUID(tenant_id)`
  matching the local str→UUID coercion at l.1360/1411/1429). Multi-site kwarg plumbing per
  `security.md` — every call site in the same change.
- Added `tests/integration/test_rls_bind_tenant_writes.py` (3 Tier-2 tests): run the REAL
  methods on an engine whose every connection `SET`s `ROLE` to a non-superuser,
  non-BYPASSRLS `sequor_app_rls_test` role (production-like: DML on tenant_encryption_keys
  too, since the app legitimately reads per-tenant keys via KeyManager). The `bind_tenant`
  inside each method is what makes the op succeed.

### Teeth verification (the test genuinely catches the bug)

- Author disabled `bind_tenant` in `vector_store.store_chunks` → test FAILED with the exact
  predicted error: `psycopg.errors.InsufficientPrivilege: new row violates row-level security
policy for table "document_chunks"`.
- Confirming reviewer independently re-verified teeth for `ingestion` + `learning` (disabled
  bind → each test FAILED; restored).

## Convergence receipt (reproducible — `verify-resource-existence.md` MUST-4)

Round 1 (reviewer + security-reviewer): 3 HIGH + 1 MEDIUM + 3 advisory → all HIGHs fixed.
Round 2 (independent confirming reviewer on the fix shard): **ROUND VERDICT: CLEAN** —
re-verified all 5 bind placements, all 6 call sites type-correct, completeness (8
`AsyncSession` files, all bound), and mechanically re-ran the teeth for ingestion + learning.

```
pytest --collect-only -q → 572 collected, exit 0
pytest -q (post-fix):
  RUN 1: 563 passed, 8 skipped, 1 xfailed
  RUN 2: 563 passed, 8 skipped, 1 xfailed   (0 failed; +3 vs the 560 floor = the new tests)
```

The single WARN (`StarletteDeprecationWarning: httpx + starlette.testclient`) is third-party,
test-only, predates Wave-1 → Deferred (per `observability.md` Rule 5; resolve = migrate
TestClient to httpx2, out of wave scope).

**Wave-1 bind_tenant sweep is now COMPLETE. WAVE-1 REDTEAM CONVERGED.**

## Deferred advisory findings (non-blocking; not the bind_tenant class)

- **MEDIUM — `onboarding/app.py::stripe_webhook`**: opens a session with no bind. NOT
  exploitable today (`billing/service.py` only touches `Tenant`, the root entity, not
  RLS-scoped). Latent trap: a future webhook event writing a tenant-scoped row would silently
  fail-closed. Recommend a `# NOTENANT: Tenant is root, not RLS-scoped` anchor comment, or
  bind via the metadata tenant_id.
- **LOW — migration `b7d2a9e5f401` docstring drift**: its prose lists the legacy
  `resolve_backup_contact_by_email_blind_index` as a current SECURITY DEFINER exemption, but
  the follow-up `e1d2c3b4a506` DROPs it. `alembic upgrade head` yields the correct final
  state; `db/rls.py` correctly enumerates only the 3 current functions. Migrations are
  append-only (`schema-migration.md` Rule 4) — cannot edit; the live code is correct.
- **LOW — `_orm_to_dict` projects Account.owner_email/email_address (encrypted PII)** into
  every crud Account dict; `digest.send_all_accounts` loads full dicts but uses only `id`.
  Not a leak (decrypts under the correct tenant scope). Pre-existing; a `_PII_COLUMNS`
  redactor is a nice-to-have, out of Wave-1 scope.

## Verdict

Wave-1's own diff was already converged (journal 0022); this round closed the cross-cutting
interaction between Wave-1's RLS-enablement and the 4 pre-existing un-swept writers. The
fresh-session re-validation is the structural value — a `/clear` boundary forced re-derivation
rather than carrying the prior receipt on faith, and the independent reviewers caught what the
union-diff-scoped 0022 gate structurally could not.
