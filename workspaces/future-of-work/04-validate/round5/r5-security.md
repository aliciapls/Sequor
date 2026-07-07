# /redteam Round 5 — Security Re-Audit (independent re-derivation)

Date 2026-07-05 · Branch `fix/redteam-r1-security-correctness` · Posture L5_DELEGATED.
Scope: `src/sequor/**` diff (`main...HEAD`) + the 7 comms-wedge specs' § Security Threats.
Every claim re-derived from current HEAD; R1–R4 self-reports NOT trusted. Platform specs out of scope.

**Counts:** CRITICAL 0 (defect) · HIGH 0 (defect) · MEDIUM 1 · LOW 2 · plus 1 CRITICAL **LOGGED** (A1 plaintext PII, accurately tracked, BUILD-PENDING).

## Prior-fix verification — ALL HOLD

- **R1 CRITICAL auth bypass — PASS.** `auth.py::decode_token` pins `algorithms=[ALGORITHM]` (`HS256`); `alg=none` forgery rejected. `_signing_secret()` fails closed outside dev (RuntimeError on unset). All `/api/v1/portal/*` funnel through `_require_auth()` → `_get_session_operator()` → `decode_token()`. Probes `TestR1AuthBypass::test_alg_none_forgery_rejected` + `test_tampered_signature_rejected` green.
- **R2 fail-closed encryption default — PASS.** `config.py app_env="production"`; `encrypted_column.py` bind/result both raise `RuntimeError` when `_current_tenant_key.get() is None` and `app_env != "development"`.
- **R2 admin/upload/timing — PASS.** Admin backfill 403 on non-admin; errors carry IDs not raw exceptions. Login timing equalized via `verify_password(password, _DUMMY_PASSWORD_HASH)` on absent-contact/null-hash. Onboarding upload bounded (`read(_MAX_UPLOAD_BYTES+1)` → 413).
- **R3/R4 — ALL HOLD.** 2nd-door portal upload bounded + `_oversized_body()` Content-Length guard on Stripe/email/WhatsApp; rate limiter evicts-oldest and keeps enforcing (`TestR3N3RateLimiterFailClosed`); DNS `_DNS_DOMAIN_RE` uses `\Z`, `_dns_limiter` 30/hr, `resolve(lifetime=5.0)`, gated order; unsigned inbound email rejected in prod (missing+invalid signature); DNS errors logged with `exc_info=True`.

## Injection / Secrets / Encryption / Signatures — CLEAN

- Every raw `text()` site parameterized (`ai/learning.py` C2 verified — `{account_filter}` is a fixed literal `"AND account_id = :account_id"`, vector passed as bound `:emb`; `vector_store.py`, `onboarding/app.py`, `db/crud.py` all bound). DDL identifiers pass `validate_identifier()`. No `eval`/`exec`/`shell=True`.
- No hardcoded secrets; AES-256-GCM + per-tenant HKDF, fail-closed; master key length-checked. WhatsApp HMAC `compare_digest`; SendGrid ECDSA + Stripe `construct_event` on raw body; all fail closed on missing/invalid.

## NEW findings

### R5-01 (MEDIUM, NEW/under-logged) — Unauthenticated document ingestion into an attacker-named tenant

`onboarding/app.py::upload_document` (`POST /api/v1/onboarding/upload`) takes `tenant_id`/`account_id` as attacker-supplied form fields, validates only UUID-parse, ingests directly into that tenant's RAG store — no auth, no ownership proof. Ingested chunks feed the auto-reply pipeline → RAG-poisoning vector. Mitigations: `tenant_id` is an unguessable 122-bit UUID; row FK requires the tenant to pre-exist; endpoint rate-limited (20/hr). The auth-gating half is NOT explicitly logged (unlike N2's DNS flow-decision). Disposition: gate behind a short-lived onboarding token OR add a DEVIATIONS row mirroring N2's flow-decision framing.

### R5-02 (LOW, NEW) — WhatsApp verify-token compared non-constant-time

`whatsapp_webhook_verify`: `if token != expected_token` — plain `!=` on a secret (weak timing oracle). Only Meta's one-time subscription GET challenge, not per-request auth. Fix: `hmac.compare_digest`.

### R5-03 (LOW, NEW/claim-mismatch) — "JWT_SECRET ≥32 bytes enforced" is warn-only

`auth.py::_signing_secret`: a set-but-short secret logs `auth.jwt_secret_too_short` and RETURNS the short secret. Empty-secret is enforced (RuntimeError); the <32-byte case is not. R3 merge-gate states "JWT_SECRET (≥32 bytes)" as if enforced. Fix: enforce ≥32 at startup (consistent with the app's fail-closed posture + the stated merge gate) OR amend the claim to "warned, not enforced."

## Logged-deviation verification (accurate, not hidden bugs)

- **A1 (CRITICAL, LOGGED)** — message bodies plaintext at rest; accurately logged with C1/C2/C3 rationale. **No NEW plaintext-PII path introduced by the diff** (plaintext surfaces are exactly A1/C2's enumerated set; diff adds masked-only logging `_mask_ip/_mask_email/_mask_phone`, no new clear-text store). Correctly CRITICAL-but-BUILD-PENDING behind F5.
- **A2 (LOGGED)** — RLS ratified; per-tenant schema code unused, live isolation app-layer `WHERE tenant_id`. Accurate.
- **N2/N3/N4/N5 (LOGGED)** — half-fixed/half-deferred verified accurate; none masks a hidden bug.

## Bottom line

R1–R4 security fixes all hold. Defect surface **0 CRITICAL / 0 HIGH** un-logged. One CRITICAL (A1) accurately logged + BUILD-PENDING. New: R5-01 (MED, recommend gate-or-log), R5-02/R5-03 (LOW hardening/claim-accuracy).
