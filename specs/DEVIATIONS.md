# Spec Deviations Register — comms-wedge (SHIPPED)

Authoritative log of every known divergence between the 7 shipped comms-wedge specs
and `src/sequor/`, per `.claude/rules/specs-authority.md` Rule 6 (log deviation with
rationale + flag user-visible changes for approval). Evidence: `workspaces/future-of-work/04-validate/round3/`.

Dispositions: **FIXED** (code now matches spec, closed this round) · **RECONCILE**
(spec is self-contradictory or code-vs-spec value mismatch; recommended canonical value
pending user ratification) · **BUILD-PENDING** (code does not yet implement; scoped for a
value-ranked wave behind the F5 validation gate) · **COUNSEL-PENDING** (a compliance-fact
decision that needs legal input).

> Convergence note: these are LOGGED deviations, not un-logged divergences — they do not
> count as open `/redteam` HIGH findings. The BUILD-PENDING items are unbuilt-feature work
> trackers whose canonical home is the workspace ledger + `04-validate/round3/00-DECISION-PACKET-R3.md`
> (per `spec-accuracy.md` Rule 4); this register keeps the decision + rationale.

> **RATIFIED 2026-07-05** (user "approved all"): A1 encryption → BUILD (scoped wave, paired
> with A2); **A2 tenant isolation → PostgreSQL RLS** (below); A3 threshold → the conservative
> 95%/80–95% Badge table; A4 feature-moats → sequence behind the F5 validation gate; all
> RECONCILE contradictions → the recommended canonical values, now **applied to the spec files**
> (see each row). PR #7 merge remains the owner's action (production deploy).

