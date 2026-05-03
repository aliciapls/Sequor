# RISK: BM25 Computed in Python Over Full Table Scan

## Severity: HIGH

## What

BM25 relevance scoring fetches ALL document chunks for a tenant into Python memory, then computes BM25 in a Python loop. Spec implies database-side indexing.

## Location

`src/sequor/ai/vector_store.py` — `VectorStore.search()` method

## Spec Requirement

From `specs/rag-pipeline.md` § "Indexing":

> Inverted index: keyword → chunks for BM25 hybrid retrieval

This implies database-side BM25 index, not Python-side computation over full table.

## Evidence

```python
# Current: fetch ALL chunks into memory
result = await session.execute(
    select(DocumentChunk).where(DocumentChunk.tenant_id == tenant_id)
)
chunks = result.scalars().all()

# Then compute BM25 in Python loop over every chunk
for chunk in chunks:
    score = self._bm25_score(query, chunk.chunk_text)  # O(n) per query
```

## Impact

At 1,000 chunks: acceptable. At 100,000 chunks (small business document base): 100K row fetch per query = 10+ second retrieval latency, exceeding spec's 800ms P95 target.

## Fix Options

1. Database-side BM25 with PostgreSQL full-text search indexes
2. Pre-computed BM25 scores stored with chunks
3. Limit chunk fetch with keyword pre-filter before BM25 scoring

## Status

Open — scalability concern for production
