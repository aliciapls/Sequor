# Red Team Validation Report — Branch 2 (feat/ai-rag-pipeline)

**Date**: 2026-05-03
**Scope**: Branch 2 AI/RAG pipeline implementation
**Agents**: analyst, testing-specialist, security-reviewer, value-auditor

---

## Convergence Status

| Criterion                         | Result                            |
| --------------------------------- | --------------------------------- |
| 0 CRITICAL findings               | FAIL — 1 CRITICAL                 |
| 0 HIGH findings                   | FAIL — 5 HIGH                     |
| 2 consecutive clean rounds        | NO                                |
| Spec compliance: 100%             | FAIL — 11 PASS, 5 FAIL            |
| New code has new tests            | FAIL — 0 tests for 10 new modules |
| Frontend integration: 0 mock data | PASS                              |

**BLOCKED** — Cannot converge. CRITICAL and HIGH findings must be fixed.

---

## Critical Findings

### CRITICAL-1: SQLAlchemy Positional Parameter Bug

**Severity**: CRITICAL — will fail at runtime with PostgreSQL

**Locations**:

- `src/sequor/email/auto_reply.py:247` — `$1-$7` in INSERT responses
- `src/sequor/email/auto_reply.py:294` — `$1-$2` in SELECT backup_contacts
- `src/sequor/email/auto_reply.py:316` — `$1-$6` in INSERT escalations
- `src/sequor/ai/ingestion.py:291` — `$1-$8` in INSERT documents

**Problem**: PostgreSQL `$N` notation used in SQLAlchemy `session.execute()` which expects `:name` named parameters.

**Fix**: Wrap SQL in `text()` and use named parameters:

```python
from sqlalchemy import text
await session.execute(
    text("""
    INSERT INTO responses (id, tenant_id, ...) VALUES (gen_random_uuid(), :tenant_id, ...)
    """),
    {"tenant_id": context.tenant_id, ...}
)
```

---

## High Findings

### HIGH-1: Zero Tests for All AI Pipeline Modules

**Severity**: HIGH — regression blind spot

All 10 new modules have ZERO importing tests:

- `sequor.ai.classifier` — MessageClassifier
- `sequor.ai.ingestion` — DocumentIngester
- `sequor.ai.rag_pipeline` — RAGPipeline
- `sequor.ai.learning` — LearningLoop
- `sequor.ai.response` — ResponseGenerator
- `sequor.ai.vector_store` — VectorStore
- `sequor.ai.chunker` — Chunking strategies
- `sequor.ai.document_parser` — Document parsers
- `sequor.ai.client` — OllamaClient
- `sequor.email.auto_reply` — AutoReplyService

**Verification**:

```bash
pytest --collect-only -q tests/
# 10 tests collected, 4 errors (missing sequor module — not installed dev mode)
grep -rln "from sequor.ai.classifier import" tests/
# ZERO
```

### HIGH-2: Answerability < 0.3 Filtering Not Implemented

**Severity**: HIGH — increases hallucination risk

`min_answerability` parameter defined in `VectorStore.search()` but never used to filter passages.

**Spec requirement** (`specs/rag-pipeline.md`): "If answerability < 0.3, the passage is excluded even if vector similarity is high."

**Location**: `src/sequor/ai/vector_store.py:106`

### HIGH-3: Document Status State Machine Not Implemented

**Severity**: HIGH — breaks staleness detection

Documents created directly with `status=ready` instead of `pending → indexing → ready` flow.

**Spec requirement** (`specs/rag-pipeline.md`): Upload generates `pending` → `indexing` → `ready`

**Location**: `src/sequor/ai/ingestion.py:281`

### HIGH-4: Three-Tier Confidence Thresholds Not Implemented

**Severity**: HIGH — degrades user experience

Only two tiers implemented (auto-reply vs escalate). Spec requires three tiers:

- > 90%: auto-reply
- 60-90%: escalate WITH AI draft for review
- < 60%: escalate WITHOUT AI draft

**Location**: `src/sequor/ai/response.py:103-113`

