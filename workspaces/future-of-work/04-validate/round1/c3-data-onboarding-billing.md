# /redteam Round 1 — Cluster C3: Data-model + Onboarding + Billing (spec-compliance)

Repo: `/Users/esperie/repos/projects/Sequor` · Scope: SHIPPED comms-wedge specs only
(`specs/data-model.md`, `specs/onboarding.md`, `specs/business-model.md`).
Platform specs are target-state and NOT in scope.

Method per `.claude/skills/spec-compliance/SKILL.md`: literal acceptance assertions
extracted from each spec, each verified against actual code via `grep`/`ast`/runtime
import. File existence is not compliance.

---

## 1. Assertion tables

### 1a. `specs/data-model.md`

| #   | spec assertion                                                                                                                                                                    | verification command                                                                          | actual output                                                                                                                                                    | verdict                                     |
| --- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------- |
| D1  | Core entities present: Tenant, Account, BackupContact, Contact, ChannelConsent, Message, Classification, RAGRetrieval, Document, Response, Escalation, AuditEntry, RoutingOutcome | `grep -c "^class .*Base)" src/sequor/db/models.py` + read                                     | All 13 present as ORM classes (plus DocumentChunk, LearnedAnswer, KeyPhraseMapping)                                                                              | PASS                                        |
| D2  | `confidence_badge: enum (high, moderate, low, uncertain)` (line 166)                                                                                                              | `ast` walk of `ConfidenceBadge`                                                               | `ConfidenceBadge members: ['high', 'moderate', 'low']` — **`uncertain` MISSING**                                                                                 | **FAIL (F1)**                               |
| D3  | `ConfidenceBadge('uncertain')` must be a valid badge (code + DB use it)                                                                                                           | `python -c "ConfidenceBadge('uncertain')"`                                                    | `ValueError -> 'uncertain' is not a valid ConfidenceBadge`                                                                                                       | **FAIL (F1)**                               |
| D4  | Tenant has `whatsapp_bsp_account_id: string (optional)` (line 22)                                                                                                                 | `grep -rn whatsapp_bsp_account_id src/`                                                       | no match in src (only in spec)                                                                                                                                   | **FAIL (F8)**                               |
| D5  | Separate schema per tenant; "shared schema with tenant_id is NOT sufficient for PDPA" (lines 5-7, 409)                                                                            | `grep -rn get_tenant_session src/ tests/` (excl. def)                                         | **zero production call sites**; `search_path` only in `database.py:116` (unused helper)                                                                          | **FAIL (F2)**                               |
| D6  | "All foreign keys use `ON DELETE RESTRICT`" (line 321); cascade at app layer not DB                                                                                               | `grep -c "ondelete='CASCADE'"` / `'RESTRICT'` in migration                                    | 25 CASCADE, 0 RESTRICT; `audit_entries.tenant_id → CASCADE` (migration:190)                                                                                      | **FAIL (F4)**                               |
| D7  | AuditEntry: doer_type/doer_id/action_type/recipient_type/recipient_id/message_id/metadata/occurred_at; occurred_at immutable                                                      | read `models.py:643-673`                                                                      | all fields present; `metadata_` mapped to column `"metadata"`; append-only via `audit()` helper (insert-only)                                                    | PASS (immutability convention-only; see F4) |
| D8  | AuditEntry contains ZERO PII; `metadata` only structured refs (line 383)                                                                                                          | read `audit.py`, `compliance.py:211`                                                          | audit metadata carries `erased_fields` list / category refs — no PII                                                                                             | PASS                                        |
| D9  | Erasure: hard-delete Contact, Message content, Response, RoutingOutcome; delete Channelconsent (§Erasure lines 385-394)                                                           | read `compliance.py::erase_contact_pii`                                                       | soft-nulls Contact PII; nulls embeddings; erases LearnedAnswer text; **Message body / Response.content NOT erased; ChannelConsent / RoutingOutcome NOT deleted** | **FAIL (F3)**                               |
| D10 | All PII fields encrypted at rest, AES-256, tenant-specific keys (line 404)                                                                                                        | read `encrypted_column.py` / `encryption_keys.py`                                             | AES-256-GCM + HKDF per-field, per-tenant keys ✓ — BUT plaintext fallback when `APP_ENV=development` (the default)                                                | PARTIAL (**F6**)                            |
| D11 | Entities OOOConfiguration, RoutingThresholdConfig, RoutingOutcomeAggregate (lines 232-300)                                                                                        | `grep -n "class OOOConfiguration\|RoutingThresholdConfig\|RoutingOutcomeAggregate" models.py` | no match — **3 spec entities unimplemented**                                                                                                                     | **FAIL (F5)**                               |
| D12 | Parameterized queries; no f-string/concat SQL                                                                                                                                     | `grep -rnE "execute\(text\(f\|execute\(f"` src/                                               | only `schema_manager.py:129` DROP SCHEMA f-string, identifier `validate_identifier`-guarded → safe                                                               | PASS                                        |
| D13 | No raw PII in logs; contact IDs / hashes used                                                                                                                                     | read logging call sites in onboarding/compliance                                              | emails masked via `mask_email`; tenant/contact IDs logged as str(UUID)                                                                                           | PASS                                        |

