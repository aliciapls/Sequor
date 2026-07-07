# /redteam Round 1 — Cluster C2: RAG Pipeline + Response Accuracy (spec-compliance)

Scope: SHIPPED comms-wedge specs `specs/rag-pipeline.md` + `specs/response-accuracy.md` vs
`src/sequor/ai/*.py` + `src/sequor/escalation/*.py`. Platform (target-state) specs are OUT of scope.
Method per `.claude/skills/spec-compliance/SKILL.md` — literal assertion extraction, mechanical verification.

Environment: SQLAlchemy 2.0.51, pydantic-settings BaseSettings (env-driven config). All 13 cluster
modules have ≥1 importing test file (testing.md § "new module needs importing test" — CLEAN).

---

## Assertion table — specs/rag-pipeline.md

| spec assertion                                                                    | verification command                                           | actual output                                                                                                                              | verdict                                                                                                              |
| --------------------------------------------------------------------------------- | -------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Hybrid retrieval: vector 0.7 + BM25 0.3                                           | `grep -nE 'VECTOR_WEIGHT                                       | BM25_WEIGHT' src/sequor/ai/vector_store.py`                                                                                                | `40: VECTOR_WEIGHT = 0.7` `41: BM25_WEIGHT = 0.3`; `148: combined = VECTOR_WEIGHT*vector + BM25_WEIGHT*bm25`         | PASS |
| Embeddings stored in pgvector                                                     | `grep -n 'embedding' src/sequor/ai/vector_store.py`            | INSERT into `document_chunks(... embedding ...)` (l.76-88); learned_answers uses `embedding <=> :emb::vector` (learning.py l.191)          | PASS (storage); but retrieval computes cosine in Python over all tenant chunks (l.145), not pgvector `<=>` — see F10 |
| RAG triggered if classify conf >60% AND cat != high_stakes                        | `grep -nA4 'def should_use_rag' src/sequor/ai/classifier.py`   | l.285-288 `confidence > 0.6 and category != HIGH_STAKES`                                                                                   | PASS (spec makes this deterministic — not an agent-reasoning violation)                                              |
| Answerability score via LLM cross-check                                           | `grep -n '_score_answerability' src/sequor/ai/rag_pipeline.py` | l.149-189, LLM prompt yes/no→float                                                                                                         | PASS                                                                                                                 |
| Final passage score = relevance × answerability                                   | `sed -n '111p' src/sequor/ai/rag_pipeline.py`                  | `final_score = result.combined_score * answerability`                                                                                      | PASS                                                                                                                 |
| **If answerability < 0.3, passage EXCLUDED even if vector sim high**              | `grep -nE '0\.3\|answerability' src/sequor/ai/rag_pipeline.py` | `min_score=0.3` is the COMBINED-score floor in vector_store; NO filter drops passages on `answerability < 0.3` — all appended (l.107-123)  | **FAIL — F2**                                                                                                        |
| Synthesis top-5 passages to LLM (GPT-4o or equiv)                                 | `grep -n 'top_k' src/sequor/ai/response.py`                    | `top_k=5` (l.101,266); LLM via config `settings.llm_model` (Ollama, override via env)                                                      | PASS                                                                                                                 |
| Synthesis system prompt: "Do not add info not in docs… cite… if uncertain say so" | `sed -n '231,236p' src/sequor/ai/rag_pipeline.py`              | base_system contains all three clauses                                                                                                     | PASS                                                                                                                 |
| Synthesis confidence = weighted avg of answerability × LLM confidence             | `sed -n '126,132p;277,279p' src/sequor/ai/rag_pipeline.py`     | `synthesis_confidence = max(answerability)`; `overall = synthesis_conf × (1.0\|0.5 halluc)` — MAX not weighted-avg; no LLM-confidence term | FAIL (partial) — F9                                                                                                  |
| Hallucination post-check: 2nd LLM call, uncited claims                            | `grep -n '_check_hallucination' src/sequor/ai/rag_pipeline.py` | l.307-363, JSON `{passed,uncited_claims}`                                                                                                  | PASS                                                                                                                 |
| If >50% claims uncited → reject                                                   | `sed -n '356,357p' src/sequor/ai/rag_pipeline.py`              | `if uncited > len(passages)*0.5: passed=False`                                                                                             | PASS                                                                                                                 |
| No-relevant-docs → "I don't have information…forwarded for review"                | `sed -n '218,225p' src/sequor/ai/rag_pipeline.py`              | matches spec §"No Relevant Documents Found" (spec-mandated fixed string, NOT a fake RAG answer)                                            | PASS                                                                                                                 |
| Learned answers marked source_type `human_answer`                                 | `grep -n 'human_answer\|SourceType' src/sequor/ai/learning.py` | l.155 `SourceType.human_answer.value`                                                                                                      | PASS                                                                                                                 |
| Only confirmed resolutions learned; min meaningful length                         | `sed -n '85,96p' src/sequor/ai/learning.py`                    | requires `escalation_id`; rejects empty / <10 chars                                                                                        | PASS                                                                                                                 |
| Later human answer contradicting earlier → more recent wins                       | `sed -n '186,201p' src/sequor/ai/learning.py`                  | `ORDER BY embedding <=> :emb::vector` — distance only, NO recency tiebreak                                                                 | FAIL (minor) — F8                                                                                                    |
| Index age tracking: last_indexed_at; stale flagged in retrieval                   | `grep -rni 'stale\|last_indexed_at' src/sequor/ai/`            | ingestion.py sets `last_indexed_at`; retrieval/synthesis NEVER read it or flag staleness                                                   | **FAIL — F4**                                                                                                        |