> **R5 holistic redteam 2026-07-05** (post-ratification re-derivation, 4 parallel auditors,
> re-derived from scratch): the R1–R4 defect fixes all HOLD (0 CRITICAL / 0 HIGH un-logged
> defects). R5 closed the two RECONCILE residuals the banner above over-claimed as fully applied
> — **CS-5** (message-routing named-template count reconciled 5→6 to match the shipped list) and
> **CS-6** (Free-tier 7-day row added to `data-model.md`'s retention table) — added 3 behavioral
> regression tests (keyphrase name-resolution, 500-no-traceback-leak, WhatsApp constant-time
> verify), 1 code hardening (R5-02), and logged 6 further spec-vs-code divergences + 2 security
> findings in the **§ R5 additions** section at the foot of this file.

## FIXED this round (code now matches spec)

| ID    | Spec claim                                             | Fix                                                   |
| ----- | ------------------------------------------------------ | ----------------------------------------------------- |
| NEW-3 | `rag-pipeline.md:89` answerability<0.3 excluded        | `_ANSWERABILITY_FLOOR` exclusion in `rag_pipeline.py` |
| NEW-5 | `rag-pipeline.md:102` >50% of CLAIMS un-cited → reject | per-claim ratio via `total_claims`                    |

## BUILD-PENDING (code under-delivers vs an affirmative spec claim; recommend a scoped build)

### A1 — PII-at-rest encryption — BUILT (2026-07-05, shard 1b; redteam R7 converged)

- **Spec:** `data-model.md` "All PII fields encrypted at rest (AES-256)"; message content = "PII — high sensitivity".
- **Status:** DELIVERED. All PII columns are now `EncryptedString` (AES-256-GCM + per-tenant
  HKDF): the email/phone identifiers (Account/BackupContact/Contact — pre-existing) plus the
  nine wrapped in shard 1b (Message.subject/body_text/body_raw, Response.content,
  LearnedAnswer.question_text/answer_text, Classification.reasoning, Escalation.resolution_summary,
  Contact.name). Every read/write path binds the per-tenant key via `set_tenant_context`/
  `bind_tenant` before access; `EncryptedString` fail-closes outside development. Verified by
  the Tier-2 round-trip suite (ciphertext-at-rest, plaintext-on-read, per-tenant isolation,
  fail-closed, learning raw-SQL round-trip, erasure) + unit 438 / 1 xfailed.
- **Migration:** `a1f4c82d6e90_encrypt_pii_columns` widens the two bounded VARCHAR columns
  (contacts.name, messages.subject) to TEXT so ciphertext can't overflow; the other seven were
  already TEXT. Schema-only (no backfill) — greenfield-safe; see the migration docstring for
  the existing-data caveat.
- **Note (lookup gap, separate concern — tracked in `todos/active/BUILD-WAVE-data-layer-security.md`
  §1f + journal/0013, NOT an encryption gap):** inbound routing resolves the Account BY its
  encrypted email column, which cannot match (random nonce). The data is encrypted at rest as
  specced; the resolution path needs a blind index.
- **Why this is a scoped multi-shard build, NOT a same-session wrap** (R3 code-quality C1/C2/C3):
  - **C1** — every ORM write path (`email/auto_reply._record_response`, `whatsapp/auto_reply._record_response`, `email/inbound`) creates rows with NO `set_tenant_key` call → wrapping the columns fires the fail-closed `RuntimeError` and breaks the whole auto-reply pipeline. Encryption requires wiring `set_tenant_key` at every write path first.
  - **C2** — `ai/learning.py` reads/writes `learned_answers` via RAW `text()` SQL that bypasses the TypeDecorator → would store plaintext that the ORM digest read then cannot decrypt (`InvalidTag`). LearnedAnswer encryption requires reconciling that raw-SQL layer.
  - **C3** — the digest read path must set the per-account key inside the tenant loop.
- **Recommendation:** BUILD as its own value-ranked wave (set_tenant_key plumbing → column wrap → raw-SQL reconciliation → Tier-2 round-trip test on real Postgres). Building it partially would ship a CRITICAL regression worse than the current state, so it is NOT closed this session.
- **chunk_text sub-item:** the ORM `DocumentChunk.chunk_text` is a near-dead parallel store; the real chunk text lives in `vector_store.py` raw pgvector SQL, which needs plaintext for LLM retrieval → encrypting it is decrypt-on-read design work (separate sub-shard).

### NEW-1 — Confidence badge never rendered (HIGH) — recommend BUILD (or remove the kwarg)

- **Spec:** `response-accuracy.md:55-57` badge is a "fixed governance control": WhatsApp footer "[Auto-generated; N% confidence. Reply STOP…]", email `X-AI-Confidence` header + footer.
- **Reality:** `templates.py build_auto_reply_email(confidence_badge)` — the kwarg has zero uses (silent no-op, zero-tolerance 3c); no `X-AI-Confidence` header; WhatsApp footer omits confidence + the "Reply STOP" opt-out phrasing (NEW-8).
- **Recommendation:** BUILD the badge/footer rendering on both channels. (Interim honesty option: remove the unused `confidence_badge` kwarg so the API stops advertising behaviour it doesn't perform — but the governance control is specced, so BUILD is preferred.)

### NEW-4 — Staleness warning not implemented (MED) — recommend BUILD

- **Spec:** `response-accuracy.md:134` / `rag-pipeline.md:66` — badge shows "may be outdated" when a retrieved doc is >7d old.
- **Reality:** `Document.last_indexed_at` written but never read by retrieval/synthesis. → build the staleness join + badge annotation.

### WhatsApp test suite (HIGH, coverage) — recommend BUILD

- All 7 `src/sequor/whatsapp/` modules have 0 importing tests, including `signature.py` (webhook HMAC — a security control that works but is untested) and `rate_limiter.py`. → add Tier-1/2 coverage; the signature + rate-limit tests are the highest priority (untested security controls on a shipped channel).

## A2 — Tenant isolation — RESOLVED (2026-07-05, user-ratified): adopt PostgreSQL Row-Level Security (RLS)

Decision: neither literal schema-per-tenant NOR plain column-isolation — adopt **PostgreSQL Row-Level Security** on the shared schema.

- **Spec today:** `data-model.md` "separate schema per tenant … shared schema with tenant_id NOT sufficient for PDPA".
- **Reality:** per-tenant schemas created at signup but `get_tenant_session` (the `SET search_path` helper) has ZERO callers; every live path uses `AsyncSession(engine)` + `WHERE tenant_id`. Isolation is **application-enforced only** — one forgotten `WHERE tenant_id` leaks across tenants.
- **Why RLS is optimal long-term (the analysis):**
  - The spec's real objection to "just a tenant_id column" is that a column filter is app-enforced — a single missing `WHERE` leaks. RLS moves enforcement **into the database**: `ENABLE ROW LEVEL SECURITY` + `CREATE POLICY tenant_isolation USING (tenant_id = current_setting('app.current_tenant')::uuid)`. The DB refuses another tenant's rows even when app code forgets the filter — the defense-in-depth the spec wants, at a layer an app bug can't bypass.
  - **Scales** where schema-per-tenant does not: schema-per-tenant sprawls to thousands of schemas and multiplies **every migration** by tenant count; RLS keeps ONE schema + ONE migration path.
  - **PDPA-defensible:** DB-layer, auditable, declarative per-table policies — the industry-standard multi-tenant Postgres pattern and the modern equivalent of namespace separation. (Confirm-not-block: have counsel confirm DB-enforced RLS meets the PDPA segregation intent.)
  - **Shares plumbing with A1:** RLS needs `SET app.current_tenant` at every connection checkout — the SAME per-request tenant-context wiring A1's `set_tenant_key` needs. One connection-boundary hook sets both.
- **Build shape (its own wave, paired with A1):** (1) connection-checkout hook sets `app.current_tenant` (+ encryption key) from the authenticated tenant; (2) RLS-enable + `tenant_isolation` policy migration on every tenant-scoped table; (3) drop the unused per-tenant schemas + `get_tenant_session`; (4) Tier-2 test: a session scoped to tenant A cannot read tenant B even with a filter-less query.
- **Con (honest):** RLS correctness hinges on the GUC being set on EVERY checkout (a miss = policy sees no tenant → rows hidden → fails closed, safe but breaks the query); policies tested per table. Same discipline as the A1 key plumbing — which is why they pair.
- **Spec action (deferred to the A1+A2 build wave, so spec + code land together per `spec-accuracy.md`):** amend `data-model.md` "separate schema per tenant" → "DB-enforced tenant isolation via PostgreSQL Row-Level Security (shared schema + per-row `tenant_id` policy)".

## RECONCILE — RESOLVED 2026-07-05 (canonical values applied to the spec files)

All rows below were ratified and the canonical value has been **written into the spec files**
(`message-routing.md`, `rag-pipeline.md`, `data-model.md`, `channel-coordination.md`,
`response-accuracy.md`). Each spec edit cites this register + the resolution date. The A3 CODE
unification (auto-send gate) remains a scoped safety-critical shard — the spec horn is resolved
to the 95% Badge table; the code paths unify in the A3 build (needs Tier-2 PG).

| ID    | Contradiction                                                                                                                                                                                         | Recommended canonical                                                                         | Rationale                                                                                                                                                                                                                                      |
| ----- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| A3    | `response-accuracy.md` ">90% auto-send" (Option C) vs ">95% High / 80–95% Moderate" (Badge table); code uses classifier confidence to gate but synthesis confidence to badge; thresholds 0.9/0.85/0.8 | **Badge table (>95% High, 80–95% Moderate) + gate and badge on the SAME confidence quantity** | More conservative auto-send is the safer default for a compliance-sensitive comms product; the classifier-vs-synthesis mismatch is a genuine bug. Code unification is safety-critical + needs Tier-2 verification → its own shard (see below). |
| CS-1  | Dedup window 48h (`message-routing.md`) vs 72h (`channel-coordination.md`)                                                                                                                            | **72h**                                                                                       | The longer window is safer against split escalations; confirm against shipped `escalation/thread_key.py`.                                                                                                                                      |
| CS-2  | Dedup key: embedding-similarity vs `SHA256(thread_key)`                                                                                                                                               | **SHA256 thread_key** (shipped `escalation/thread_key.py`)                                    | Amend `message-routing.md` to the mechanism the code actually ships.                                                                                                                                                                           |
| CS-3  | Staleness flat 7d vs 7d/30d by doc type                                                                                                                                                               | **7d rosters/price-lists, 30d policies**                                                      | The type-aware rule is the more specific/correct one.                                                                                                                                                                                          |
| CS-4  | Audit retention flat 24-mo vs tiered 90d/12mo/24mo                                                                                                                                                    | **tiered by plan**                                                                            | Matches `business-model.md` pricing; the flat 24-mo PDPA floor applies to the Enterprise tier. **Product/compliance call — ratify.**                                                                                                           |
| CS-5  | Template minimum 5 vs 6 vs 8 (all in `message-routing.md`)                                                                                                                                            | **8** (the onboarding pre-approval figure)                                                    | Reconcile the three counts to one.                                                                                                                                                                                                             |
| CS-6  | Free-tier audit retention only in `business-model.md` (7d)                                                                                                                                            | add Free row to `data-model.md` retention table                                               | Gap, not a contradiction.                                                                                                                                                                                                                      |
| NEW-2 | Embedding: spec `text-embedding-3-small`/1536-dim vs code `nomic-embed-text`/`Vector(768)`                                                                                                            | **amend spec to 768/nomic (shipped)** + guard the OpenAI fallback                             | Code ships 768; the 1536 OpenAI fallback would fail to insert into `Vector(768)` — fix or gate the fallback.                                                                                                                                   |
| NEW-7 | `EscalationStatus`: code has `notification_pending` (not in `data-model.md`); `channel-coordination.md` references `pending_ooo_return` (in neither)                                                  | **reconcile the enum to the shipped set**                                                     | Three-way drift; pick the code's enum as truth, fix both specs.                                                                                                                                                                                |

### A3 code unification (safety-critical — scoped shard, not this session)

Reviving `should_auto_respond` (`classifier.py`, currently dead) as the single auto-send predicate, feeding it `Account.confidence_threshold`, restoring the urgency guard on the learned-answer path, and making WhatsApp honor `was_auto_sent` (currently asymmetric with email) is the correct unification. It touches the machine-reply-without-human safety gate across `classifier.py`/`response.py`/`email/auto_reply.py`/`whatsapp/auto_reply.py` and needs Tier-2 verification (real infra) — so it is scoped as its own shard rather than changed unverified this session.

## Deferred security hardening (logged from R3; see `r3-security.md`)

- **N2 auth-gating** — whether the DNS endpoints must sit behind login is a flow decision (does the onboarding UI call them pre-login?). Resolver timeout + rate limit + hostname validation ARE fixed; auth-gating pending the flow decision.
- **N3 serverless store** — the in-process limiter is now fail-closed, but multi-instance/serverless effectiveness needs a shared store (Redis) — provisioning decision.
- **N4 replay/timestamp** — the empty-body-skip is fixed; binding a signed timestamp to reject replays needs the real SendGrid signed-timestamp format.
- **N5 prompt-injection** — LLM-side instruction/data separation across 4 prompt sites (blast radius bounded: self-targeted, tenant-scoped, confidence-gated). Mitigation must stay LLM-side per `agent-reasoning.md`, not deterministic filtering.

## Data-model limitation (logged; not a regression)

### Digest tenant-scoping over-counts for multi-account tenants

`digest/service.py::gather_digest_data` scopes escalations + responses by `tenant_id`
only (a `Message` carries no account FK), using `account_id` solely for the account
name, `LearnedAnswer` scoping, and the backup-recipient lookup. Correct for the current
one-account-per-tenant fixtures and the shipped data model, but a tenant with >1 account
would see each account's digest report ALL of the tenant's escalations/responses. If
multi-account tenants become a supported shape, add an account linkage to `Message`
(or join escalations→message→contact→account) and re-scope. Not introduced by R3.

## Architecture note (whole-codebase, out of redteam scope)

Sequor's data layer is raw SQLAlchemy + FastAPI, not DataFlow. The framework-first hook fires on every `src/` edit; a DataFlow migration is a whole-codebase architectural decision, out of this redteam's scope. Logged so the recurring hook advisory is not mistaken for a per-edit defect.

## R5 additions (2026-07-05 holistic redteam — newly-logged divergences)

Evidence: `workspaces/future-of-work/04-validate/round5/`. None is a live CRITICAL/HIGH defect;
each is a spec-vs-code under-delivery (now LOGGED, so it does not count as an open `/redteam`
finding) or a security-hardening/flow decision. Builds sequence behind the F5 validation gate.

### F1 — Upload malware scan (MED) — recommend BUILD

- **Spec:** `rag-pipeline.md` upload flow "File is scanned for malware (ClamAV or equivalent) before processing" — now softened to a deviation pointer.
- **Reality:** no malware/AV scan in `src/sequor/` (`grep -rni 'malware\|clamav\|virus' src/sequor/` → 0). Uploads are size-bounded (25MB) + extension/filename validated, but not AV-scanned.
- **Disposition:** BUILD behind F5 (needs an AV service/daemon — a provisioning decision, class of N3). Size + extension + path-traversal guards ship today.

### F2 — PDPA retention-purge job (HIGH — compliance) — PARTIAL (core shipped, shard 1d)

- **Spec:** `data-model.md` § "Data Retention Schedule" — retention is PDPA policy, enforced via a scheduled purge job.
- **Shipped (shard 1d):** `src/sequor/db/retention.py::run_retention_purge_once` — a per-tenant sweep that bulk-deletes `Message` / `AuditEntry` / `Escalation` rows older than the plan's retention (7d free / 90d starter / 365d professional / 730d enterprise), writing one summary `AuditEntry(action="retention.purge")` per purged tenant. Each tenant is bound in a fresh `AsyncSession` (`bind_tenant` sets the RLS GUC + encryption key; an explicit `WHERE tenant_id` is defense-in-depth). Wired into the app lifespan via `create_retention_scheduler` — opt-in (`retention_purge_enabled`, default OFF until the deploy role/env is configured, since RLS is no-FORCE). Tier-2: `tests/integration/test_retention_purge.py` (per-plan cutoffs, all-three-tables + audit entry, cross-tenant isolation).
- **Deferred (1d-tail):** Free-tier `Contact` (7d) and `Document` (7d) purge. `Contact` has no `created_at` column — needs a schema decision (`last_seen` is last activity, not creation, so it is the wrong key). `Document` purge requires the RAG chunk/embedding cascade. Both remain PDPA policy in `data-model.md` but are not yet machine-enforced.
- **Why it matters:** PDPA **over-retention** risk — customer PII kept indefinitely past the stated retention floor. The shipped job closes it for the highest-sensitivity PII (message content) and the accountability records (audit, escalation).

### F3 — Routing flywheel not built (MED) — recommend BUILD (A4-themed moat)

- **Spec:** `message-routing.md` § Outcome Tracking Instrumentation previously claimed "not a future feature … architected from day 1" — now corrected.
- **Reality:** `RoutingOutcome` model class exists (`db/models.py`) but **no code writes rows**; `RoutingThresholdConfig` / `RoutingOutcomeAggregate` have **no model class**; no nightly aggregation job. The learning loop is unbuilt.
- **Disposition:** BUILD behind F5 as an A4-class moat feature (outcome write path → nightly aggregate → per-tenant threshold calibration). Needs Tier-2.

### NEW-8 — WhatsApp auto-reply footer missing confidence + "Reply STOP" opt-out (HIGH) — recommend BUILD

(Defines the id referenced by the A1/NEW-1 row above.) **Spec:** `response-accuracy.md` requires the WhatsApp auto-reply footer to carry "[Auto-generated; N% confidence. Reply STOP to opt out]". **Reality:** the WhatsApp footer omits both the confidence figure and the "Reply STOP" opt-out phrasing. Pairs with NEW-1 (confidence badge) — same badge/footer render build on the WhatsApp channel, behind F5.

### rag-uncited-1 — ANY-uncited (1–50%) does not reduce confidence / route to backup (MED)

- **Spec:** `rag-pipeline.md` § Hallucination Detection — "If un-cited claims are found: response is flagged, confidence reduced, and routed to backup review" (i.e. ANY un-cited claim, not only >50%).
- **Reality:** the code acts only at the `>50%` **rejection** threshold; the 1–50% "reduce confidence + route to backup" sub-threshold path is not implemented. Predates this branch (the R3 per-claim fix corrected the >50% math only).
- **Disposition:** RECONCILE — either build the 1–50% graded-confidence path (safety-improving) or amend the spec to the shipped binary rule. A product/safety call; pairs with the A3 auto-send-gate shard (needs Tier-2).

### R5-01 — Onboarding document upload is unauthenticated / tenant-unproven (MED — security, flow decision)

- **Reality:** `POST /api/v1/onboarding/upload` (`onboarding/app.py::upload_document`) takes `tenant_id`/`account_id` as attacker-supplied form fields, validates only UUID-parse, and ingests into that tenant's RAG store with **no auth / no ownership proof** → a RAG-poisoning vector. Mitigations that ship today: `tenant_id` is an unguessable 122-bit UUID, the row FK requires the tenant to pre-exist, and the endpoint is rate-limited (20/hr).
- **Disposition:** the auth-gating half is a **flow decision** (same class as N2 — does the pre-login onboarding wizard call this endpoint before a session exists?). Recommend gating behind a short-lived onboarding token; requires the onboarding-flow decision. The memory-bound half (R3) is fixed and holds.

### R5-03 — JWT_SECRET ≥32-byte floor is warned, not enforced (LOW — claim accuracy)

- **Reality:** `auth.py::_signing_secret` deliberately logs `auth.jwt_secret_too_short` and returns a set-but-short secret ("do not hard-break a running deployment"); only the **unset** case fails closed. The R3 merge-gate note states "JWT_SECRET (≥32 bytes)" as if enforced.
- **Disposition:** claim corrected — a short secret is **warned, not rejected** (128-bit HMAC is still infeasible to brute-force). Recommended hardening: enforce ≥32 bytes at **startup** (consistent with the unset-secret fail-closed boot posture) — an owner deploy-config decision, not changed unprompted here to avoid breaking a running deploy with a short secret.

## R7 additions (2026-07-05 build-wave Tier-2 activation — newly-surfaced)

Evidence: `workspaces/future-of-work/04-validate/round7/` (this session). Surfaced while
wiring the Tier-2 PostgreSQL feedback loop (dedicated `sequor-test-pg` pgvector container)
that the A1/A2/F2/A3 build wave requires. The loop had been **dark** — the committed
integration suite had never run against a live Postgres (stale `drop_all()` calls, no
per-test DB isolation), which masked the finding below. Wave-0 (green the loop) fixes:
`drop_all(force=True)` in `test_db_init.py`, `plan "starter"→"free"` (spec-verified: Free is
the entry tier), and `tests/integration/conftest.py` autouse per-test truncate + per-tenant
schema drop. Unit suite unaffected (437 pass in the normal env).

### R7-01 — `backup_contacts` conflates owner-login identity with escalation backup contact (HIGH — correctness/routing) — recommend BUILD (own shard)

- **Reality:** `onboarding/service.py` signup creates ONE `BackupContact` row mixing the
  backup person's `name`/`tier` with the OWNER's `email` + `password_hash` +
  `email_blind_index`. `backup_contacts` is simultaneously the operator-login table
  (`onboarding/app.py` login: `WHERE email_blind_index = blind_index(owner_email)` +
  `verify_password`) AND the escalation recipient table
  (`escalation/service.py`: tier-1/tier-2 send `to=backup["email"]`).
- **Impact:** the designated backup person's `backup_email` is **discarded** (only their
  name is stored); every escalation emails the **account owner**, not the backup person —
  the backup-contact feature is silently non-functional. The blind-index dedup also keys on
  the owner's email, so the "duplicate email" check compares owner-vs-owner.
- **Why it's a design change, not a one-liner:** one row cannot hold both the owner's
  blind index (login lookup needs `blind_index(owner_email)`) and the backup's email (an
  `EncryptedString` whose blind index must be consistent with its own value). The two are
  different people/emails. Correct fix = separate the owner-login identity (own row/table
  keyed on owner_email + password) from the escalation backup contact (backup person's
  email), and re-point login + escalation accordingly. Touches auth (security-critical),
  schema (migration), signup, and escalation routing.
- **Tripwire:** `tests/integration/test_onboarding_integration.py::test_signup_creates_backup_contact`
  is `xfail(strict=True)` referencing this row — it auto-fails (XPASS) the moment the fix
  lands, forcing removal of the marker in the same shard (per `testing.md` xfail-strict).
- **Disposition:** BUILD as its own value-ranked shard in the build wave (pairs with the
  A1 data-layer wave — both touch the tenant-key/connection boundary and the same models).
