# 0010 — GAP: R3/R4 redteam convergence + the encryption-is-multi-hop learning

Type: GAP
Date: 2026-07-05
Phase: 04-validate (Round 3 + Round 4)

## What happened

Round 3 ran 4 parallel reviewers (spec-parity, security, test-coverage, code-quality) over the 7 shipped comms-wedge specs; Round 4 ran 3 adversarial verifiers over the fixes. The defect surface converged: 9 database-independent defects fixed + probe-guarded, all 3 R4 verifiers returning VERIFIED / all-CLOSED / all-DELIVERED with no un-logged HIGH.

## The load-bearing learning (why this is a GAP, not just a RISK)

**"Encrypt the PII columns" (decision-packet A1) is NOT a column-wrap — it is a multi-hop, multi-invariant build, and a naive fix ships a CRITICAL regression.** The R3 code-quality reviewer caught three coupled facts the R2 packet's "BUILD (the primitive already exists)" framing missed:

- **C1** — every ORM write path (`email/auto_reply._record_response`, `whatsapp/auto_reply._record_response`, `email/inbound`) creates rows with NO `set_tenant_key` call. `EncryptedString` fails CLOSED, so wrapping the columns would raise `RuntimeError` on every write → the whole auto-reply pipeline breaks. Encryption requires wiring `set_tenant_key` at every write path FIRST.
- **C2** — `ai/learning.py` reads/writes `learned_answers` via RAW `text()` SQL that bypasses the TypeDecorator → it would store plaintext that the ORM digest read then cannot decrypt (`InvalidTag`). Encrypting `LearnedAnswer` is incoherent with its raw-SQL layer until that layer is reconciled.
- **C3** — the digest read path must set the per-account key inside the tenant loop (and, separately, `gather_digest_data` must avoid loading the encrypted `Account` columns — fixed this session by selecting only `name`/`escalation_sla_hours`).

**Disposition:** A1 is scoped as its own value-ranked wave (set_tenant_key plumbing → column wrap → raw-SQL reconciliation → Tier-2 round-trip on real Postgres), logged in `specs/DEVIATIONS.md`. Building it partially was correctly REFUSED — a partial build regresses worse than the current plaintext state. This is the `autonomous-execution.md` MUST-4 boundedness clause in action: the gap exceeds one shard, so it's a new shard, not a same-session continuation.

## Secondary learnings

- **Same-class sibling discipline paid off twice.** R3 security found N1 (the R2-M6 upload-bound fix left un-hardened on the sibling portal handler); R4 security found the same class again on the 3 webhook `request.body()` handlers. Both fixed in-shard per MUST-4 rather than deferred.
- **The reviewers earned their cost.** R4 caught 3 LOW issues _in the R3 fix code_ (DNS `$`-vs-`\Z` newline, FIFO-mislabeled-LRU comment, hallucination `total_claims==0` fail-open) that the author (me) introduced — the adversarial-verify round is not ceremony.
- **Commit-accuracy caught over-claim.** Closure-parity flagged that `3c68654`'s "each with a regression probe" was over-claimed (4 defects had code but no probe); fixed by a follow-up delivering the probes, per `git.md`.

## Convergence gap that remains (honest)

Literal 0-HIGH is NOT reached: the spec-ahead CRITICAL (A1) + HIGH (A2 schema/PDPA, NEW-1 badge, A3 threshold) are logged deviations awaiting the user's product/compliance/F5 decisions. The defect surface converged; the product surface is the user's gate.