## Assertion table — specs/response-accuracy.md

| spec assertion                                                                                                                               | verification command                                                                              | actual output                                                                                                                                                                                                                                 | verdict             |
| -------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------- |
| Option C confidence badge on every AI response                                                                                               | `grep -n 'confidence_badge' src/sequor/ai/response.py`                                            | `ResponseResult.confidence_badge` populated on all paths                                                                                                                                                                                      | PASS (field exists) |
| Badge levels: >95 High / 80-95 Moderate / 60-80 Low / <60 Uncertain                                                                          | `sed -n '281,288p' src/sequor/ai/rag_pipeline.py` + `sed -n '228,235p' src/sequor/ai/response.py` | rag: `0.9→high, 0.6→moderate, 0.4→low`; learned: `0.8→high, 0.6→moderate, 0.4→low`. Neither matches spec (95/80/60); the two code paths disagree; text "high" ≠ spec "High confidence"                                                        | **FAIL — F6**       |
| conf >90% auto-send (Option C)                                                                                                               | `sed -n '107,118p' src/sequor/ai/response.py`                                                     | `was_auto_sent = classification.confidence >= 0.9 AND is_routine AND synthesis badge in [high,moderate] AND not complex` — gates on CLASSIFIER conf, not response conf; a 0.6-confidence "moderate" synthesis auto-sends when classifier ≥0.9 | **FAIL — F5**       |
| Badge display: WhatsApp footer "[Auto-generated; X% confidence. Reply STOP…]"; email X-AI-Confidence header; badge NOT editable/configurable | `grep -rnE 'X-AI-Confidence\|% confidence\|Reply STOP\|Auto-generated' src/`                      | `NO BADGE-DISPLAY MATCH in src/` — badge computed but NEVER rendered to any channel                                                                                                                                                           | **FAIL — F3**       |
| High-stakes: never auto-respond, route to human immediately; no RAG                                                                          | `sed -n '86,87p;146,171p' src/sequor/ai/response.py`                                              | `if category==HIGH_STAKES: _handle_high_stakes` returns `was_auto_sent=False, escalation_needed=True`, no RAG call                                                                                                                            | PASS                |
| High-stakes routed via LLM classification (not code keyword match)                                                                           | `grep -n 'high_stakes' src/sequor/ai/classifier.py`                                               | category assigned by LLM classify (l.118-128); no keyword `if` — LLM-first CLEAN                                                                                                                                                              | PASS                |
| Semi-routine: no reply within SLA (default 4h) → auto-escalate to backup                                                                     | `grep -n 'default_escalation_sla_hours' src/sequor/config.py`                                     | `46: default_escalation_sla_hours: int = 4`; scheduler → `find_breached_escalations` → `escalate_to_second_tier`                                                                                                                              | PASS                |
| Escalation email carries contact msg + AI draft + confidence + citations                                                                     | `sed -n '148,176p' src/sequor/escalation/service.py`                                              | `_build_email` + `build_escalation_subject` pass ai_summary, confidence_score, suggested_response                                                                                                                                             | PASS                |
| D/T/R audit row per state transition (immutable)                                                                                             | `grep -n '_write_audit\|def _write_audit' src/sequor/escalation/service.py`                       | audit written on created/resolved; but `_write_audit` resolves session via `getattr(_session_inner)/_session` — if None, logs error + SKIPS row (l.676-679)                                                                                   | FAIL (partial) — F7 |
| Classifier conf < 20% → route to backup, no response                                                                                         | `sed -n '140,153p' src/sequor/ai/classifier.py`                                                   | classify exception → `confidence=0.0` default (routes to backup); explicit <0.20 branch not present but 0.0 satisfies routing                                                                                                                 | PASS (behavioral)   |
| Thresholds below 70% auto-send require explicit user ack                                                                                     | `grep -rn 'acknowledge\|70' src/sequor/ai/ src/sequor/config.py`                                  | no threshold-config surface in cluster; likely config/API layer — UNVERIFIED in scope                                                                                                                                                         | UNCLEAR             |
| Model names / API keys from .env not hardcoded                                                                                               | `sed -n '26,32p' src/sequor/config.py`                                                            | `Settings(BaseSettings)` env-driven; `llm_model`/`embedding_model`/`openai_embedding_model` are documented module-level constants overridable via env — env-models carve-out COMPLIANT                                                        | PASS                |

