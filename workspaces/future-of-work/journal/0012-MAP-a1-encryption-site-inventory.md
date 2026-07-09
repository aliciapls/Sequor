# 0012 — MAP: A1 encryption site inventory (shard 1b)

Date 2026-07-05 · Branch `feat/data-layer-security` · Session: build-wave session 2.

## Context

`/autonomize` on the ratified build wave. Wave 0 activated the (previously dark) Tier-2
loop; shard 1a landed the tenant-context boundary. Shard 1b (A1 PII-at-rest encryption) turns
out to be **~30 read/write sites across 7 files** — far larger than one shard's careful
budget, and DEVIATIONS warns a _partial_ wrap ships a fail-closed regression worse than today.
So 1b is deferred to a fresh focused session; this entry preserves the exhaustive map (two
independent mapping-agent passes agreed) so nothing is re-derived.

## Key mechanics (bear on every site)

- `EncryptedString` (`db/encrypted_column.py`) short-circuits on `None`: only **non-NULL**
  writes/reads of a target column need the key. Non-NULL touch with no key + `app_env !=
"development"` → `RuntimeError` (fail-closed). Dev stores plaintext (fail-open).
- Key installed only by `set_tenant_context(session, tenant_id)` / `bind_tenant(...)`
  (`db/tenant_context.py`). `bind_tenant` is the guarded one-liner (no-op if no master key).
- **Reference-correct pattern already in tree:** `compliance.py:111-114` — `if
settings.encryption_master_key: await set_tenant_context(session, tenant_id)` before ORM
  writes. Every site below needs this shape.
- **Architectural insight:** most sites use a **passed-in session** (SessionCrud / db_express)
  → set context ONCE at the request boundary (webhook handler / portal endpoint), not per
  operation. Only the own-session openers (auto_reply, learning, portal endpoints) need
  per-method wiring. Mind the GUC is transaction-local (SET LOCAL) — re-set after any commit.

## Columns to wrap (models.py)

`Message.subject/body_text/body_raw`, `Response.content`, `LearnedAnswer.question_text`
(field_name `learned_question`), `LearnedAnswer.answer_text` (`learned_answer`),
`Classification.reasoning` (**ORPHANED — never written/read by any code; inert but harmless**),
`Escalation.resolution_summary`, `Contact.name`.

## WRITE sites (need key before non-NULL write)

| site                                      | function                      | column                                                        | tenant_id               | session                      | done?            |
| ----------------------------------------- | ----------------------------- | ------------------------------------------------------------- | ----------------------- | ---------------------------- | ---------------- |
| email/inbound.py:120                      | process_sendgrid_payload      | Message.subject/body_text/body_raw                            | account["tenant_id"]    | self._db (opened app.py:356) | no               |
| email/inbound.py:206                      | _try_resolve_escalation       | Escalation.resolution_summary                                 | tenant_id param         | self._db                     | no               |
| email/inbound.py:337                      | _resolve_or_create_contact    | Contact.name                                                  | tenant_id param         | self._db                     | no               |
| whatsapp/inbound.py:113                   | _process_single               | Message.body_text                                             | account["tenant_id"]    | self._db (app.py:509)        | no               |
| whatsapp/inbound.py:181                   | _resolve_or_create_contact    | Contact.name                                                  | tenant_id param         | self._db                     | no               |
| email/auto_reply.py:236                   | _record_response              | Response.content                                              | context.tenant_id       | own AsyncSession             | **DONE d3a4abd** |
| whatsapp/auto_reply.py:249                | _record_response              | Response.content                                              | context.tenant_id       | own AsyncSession             | **DONE d3a4abd** |
| email/auto_reply.py _create_escalation    | (reads inside svc)            | Msg/Contact reads                                             | context.tenant_id       | own AsyncSession             | **DONE d3a4abd** |
| whatsapp/auto_reply.py _create_escalation | (reads inside svc)            | Msg/Contact reads                                             | context.tenant_id       | own AsyncSession             | **DONE d3a4abd** |
| escalation/service.py:342                 | resolve_escalation            | Escalation.resolution_summary                                 | existing["tenant_id"]   | self._db                     | no               |
| escalation/service.py:488                 | process_breached_escalation   | Escalation.resolution_summary                                 | escalation["tenant_id"] | self._db                     | no               |
| onboarding/app.py:1036                    | portal_api_escalation_resolve | Escalation.resolution_summary                                 | operator["tenant_id"]   | own AsyncSession             | no               |
| ai/learning.py:141                        | _store_learned_answer         | question_text/answer_text — **RAW SQL, must encrypt_field()** | tenant_id param         | own AsyncSession             | no               |
| escalation/service.py:125,263             | create/escalate               | resolution_summary NULL → SAFE without key                    | —                       | —                            | n/a              |

## READ sites (decrypt; need key before non-NULL read)

email/inbound.py:255 (_capture_learning, Message.body_text), :286/299 (_forward_reply,
Message.subject), :360/372 (**\_find_parent_message — NO tenant_id in signature; plumb from
account["tenant_id"] or set at request boundary**); whatsapp/inbound.py:204
(_check_session_expired, Message.body_text); escalation/service.py:107/111/273/274
(create/escalate reads Message._/Contact.name), :585 (check_contradiction, Response.content;
tenant only via escalation["tenant_id"] after l.581); digest/service.py:144/149/154/161
(\_gather_stats — Escalation.resolution_summary/Response.content/**LearnedAnswer.* raw-plaintext
mismatch*_), :264/290/301/311 (gather_digest_data — same, ORM); ai/learning.py:189
(search_learned_answers — **RAW SQL, must decrypt_field()**); onboarding/app.py:930
(portal_api_messages), :976 (portal_api_escalations), :1059 (portal_api_escalation_detail),
:1119 (portal_api_contacts) — all own AsyncSession with operator["tenant_id"] in scope.
`app.py portal_api_dashboard` = count-only, SAFE. compliance.py reads = already guarded ✓.

## The learning.py divergence (crux — risky site #1)

`_store_learned_answer` (RAW INSERT, plaintext) + `search_learned_answers` (RAW SELECT,
plaintext) are self-consistent BUT bypass encryption. Once columns are wrapped, the ORM digest
reads (`select(LearnedAnswer)`) call `decrypt_field()` on that plaintext → base64/GCM failure.
Fix: `_store_learned_answer` calls `encrypt_field(key, "learned_question"/"learned_answer", ...)`
before INSERT; `search_learned_answers` calls `decrypt_field(...)` after SELECT — field_names
MUST match the ORM column declarations. `encrypt_field`/`decrypt_field` already extracted
(`96c1a45`) for exactly this. Load the tenant key in learning.py (it owns its session + has
tenant_id).

## Done this session / next

Done: crypto extraction (`96c1a45`), bind_tenant + 4 own-session auto_reply sites (`d3a4abd`).
Next (1b, one focused session): wire remaining ~24 sites (prefer per-request-boundary for the
self._db/passed-in ones), plumb tenant into _find_parent_message, wrap the 8 columns, reconcile
learning.py raw SQL, fix erasure (test_compliance_erasure non-deterministic under master key),
add a Tier-2 round-trip test that runs with APP_ENV=production so fail-closed catches any missed
site. Then 1c (RLS), 1d (F2 purge), 1e (R7-01), Waves 2-3, holistic redteam.
