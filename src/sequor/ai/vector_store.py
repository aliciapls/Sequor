"""Vector store using pgvector for hybrid retrieval.

Hybrid retrieval combines:
- Vector similarity search (0.7 weight)
- BM25 keyword match (0.3 weight)
"""

import math
import re
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

logger = structlog.get_logger()


@dataclass
class SearchResult:
    """A search result with combined score."""

    chunk_id: UUID
    document_id: UUID
    chunk_text: str
    similarity_score: float
    bm25_score: float
    combined_score: float
    metadata: dict[str, Any]


class VectorStore:
    """Hybrid vector + BM25 search using pgvector.

    Uses cosine similarity for vectors and BM25 for keyword matching.
    Combined score = 0.7 * normalized_vector + 0.3 * normalized_bm25
    """

    VECTOR_WEIGHT = 0.7
    BM25_WEIGHT = 0.3
    BM25_K1 = 1.5
    BM25_B = 0.75

    def __init__(self, engine: AsyncEngine) -> None:
        """Initialize the vector store.

        Args:
            engine: SQLAlchemy async engine
        """
        self._engine = engine

    async def store_chunks(
        self,
        tenant_id: UUID,
        document_id: UUID,
        chunks: list[tuple[int, str, list[float]]],
    ) -> int:
        """Store document chunks with embeddings.

        Args:
            tenant_id: Tenant ID for multi-tenancy
            document_id: Document ID
            chunks: List of (chunk_index, chunk_text, embedding) tuples

        Returns:
            Number of chunks stored
        """
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(self._engine) as session:
            for chunk_index, chunk_text, embedding in chunks:
                await session.execute(
                    text(
                        """
                    INSERT INTO document_chunks
                    (id, tenant_id, document_id, chunk_text, chunk_index, embedding, created_at)
                    VALUES (gen_random_uuid(), :tenant_id, :document_id, :chunk_text, :chunk_index, :embedding, NOW())
                    ON CONFLICT (tenant_id, document_id, chunk_index)
                    DO UPDATE SET chunk_text = :chunk_text, embedding = :embedding
                    """
                    ),
                    {
                        "tenant_id": tenant_id,
                        "document_id": document_id,
                        "chunk_text": chunk_text,
                        "chunk_index": chunk_index,
                        "embedding": embedding,
                    },
                )
            await session.commit()

        logger.info(
            "vector_store.store_chunks.ok",
            tenant_id=str(tenant_id),
            document_id=str(document_id),
            chunk_count=len(chunks),
        )
        return len(chunks)

    async def search(
        self,
        tenant_id: UUID,
        query_embedding: list[float],
        query_text: str,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> list[SearchResult]:
        """Hybrid search combining vector similarity and BM25.

        Args:
            tenant_id: Tenant ID for multi-tenancy
            query_embedding: Query embedding vector
            query_text: Raw query text for BM25
            top_k: Number of results to return
            min_score: Minimum combined score threshold

        Returns:
            List of SearchResult objects ranked by combined score
        """
        from sqlalchemy.ext.asyncio import AsyncSession

        from sqlalchemy import text

        async with AsyncSession(self._engine) as session:
            result = await session.execute(
                text(
                    """
                    SELECT id, document_id, chunk_text, embedding
                    FROM document_chunks
                    WHERE tenant_id = :tenant_id
                    """
                ),
                {"tenant_id": tenant_id},
            )
            all_chunks = result.fetchall()

        if not all_chunks:
            logger.info("vector_store.search.empty", tenant_id=str(tenant_id))
            return []

        bm25_scores = self._compute_bm25(all_chunks, query_text)

        results = []
        for chunk in all_chunks:
            embedding = chunk.embedding
            if embedding is None:
                continue

            vector_score = self._cosine_similarity(query_embedding, list(embedding))
            bm25_score = bm25_scores.get(str(chunk.id), 0.0)

            combined = self.VECTOR_WEIGHT * vector_score + self.BM25_WEIGHT * bm25_score

            if combined >= min_score:
                results.append(
                    SearchResult(
                        chunk_id=chunk.id,
                        document_id=chunk.document_id,
                        chunk_text=chunk.chunk_text,
                        similarity_score=vector_score,
                        bm25_score=bm25_score,
                        combined_score=combined,
                        metadata={},
                    )
                )

        results.sort(key=lambda x: x.combined_score, reverse=True)
        results = results[:top_k]

        logger.info(
            "vector_store.search.ok",
            tenant_id=str(tenant_id),
            total_chunks=len(all_chunks),
            results_returned=len(results),
            top_score=results[0].combined_score if results else 0,
        )

        return results

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=True))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)

    def _compute_bm25(self, chunks: list[Any], query: str) -> dict[str, float]:
        """Compute BM25 scores for chunks against query."""
        if not chunks:
            return {}

        query_terms = self._tokenize(query)
        if not query_terms:
            return {}

        chunk_texts = [c.chunk_text for c in chunks]
        avg_doc_len = sum(len(self._tokenize(t)) for t in chunk_texts) / len(chunks)
        if avg_doc_len == 0:
            avg_doc_len = 1

        doc_freq = {}
        for chunk in chunks:
            doc_terms = set(self._tokenize(chunk.chunk_text))
            for term in query_terms:
                if term in doc_terms:
                    doc_freq[term] = doc_freq.get(term, 0) + 1

        n = len(chunks)
        scores = {}

        for chunk in chunks:
            chunk_terms = self._tokenize(chunk.chunk_text)
            doc_len = len(chunk_terms)
            score = 0.0

            for term in query_terms:
                if term in doc_freq:
                    df = doc_freq[term]
                    tf = chunk_terms.count(term)
                    idf = math.log((n - df + 0.5) / (df + 0.5) + 1)
                    tf_component = (
                        tf
                        * (self.BM25_K1 + 1)
                        / (
                            tf
                            + self.BM25_K1 * (1 - self.BM25_B + self.BM25_B * doc_len / avg_doc_len)
                        )
                    )
                    score += idf * tf_component

            scores[str(chunk.id)] = score

        max_score = max(scores.values()) if scores else 1.0
        if max_score > 0:
            scores = {k: v / max_score for k, v in scores.items()}

        return scores

    def _tokenize(self, text: str) -> list[str]:
        """Simple tokenization: lowercase, alphanumeric only."""
        return re.findall(r"\b[a-z0-9]+\b", text.lower())