### 1b. `specs/onboarding.md`

| #   | spec assertion                                                                                      | verification command                                        | actual output                                                                                                                                                                                      | verdict                                   |
| --- | --------------------------------------------------------------------------------------------------- | ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------- |
| O1  | 5-step flow: account creation, account(comm point), docs(optional), escalation chain, routing rules | read `schemas.py::OnboardingRequest` + `service.py::signup` | org_name/owner_email/owner_password (S1), account_name/ownership_type (S2), DocumentUploadRequest (S3), backup_name/backup_email/escalation_sla_hours (S4), routing_rule (S5) — all fields present | PASS                                      |
| O2  | Routing rule templates A/B/C (all-to-backup / faq-only / full-ai)                                   | `grep -n "ROUTING_RULES" service.py` + schema pattern       | `all_to_backup / faq_only / full_ai` in `ROUTING_RULES`; schema `pattern=^(all_to_backup\|faq_only\|full_ai)$`                                                                                     | PASS                                      |
| O3  | Escalation default 4 hours                                                                          | read `schemas.py:31`, `config.py:46`                        | `escalation_sla_hours: int = Field(ge=1, le=72, default=4)`; `default_escalation_sla_hours = 4`                                                                                                    | PASS                                      |
| O4  | Email-first; WhatsApp optional, start email-only                                                    | read `service.py::signup`                                   | `channels=["email"]` at signup (WhatsApp added later per spec) — consistent with "start with email only"                                                                                           | PASS                                      |
| O5  | System generates DNS records for email channel (Step 2)                                             | `ls src/sequor/dns/` + `grep generate`                      | `dns/service.py` present with DNS record generation                                                                                                                                                | PASS (dns cluster; not deep-audited here) |
| O6  | PDPA consent accepted at signup (Step 1)                                                            | `grep -n pdpa_consent_recorded_at service.py`               | `pdpa_consent_recorded_at=None` set at Tenant create — **consent field left None at signup**                                                                                                       | PARTIAL (**F7-note**)                     |
| O7  | Input validation before DB write (Pydantic)                                                         | read `schemas.py`                                           | HTML rejection, path-traversal reject, password strength, EmailStr, length bounds                                                                                                                  | PASS                                      |

### 1c. `specs/business-model.md`

| #   | spec assertion                                                   | verification command                               | actual output                                                                                                                                 | verdict          |
| --- | ---------------------------------------------------------------- | -------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- | ---------------- |
| B1  | Per-account pricing, not per-seat                                | read `billing/service.py::create_checkout_session` | `line_items=[{price:starter, quantity:1}]`, metadata tenant_id — per-account                                                                  | PASS             |
| B2  | Plans: free, starter, professional, enterprise                   | `ast` `TenantPlan`                                 | `TenantPlan = free/starter/professional/enterprise` (model)                                                                                   | PASS (model)     |
| B3  | Starter $20/month                                                | `grep STARTER_PRICE billing/service.py`            | `STARTER_PRICE_SGD = 20`                                                                                                                      | PASS             |
| B4  | Billing transitions across all 4 tiers                           | read `handle_webhook` + handlers                   | only free↔starter wired; `_handle_*` set `starter` or `free` only — **Professional/Enterprise upgrade + per-message overage not implemented** | PARTIAL (**F9**) |
| B5  | Webhook signature verification (no unauthenticated plan changes) | read `verify_webhook_signature`                    | `stripe.Webhook.construct_event` with `stripe_webhook_secret`; raises on missing secret / bad sig                                             | PASS             |
| B6  | Webhook idempotency (no double-processing)                       | read `is_event_processed`/`mark_event_processed`   | TTL+bounded dedup map (72h / 10k cap)                                                                                                         | PASS             |

