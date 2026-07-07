# R5 Spec-Parity Audit — Sequor comms-wedge (SHIPPED specs)

Re-derived from scratch against `fix/redteam-r1-security-correctness` @ HEAD. Scope: the 7 shipped
comms-wedge specs only. No prior round's self-report, DEVIATIONS disposition, or R3 packet trusted;
every row shows the literal command + actual output. Platform/vision specs out of scope.

Method: `.claude/skills/spec-compliance/SKILL.md`. Governance honored: evidence-first (inline output),
spec-accuracy R1 (every cited symbol grep-resolves), specs-authority R6 (a divergence is "handled"
only if LOGGED with a disposition matching code reality), symbol-anchored citations.

---

## Headline

The big-ticket divergences the prior rounds logged (A1 encryption, A2 tenant isolation, A3
threshold/badge unification, NEW-1 confidence badge, NEW-4 staleness, NEW-3/NEW-5 RAG floors,
NEW-7 enum) are all **verified accurate** against code — DEVIATIONS is faithful on those.

Adversarial sweep surfaced **three affirmative shipped-behavior claims that are absent in code and
NOT in DEVIATIONS** (F1 malware scan, F2 retention purge job, F3 routing flywheel), plus **three
register/spec-resolution accuracy defects** (F4 CS-6 Free-row never landed, F5 CS-5 residual
5-vs-6 template count, F6 NEW-8 dangling id). None is a phantom _symbol_ citation — every code
symbol the specs cite resolves.

---

## NEW (un-logged) findings

### F1 — Malware scan specced "before processing" is entirely absent (MED, NEW)

- **Spec (affirmative shipped claim):** `rag-pipeline.md` §"1. Upload and Validation" — "File is
  scanned for malware (ClamAV or equivalent) before processing".
- **Code:** zero implementation.
  ```
  $ grep -rni "malware\|clamav\|virus\|antivirus" src/sequor/
  >>> ZERO malware-scan references in entire src/sequor <<<
  ```
  `ingestion.py` enforces `MAX_FILE_SIZE = 25 * 1024 * 1024` and a SHA-256 `file_hash`, but no
  malware scan gate exists on the PDF/DOCX/XLSX/image upload path.
- **Classification:** NEW — no malware/scan row anywhere in `specs/DEVIATIONS.md`. An affirmative
  pre-processing security gate under-delivered and unlogged (specs-authority R6). Blast radius is
  bounded (upload path is onboarding/auth-gated + size-capped), hence MED not HIGH — but per the
  task's NEW-divergence framing it qualifies as a real finding.

### F2 — PDPA retention auto-deletion "nightly batch job" is not implemented (MED→HIGH, NEW)

- **Spec (affirmative, ×3 specs):** `data-model.md` §"Data Retention Schedule" — "Auto-deletion is
  enforced via a nightly batch job that purges records older than the retention period"; also
  `data-model.md` §RoutingOutcomeAggregate — "Raw RoutingOutcome records are purged after 90 days";
  retention tiers restated in `response-accuracy.md` §Audit Trail and `business-model.md`.
- **Code:** no retention/purge job exists.
  ```
  $ grep -rniE "retention|purge|cleanup|older_than|cron|scheduled|days=90" src/sequor/ | grep -v test
  src/sequor/billing/service.py:28: def _cleanup_old_event_ids()   # idempotency dedup — unrelated
  src/sequor/onboarding/app.py:864: week_ago = now - timedelta(days=7)  # digest window — unrelated
  ```
  `escalation/scheduler.py::SLAScheduler` is an SLA-breach checker only, not a retention purge.
- **Classification:** NEW — not in DEVIATIONS. This is a stated PDPA hard-requirement (retention
  _limitation_); its absence means PII is retained indefinitely past the specced 90d/12mo/24mo
  schedule. Rated MED given the persistence layer is broadly not production-hardened (consistent
  with A1/A2 pending), but the PDPA framing supports HIGH.

### F3 — Routing Intelligence Flywheel: no producer + 2 phantom entities vs "architected from day 1" (MED, NEW / partially A4-themed)

