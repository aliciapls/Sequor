# /redteam Round 2 — Decision Packet

Date: 2026-07-05 · Branch `fix/redteam-r1-security-correctness` · Posture L5_DELEGATED.
Inputs: `r2-security.md`, `r2-correctness.md`, `r2-spec-parity.md` (all three independently re-derived, evidence-quoted).

This packet is the human-decision surface. Everything above the line was closed autonomously this session (defects — zero-tolerance obligations, no product call). Everything below needs your ratify/override because it is a product-truth, compliance, or prod-deploy decision.

## Autonomously closed this session (defect closure — no decision needed)

| Fix                                                | Was                                                                                                         | Now                                                                                   | Evidence                                                              |
| -------------------------------------------------- | ----------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | --------------------------------------------------------------------- |
| `select` NameError (HIGH)                          | every `POST /api/v1/portal/keyphrase/mappings` → hard 500                                                   | local `select` import added                                                           | AST free-name sweep: 0 hits                                           |
| `settings` NameError (MED, silent)                 | admin backfill → NameError swallowed → 200 with 0 rows                                                      | local `settings` import added                                                         | AST sweep: 0 hits                                                     |
| M1 encryption fail-OPEN default                    | `app_env="development"` default → prod without APP_ENV writes plaintext PII                                 | default flipped to `"production"` (fail-closed); dev sets APP_ENV=development in .env | `config.py` + regression test                                         |
| M4 admin cross-tenant op                           | any authenticated operator could iterate all tenants + raw exception echoed                                 | gated on `role=="admin"`; raw `{e}` no longer returned                                | 2 new regression tests (401/403)                                      |
| M6 upload memory DoS                               | onboarding upload `file.read()` unbounded                                                                   | bounded read at 25MB + 413                                                            | mirrors portal cap                                                    |
| L2 login timing oracle                             | bcrypt skipped on absent-email → enumeration                                                                | dummy-bcrypt on no-contact/no-hash paths                                              | —                                                                     |
| L1 dead/broken `_portal_guard`                     | unreachable, `sessionStorage` undefined-name                                                                | deleted                                                                               | Pyright: symbol gone                                                  |
| F-C4-05 `test_config` isolation                    | asserted env values, not defaults                                                                           | clears APP_ENV/DEBUG → tests true defaults                                            | pre-existing failure closed                                           |
| F-C4-05 signup validation tier-violation (7 tests) | `handle_signup` ran `init_db()` (DB connect) BEFORE Pydantic validation → invalid input 500s instead of 422 | validation moved ahead of all DB access                                               | 7 pre-existing failures closed; 7/7 now return 422 without a database |

All 6 Round-1 ①-defects independently re-confirmed CLOSED. 0 CRITICAL, 0 NEW HIGH.

---

## GROUP A — Product-truth decisions (these block literal 0-HIGH convergence)

The residual HIGHs are **not defects** — they are places where the SHIPPED spec claims a feature the code has honestly not wired yet (spec-ahead-of-code). Closing them means either BUILDING the feature or AMENDING the spec claim. That is a product call, not an agent call.

**The strategic frame first (this shapes everything below):** driving comms-wedge to 0-HIGH means building ~11 specced-but-unwired feature-moats. Your own repivot brief flags F5 (validate director-as-buyer) as "top priority; gates scale" before scaling the build. So the convergence question is entangled with the pivot question. My recommendation is **not** "build all 11 now for a green banner" — it is: settle the 3 product-truth items below now (cheap, makes the spec honest), then sequence the feature-moat builds behind the F5 validation decision via a value-ranked `/todos` wave, rather than cram them.

### A1 — Message-body encryption

