# Build Wave — Data-Layer Security & Compliance

Value-ranked, user-ratified 2026-07-05 ("approved all": F5 greenlit → builds unblocked;
fold F2 into A1/A2; gate R5-01). Source of truth for each item: `specs/DEVIATIONS.md`.
Branch: `feat/data-layer-security` (off `fix/redteam-r1-security-correctness` = PR #7, so
the R1–R6 security fixes are inherited; kept separate so PR #7 stays security-only).

Tier-2 feedback loop (prerequisite): dedicated `sequor-test-pg` pgvector:pg16 container on
`127.0.0.1:5440/sequor` (trust auth, throwaway). Run tests with:
`DATABASE_URL=postgresql://postgres@localhost:5440/sequor ENCRYPTION_MASTER_KEY=<b64-32B>
JWT_SECRET=<≥32B> APP_ENV=development .venv/bin/python -m pytest ...`

## Wave declaration (per `.claude/rules/wave-loop.md` MUST-1)

- **Wave 0 — Activate the Tier-2 loop** ✅ DONE (`ee653a5`). Value-anchor: no build item is
  verifiable without a live PG loop; the loop was dark. Surfaced R7-01.
- **Wave 1 — Data-layer security (A1 + A2 + F2 + R7-01).** HIGHEST value (CRITICAL PII
  encryption + PDPA). Shares the tenant-context connection boundary → one wave, sharded:
  - **1a — Tenant-context boundary (FOUNDATION, serial keystone).** One helper sets BOTH the
    per-tenant encryption key (`set_tenant_key`) AND the RLS GUC (`SET app.current_tenant`)
    at session checkout, wired at every write/read path. A1 + A2 both depend on it.
    Value-anchor: `data-model.md` "All PII encrypted at rest" + PDPA tenant segregation.
  - **1b — A1 column encryption.** ✅ DONE + redteam-CONVERGED (R7, 3 rounds). Wrapped 9
    PII columns in EncryptedString; wired `bind_tenant` at every site; reconciled
    `ai/learning.py` raw SQL (C2); erasure deterministic; Tier-2 round-trip green.
    Commits `ab7c751`…`8477cfe`. Unit 438 / Tier-2 46, both / 1 xfailed.
  - **1c — A2 RLS.** ✅ DONE + redteam-CONVERGED (3 rounds: R1 `auth_login` HIGH →
    R2 portal `bind_tenant` sweep → R3 both CLEAN). Closes DEVIATIONS §A2 + the spec
    action (`data-model.md` amended). Receipts: journal/0016 (build) + journal/0017
    (deferred GAP); commits `d8bab0a` + `a34525f` + `64fc842`. RLS + `tenant_isolation`
    policy (`USING`+`WITH CHECK`, `missing_ok` fail-closed) on all 15 tenant-scoped
    tables; `tenant_encryption_keys` exempt (chicken-and-egg); `bind_tenant` now always
    sets the GUC (dev too); 3 `SECURITY DEFINER` lookup functions for the cross-tenant
    discovery paths (inbound resolvers + login); `SLAScheduler` per-tenant commit
    boundary; dead schema-per-tenant machinery removed; ~10 portal endpoints + startup
    - admin backfill bound via `bind_tenant` (Multi-Site sweep); `delete_document`
      raw-conn GUC + a pre-existing table-name typo fix. **Deploy note: RLS is no-FORCE
      → app must connect as a non-owner role** for the policy to constrain it. Tier-2:
      4 new RLS tests (filter-less isolation, fail-closed, WITH CHECK write-block,
      SECURITY DEFINER bypass + auth_login regression) under a non-superuser role.
      Unit 421/1-xfailed; Tier-2 55/1-xfailed. 6 LOW/MED deferrals → follow-up "1c-tail".
  - **1d — F2 PDPA retention-purge job.** Scheduled purge of rows past their per-tier
    retention; Tier-2 test. Value-anchor: `data-model.md` retention schedule (PDPA
    over-retention). Shares scheduler plumbing.
  - **1e — R7-01 login/backup separation.** Separate owner-login identity from the escalation
    backup contact; re-point login + escalation; clears the xfail tripwire. Touches auth.
  - **1f — Account inbound-lookup blind index (CRITICAL — blocked first prod deploy).**
    ✅ DONE + redteam-CONVERGED (4 rounds: R1 security+reviewer → R2 adversarial → R3 inline →
    R4 final-gate CONFIRMED). Closes journal/0013 (AMENDMENT 0014). Commits `aca5672` +
    `578fd9f` + `4faba46`. Added `Account.owner_email_blind_index` + `email_address_blind_index`
    (HMAC under the global master-key-derived lookup key; both UNIQUE), populated in signup;
    rewrote both `inbound._resolve_account` to look up by blind index / plain `whatsapp_phone`
    via `SessionCrud.raw_execute` (raw `text()` projection, SELECT-only guard) — mirrors
    `onboarding/app.py::auth_login`. Dev (no master key) falls back to the plaintext ORM path.
    Declared `alembic>=1.13.0` in pyproject (was imported by migrations but undeclared). Tier-2:
    5 new tests (incl. UNIQUE regression + a prod-fail-close/resolver-success proof). Unit
    438/1-xfailed (hermetic both env regimes); Tier-2 51/1-xfailed. 5 LOW/info deferrals tracked
    in journal/0015 (none block prod).

### Shard 1b implementation map (derived this session — verify against the live code)

**Done:** crypto extraction — `encrypt_field`/`decrypt_field` in `encrypted_column.py`
(`96c1a45`), so the raw-SQL path can produce byte-compatible ciphertext.

**Columns to wrap in `EncryptedString` (models.py):** `Message.subject/body_text/body_raw`,
`Response.content`, `LearnedAnswer.question_text` (field_name `learned_question`),
`LearnedAnswer.answer_text` (`learned_answer`), `Classification.reasoning`,
`Escalation.resolution_summary`, `Contact.name`. (Contact.email/phone, BackupContact.*,
Account.whatsapp_phone already encrypted.)

**Write/read sites needing `set_tenant_context` (three session patterns — a MISSED one
fails-closed in prod):**

- raw `AsyncSession`: `email/auto_reply._record_response` + `_create_escalation`;
  `whatsapp/auto_reply._record_response` + `_create_escalation` (all have `context.tenant_id`).
- raw `AsyncSession` + RAW SQL (C2 reconciliation): `ai/learning._store_learned_answer`
  (encrypt q/a via `encrypt_field` before INSERT) + `search_learned_answers` (decrypt after
  SELECT) — must use the SAME field_names as the ORM columns.
- `self._db` express: `email/inbound` (Contact + Message create) — find where that session
  lives and set context on it.
- passed-in session (ORM read → decrypts): `digest.gather_digest_data` (reads Escalation/
  Response/LearnedAnswer); ALSO `digest._gather_stats` raw dict path reads question_text.
- Verify classifier/rag read paths (Classification.reasoning, Message bodies) — pending the
  mapping agent's inventory (append here).

**Erasure fix (part of 1b):** `test_compliance_erasure` is non-deterministic under
ENCRYPTION_MASTER_KEY (mocked tenants lack a provisioned key). Make erasure + its tests
deterministic under mandatory encryption.

**Suggested order:** (1b.1) wire `set_tenant_context` at every site — LOW risk, no crypto yet,
verify green, commit. (1b.2) wrap columns + a Tier-2 round-trip test that asserts ciphertext-
in-DB / plaintext-on-read AND exercises each write path with a real key (fail-closed catches
misses). (1b.3) reconcile `learning.py` raw SQL. (1b.4) erasure fix. Commit as coherent 1b.

- **Wave 2 — A3 auto-send gate unification.** Revive `should_auto_respond` as the single
  auto-send predicate @ 95% Badge table; gate + badge on the same confidence quantity; make
  WhatsApp honor `was_auto_sent`. Safety-critical; needs Tier-2. Value-anchor: DEVIATIONS A3.
- **Wave 3 — A4 moats + R5-01.** NEW-1/NEW-8 confidence badge/footer (email + WhatsApp),
  NEW-4 staleness warning, WhatsApp test suite, F3 routing flywheel, R5-01 onboarding-upload
  token gate. Value-anchor: DEVIATIONS A4/F3/NEW-8, user-ratified.

Inter-wave gate (G1–G5 per wave-loop MUST-2) fires after Waves 1 and 2. Holistic redteam to
convergence after the final wave.

## Out of wave scope (unchanged)

- Platform target-state (M0–M10 todos) — vision, not gaps (`specs/_index.md`).
- PR #7 merge = owner action (Vercel env: JWT_SECRET / ENCRYPTION_MASTER_KEY / APP_ENV).
- `/whoami --enroll-genesis` before next `/release` (fresh-substrate repo).
