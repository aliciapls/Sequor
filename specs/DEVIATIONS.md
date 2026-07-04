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
> count as open `/redteam` HIGH findings. The BUILD-PENDING / COUNSEL-PENDING items are the
> product/compliance decisions surfaced for the user in `04-validate/round3/00-DECISION-PACKET-R3.md`.

## FIXED this round (code now matches spec)

| ID    | Spec claim                                             | Fix                                                   |
| ----- | ------------------------------------------------------ | ----------------------------------------------------- |
| NEW-3 | `rag-pipeline.md:89` answerability<0.3 excluded        | `_ANSWERABILITY_FLOOR` exclusion in `rag_pipeline.py` |
| NEW-5 | `rag-pipeline.md:102` >50% of CLAIMS un-cited → reject | per-claim ratio via `total_claims`                    |

## BUILD-PENDING (code under-delivers vs an affirmative spec claim; recommend a scoped build)

### A1 — PII-at-rest encryption (CRITICAL) — recommend BUILD

- **Spec:** `data-model.md` "All PII fields encrypted at rest (AES-256)"; message content = "PII — high sensitivity".
- **Reality:** `Message.body_text/body_raw/subject`, `Response.content`, `LearnedAnswer.*_text`, `Classification.reasoning`, `Escalation.resolution_summary`, `Contact.name`, `Account.whatsapp_phone` stored plaintext. `EncryptedString` (AES-256-GCM + per-tenant HKDF) exists but is applied only to email/phone identifiers.
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

## COUNSEL-PENDING (compliance fact — needs legal input)

### A2 — Schema-per-tenant isolation (HIGH)

- **Spec:** `data-model.md` "separate schema per tenant … shared schema with tenant_id NOT sufficient for Singapore PDPA".
- **Reality:** per-tenant schemas created at signup but `get_tenant_session` (`SET search_path`) has ZERO callers; every live path uses `AsyncSession(engine)` + `WHERE tenant_id` on public tables. Isolation hinges on the (now fail-closed) JWT.
- **Recommendation:** get a PDPA determination first. If column-isolation + strong tenant-scoping is acceptable → AMEND the spec (cheap). If the schema-per-tenant mandate stands → BUILD (route every query through `get_tenant_session`; large invariant-heavy refactor, its own wave). Do NOT amend a written PDPA statement without counsel on record.

## RECONCILE (spec self-contradiction or value mismatch; recommended canonical value — RATIFY/OVERRIDE)

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

## Architecture note (whole-codebase, out of redteam scope)

Sequor's data layer is raw SQLAlchemy + FastAPI, not DataFlow. The framework-first hook fires on every `src/` edit; a DataFlow migration is a whole-codebase architectural decision, out of this redteam's scope. Logged so the recurring hook advisory is not mistaken for a per-edit defect.
