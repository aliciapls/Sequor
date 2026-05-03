# GAP: All AI Pipeline Modules Have Zero Tests

## Severity: HIGH

## What

All 10 new modules from Branch 2 have ZERO importing tests:

- sequor.ai.classifier — MessageClassifier
- sequor.ai.ingestion — DocumentIngester
- sequor.ai.rag_pipeline — RAGPipeline
- sequor.ai.learning — LearningLoop
- sequor.ai.response — ResponseGenerator
- sequor.ai.vector_store — VectorStore
- sequor.ai.chunker — Chunking strategies
- sequor.ai.document_parser — Document parsers
- sequor.ai.client — OllamaClient
- sequor.email.auto_reply — AutoReplyService

## Evidence

```bash
pytest --collect-only -q tests/
# Result: 10 tests collected, 4 errors (missing sequor module)
grep -rln "from sequor.ai.classifier import" tests/
# Result: ZERO
```

## Spec Requirements

- TODO-07 acceptance: "Test messages classified correctly across all 4 categories; confidence scores reasonable"
- TODO-08 acceptance: "chunks created and embedded; vector similarity search returns relevant chunks"
- TODO-10 acceptance: "Test messages at different confidence levels route correctly"

## Impact

- SQLAlchemy positional param bug would be caught by integration tests
- Any regression in classification, RAG retrieval, or email threading goes undetected
- Branch cannot pass red team gate criterion: "New code has new tests"

## Fix Required

Write Tier 2 integration tests for each module that:

1. Import through the framework facade (not directly)
2. Use real infrastructure (no mocks)
3. Assert externally observable behavior

## Status

Open — needs tests before merge
