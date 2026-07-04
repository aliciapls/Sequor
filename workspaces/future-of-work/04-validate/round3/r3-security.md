# /redteam Round 3 — Security Re-Audit (independent re-derivation)

Scope: `src/sequor/` (raw SQLAlchemy + FastAPI). Every claim re-derived from current code on branch `fix/redteam-r1-security-correctness`; prior rounds not trusted. Posture L5_DELEGATED.

## Counts

- CRITICAL: 0 · HIGH: 0 · MED: 3 (N1, N2, N3) · LOW: 3 (N4, N5, N6)

## R1/R2 fix verification — ALL PASS (evidence quoted inline by the auditor)

1. **CRITICAL auth bypass (R1)** — PASS. `auth.py` `decode_token` pins `algorithms=[ALGORITHM]` (HS256); every `/api/v1/portal/*` route funnels through `_require_auth`.
2. **Fail-closed encryption default** — PASS. `config.py` `app_env: str = "production"`.
3. **JWT_SECRET / ENCRYPTION_MASTER_KEY fail-closed** — PASS. `auth.py` raises when secret empty outside dev; `encryption_keys.py`/`encrypted_column.py` raise in production when no tenant key.
4. **Admin cross-tenant op gated** — PASS. `app.py` `if operator.get("role") != "admin": raise 403`; no raw `{e}` echoed.
5. **Upload memory DoS (onboarding path)** — PASS. `app.py:195` bounded `read(_MAX+1)` + 413.
6. **Login timing oracle** — PASS. dummy-bcrypt on absent-contact + null-hash paths.
   Also clean: SQLi (all `text()` sites parameterized / identifier-validated), WhatsApp webhook HMAC (`compare_digest`), no `eval/exec/shell=True/pickle/yaml.load`, tenant isolation on portal queries + vector/learned search.

## NEW findings + DISPOSITION (this session)

- **N1 (MED) — Unbounded upload read on the AUTHENTICATED portal path** (`onboarding/app.py` `portal_api_upload_document`) — same bug-class as the R2-M6 fix left un-hardened on the sibling handler. **FIXED** this session (bounded `read(_MAX+1)` + 413), per `autonomous-execution.md` MUST Rule 4 (same-class sibling in shard budget).
- **N2 (MED) — Unauthenticated DNS endpoints; no rate limit, no resolver timeout, weak validation** (`/api/v1/dns/records`, `/api/v1/dns/verify`). **PARTIALLY FIXED**: resolver timeout (`lifetime=5s`), per-IP rate limiter (30/hr), strict hostname regex added. **DEFERRED (flow decision)**: whether these must sit behind auth depends on whether the onboarding UI calls them pre-login — logged deviation for the user (packet M5).
- **N3 (MED) — In-memory rate limiter fails OPEN at capacity** (`rate_limiter.py` returned `True` when `_MAX_TRACKED_KEYS` reached → throttle bypass by key-flooding). **FIXED**: fail-closed with LRU eviction of the oldest key. (Serverless multi-instance ineffectiveness — needs a shared store — remains a logged deviation; packet M7.)
- **N4 (LOW) — SendGrid inbound: empty body skipped verification; no replay/timestamp protection.** **PARTIALLY FIXED**: production now rejects any webhook it cannot verify (empty body OR missing signature). **DEFERRED**: timestamp/replay binding needs the real SendGrid signed-timestamp format (packet M8).
- **N5 (LOW) — Prompt-injection: no instruction/data separation on the auto-send LLM path** (`rag_pipeline.py`, `classifier.py`). Blast radius bounded (self-targeted reply, tenant-scoped retrieval, confidence-gated). **DEFERRED (design)**: LLM-side instruction/data separation across 4 prompt sites — logged deviation (mitigation must stay LLM-side per `agent-reasoning.md`, not deterministic filtering; packet M9).
- **N6 (LOW) — Silent error hiding in DNS checks** (redundant `Exception` in tuple + no log). **FIXED**: specific "record absent" caught silently (expected), unexpected errors logged at WARN.

## Full report source

Auditor's full evidence-quoted findings captured in the orchestrator transcript (security-reviewer, Round 3, 2026-07-05).