---

## 2. Findings

### [HIGH] F1 — `ConfidenceBadge` enum missing spec-required `uncertain`; recording an uncertain response raises ValueError

- **file:line**: `src/sequor/db/models.py:136-140` (`ConfidenceBadge` = high/moderate/low only); coercion at `src/sequor/email/auto_reply.py:232` and `src/sequor/whatsapp/auto_reply.py:245` (`badge = ConfidenceBadge(response_result.confidence_badge)`); unconditional call at `email/auto_reply.py:146`.
- **evidence**:
  - `ast` → `ConfidenceBadge members: ['high', 'moderate', 'low']`
  - `python -c "ConfidenceBadge('uncertain')"` → `ValueError -> 'uncertain' is not a valid ConfidenceBadge`
  - Synthesis code emits `"uncertain"`: `ai/response.py:164,235`, `ai/rag_pipeline.py:222,288`, `email/auto_reply.py:205`.
  - DB migration DOES include it: `migrations/.../5ab03308b1f3_initial_schema.py:257` → `sa.Enum('high','moderate','low','uncertain', ...)`.
  - `email/auto_reply.py:146` calls `_record_response` UNCONDITIONALLY, before the escalate/send branch (line 155). An uncertain synthesis result therefore reaches `ConfidenceBadge("uncertain")` → ValueError → caught by the broad `except Exception` (line 192) → returns `response_recorded=False`. The response is silently NOT persisted and the crash is masked as a generic error.