- **Spec (affirmative "not a future feature"):** `message-routing.md` §"Outcome Tracking
  Instrumentation" — "This is not a future feature. It is architected from day 1 - Every routing
  decision logs a `RoutingOutcome` record at the time of routing ... A nightly aggregation job
  computes per-category acceptance rates". `data-model.md` documents full schemas for
  `RoutingOutcome`, `RoutingThresholdConfig`, and `RoutingOutcomeAggregate`.
- **Code reality:**
  ```
  $ grep -n "class RoutingOutcome\|class RoutingThreshold\|class RoutingOutcomeAggregate" src/sequor/db/models.py
  720:class RoutingOutcome(Base):        # shell model only
  # RoutingThresholdConfig  → NO class
  # RoutingOutcomeAggregate → NO class
  $ grep -rniE "RoutingOutcome\(|routing_outcomes.*INSERT|create\(\"RoutingOutcome" src/sequor/ | grep -v test
  # (empty) — RoutingOutcome is never WRITTEN on any routing decision; no producer
  ```
  `RoutingOutcome` is a registered but never-populated table; the other two entities have no model
  class; the nightly aggregation job does not exist.
- **Classification:** the _decision_ to defer feature-moats is themed under the ratified **A4**
  ("feature-moats → sequence behind the F5 validation gate", banner-only). But the SPECIFICS are
  un-logged: (a) `RoutingThresholdConfig`/`RoutingOutcomeAggregate` are documented entities that
  fail grep as model classes; (b) `RoutingOutcome` has zero producers; (c) the spec text
  "architected from day 1 / Every routing decision logs a RoutingOutcome record" affirmatively
  claims shipped behavior that is absent — a `spec-accuracy.md` Rule 5 violation (spec describes
  only shipped behavior) that A4's deferral banner does not cure. MED.

---

## Register / spec-resolution accuracy defects

### F4 — CS-6 "Free row added to data-model retention table" never landed (MED, NEW)

- **Register claim:** DEVIATIONS banner — "all RECONCILE contradictions → the recommended canonical
  values, now **applied to the spec files**"; CS-6 canonical = "add Free row to data-model.md
  retention table".
- **Reality:** no Free tier anywhere in `data-model.md`.
  ```
  $ grep -c "Free" specs/data-model.md
  0
  ```
  The `data-model.md` §"Data Retention Schedule" table has only Starter/Professional/Enterprise
  columns; `business-model.md` still states Free "Audit log: 7-day retention". CS-6 is the ONE
  RECONCILE row whose spec edit did not land, so the register's "applied to the spec files" claim
  over-states (verify-claims-before-write class). Gap, not a hard contradiction — MED.

### F5 — CS-5 residual intra-spec template count 5 vs 6 (LOW, NEW)

- `message-routing.md:26` — "these **5** named templates are the mandatory minimum set —
  acknowledgement, OOO notice, escalation notice, urgent routing, 'I don't have this information'
  notice" (5; omits `human_override`).
- `message-routing.md:97-104` — "**Minimum required templates** (pre-approved at onboarding):" then
  enumerates **6** (`oo_acknowledgement, oo_notice, escalation_notice, no_information,
human_override, urgent_routing`).
- CS-5 claimed resolution "5-vs-6-vs-8 → 8 pre-approved, 5 named-required ⊆ 8" but left the 6-item
  "Minimum required templates" list intact, so the _named-required minimum_ is stated as both 5 and 6. Residual contradiction. LOW (code enforces no fixed template set —
  `whatsapp/sender.py::send_template_message` validates `^[a-z0-9_]{1,64}$` only — so no code impact).

### F6 — NEW-8 is a dangling register id (LOW, NEW)

- `DEVIATIONS.md` NEW-1 Reality bullet cites "(NEW-8)" for the WhatsApp-footer / "Reply STOP"
  omission, but no NEW-8 row is defined:
  ```
  $ grep -n "NEW-8" specs/DEVIATIONS.md
  47:...WhatsApp footer omits confidence + the "Reply STOP" opt-out phrasing (NEW-8).
  ```
  The substance is covered by NEW-1's disposition (BUILD the badge/footer), so no substantive open
  gap — but the id resolves to nothing. LOW.