- **Spec claims:** `data-model.md` — _"All PII fields encrypted at rest (AES-256, tenant-specific keys)"_; message content classified _"PII — high sensitivity"_.
- **Code reality:** `models.py` — `Message.body_text/body_raw/subject`, `Response.content`, `DocumentChunk.chunk_text`, `LearnedAnswer` text are plaintext `Text`; only identifiers (email/phone) use `EncryptedString`.
- **Recommendation: BUILD** (wrap content columns in `EncryptedString` — the primitive already exists and is proven on identifiers).
- **Why:** an unqualified PDPA claim that the code contradicts is both a compliance exposure and a zero-tolerance "fake-encryption" class; a DB-read/backup leak exposes all customer comms in clear.
- **Honest con:** encrypted `Text` columns can't be `LIKE`/full-text searched in SQL (RAG already uses a separate vector path, so impact is limited); existing rows need a backfill migration; small per-row crypto cost.
- **Alternative (OVERRIDE):** AMEND the spec to "identifiers encrypted; message bodies plaintext" **with explicit PDPA sign-off** that this is acceptable.
- **→ RATIFY (build) / OVERRIDE (amend + sign-off): ________**

### A2 — Schema-per-tenant isolation

- **Spec claims:** `data-model.md` — _"separate schema per tenant, not just tenant_id column … shared schema with tenant_id is NOT sufficient for Singapore PDPA compliance."_
- **Code reality:** per-tenant schemas are _created_ at signup then never used; every live path uses `AsyncSession(engine)` + `WHERE tenant_id ==` on `public` tables. `get_tenant_session` (the `SET search_path` helper) has zero callers. Isolation currently hinges on the (now fail-closed) JWT.
- **Recommendation: RECONCILE — get a PDPA determination first, then decide.** This is the one item I will not pick for you: the spec asserts column-isolation is _legally_ insufficient, so the choice is a compliance fact, not an engineering preference.
  - If counsel says column-isolation + strong tenant-scoping is acceptable → **AMEND** the spec (cheap).
  - If the schema-per-tenant mandate stands → **BUILD** (route every query through `get_tenant_session`).
- **Honest con of BUILD:** touches every query path — a large, invariant-heavy refactor best done as its own value-ranked wave. **Con of AMEND:** you are overriding a written PDPA compliance statement — do it only with counsel on record.
- **→ RATIFY (build) / OVERRIDE (amend w/ PDPA sign-off) / DEFER pending counsel: ________**

### A3 — F11 auto-send threshold contradiction (spec-internal)

- **Spec contradicts itself:** `response-accuracy.md` says both _">90% → auto-send"_ (Options C) and _">95% High / 80–95% Moderate → auto-send with badge"_ (Badge table). Code cannot satisfy both; the two code paths (`0.9` vs `0.8` "high") match neither.
- **Recommendation: pick the Badge table (>95% high, 80–95% moderate).** More conservative on the auto-send gate — fewer machine replies going out without a human, which is the safer default for a compliance-sensitive comms product.
- **Honest con:** more messages route to a human (higher human load, slower responses) than the >90% rule would.
- **→ RATIFY (>95% table) / OVERRIDE (>90% rule) / OTHER: ________**

### A4 — The feature-moat builds (determinate BUILD, but large — sequence, don't cram)

All specced as HARD success-criteria, all currently unwired. These ARE the product ("F1 build the product"). Recommend planning them as value-ranked `/todos` waves **behind the F5 validation gate**, not cramming for a convergence banner:

- RoutingOutcome instrumentation · HUMAN-override persistence (WhatsApp compliance — _non-negotiable_) · multi-channel dedup/thread-key · unified Escalation fields + contradiction wiring · digest scheduling wiring
- Confidence-badge rendering (WhatsApp footer / email header) · staleness warning · answerability<0.3 exclusion (hallucination control) · badge-threshold fix (after A3)
- WhatsApp test suite (7 modules, 0 tests) · `ai.ingestion` + `onboarding.api` importing tests · digest API decomposition (`gather_digest_data`/`format_digest_email` — unblocks integration collection)
- **→ Sequence behind F5 validation (recommended) / build now as a convergence wave / other: ________**

