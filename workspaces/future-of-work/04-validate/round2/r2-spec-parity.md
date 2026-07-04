# /redteam Round 2 — Spec-Parity Decision Packet (comms-wedge)

Date: 2026-07-04 · Branch `fix/redteam-r1-security-correctness` · Posture L5_DELEGATED · Read-only on `src/`.
Scope: every Round-1 deferred HIGH feature-gap, resolved to an authoritative BUILD / AMEND-SPEC / RECONCILE input.

Method (per evidence-first-claims MUST-1): each row quotes BOTH the SHIPPED spec line AND the actual code line, re-verified against the current fix-branch tree (line numbers below are the branch's current lines; the fix pass shifted several off the Round-1 values). Every "spec says X / code does Y" pair was re-run this round; empty greps were re-run to confirm true absence.

Repo layout note: specs live at repo-root `specs/`, code at `src/sequor/` (not under the workspace). The Round-1 `session_for_tenant` reference is the function actually named `get_tenant_session` in `db/database.py`.

---

## Decision table

| # | Item | Spec claim (file — quote) | Code reality (file — quote) | Delta severity | Disposition |
|---|------|---------------------------|-----------------------------|----------------|-------------|
| 1 | Message-body encryption | `data-model.md` § Security by Design: *"All PII fields encrypted at rest (AES-256, tenant-specific keys)"*; § Personal Data Categories: *"Message content (body, subject, attachments) \| PII — high sensitivity"* | `db/models.py` — `Message.subject` (`mapped_column(String(500))`), `body_text`/`body_raw` (`mapped_column(Text)`) are plaintext; `EncryptedString` wraps only identifiers (`owner_email`, `contact_email/phone`, `backup_email/phone`). Same plaintext on `DocumentChunk.chunk_text`, `LearnedAnswer.question_text/answer_text`, `Response.content`, `Escalation.resolution_summary`. | HIGH | **RECONCILE** |
| 2 | Schema-per-tenant isolation | `data-model.md` § Multi-Tenancy: *"separate PostgreSQL schemas per tenant … Namespace separation (shared schema with tenant_id) is NOT sufficient for Singapore PDPA compliance"*; § Security by Design: *"Tenant isolation enforced at the database schema level (separate schema per tenant, not just tenant_id column)"* | `db/database.py::get_tenant_session` issues `SET search_path TO "<schema>"` but has **zero callers** in `src/`. `onboarding/service.py::signup` calls `create_tenant_schema` (creates the per-tenant schema), so schemas are created then left empty; all live read/write paths use a plain `AsyncSession(engine)` + `WHERE tenant_id ==` on `public` tables. | HIGH | **RECONCILE** |
| 3 | Digest API drift | (no spec claim — this is a test↔impl drift). `channel-coordination.md` § Daily Digest promises the email; the *API shape* is unspecced. | Canonical shipped surface = **class `DigestService`** in `digest/service.py`: `async def send_digest(self, …)`, `async def send_all_tenants(self)`, module fns `build_digest_email` / `build_digest_subject`. Unit suite `tests/unit/test_digest_service.py` (8 tests) drives the class. Three integration/e2e files import module-level `gather_digest_data` / `format_digest_email` / `send_digest` — **which do not exist** → `ImportError` aborts `tests/integration/` collection. | HIGH | **BUILD** |
| 4a | RoutingOutcome instrumentation (c1-H2) | `message-routing.md` § Outcome Tracking Instrumentation: *"This is not a future feature. It is architected from day 1: Every routing decision logs a RoutingOutcome record at the time of routing."* | `RoutingOutcome` appears only in `db/models.py` (model) + the initial migration. **Zero write sites**; `auto_response_accepted`/`auto_response_rejected` are never assigned in any code path. | HIGH — **HARD** ("architected from day 1") | **BUILD** |
| 4b | HUMAN-override persistence (c1-H3) | `message-routing.md` § Hard Compliance Requirements (*"non-negotiable — violation results in API access revocation"*) → HUMAN rejection path: *"The contact's future messages are tagged human_override = true and never auto-responded"*, *"receives a template message: 'A team member will respond shortly'"*, *"The auto_response_rejected flag is set in RoutingOutcome"*. `data-model.md` defines `Contact.human_override: boolean`. | `whatsapp/inbound.py` writes `human_override` onto the **current Message only** (`message_data["human_override"] = True`), never onto `Contact`. Webhook guard `onboarding/app.py` (`if result.get("status")=="created" and not result.get("human_override")`) reads THIS message's per-body detection, so a contact who once said "HUMAN" is auto-replied on the next message. No `human_override` template send; `auto_response_rejected` never written. | HIGH — **HARD** (WhatsApp compliance, non-negotiable) | **BUILD** |
| 4c | Multi-channel dedup / thread-key (c1-H5) | `message-routing.md` § Multi-Channel Deduplication: *"the system MUST detect this and prevent duplicate escalations"* (48hr window, email+phone+name identity, similarity >70%); `channel-coordination.md` § Thread Key: *"within 72 hours belong to the same escalation"*. | `escalation/thread_key.py::derive_thread_key` matches the spec derivation but has **zero production callers** (only the package re-export). No dedup logic anywhere; `Escalation` model has no `thread_key`/`channel` column; every inbound message creates its own escalation. | HIGH — **HARD (MUST)**, large moat feature | **BUILD** |
| 4d | Unified Escalation fields + contradiction wiring (c1-H6) | `channel-coordination.md` § Unified Escalation Record lists `thread_key, channel, ai_summary, routing_reason, suggested_response`; § Contradictory Response Prevention: *"Every escalation record stores: ai_auto_replies … human_replies …"*, *"The backup MUST NOT send an email response that contradicts the WhatsApp reply"*. | `db/models.py::Escalation` columns end at `resolution_summary` — **none** of `thread_key`/`channel`/`ai_summary`/`routing_reason`/`suggested_response`/`ai_auto_replies`/`human_replies` exist. `escalation/service.py` computes `ai_summary`/`routing_reason`/`suggested_response` then only emails them (never persists). `check_contradiction` has zero production callers (unit-test only). | HIGH — **HARD (MUST)**, large moat feature | **BUILD** |
| 4e | Digest/recap scheduling (c1-H7) | `channel-coordination.md` § Daily Digest: *"Every morning, the account owner receives a digest email"*; § Weekly Recap (Professional+). | Builders exist AND the class is unit-tested, but `DigestService.send_all_tenants` and `email/templates.py::build_weekly_recap_email` have **zero in-repo callers**; `escalation/scheduler.py` contains no digest/recap references. | HIGH — **HARD** promise, but small gap | **BUILD** (see cron caveat) |
| 5a | Confidence-badge rendering (c2-F3) | `response-accuracy.md` § Badge Display: *"In WhatsApp: appended as a footer note — '[Auto-generated; 92% confidence. Reply STOP to speak with a human]'"*, *"In email: added as an X-AI-Confidence header + visible footer"*, *"The badge MUST NOT be editable by the AI or configurable by the user — it is a fixed governance control"*. | Grep across all of `src/` for `X-AI-Confidence` / `Reply STOP` / `Auto-generated` / `% confidence` → **zero matches**. The badge is computed (`ResponseResult.confidence_badge`) but never rendered to any channel. | HIGH — **HARD** ("MUST", "fixed governance control") | **BUILD** |
| 5b | Staleness warning (c2-F4) | `response-accuracy.md` § Staleness Detection: *"The response confidence badge MUST include a staleness warning if any retrieved document is >7 days old: '[Sources may be outdated — last updated X days ago]'"*; `rag-pipeline.md` § Index Age Tracking: *"Stale documents (>threshold) are flagged in retrieval — badge shows 'may be outdated'."* | `ingestion.py` writes `last_indexed_at`, but grep of `vector_store.py` + `rag_pipeline.py` for `stale`/`last_indexed_at`/`outdated` → **zero matches**. Retrieval never selects the timestamp; synthesis never appends a staleness clause. | HIGH — **HARD (MUST)** | **BUILD** |
| 5c | Answerability<0.3 exclusion (c2-F2) | `rag-pipeline.md` § Retrieval Confidence Scoring: *"If answerability < 0.3, the passage is excluded even if vector similarity is high."*; `response-accuracy.md` § Hallucination Controls: *"If no, do not use passage even if vector similarity is high."* | `rag_pipeline.py::retrieve` computes `answerability` and multiplies it into `final_score`, then appends **every** passage — grep for a `< 0.3` / `continue` exclusion branch → **none**. Low-answerability passages still feed synthesis. | HIGH — **HARD (MUST)**, hallucination control | **BUILD** |
| 5d | Badge-threshold drift (c2-F6) | `response-accuracy.md` § Confidence Badge — Badge Levels table: `>95% High / 80-95% Moderate / 60-80% Low / <60% Uncertain`. | Two code paths, both wrong AND mutually inconsistent: `rag_pipeline.py` (RAG path) `>=0.9→high, >=0.6→moderate, >=0.4→low, else uncertain`; `response.py` (learned path) `>=0.8→high, >=0.6→moderate, >=0.4→low, else uncertain`. Neither matches spec floors (0.95/0.80/0.60); the two disagree on the "high" boundary (0.9 vs 0.8). | HIGH | **BUILD** (blocked on F11 first) |
| 5e | F11 spec-internal contradiction | `response-accuracy.md` § Response Options C: *"For confidence > 90%: auto-send … 60-90%: route to backup … <60%: … suggested response"* vs § Badge Levels table: *">95% … Auto-send"* and *"80-95% … Auto-send with explicit badge"*. Two different auto-send thresholds; code cannot satisfy both. | (spec-only defect — not a code claim) | HIGH — spec-author gate | **RECONCILE** |
| 6a | WhatsApp subsystem zero tests (c1-H4 / c4) | Governance `testing.md` § Audit Mode: *"every new module MUST have ≥1 importing test — zero importing tests = HIGH."* Security: `verify_meta_signature` is the inbound webhook verifier; `is_human_override` is the compliance detector. | All **7** `whatsapp/*` modules (`sender, auto_reply, rate_limiter, inbound, parser, utils, signature`) have **0** importing test files. `verify_meta_signature` and `is_human_override` are referenced by zero test files. | HIGH | **BUILD** (test suite) |
| 6b | `auth` coverage (Round-1 c4) | Same audit-mode rule. | **CLOSED this fix pass** — `tests/unit/test_auth.py` (`import sequor.auth as auth`, 6 cases) now covers the JWT surface. | — | **CLOSED** (no action) |
| 6c | `ai.ingestion` coverage | Same audit-mode rule. | Referenced **only** as a mock-patch target: `tests/unit/test_document_upload_api.py` `@patch("sequor.ai.ingestion.DocumentIngester.ingest", …)`. No behavioral importing test; the module is stubbed out where referenced. | MEDIUM/HIGH | **BUILD** (thin behavioral test) |
| 6d | `onboarding.api` coverage | Same audit-mode rule. | `onboarding/api.py::handle_signup` (the signup endpoint handler) has **0** importing tests. The similarly-named `tests/unit/test_onboarding_api.py` drives the app via an HTTP test client, not this module. | HIGH | **BUILD** (importing test) |

---

## Per-item recommendation + rationale

**1 — Message-body encryption → RECONCILE (lean BUILD).** The spec makes an *unqualified* PDPA claim ("All PII fields encrypted at rest") and classifies message content as high-sensitivity PII, while the code stores it plaintext — a fake-encryption gap under zero-tolerance. Both dispositions are viable: BUILD is mechanically cheap (the `EncryptedString` type already exists and is used for identifiers, so wrapping `body_text`/`body_raw`/`subject`/`chunk_text`/`content` is a column-type change + migration), but full-content encryption has real implications for any future search/analytics over bodies. Because the choice trades a PDPA-faithful posture against query flexibility, it is the human's compliance call. Recommend BUILD (honor the stated hard PDPA requirement); AMEND requires explicit PDPA sign-off that plaintext-at-rest bodies are acceptable.

**2 — Schema-per-tenant isolation → RECONCILE.** The spec explicitly states shared-schema + tenant_id is "NOT sufficient for Singapore PDPA compliance," yet that is exactly what ships; the schema-per-tenant machinery is half-built (schemas created at signup, `get_tenant_session` never used). This is an architecture + compliance decision, not a bug: BUILD = route all tenant queries through `get_tenant_session`/`SET search_path` (substantial, touches every portal + inbound path); AMEND = accept column isolation with a documented PDPA sign-off AND delete the dead schema-creation path. Human must pick — and note that today's column-only isolation currently hinges on the (now-fixed) JWT, so the residual risk is real either way.

**3 — Digest API → BUILD.** Canonical surface is the `DigestService` class (real send path, 8 unit tests). The three integration/e2e tests encode a stale *function* API that never shipped and abort collection. Fix in one PR: either add thin module-level `gather_digest_data` / `format_digest_email` / `send_digest` wrappers delegating to the class (the tests encode the intended function contract), or rewrite the three tests to drive the class. Recommend the wrappers + re-run `--collect-only` to green. No spec claim is at stake, so this is not AMEND.

**4a RoutingOutcome → BUILD (HARD).** Spec language is categorical: "not a future feature … architected from day 1." A model+table with zero writers is the orphan pattern; the routing-flywheel moat has no source data. Write a `RoutingOutcome` row at each routing decision and update `auto_response_accepted/rejected` when the outcome is known.

**4b HUMAN-override persistence → BUILD (HARD).** Sits under "Hard Compliance Requirements … non-negotiable — violation results in API access revocation." Today a contact who requested a human is still auto-replied on later messages. Persist the override on `Contact` (the field already exists in the data model), force-escalate + suppress auto-reply whenever the contact carries it, send the `human_override` template, and set `auto_response_rejected`.

**4c Multi-channel dedup / thread-key → BUILD (HARD, large).** Spec uses "MUST detect … prevent duplicate escalations." The derivation function exists but is never called and the Escalation model lacks `thread_key`/`channel`. This is a genuine feature build (columns + dedup lookup at escalation creation); it is HARD-stated, but its size means the human may choose to scope/sequence it — surface it as HARD with a scoping note rather than a silent defer.

**4d Unified Escalation fields + contradiction → BUILD (HARD, large).** Same MUST-language moat. Extend the Escalation model (or a linked table) with the seven spec fields, persist `ai_summary`/`routing_reason`/`suggested_response` at creation, record every AI/human reply, and call `check_contradiction` on the human reply-send path. Pairs naturally with 4c (both need `thread_key`/`channel`).

**4e Digest/recap scheduling → BUILD (HARD, small) — cron caveat.** The builders exist and the class is tested; only the in-repo trigger is missing. Wire `send_all_tenants` + weekly recap into `escalation/scheduler.py` (or a documented entrypoint). Caveat: if an out-of-repo cron already calls `send_all_tenants` in `deploy/`, the correct disposition flips to AMEND-SPEC — cite the cron in the spec and add an integration test. Verify `deploy/` before building a duplicate scheduler.

**5a Badge rendering → BUILD (HARD).** "Fixed governance control … MUST NOT be editable." Contacts currently receive AI replies with no confidence signal and no human-handoff prompt. Render the WhatsApp footer + email `X-AI-Confidence` header at the send boundary; mark non-editable.

**5b Staleness warning → BUILD (HARD).** "The response confidence badge MUST include a staleness warning …". Select `last_indexed_at` in retrieval, compare to the per-doc-type threshold, append the staleness clause to the badge.

**5c Answerability<0.3 exclusion → BUILD (HARD).** A stated hallucination control that never fires. Add the exclusion (`if answerability < 0.3: continue`) before passages feed synthesis.

**5d Badge-threshold drift → BUILD, but sequence after 5e.** Collapse both paths into one shared badge classifier using the spec floors and labels. Do NOT land until F11 is resolved — the "high/auto-send" boundary depends on which threshold the spec authors keep.

**5e F11 spec-internal contradiction → RECONCILE.** The spec specifies two different auto-send thresholds (>90% in Option C vs >95%/80-95% in the badge table). Code cannot be compliant with both. Spec-author/human must pick one auto-send threshold BEFORE 5d (and the F5 auto-send-gate fix) can be made correct.

**6a WhatsApp zero tests → BUILD.** Seven modules incl. the webhook signature verifier and the override detector ship untested. Add Tier-1 unit tests (`verify_meta_signature` valid/missing/malformed/mismatch; `is_human_override` exact/starts-with/"human resources"/empty; `parse_meta_webhook_payload`) + a Tier-2 inbound→auto-reply wiring test.

**6b auth → CLOSED.** The fix pass added `tests/unit/test_auth.py`; no action.

**6c ai.ingestion → BUILD (thin).** The only reference mocks the module out, so ingestion behavior is unverified. Add ≥1 behavioral importing test for `DocumentIngester.ingest`.

**6d onboarding.api → BUILD.** `handle_signup` has no importing test (the like-named file tests the HTTP app, not this handler). Add a direct importing test.

---

## Disposition summary

| Item | Disposition | Spec-strength |
|------|-------------|---------------|
| 1 Message encryption | RECONCILE (lean BUILD) | unqualified PDPA claim |
| 2 Schema-per-tenant | RECONCILE | explicit "column NOT sufficient" |
| 3 Digest API drift | BUILD | test↔impl drift (no spec) |
| 4a RoutingOutcome | BUILD | HARD ("day 1") |
| 4b HUMAN-override persistence | BUILD | HARD (non-negotiable) |
| 4c Multi-channel dedup | BUILD | HARD (MUST), large |
| 4d Escalation fields/contradiction | BUILD | HARD (MUST), large |
| 4e Digest scheduling | BUILD | HARD, small (cron caveat) |
| 5a Badge rendering | BUILD | HARD (governance control) |
| 5b Staleness warning | BUILD | HARD (MUST) |
| 5c Answerability<0.3 | BUILD | HARD (MUST) |
| 5d Badge-threshold drift | BUILD (after 5e) | HARD |
| 5e F11 contradiction | RECONCILE | spec-author gate |
| 6a WhatsApp zero tests | BUILD | HARD (audit-mode) |
| 6b auth tests | CLOSED | — |
| 6c ai.ingestion tests | BUILD | MED/HIGH |
| 6d onboarding.api tests | BUILD | HIGH |

Two RECONCILE items (1, 2) and one spec-author RECONCILE (5e) are the only rows needing a human product/compliance decision before build; everything else is a determinate BUILD (or already CLOSED).