---

## Findings

**[HIGH] F1 — Hybrid retrieval path raises at runtime (raw SQL string, no `text()`)**
`src/sequor/ai/vector_store.py:123-131` — `search()` calls `session.execute("""SELECT … """, {...})` with a
bare string. `store_chunks` imports `from sqlalchemy import text` locally (l.69) but `search` does NOT wrap
its query. On SQLAlchemy 2.0.51 this raises before any row is read.
Evidence: `.venv/bin/python -c "…AsyncSession…s.execute('SELECT 1', {})"` → `ArgumentError: Textual SQL
expression 'SELECT 1' should be explicitly declared as text('SELECT …')`.
Spec ref: rag-pipeline §Retrieval "Hybrid search: vector similarity + BM25" — the primary retrieval path.
Impact: every document-RAG query errors; only the learned-answer path (learning.py, correctly uses `text()`)
functions. zero-tolerance Rule 1/6: documented behavior the code does not perform.
Fix: `from sqlalchemy import text` at module scope and wrap: `await session.execute(text("""SELECT …"""), {...})`.

**[HIGH] F2 — Answerability < 0.3 exclusion not implemented**
`src/sequor/ai/rag_pipeline.py:107-123` — answerability is computed and multiplied into `final_score`, but no
branch excludes passages whose answerability < 0.3; all retrieved passages are appended and fed to synthesis.
Spec ref: rag-pipeline §Retrieval-Confidence-Scoring l.89 "If answerability < 0.3, the passage is excluded
even if vector similarity is high"; response-accuracy §Hallucination l.122 "If no, do not use passage even if
vector similarity is high." This is a stated hallucination control that never fires.
Fix: `if answerability < 0.3: continue` before appending (or filter passages before synthesize).

**[HIGH] F3 — Confidence badge never rendered to any channel (governance control absent)**
`grep -rnE 'X-AI-Confidence|% confidence|Reply STOP|Auto-generated' src/` → no matches across all of `src/`.
The badge is computed (`ResponseResult.confidence_badge/confidence_score`) but no WhatsApp footer
("[Auto-generated; X% confidence. Reply STOP…]") and no email `X-AI-Confidence` header/footer exist.
Spec ref: response-accuracy §Badge-Display l.54-57 — the badge is "a fixed governance control" that MUST be
attached. Rendering surface may belong to the message-routing cluster, but it is absent product-wide.
Impact: contacts receive AI replies with no confidence signal and no human-handoff prompt.
Fix: render badge as WhatsApp footer + email X-AI-Confidence header at the send boundary; mark non-editable.

**[HIGH] F4 — Staleness warning not implemented**
`grep -rni 'stale|last_indexed_at' src/sequor/ai/` → only `ingestion.py` writes `last_indexed_at`; retrieval
(`vector_store.search`) never selects it and synthesis (`rag_pipeline.synthesize`) never appends a staleness
warning to the badge.
Spec ref: response-accuracy §Staleness-Detection l.132-134 "confidence badge MUST include a staleness warning
if any retrieved document is >7 days old: '[Sources may be outdated — last updated X days ago]'"; rag-pipeline
§Index-Age-Tracking l.66 "Stale documents (>threshold) are flagged in retrieval — badge shows 'may be outdated'."
Fix: select `last_indexed_at` in search; compare to per-doc-type threshold; append staleness clause to badge.

**[MED] F5 — Auto-send gates on classifier confidence, not response confidence**
`src/sequor/ai/response.py:107-118` — `was_auto_sent = classification.confidence >= 0.9 AND … synthesis badge
in [high, moderate] …`. The auto-send decision keys on the CLASSIFIER's confidence while the badge shown to the
contact is the SYNTHESIS confidence. A synthesis badge of "moderate" (overall_confidence as low as 0.6) is
auto-sent whenever the classifier is ≥0.9.
Spec ref: response-accuracy §Response-Options-C l.33 "For confidence > 90%: auto-send" where confidence is the
response confidence ("I'm X% confident this answer is correct"); Core-Design-Principle l.5 "sending wrong
information is worse than sending none."
Fix: gate auto-send on the synthesized response confidence (`synthesis.confidence >= 0.9`), not classifier confidence.
(Note: interacts with the spec-internal contradiction F11 — resolve the threshold first.)