---

## GROUP B — PR #7 merge (production deploy)

PR #7 (this branch) carries the Round-1 CRITICAL auth-bypass fix + 6 HIGH fixes + this session's defect closures. Vercel preview is green. **Merging to main triggers a Vercel production deploy.**

- **Recommendation:** before merge, confirm these are set in the Vercel production environment: `JWT_SECRET` (≥32 bytes — else the app now _refuses to start_, which is the intended fail-closed), `ENCRYPTION_MASTER_KEY`, and `APP_ENV=production`. Then merge with admin.
- **Why the confirm gate:** the M1 fail-closed change means an unset `APP_ENV` now defaults to production (correct) — but a _missing_ `JWT_SECRET`/`ENCRYPTION_MASTER_KEY` in prod will now fail-closed loudly rather than silently using insecure fallbacks. That is the desired behavior, but it means the env must be complete before the deploy or the app won't boot.
- **→ CONFIRM env is set + merge / hold: ________**

---

## GROUP C — Deferred defects (why, and disposition)

Real but **not** database-independent or in-scope this session:

- **Digest API decomposition** — determinate BUILD (extract `gather_digest_data`/`format_digest_email` from `DigestService`) but needs real Postgres to verify the 5 Tier-2/3 tests; blocks integration `--collect-only`. → build in an infra-enabled session.
- **`key_phrase_mappings` missing migration** (NEW, MED) — masked by `create_all` in dev; prod Alembic-only would 500 even after the `select` fix. Needs a real-PG migration test (`schema-migration.md` Rule 5). → migration + PG test.
- **M5 unauthenticated DNS `/verify`** — server-side DNS lookup oracle; but these may be _pre-auth onboarding_ steps, so adding auth needs a flow decision (does the onboarding UI call them before login?). `/records` is a pure function (no network) — only `/verify` is the real risk.
- **M7 rate-limiter** (fail-open + serverless-ineffective) — needs a shared store (Redis) provisioning decision.
- **M8 SendGrid webhook** (disabled-by-default + lossy decode + no replay) — needs the real SendGrid signature/timestamp format to verify.
- **M9 prompt-injection** on the auto-send path — design work (instruction/data separation).
- **`test_contains_form` (last F-C4-05 unit failure) — surfaces a possible frontend↔API contract gap, NOT just a stale test.** Evidence: `/` serves `signup.html` (marketing landing, "Get started" → `/portal/signup`); `/portal/signup` renders `register.html` whose form (`id="signup-form"`) uses fields **`first_name`, `last_name`, `company`, `email`** (via `id=`); but the signup **API** `POST /api/v1/onboarding` expects **`org_name`, `owner_email`, `owner_password`** (per `OnboardingRequest`). The test asserted the OLD inline `/` form with `name="org_name"`/`name="owner_email"`. NOT silently rewritten — doing so would mask the field-name mismatch. **Two questions for you:** (a) confirm the marketing-`/` + `/portal/signup`-form design is intended (repivot); (b) does `register.html`'s form actually submit correctly to the API contract (needs the form's JS + a real submit walk to verify — I could not confirm the company→org_name / email→owner_email mapping exists). → decide, then the test is updated to match the real signup surface.
- **7 signup-validation tier failures — FIXED this session** (validation moved before DB access); the remaining DB-dependent tests are integration-tier and need live Postgres.
- **Pyright latent None-access** at `app.py:619` (`account_id` on None) and `app.py:1253` (None subscript) — newly surfaced, same crash-class as the NameErrors; worth a follow-up sweep.

## Convergence status

- **0 CRITICAL, 0 NEW HIGH.** All 6 ①-defects + this session's 8 defect closures confirmed.
- **NOT at 0-HIGH** — the residual HIGHs are the Group-A product feature-moats. Literal convergence requires the Group-A decisions + the feature builds. That is a product/strategy gate (F5), not an autonomous one.