### HIGH-5: BM25 Computed in Python Over Full Table Scan

**Severity**: HIGH — scalability risk at production volumes

`VectorStore.search()` fetches ALL chunks for a tenant into Python memory, then computes BM25 in a Python loop. Will degrade catastrophically at 100K+ chunks.

**Spec target**: 800ms P95 retrieval latency. Full table scan at scale = 10+ seconds.

**Location**: `src/sequor/ai/vector_store.py`

---

## Spec Compliance Summary

| Spec                    | Assertion                                               | Status   | Severity |
| ----------------------- | ------------------------------------------------------- | -------- | -------- |
| rag-pipeline.md         | File type support (PDF, DOCX, XLSX, CSV, TXT, PNG, JPG) | PASS     | —        |
| rag-pipeline.md         | Three chunking strategies                               | PASS     | —        |
| rag-pipeline.md         | Embedding model from .env                               | PASS     | —        |
| rag-pipeline.md         | Hybrid retrieval 0.7/0.3 weights                        | PASS     | —        |
| rag-pipeline.md         | Retrieval confidence = relevance × answerability        | PASS     | —        |
| rag-pipeline.md         | Answerability < 0.3 excluded                            | **FAIL** | HIGH-2   |
| rag-pipeline.md         | Top 5 passages                                          | PASS     | —        |
| rag-pipeline.md         | Citation format [Source: ...]                           | PASS     | —        |
| rag-pipeline.md         | Hallucination detection via 2nd LLM call                | PASS     | —        |
| rag-pipeline.md         | Learned answers source_type = human_answer              | PASS     | —        |
| rag-pipeline.md         | Document status flow (pending→indexing→ready)           | **FAIL** | HIGH-3   |
| response-accuracy.md    | Three-tier confidence thresholds                        | **FAIL** | HIGH-4   |
| response-accuracy.md    | High-stakes always escalate                             | PASS     | —        |
| response-accuracy.md    | Confidence badge in footer                              | PASS     | —        |
| data-model.md           | Classification entity fields                            | PASS     | —        |
| data-model.md           | LearnedAnswer entity fields                             | PASS     | —        |
| channel-coordination.md | Escalation record fields                                | PASS     | —        |

---

## Value Audit Findings

### RISK: RAG Feasibility Unvalidated

Per `specs/rag-pipeline.md` § "Pre-Build Validation", build only proceeds if:

- Answerability rate from real documents > 70%
- Hallucination rate < 10%
- False positive rate < 15%

**No evidence this validation was performed.** No scripts, benchmarks, or real documents tested.

### GAP: Auto-Reply Has No Trigger

`AutoReplyService.process_message()` is fully implemented but NO webhook endpoint exists to call it. Pipeline never runs in production.

### GAP: Document Upload Has No API

`DocumentIngester.ingest()` is fully implemented but NO API endpoint exists to call it.

---

## Log Triage

```
Dependency warnings from pip check (not from this branch):
- refinitiv-data 1.6.2 / numpy 2.4.4
- openbb-core 1.6.7 / uvicorn 0.42.0
- mcp-yahoo-finance 0.1.3 / mcp 0.9.1
- eikon 1.1.18 / idna 3.11
These are pre-existing environment issues, not introduced by this branch.
```

---

## Required Fixes Before Merge

1. **CRITICAL**: Fix PostgreSQL positional param bug in `auto_reply.py` and `ingestion.py`
2. **HIGH**: Add integration tests for all 10 AI modules
3. **HIGH**: Implement answerability < 0.3 filtering
4. **HIGH**: Implement document status state machine
5. **HIGH**: Implement three-tier confidence thresholds
6. **HIGH**: Address BM25 scalability (defer to post-beta acceptable with tracking issue)

---

## Journal Entries Created

- `0001-RISK-sqlalchemy-positional-params.md`
- `0002-GAP-no-integration-tests.md`
- `0003-GAP-answerability-filtering.md`
- `0004-GAP-document-status-flow.md`
- `0005-GAP-three-tier-thresholds.md`
- `0006-RISK-bm25-scalability.md`
