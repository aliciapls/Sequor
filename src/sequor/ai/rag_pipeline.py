"""RAG pipeline for retrieval-augmented generation.

Combines document retrieval with LLM synthesis for question answering.
Includes hallucination detection via cross-check prompts.
"""

import json
from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

from sequor.ai.vector_store import VectorStore

logger = structlog.get_logger()


@dataclass
class RetrievalResult:
    """Result from RAG retrieval."""

    passages: list[dict]
    retrieval_confidence: float
    synthesis_confidence: float
    answerability_scores: list[float]


@dataclass
class SynthesisResult:
    """Result from RAG synthesis."""

    answer: str
    sources: list[dict]
    confidence: float
    confidence_badge: str
    hallucination_check_passed: bool
    uncited_claims: int


class RAGPipeline:
    """RAG pipeline for document retrieval and synthesis.

    Orchestrates:
    1. Query embedding generation
    2. Hybrid retrieval (vector + BM25)
    3. Answerability scoring via LLM
    4. Synthesis with context
    5. Hallucination detection
    """

    def __init__(
        self,
        vector_store: VectorStore,
        llm_client: Any,
    ) -> None:
        """Initialize RAG pipeline.

        Args:
            vector_store: VectorStore instance for hybrid search
            llm_client: OllamaClient instance for LLM calls
        """
        self._vector_store = vector_store
        self._llm = llm_client

    async def retrieve(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 5,
        min_score: float = 0.3,
    ) -> RetrievalResult:
        """Retrieve relevant passages for a query.

        Args:
            tenant_id: Tenant ID for multi-tenancy
            query: User query
            top_k: Number of passages to retrieve
            min_score: Minimum combined score threshold

        Returns:
            RetrievalResult with passages and confidence scores
        """
        logger.info("rag.retrieve.start", tenant_id=str(tenant_id), query_length=len(query))

        query_embedding = await self._llm.generate_embeddings([query])
        if not query_embedding:
            logger.error("rag.retrieve.embedding_failed")
            return RetrievalResult(
                passages=[],
                retrieval_confidence=0.0,
                synthesis_confidence=0.0,
                answerability_scores=[],
            )

        results = await self._vector_store.search(
            tenant_id=tenant_id,
            query_embedding=query_embedding[0],
            query_text=query,
            top_k=top_k,
            min_score=min_score,
        )

        answerability_scores = []
        passages = []

        for result in results:
            answerability = await self._score_answerability(query, result.chunk_text)
            answerability_scores.append(answerability)

            final_score = result.combined_score * answerability
            passages.append(
                {
                    "chunk_id": str(result.chunk_id),
                    "document_id": str(result.document_id),
                    "text": result.chunk_text,
                    "similarity_score": result.similarity_score,
                    "bm25_score": result.bm25_score,
                    "combined_score": result.combined_score,
                    "answerability": answerability,
                    "final_score": final_score,
                }
            )

        if passages:
            retrieval_confidence = max(p["combined_score"] for p in passages)
            synthesis_confidence = (
                max(p["answerability"] for p in passages) if answerability_scores else 0.0
            )
        else:
            retrieval_confidence = 0.0
            synthesis_confidence = 0.0

        logger.info(
            "rag.retrieve.ok",
            tenant_id=str(tenant_id),
            passages_count=len(passages),
            retrieval_confidence=retrieval_confidence,
            synthesis_confidence=synthesis_confidence,
        )

        return RetrievalResult(
            passages=passages,
            retrieval_confidence=retrieval_confidence,
            synthesis_confidence=synthesis_confidence,
            answerability_scores=answerability_scores,
        )

    async def _score_answerability(
        self,
        query: str,
        passage: str,
    ) -> float:
        """Score how well a passage answers the query.

        Uses an LLM cross-check prompt to determine if the passage
        can answer the user's question.

        Args:
            query: User query
            passage: Retrieved passage

        Returns:
            Answerability score (0.0 - 1.0)
        """
        prompt = f"""Given this user question and retrieved passage, rate how well the passage answers the question.

Question: {query}

Passage: {passage}

Does this passage contain information that can help answer the user's question?

Respond with only a number between 0.0 and 1.0:
- 1.0 = The passage fully answers the question
- 0.7 = The passage partially answers the question
- 0.3 = The passage is related but doesn't answer
- 0.0 = The passage is unrelated

Score:"""

        try:
            response = await self._llm.generate(prompt, temperature=0.0)
            response = response.strip().split()[0]
            score = float(response)
            return max(0.0, min(1.0, score))
        except (ValueError, IndexError):
            logger.warning("rag.answerability.parse_failed", response=response)
            return 0.5

    async def synthesize(
        self,
        tenant_id: UUID,
        query: str,
        retrieval_result: RetrievalResult,
        system_instructions: str | None = None,
    ) -> SynthesisResult:
        """Synthesize an answer from retrieved passages.

        Args:
            tenant_id: Tenant ID
            query: User query
            retrieval_result: Result from retrieve()
            system_instructions: Optional system prompt additions

        Returns:
            SynthesisResult with answer, sources, and confidence
        """
        logger.info(
            "rag.synthesize.start",
            tenant_id=str(tenant_id),
            query_length=len(query),
            passage_count=len(retrieval_result.passages),
        )

        if not retrieval_result.passages:
            logger.info("rag.synthesize.no_passages")
            return SynthesisResult(
                answer="I don't have information about this in the available documents. Your enquiry has been forwarded for review.",
                sources=[],
                confidence=0.0,
                confidence_badge="uncertain",
                hallucination_check_passed=True,
                uncited_claims=0,
            )

        passages_context = "\n\n".join(
            f"[Passage {i + 1}]\n{p['text']}" for i, p in enumerate(retrieval_result.passages)
        )

        base_system = (
            "You are a helpful AI assistant. Answer the user's question based ONLY on the "
            "provided passages. Do not add information not present in the retrieved documents. "
            "Cite each factual claim with a source in brackets like [Source: FAQ.pdf, Q3]. "
            "If you cannot answer from the passages, say so clearly."
        )

        system = f"{base_system}\n\n{system_instructions}" if system_instructions else base_system

        prompt = f"""Context passages:
{passages_context}

User question: {query}

Please answer based on the passages above. Cite your sources using [Source: doc_name, location] format."""

        try:
            answer = await self._llm.generate(prompt, system=system, temperature=0.3)
        except Exception as e:
            logger.error("rag.synthesize.llm_failed", error=str(e))
            return SynthesisResult(
                answer="I encountered an error generating a response. Please try again.",
                sources=[
                    {"text": p["text"][:100], "doc_id": p["document_id"]}
                    for p in retrieval_result.passages
                ],
                confidence=retrieval_result.synthesis_confidence * 0.5,
                confidence_badge="low",
                hallucination_check_passed=False,
                uncited_claims=0,
            )

        sources = [
            {
                "chunk_id": p["chunk_id"],
                "document_id": p["document_id"],
                "text": p["text"][:200],
                "answerability": p["answerability"],
            }
            for p in retrieval_result.passages
        ]

        hallucination_result = await self._check_hallucination(
            query, answer, retrieval_result.passages
        )

        overall_confidence = retrieval_result.synthesis_confidence * (
            1.0 if hallucination_result["passed"] else 0.5
        )

        if overall_confidence >= 0.9:
            badge = "high"
        elif overall_confidence >= 0.6:
            badge = "moderate"
        elif overall_confidence >= 0.4:
            badge = "low"
        else:
            badge = "uncertain"

        logger.info(
            "rag.synthesize.ok",
            tenant_id=str(tenant_id),
            confidence=overall_confidence,
            badge=badge,
            hallucination_passed=hallucination_result["passed"],
        )

        return SynthesisResult(
            answer=answer,
            sources=sources,
            confidence=overall_confidence,
            confidence_badge=badge,
            hallucination_check_passed=hallucination_result["passed"],
            uncited_claims=hallucination_result["uncited_claims"],
        )

    async def _check_hallucination(
        self,
        query: str,
        answer: str,
        passages: list[dict],
    ) -> dict:
        """Check if the answer contains claims not supported by passages.

        Args:
            query: Original user query
            answer: Generated answer
            passages: Retrieved passages

        Returns:
            Dict with 'passed' bool and 'uncited_claims' count
        """
        prompt = f"""Review this answer and check if every factual claim is supported by the provided passages.

Original question: {query}

Answer: {answer}

Passages:
{chr(10).join(f"[Passage] {p['text']}" for p in passages)}

Check each factual claim in the answer. For each claim:
- If it appears in the passages, it's cited
- If it doesn't appear but could be inferred, note it
- If it's a clear addition not supported by any passage, mark it un-cited

Respond with a JSON object:
{{"passed": true/false, "uncited_claims": number, "notes": "brief explanation"}}

Focus on factual claims, not the answer's framing or structure."""

        try:
            response = await self._llm.generate(prompt, temperature=0.0)
            response = response.strip()
            if response.startswith("```json"):
                response = response[7:]
            if response.startswith("```"):
                response = response[3:]
            if response.endswith("```"):
                response = response[:-3]

            result = json.loads(response.strip())
            passed = result.get("passed", True)
            uncited = result.get("uncited_claims", 0)

            if uncited > len(passages) * 0.5:
                passed = False

            return {"passed": passed, "uncited_claims": uncited}

        except (json.JSONDecodeError, Exception) as e:
            logger.warning("rag.hallucination.check_failed", error=str(e))
            return {"passed": False, "uncited_claims": 0}

    async def query(
        self,
        tenant_id: UUID,
        query: str,
        top_k: int = 5,
    ) -> SynthesisResult:
        """Full RAG query: retrieve and synthesize in one call.

        Args:
            tenant_id: Tenant ID
            query: User query
            top_k: Number of passages to retrieve

        Returns:
            SynthesisResult with answer and confidence
        """
        retrieval_result = await self.retrieve(
            tenant_id=tenant_id,
            query=query,
            top_k=top_k,
        )

        return await self.synthesize(
            tenant_id=tenant_id,
            query=query,
            retrieval_result=retrieval_result,
        )
