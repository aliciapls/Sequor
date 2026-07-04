# /redteam Round 3 — Spec-Parity Audit (independent re-derivation)

Scope: the 7 SHIPPED comms-wedge specs vs `src/sequor/`. Platform specs excluded (TARGET-STATE per `specs/_index.md`). Field-level assertions, grep/AST verified.

## Counts (as found)

- CRITICAL 1 · HIGH 6 · MED 7 · LOW 3 · cross-spec contradictions 6

## Confirmed items 1–3 (were Group A in the R2 packet)

- **Item 1 — PII-at-rest encryption (CRIT).** `data-model.md` claims "All PII fields encrypted at rest (AES-256)"; message content classified "PII — high sensitivity". `models.py` stores `Message.body_text:415/body_raw:416/subject:414`, `Response.content:613`, `LearnedAnswer.question_text/answer_text:580-581`, `DocumentChunk.chunk_text:548`, `Classification.reasoning:457`, `Escalation.resolution_summary:669`, `Contact.name`, `Account.whatsapp_phone:258` as PLAINTEXT `Text`/`String`. Only email/phone identifiers use `EncryptedString`. Un-logged divergence. → **A1 (see deviations log).**
- **Item 2 — schema-per-tenant isolation (HIGH).** `data-model.md`: "separate schema per tenant … shared schema with tenant_id NOT sufficient for PDPA". Schemas are created at signup (`onboarding/service.py:214`) but `get_tenant_session` (the only `SET search_path` helper, `database.py:116`) has ZERO callers; every live path uses `AsyncSession(engine)` + `WHERE tenant_id`. Isolation hinges on the (now fail-closed) JWT. → **A2 (needs PDPA counsel; deviations log).**
- **Item 3 — auto-send threshold contradiction (HIGH).** `response-accuracy.md` self-contradicts: Options C ">90% auto-send" vs Badge table ">95% High / 80–95% Moderate". Code diverges AND is internally inconsistent: auto-send gates on CLASSIFIER confidence (`response.py:118`) while the displayed badge uses SYNTHESIS confidence; three threshold sets (0.9 / 0.85 / 0.8); `Account.confidence_threshold` never read. → **A3 (see deviations log).**

## NEW findings

- **NEW-1 (HIGH) — Confidence badge never rendered; documented `confidence_badge` kwarg is a silent no-op** (zero-tolerance 3c). `templates.py:117 build_auto_reply_email(confidence_badge)` unused; no `X-AI-Confidence` header; WhatsApp footer omits confidence. → deviations log (NEW-1).
- **NEW-2 (MED) — Embedding model/dims diverge.** Spec: `text-embedding-3-small`, 1536-dim. Code: `Vector(768)`, `nomic-embed-text`. OpenAI fallback returns 1536 → cannot insert into `Vector(768)` (latent). → spec amend to reflect shipped 768/nomic + fix/guard the fallback (deviations log).
- **NEW-3 (MED) — Answerability<0.3 exclusion not implemented.** `rag-pipeline.md:89`. **FIXED** this session (`_ANSWERABILITY_FLOOR` exclusion in `rag_pipeline.py`).
- **NEW-4 (MED) — Staleness warning not implemented.** `response-accuracy.md:134` / `rag-pipeline.md:66`. `last_indexed_at` written but never read by retrieval/synthesis. → feature build (deviations log).
- **NEW-5 (MED) — Hallucination denominator wrong.** `rag_pipeline.py` compared uncited-claims to passage count, not claim count. **FIXED** this session (per-claim ratio via `total_claims`).
- **NEW-6 (LOW) — `should_auto_respond` orphan / divergent second gate.** Part of A3.
- **NEW-7 (LOW) — Escalation status enum drift.** `notification_pending` in code not spec; `pending_ooo_return` in `channel-coordination.md` in neither enum nor code. → spec reconcile (deviations log).
- **NEW-8 (LOW) — WhatsApp "Reply STOP" opt-out phrasing missing** from the shipped footer. → part of NEW-1 badge/footer feature.

## Cross-spec contradictions

- **CS-1 (HIGH) — Dedup window 48h (`message-routing.md`) vs 72h (`channel-coordination.md`).** → spec reconcile (deviations log).
- **CS-2 (HIGH) — Dedup key mechanism** embedding-similarity vs `SHA256(thread_key)`. Code ships `escalation/thread_key.py`. → spec reconcile to shipped mechanism.
- **CS-3 (MED) — Staleness threshold** flat 7d vs 7/30d by doc type.
- **CS-4 (MED) — Audit retention** flat 24-month vs tiered 90d/12mo/24mo.
- **CS-5 (MED) — Template minimum count** 5 vs 6 vs 8 within `message-routing.md`.
- **CS-6 (LOW) — Free-tier audit retention** only in `business-model.md`.

## Disposition summary

- FIXED this session: NEW-3, NEW-5.
- Autonomous spec reconciliations (pick canonical/safer + log deviation): Item 3 (A3 spec horn), NEW-2, NEW-7, CS-1..CS-6.
- Feature-moat / compliance builds — logged deviations behind F5: A1 (encryption), A2 (schema-per-tenant/counsel), NEW-1+NEW-8 (badge+footer), NEW-4 (staleness).
  Full evidence-quoted findings captured in the orchestrator transcript (analyst, Round 3, 2026-07-05).