---

## Confirmed LOGGED-and-accurate (not open findings — DEVIATIONS matches code)

| DEVIATIONS row       | Spec claim                                                         | Code reality (verified)                                                                                                                                                                                                                          | Verdict                                    |
| -------------------- | ------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------ |
| A1                   | `data-model.md` "All PII fields encrypted at rest (AES-256)"       | `EncryptedString` wraps ONLY `owner_email, email_address, backup_email, backup_phone, contact_email, contact_phone` (models.py:250-333); `Message.body_text/raw/subject`, `Response.content`, `Contact.name`, `Account.whatsapp_phone` plaintext | LOGGED-accurate (BUILD-PENDING)            |
| A2                   | `data-model.md` "separate schema per tenant"                       | `get_tenant_session` (database.py:108) has **0 callers**; `schema_manager.py:92` creates per-tenant schemas at signup; live paths use `WHERE tenant_id`                                                                                          | LOGGED-accurate (RLS decision)             |
| A3                   | Badge table vs Option-C ">90%"; classifier-gate vs synthesis-badge | `response.py:268` gate = `classification.confidence >= 0.9`; badge = `synthesis.confidence_badge` (:279); learned path gate `>=0.85` (:214), badge cutoffs `0.8/0.6/0.4` (:228-235); `classifier.should_auto_respond` has **0 callers** (dead)   | LOGGED-accurate (RECONCILE + scoped shard) |
| NEW-1                | badge footer / `X-AI-Confidence` header                            | `templates.py::build_auto_reply_email(confidence_badge)` — kwarg never referenced in body (silent no-op, zero-tol 3c); `grep X-AI-Confidence src/` = 0                                                                                           | LOGGED-accurate                            |
| NEW-3                | `rag-pipeline.md:89` answerability<0.3 excluded                    | `rag_pipeline.py:20` `_ANSWERABILITY_FLOOR = 0.3`; `:119` `if answerability < _ANSWERABILITY_FLOOR: continue`                                                                                                                                    | LOGGED-accurate (FIXED)                    |
| NEW-5                | `rag-pipeline.md:102` >50% claims uncited → reject                 | `rag_pipeline.py:373` `if total_claims > 0 and uncited/total_claims > 0.5` + malformed-judge guard `:375`                                                                                                                                        | LOGGED-accurate (FIXED)                    |
| NEW-4                | `last_indexed_at` staleness badge                                  | written only (ingestion.py/onboarding app.py); no read/`staleness`/`outdated` in retrieval                                                                                                                                                       | LOGGED-accurate (BUILD-PENDING)            |
| NEW-7                | `EscalationStatus.notification_pending`, no `pending_ooo_return`   | models.py:153-158 = `pending, acknowledged, resolved, expired, notification_pending`                                                                                                                                                             | LOGGED-accurate (FIXED)                    |
| Digest multi-account | over-counts for >1 account/tenant                                  | matches shipped `digest/service.py` scoping                                                                                                                                                                                                      | LOGGED-accurate (limitation)               |

## Verified-MATCH (spec claim confirmed shipped — no divergence)