**[MED] F6 — Confidence-badge thresholds drift from spec AND disagree between code paths**
Spec badge table (response-accuracy l.46-51): >95 High / 80-95 Moderate / 60-80 Low / <60 Uncertain.
`rag_pipeline.py:281-288`: `0.9→high, 0.6→moderate, 0.4→low, else uncertain`.
`response.py:228-235` (learned path): `0.8→high, 0.6→moderate, 0.4→low, else uncertain`.
Neither matches the spec floors (0.95/0.80/0.60); the two paths disagree with each other on the "high"
boundary (0.9 vs 0.8); badge strings ("high") differ from spec labels ("High confidence").
Fix: single shared badge-classifier using spec thresholds (0.95/0.80/0.60) and spec labels; call from both paths.

**[MED] F7 — Audit write depends on private-attr reflection; silently skipped when session absent**
`src/sequor/escalation/service.py:676-679` — `_write_audit` resolves the DB session via
`getattr(self._db, "_session_inner", None) or getattr(self._db, "_session", None)`; if both are None it logs
`escalation.audit_no_session` (ERROR) and returns without writing the audit row.
Spec ref: response-accuracy §Audit-Trail l.103 "Audit rows are written for every state transition"; l.161-166
immutable/mandatory. The audit is a D/T/R governance guarantee that becomes best-effort on this express shape.
Fix: make the session an explicit constructor dependency (fail loud if audit cannot be written), not reflection.

**[LOW] F8 — Contradiction recency-precedence not implemented (learned answers)**
`src/sequor/ai/learning.py:186-201` — `search_learned_answers` orders purely by vector distance
(`ORDER BY embedding <=> :emb::vector`); no recency tiebreak when two learned answers conflict.
Spec ref: rag-pipeline §Quality-Controls l.141 "If a later human answer contradicts an earlier one, the more
recent answer takes precedence." Fix: add `created_at DESC` as a tiebreak or dedup by topic keeping newest.

**[LOW] F9 — Synthesis-confidence formula deviates from spec**
`rag_pipeline.py:126-132,277-279` — uses `max(answerability)` × hallucination penalty (1.0/0.5); spec
(rag-pipeline l.96) defines it as "weighted average of passage answerability scores × LLM confidence". No
LLM self-confidence term; MAX instead of weighted average. Fix: implement weighted-average per spec or update
spec if the max-based heuristic is intentional (spec-accuracy: spec must match shipped behavior).

**[LOW] F10 — Retrieval computes cosine in Python over all tenant chunks (not pgvector operator)**
`vector_store.py:140-148` fetches every tenant chunk then computes cosine in Python; `learning.py` correctly
uses the pgvector `<=>` operator. Also `learning.py:256-270` `_cosine_similarity` is dead code (unused).
Spec ref: rag-pipeline §Embeddings "stored in pgvector"; §Performance-Targets "Retrieval latency P95 < 800ms".
Impact: O(all-chunks) per query — scalability/perf risk, not a correctness bug. Fix: push similarity into the
`<=>` query (mirrors learning.py); delete unused `_cosine_similarity`.

**[LOW] F11 — Spec-internal contradiction (cross-spec, for spec authors)**
`specs/response-accuracy.md` §Response-Options-C (l.30-38) defines auto-send at **>90%** / route 60-90% / <60%
suggested; §Confidence-Badge-Specification (l.46-51) defines auto-send at **>95%** (High) and **80-95%**
(Moderate auto-send). The two sections specify different auto-send thresholds. Code cannot be compliant with
both. Recommend the spec pick one before F5/F6 fixes land. (Not a code defect — cross-spec contradiction.)

---

## Summary

Severity counts: **CRITICAL 0 · HIGH 4 · MED 3 · LOW 4** (11 findings).
No fake/canned LLM responses (synthesis is a real config-driven LLM call); no hardcoded model strings or secrets
(env-driven BaseSettings, env-models carve-out compliant); no LLM-first violations (classifier is LLM-driven;
`should_use_rag`/`should_auto_respond` are deterministic BY SPEC); every cluster module has an importing test.

Top 5:

1. [HIGH] F1 — `vector_store.search` passes raw SQL to `session.execute` w/o `text()` → `ArgumentError` on SA 2.0.51; document-RAG retrieval is dead on arrival (only learned-answer path works). vector_store.py:123.
2. [HIGH] F3 — confidence badge is computed but NEVER rendered (no WhatsApp footer, no `X-AI-Confidence` header) anywhere in `src/`; the "fixed governance control" is absent. response-accuracy §Badge-Display.
3. [HIGH] F4 — staleness warning unimplemented: retrieval never reads `last_indexed_at`; badge never shows "may be outdated". response-accuracy §Staleness-Detection.
4. [HIGH] F2 — answerability<0.3 exclusion missing; low-answerability passages still feed synthesis. rag_pipeline.py:107-123.
5. [MED] F5 — auto-send gates on classifier confidence, letting a 0.6 "moderate" synthesis auto-send; violates "wrong info is worse than none." response.py:118.
