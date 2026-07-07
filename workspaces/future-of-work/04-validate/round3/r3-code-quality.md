# Round 3 — Code-Quality Review (INDEPENDENT re-derivation)

Reviewer scope: `git diff main...HEAD -- src/` plus the four modification surfaces
(digest decomposition, EncryptedString wrapping, auto-send threshold unification).
Governance honored: zero-tolerance R1/2/3, evidence-first-claims (every defect quotes the line).

## Counts
- CRITICAL: 3
- HIGH: 1 (the auto-send threshold divergence — safety-critical gate)
- MED: 3
- LOW: 3

## Mechanical Sweeps (run before judgment)
- Silent fallbacks `except…pass | except Exception: return None`: **0 hits** in `src/sequor/`.
- Stubs `TODO|FIXME|HACK|STUB|NotImplementedError|placeholder`: **0 code hits** — all matches are HTML `placeholder=` input attributes + one `<!-- Billing history placeholder -->` comment in `onboarding/templates/subscription.html:91` (template markup, not logic).
- SQL string-building: **0 real hits** — every match is `.isoformat()` / template `.format()`; no query interpolation.
- AST parse of all `src/sequor/**.py`: **all files parse OK** — no NameError-class / syntax defects.
- Raw-SQL paths (`learning.py`, `vector_store.py`, `ingestion.py`) use `text()` but are **parameterized** (`:tenant_id`, `:emb`); the only f-string interpolation is `learning.py:188` `{account_filter}`, a fixed constant string (`"AND account_id = :account_id"` | `""`) — not user input. No SQLi.

---

## CRITICAL

### C1 — Encryption write paths establish no tenant-key context → fail-closed RuntimeError in production once Message/Response are wrapped
`encrypted_column.py:141` and `:165` fail closed when `settings.app_env != "development"`:
```
if settings.app_env != "development":
    raise RuntimeError("EncryptedString requires a tenant key. Call set_tenant_key() ...")
```
The production writers of the columns slated for encryption **never call `set_tenant_key`** (grep count = 0 in each):
- `email/auto_reply.py::_record_response` — writes `Response.content` via `SessionCrud` (ORM → TypeDecorator fires).
- `whatsapp/auto_reply.py::_record_response` — same.
- `email/inbound.py:113` `message = await self._db.create("Message", message_data)` — writes `Message.body_text/body_raw/subject` via `SessionCrud` (`crud.py:60-63` `model(**safe); session.add`).
Once these columns become `EncryptedString`, every inbound-message create and every response-record **raises RuntimeError in prod** (or silently stores plaintext in dev — no encryption achieved). The auto-reply pipeline breaks end-to-end. Fix: bind the tenant key at the start of each request/handler scope (the pattern `onboarding/app.py:608-609` / `608`, `711-712` already models) before any ORM write/read of an encrypted column.

### C2 — LearnedAnswer raw-SQL layer bypasses the TypeDecorator → plaintext-in-encrypted-column, then ORM read crashes on decrypt
`ai/learning.py` reads/writes `learned_answers` with raw `text()` SQL, which **does not invoke the SQLAlchemy `EncryptedString` TypeDecorator**:
```
learning.py:142  INSERT INTO learned_answers (... question_text, answer_text ...) VALUES (:question_text, :answer_text ...)
learning.py:189  SELECT id, question_text, answer_text ... FROM learned_answers
```
If `LearnedAnswer.question_text/answer_text` are wrapped in `EncryptedString`, `learning.py` stores **plaintext** (decorator skipped). But `digest/service.py:146-159` reads the same rows via `SessionCrud.list("LearnedAnswer", …)` → ORM → decorator fires → `b64decode(value)` + `AESGCM.decrypt(...)` on plaintext → `binascii.Error` / `InvalidTag` at `encrypted_column.py:175-179`. Encrypting these columns is **incoherent with their raw-SQL data layer**. Fix: either route LearnedAnswer through the ORM (so encrypt/decrypt is symmetric) or explicitly encrypt/decrypt at the raw-SQL boundary — do not half-encrypt.

### C3 — DigestService sets no tenant key yet already reads EncryptedString columns; decomposition inherits and widens the break
`digest/service.py::send_digest` reads `Account` (`:44`) and `_gather_stats` lists `Response`/`LearnedAnswer` (`:141`, `:146`) through `db_express` = `SessionCrud`. `crud.py::_orm_to_dict` (`:91-95`) iterates **every column**, so `Account.owner_email` / `email_address` (already `EncryptedString`, `models.py:250,256`) are decrypted on every read. `DigestService` has **no `set_tenant_key` call** anywhere → in production this path already hits the C1 fail-closed RuntimeError, and encrypting `Response.content` + `LearnedAnswer` widens the blast radius. The planned `gather_digest_data(db, tenant_id, account_id, hours)` MUST set the per-account tenant key before the first ORM read, per-tenant, inside the `send_all_tenants → send_all_accounts` loop (`:109-125`).

---

## HIGH

### H1 — Auto-send confidence gate is fragmented across 5 hardcoded decision points; the one configurable gate is dead code; `Account.confidence_threshold` is never read
This is the SAFETY-CRITICAL gate (machine reply sends without a human). Complete decision-point map:

| # | file:line | Gate | Threshold | Notes |
|---|-----------|------|-----------|-------|
| 1 | `classifier.py:290-308` `should_auto_respond` | category∈{routine,semi} ∧ urgency∈{low,med} ∧ conf ≥ `confidence_threshold` | **0.90** (param default) | **DEAD CODE — never called** (grep: only the def). The ONLY gate that accepts a per-account threshold. |
| 2 | `response.py:118` | `conf ≥ 0.9 ∧ is_routine ∧ has_good_synthesis ∧ ¬is_complex` | **0.9** hardcoded | primary RAG path; ignores `Account.confidence_threshold`. |
| 3 | `response.py:214` `_generate_from_learned` | `conf ≥ 0.85 ∧ category∈{routine,semi}` | **0.85** hardcoded | LOWER bar AND **drops the urgency guard** present in #1/#2 — weakest gate; `conf` here is learned-answer similarity. |
| 4 | `response.py:268` `_generate_from_rag` | `conf ≥ 0.9 ∧ badge∈{high,moderate}` | **0.9** hardcoded | fallback RAG path. |
| 5 | `email/auto_reply.py:168` | `response_result.was_auto_sent ∧ conf ≥ threshold` | **0.90** (`CONFIDENCE_THRESHOLD_AUTO_REPLY`, `:72`) | production sender; re-gates #2/#3/#4. |
| 6 | `whatsapp/auto_reply.py:166` | `conf ≥ threshold` | **0.90** (`:74`) | production sender — **does NOT check `response_result.was_auto_sent`** (asymmetric vs email #5). |
| — | `models.py:261` `Account.confidence_threshold` default **0.90**; `config.py:51` `default_confidence_threshold` 0.90; `onboarding/service.py:186` seeds 0.90 | per-account config | **0.90** | **Never consulted by any auto-send path.** Per-account tuning is silently inert. |

Supporting (non-send) gates for context: `classifier.py:286` `should_use_rag` conf > 0.6; `response.py:122` ai-draft conf ≥ 0.6; badge ladders `rag_pipeline.py:281-288` and `response.py:228-235` (0.9/0.6/0.4 and 0.8/0.6/0.4 — display only); `email/auto_reply.py:215` + `whatsapp/auto_reply.py:229` learning-use conf ≥ 0.6.

Safety impact of divergence: (a) the learned-answer path auto-sends at **0.85 with no urgency check**, so an urgent message can auto-reply where every other path would escalate; (b) WhatsApp bypasses the computed `was_auto_sent` gate, so its send decision diverges from email for identical inputs; (c) `Account.confidence_threshold` is a UI-exposed control that does nothing. Unification MUST: route all send paths through a single predicate (revive `should_auto_respond`), feed it `Account.confidence_threshold` (fallback `config.default_confidence_threshold`), restore the urgency guard on the learned path, and make WhatsApp honor `was_auto_sent`.

---

## MED

### M1 — Digest decomposition `format_digest_email(data)->(subject, body)` collapses the (html, text) pair
Current behavior: `service.py:64` `html, text = build_digest_email(data)` (`templates.py:224` returns `tuple[str, str]` = body_html, body_text) and `send_email(..., body_html=html, body_text=text)` (`:72-77`). A `(subject, body)` 2-tuple loses the html/text alternative. Preserve as `(subject, body_html, body_text)` or the plaintext MIME part is dropped.

### M2 — `gather_digest_data` must fold in the account/tenant reads + None-guards to preserve behavior
`_gather_stats` currently receives `account_name, org_name, cutoff, now` pre-computed in `send_digest` (`:44-62`). Moving to `gather_digest_data(db, tenant_id, account_id, hours)` must reproduce: account-None → return None (`:44-47`); tenant-None → org_name fallback to `account["name"]` else `"your team"` (`:49-50`); `cutoff = now - timedelta(hours=hours)`, `now = utcnow` (`:52-53`). Omitting any changes digest output.

### M3 — `EncryptedString` field-key is `field_name`-scoped; read/write MUST use identical `field_name` per column
`derive_field_key` binds the HKDF `info` to `field_name` (`:60-66`); decrypt (`:172-173`) re-derives with the column's `field_name`. Correct for a single column def, but the new wrappings MUST pass a stable, unique `field_name` per column (e.g. `EncryptedString(field_name="body_text")`) — a mismatch between the write-side and any re-read that assumes `"default"` yields `InvalidTag`. Footgun to pin at implementation.

---

## LOW

### L1 — `rag_pipeline.py:361` `except (json.JSONDecodeError, Exception)` — `Exception` supersets `JSONDecodeError` (redundant tuple). Not a silent swallow: it logs WARN and returns fail-closed `{"passed": False}` (`:362-363`). Tidy to `except Exception`.

### L2 — `classifier.py:118` calls `self._llm.generate` where `_llm` defaults to `None` (`:77,84`). If unset → `AttributeError`, caught at `:140` → returns fail-safe `SEMI_ROUTINE/0.0` (escalates). Fail-safe direction is correct; worth a typed guard for a clearer error.

### L3 — `encrypted_column.py:123` comment "safe to cache because encryption is deterministic per key" is misleading — the random 12-byte nonce (`:151`) makes ciphertext non-deterministic. `cache_ok` concerns SQLAlchemy type-caching (independent of value determinism), so behavior is fine; the comment is inaccurate.

---

## Encryption round-trip verdict
`EncryptedString` itself round-trips correctly IN ISOLATION: write = `b64encode(nonce(12) || AESGCM.encrypt(nonce, plaintext, None))` (`:151-154`); read = `b64decode → nonce=raw[:12], ct=raw[12:] → AESGCM.decrypt` (`:175-180`) — symmetric under a stable `(tenant_key, field_name)`. The R2 fix (source `app_env` from `settings`, single config source, not a second `os.environ` read) is correct and closes the divergent-default risk. The break is NOT in the primitive — it is that the app's actual read/write paths (C1 no key context, C2 raw-SQL bypass, C3 keyless digest) do not satisfy the primitive's contract.