| Assertion                                                       | Command / output                                                                                                                                                                                                                                  | Verdict                                    |
| --------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| thread_key mechanism (CS-2)                                     | `thread_key.py:60 derive_thread_key`; `:94 hashlib.sha256(...).hexdigest()`; topic=first 5 significant words (:47-57)                                                                                                                             | MATCH                                      |
| dedup 72h window (CS-1)                                         | `thread_key.py:6` + `channel-coordination.md:136` both 72h; consistent across specs                                                                                                                                                               | MATCH                                      |
| embedding model/dim (NEW-2)                                     | `config.py:32 embedding_model="nomic-embed-text"`, `:36 openai_embedding_model="text-embedding-3-small"`; `models.py:550,586 Vector(768)`                                                                                                         | MATCH                                      |
| HUMAN detection (msg-routing §2)                                | `compliance.py:54 upper == "HUMAN" or upper.startswith("HUMAN ")` — exact/starts-with, not substring                                                                                                                                              | MATCH                                      |
| STOP opt-out (data-model)                                       | `compliance.py:25 OPT_OUT_KEYWORDS={"HUMAN","STOP"}`, `:28 is_opt_out` (entire msg or first word)                                                                                                                                                 | MATCH                                      |
| high-stakes excluded from RAG/auto-send (resp-acc §High-Stakes) | `response.py:86 if category==HIGH_STAKES: _handle_high_stakes` (before RAG); `classifier.py:287 category != HIGH_STAKES`                                                                                                                          | MATCH                                      |
| ChannelConsent recorded first contact (msg-routing §1)          | `whatsapp/inbound.py:125 _ensure_consent` → `db.create("ChannelConsent", ...)` (:250); dedup via existing check (:243). Nuance: recorded at step 6 _during_ processing, not a hard pre-gate; email inbound records none (WhatsApp-scoped spec §1) | MATCH (ordering nuance, LOW/observational) |
| rate limits (msg-routing)                                       | `config.py:42 email=60/min`, `:70 whatsapp=250/min`, `:71 whatsapp_user_rate_limit_seconds=6.0`                                                                                                                                                   | MATCH                                      |
| BM25 hybrid 0.7/0.3 (rag §5)                                    | `vector_store.py:40 VECTOR_WEIGHT=0.7`, `:41 BM25_WEIGHT=0.3`, `:154 combined = 0.7*vec + 0.3*bm25`                                                                                                                                               | MATCH                                      |
| max file size 25MB (rag §1)                                     | `ingestion.py:47 MAX_FILE_SIZE = 25*1024*1024`; enforced :146                                                                                                                                                                                     | MATCH                                      |
| email threading headers (msg-routing)                           | `email/parser.py:102-104` extracts Message-Id/In-Reply-To/References                                                                                                                                                                              | MATCH                                      |
| split-state framing scan (spec-accuracy R2)                     | `rg -i 'phase-?1.*phase-?2\|TBD\|to.be.wired\|scaffold.*later\|pending.accessor' specs/{7 files}` → NO matches                                                                                                                                    | MATCH (clean)                              |

---

## Summary table

| Metric                   | Count                                                                                    |
| ------------------------ | ---------------------------------------------------------------------------------------- |
| Total assertions checked | 34                                                                                       |
| Verified-match           | 28                                                                                       |
| Divergences found        | 6                                                                                        |
| — NEW (un-logged)        | 6 (F1 malware, F2 retention, F3 flywheel, F4 CS-6, F5 CS-5 residual, F6 NEW-8)           |
| — LOGGED (accurately)    | 9 (A1, A2, A3, NEW-1, NEW-3, NEW-4, NEW-5, NEW-7, digest) — confirmed faithful, not open |
| CRITICAL                 | 0 (no phantom symbol citation — every cited code symbol resolves)                        |
| HIGH                     | 0 firm (F2 defensible as HIGH under PDPA framing)                                        |
| MED                      | 4 (F1, F2, F3, F4)                                                                       |
| LOW                      | 2 (F5, F6) + 1 observational (consent ordering)                                          |

**Convergence verdict:** NOT clean. Six NEW un-logged divergences. The prior 4 rounds converged on
the code-level correctness fixes and the register's big-ticket dispositions (all accurate) but
missed three _absent affirmative behaviors_ (malware scan, retention purge, routing flywheel) and
three _resolution-accuracy_ defects (CS-6 unlanded, CS-5 residual, NEW-8 dangling). Recommended:
add DEVIATIONS rows for F1/F2/F3 with dispositions; land the CS-6 Free-row edit or correct the
"applied to spec files" banner; reconcile CS-5 to one named-required count; define or drop NEW-8;
and correct message-routing.md's "architected from day 1" flywheel language per spec-accuracy R5.