- **spec ref**: `specs/data-model.md:166` — `confidence_badge: enum (high, moderate, low, uncertain)`.
- **governance**: zero-tolerance (documented/DB-declared value the Python model can't perform); the broad `except` masking the ValueError is a silent-fallback (Rule 3).
- **fix**: add `uncertain = "uncertain"` to `ConfidenceBadge` (models.py) so Python enum, DB enum (migration) and synthesis code agree. Add a regression test that persists a Response with each of the 4 badge values through `crud.create("responses", ...)`.

### [HIGH] F2 — Per-tenant schema isolation is orphaned; data lives in the shared public schema keyed by `tenant_id` — the exact pattern the spec forbids

- **file:line**: `src/sequor/db/database.py:107-117` (`get_tenant_session`, the ONLY code that issues `SET search_path`) — zero production callers. All services open plain `AsyncSession(get_engine())` (e.g. `email/auto_reply.py:234`, `whatsapp/auto_reply.py:247`, `onboarding/service.py:151`) against `public` and filter by `tenant_id`.
- **evidence**:
  - `grep -rn "get_tenant_session" src/ tests/` (excluding the def) → empty (no call site).
  - `grep -rn "search_path" src/` → only `database.py:109,116`.
  - `schema_manager.create_tenant_schema` clones tables into `tenant_<hex>` at signup (`service.py:221`), but nothing ever reads/writes through that schema → the tenant schemas are created and never used.
- **spec ref**: `specs/data-model.md:5-7` ("Namespace separation (shared schema with `tenant_id`) is NOT sufficient for Singapore PDPA compliance") and line 409 ("Tenant isolation enforced at the database schema level (separate schema per tenant, not just `tenant_id` column)").
- **governance**: orphan-detection (a manager/mechanism with no production call site); security/PDPA (isolation declared-but-not-applied).
- **fix**: route ALL tenant-scoped reads/writes through `get_tenant_session(tenant_id)` (or set `search_path` on every request-scoped session), and add a Tier-2 test proving a query executed for tenant A cannot see tenant B rows written into B's schema. Alternatively, if the shared-schema+`tenant_id` model is the intended design, the spec MUST be corrected (it currently forbids it) — but that requires explicit acknowledgement per `specs-authority.md` Rule 6.

### [HIGH] F3 — PDPA erasure is incomplete: message content, response content, consent records and routing outcomes are NOT erased

- **file:line**: `src/sequor/compliance.py:75-225` (`erase_contact_pii`).
- **evidence**: the function (a) UPDATEs Contact PII to `[erased]`/null (soft, not hard-delete — docstring line 84-86 explicitly "The contact row itself is kept"); (b) nulls DocumentChunk/LearnedAnswer embeddings; (c) erases LearnedAnswer text. It does NOT touch `Message.body_text`/`body_raw`/`subject`, does NOT touch `Response.content`, does NOT delete `ChannelConsent`, does NOT delete `RoutingOutcome`.
- **spec ref**: `specs/data-model.md:385-394` §Erasure implementation — step 1 Contact **hard delete**, step 2 ChannelConsent **hard delete**, step 3 Message content **hard delete**, step 4 Response content **hard delete**, step 5 RoutingOutcome **hard delete**. Message content is classified "PII — high sensitivity" (line 338).
- **governance**: zero-tolerance Rule 6 (documented behavior the code does not perform); PDPA erasure right (data-model §Individual Rights). Message-body PII survives an erasure request.
- **fix**: extend `erase_contact_pii` to erase `Message.body_text/body_raw/subject` and `Response.content` for the contact's messages, delete `ChannelConsent` and `RoutingOutcome` rows (per spec steps 2 & 5), and reconcile the soft-null vs hard-delete decision with the spec (if soft-null is intended, update the spec with rationale per `specs-authority.md` Rule 6). Add a Tier-2 erasure test asserting message bodies are gone after erasure.

### [MEDIUM] F4 — All FKs are `ON DELETE CASCADE`, contradicting spec "`ON DELETE RESTRICT` + cascade at app layer"; tenant deletion cascade-deletes immutable audit rows

- **file:line**: `src/sequor/db/models.py` (every FK uses `ondelete="CASCADE"`, e.g. lines 237, 648) and `migrations/.../5ab03308b1f3_initial_schema.py` (25× `ondelete='CASCADE'`, incl. `audit_entries.tenant_id → tenants.id` at :190).
- **evidence**: `grep -c "ondelete='CASCADE'"` → 25; `grep -c "'RESTRICT'"` → 0.
- **spec ref**: `specs/data-model.md:321-323` — "All foreign keys use `ON DELETE RESTRICT`… Tenant deletion requires all child records deleted first (cascade ordering enforced at application layer, not DB layer, to ensure audit trail integrity)… AuditEntry records are IMMUTABLE — no UPDATE or DELETE". A DB-layer CASCADE from `audit_entries.tenant_id` means deleting a Tenant hard-deletes the immutable audit log — directly defeating line 450 "Audit log is not subject to erasure".
- **governance**: specs-authority Rule 6 (silent deviation from spec); data-model audit-immutability guarantee.
- **fix**: change FKs to `RESTRICT` (or `SET NULL` where the spec's erasure flow expects anonymization) and enforce cascade ordering at the application layer per spec; OR update the spec with explicit rationale if DB CASCADE is the intended design.

### [MEDIUM] F5 — Three data-model entities unimplemented: OOOConfiguration, RoutingThresholdConfig, RoutingOutcomeAggregate

- **file:line**: `src/sequor/db/models.py` (absent).
- **evidence**: `grep -n "class OOOConfiguration\|class RoutingThresholdConfig\|class RoutingOutcomeAggregate" models.py` → no match. (`RoutingOutcome` IS implemented.)
- **spec ref**: `specs/data-model.md:232-300` lists all three as core entities (RoutingThresholdConfig, RoutingOutcomeAggregate, OOOConfiguration) with field schemas and the "flywheel loop mechanical path".
- **governance**: spec-accuracy — either the code is missing shipped entities OR the spec describes unbuilt machinery (the flywheel aggregation job) as shipped. `spec-accuracy.md` Rule 5 (spec ahead of code) vs specs-authority Rule 5 (code without spec).
- **fix**: implement the three models/migrations if they are in-scope for the wedge; otherwise move the flywheel entities to a target-state platform spec and cite the tracking todo (per `spec-accuracy.md` Rule 4).

### [MEDIUM] F6 — Encrypted columns silently store/return plaintext when `APP_ENV=development` (the default)

- **file:line**: `src/sequor/db/encrypted_column.py:131-141` (bind) and `156-166` (result).
- **evidence**: when `_current_tenant_key` is None AND `os.environ.get("APP_ENV","development") == "development"` (the default in `config.py:18`), the TypeDecorator returns the value unencrypted. Only a non-development `APP_ENV` raises. `signup` provisions a key, but any code path writing an encrypted column without a set tenant key silently persists plaintext in dev/test, and there is no `mode=`-tagged log line on the plaintext branch.
- **spec ref**: `specs/data-model.md:404` "All PII fields encrypted at rest (AES-256, tenant-specific keys)".
- **governance**: security (encryption declared-but-not-applied on a fallback path); zero-tolerance Rule 3 (silent fallback — no WARN log). Note: production is protected iff `APP_ENV != development` is actually set in every prod/staging environment; that is an ops-config dependency, not a code guarantee.
- **fix**: log a WARN (`mode=plaintext`) on the dev fallback, and gate on an explicit `ALLOW_PLAINTEXT_PII=true` flag rather than the ambient `APP_ENV` default, so plaintext PII cannot happen silently.

### [MEDIUM] F7 — `signup` swallows tenant-schema creation failure and commits the tenant anyway

- **file:line**: `src/sequor/onboarding/service.py:212-224` — `create_tenant_schema` is wrapped in `try/except Exception: logger.exception(...)` with no re-raise; `tenant.schema_name` is set (line 217) before the attempt, then `session.commit()` (line 231) runs regardless.
- **evidence**: on schema-creation failure the tenant row persists with `schema_name` pointing at a schema that does not exist, and the signup returns success.
- **spec ref**: `specs/data-model.md:5-7,409` (schema isolation is a PDPA hard requirement). (Compounds F2 — the schema is never used anyway, but the swallow is an independent silent-degradation.)
- **governance**: observability/zero-tolerance Rule 3 (logged-and-continue on a security-critical step); data-model PDPA.
- **fix**: re-raise (fail the signup) on schema-creation failure, or provision the schema in the same transaction so it rolls back atomically with the tenant.

### [LOW] F8 — Tenant field drift: spec's `whatsapp_bsp_account_id` absent; code's `schema_name` not in spec

- **file:line**: `src/sequor/db/models.py:203-219` (Tenant has `schema_name`, no `whatsapp_bsp_account_id`).
- **evidence**: `grep -rn whatsapp_bsp_account_id src/` → only in `specs/data-model.md:22`.
- **spec ref**: `specs/data-model.md:15-24` (Tenant schema).
- **fix**: add `whatsapp_bsp_account_id` (or remove from spec) and document `schema_name` in the spec — reconcile both directions.

### [LOW] F9 — Billing only implements free↔starter; Professional/Enterprise upgrade and per-message overage not wired

- **file:line**: `src/sequor/billing/service.py:117-206` (`_handle_*` set only `TenantPlan.starter` or `TenantPlan.free`); `create_checkout_session:86-97` hardcodes the Starter price.
- **evidence**: no handler transitions a tenant to `professional`/`enterprise`; no overage/per-message billing.
- **spec ref**: `specs/business-model.md:29-67` (Professional $60, Enterprise $200, per-message overage table).
- **governance**: much of business-model.md is unit-economics analysis rather than strict acceptance criteria, so LOW — but the 4-tier purchase path is a stated product surface.
- **fix**: wire Professional/Enterprise price IDs + plan transitions, or scope the wedge explicitly to Starter and note the deferral in a todo.

---

## 3. Summary

**Counts by severity:** HIGH 3 · MEDIUM 4 · LOW 2 (9 findings). No CRITICAL (no SQLi:
only f-string is `validate_identifier`-guarded; no hardcoded secrets found; every audited
module has ≥1 importing test — no zero-coverage HIGH).

**Top 5 findings (one line each):**

1. **[HIGH F1]** `ConfidenceBadge` enum lacks spec-required `uncertain`; `ConfidenceBadge("uncertain")` raises ValueError on the unconditional `_record_response` path (masked by a broad `except`) — uncertain auto-replies silently fail to persist.
2. **[HIGH F2]** Per-tenant PostgreSQL-schema isolation is orphaned — `get_tenant_session`/`search_path` has zero production call sites; data lives in the shared `public` schema keyed by `tenant_id`, the exact pattern `data-model.md:5-7` declares insufficient for PDPA.
3. **[HIGH F3]** PDPA erasure incomplete — `erase_contact_pii` never erases Message body content, Response content, ChannelConsent, or RoutingOutcome that the spec mandates hard-deleting; high-sensitivity message PII survives an erasure request.
4. **[MEDIUM F4]** All FKs are `ON DELETE CASCADE` vs spec `ON DELETE RESTRICT`; `audit_entries.tenant_id → CASCADE` lets tenant deletion hard-delete the immutable audit log.
5. **[MEDIUM F5]** Three data-model entities (OOOConfiguration, RoutingThresholdConfig, RoutingOutcomeAggregate) are listed as shipped in `data-model.md` but absent from `models.py`.
