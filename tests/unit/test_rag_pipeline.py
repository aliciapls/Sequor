"""Unit tests for sequor.ai.rag_pipeline.

Tests hallucination checking, answerability scoring, and confidence badge
assignment. Uses mock LLM and vector store.
"""

import json
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sequor.ai.rag_pipeline import RAGPipeline, RetrievalResult, SynthesisResult


@pytest.fixture
def mock_llm():
    """Create a mock LLM client."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value="test response")
    llm.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    return llm


@pytest.fixture
def mock_vector_store():
    """Create a mock VectorStore."""
    vs = AsyncMock()
    vs.search = AsyncMock(return_value=[])
    return vs


@pytest.fixture
def pipeline(mock_vector_store, mock_llm):
    """Create a RAGPipeline with mock dependencies."""
    return RAGPipeline(vector_store=mock_vector_store, llm_client=mock_llm)


# ---------------------------------------------------------------------------
# _check_hallucination
# ---------------------------------------------------------------------------


class TestCheckHallucination:
    """Tests for hallucination detection."""

    async def test_valid_json_passed_true(self, pipeline: RAGPipeline):
        """Valid JSON with passed=true returns passed=True."""
        response = json.dumps({"passed": True, "uncited_claims": 0, "notes": "All good"})
        pipeline._llm.generate = AsyncMock(return_value=response)

        result = await pipeline._check_hallucination(
            query="What is the price?",
            answer="The price is $10.",
            passages=[{"text": "Our price is $10 per month."}],
        )

        assert result["passed"] is True
        assert result["uncited_claims"] == 0

    async def test_valid_json_passed_false(self, pipeline: RAGPipeline):
        """Valid JSON with passed=false returns passed=False."""
        response = json.dumps({
            "passed": False,
            "uncited_claims": 3,
            "notes": "Multiple uncited claims",
        })
        pipeline._llm.generate = AsyncMock(return_value=response)

        result = await pipeline._check_hallucination(
            query="What is the refund policy?",
            answer="We offer full refunds within 30 days and store credit after.",
            passages=[{"text": "Refunds available within 14 days only."}],
        )

        assert result["passed"] is False
        assert result["uncited_claims"] == 3

    async def test_malformed_response_fails_closed(self, pipeline: RAGPipeline):
        """Malformed LLM response returns passed=False (fail-closed)."""
        pipeline._llm.generate = AsyncMock(return_value="This is not JSON at all")

        result = await pipeline._check_hallucination(
            query="test",
            answer="test answer",
            passages=[{"text": "test passage"}],
        )

        assert result["passed"] is False
        assert result["uncited_claims"] == 0

    async def test_json_with_markdown_fences(self, pipeline: RAGPipeline):
        """JSON wrapped in markdown fences is parsed correctly."""
        response = '```json\n{"passed": true, "uncited_claims": 0, "notes": "ok"}\n```'
        pipeline._llm.generate = AsyncMock(return_value=response)

        result = await pipeline._check_hallucination(
            query="test",
            answer="test",
            passages=[{"text": "test"}],
        )

        assert result["passed"] is True

    async def test_high_uncited_claims_overrides_passed(self, pipeline: RAGPipeline):
        """More than 50% uncited claims relative to passages forces passed=False."""
        response = json.dumps({
            "passed": True,
            "uncited_claims": 5,
            "notes": "Many uncited",
        })
        pipeline._llm.generate = AsyncMock(return_value=response)

        # Only 2 passages, so 5 uncited claims > 2 * 0.5 = 1.0
        result = await pipeline._check_hallucination(
            query="test",
            answer="test",
            passages=[{"text": "p1"}, {"text": "p2"}],
        )

        assert result["passed"] is False

    async def test_llm_exception_fails_closed(self, pipeline: RAGPipeline):
        """LLM exception during hallucination check returns passed=False."""
        pipeline._llm.generate = AsyncMock(side_effect=RuntimeError("LLM down"))

        result = await pipeline._check_hallucination(
            query="test",
            answer="test",
            passages=[{"text": "test"}],
        )

        assert result["passed"] is False
        assert result["uncited_claims"] == 0


# ---------------------------------------------------------------------------
# _score_answerability
# ---------------------------------------------------------------------------


class TestScoreAnswerability:
    """Tests for answerability scoring."""

    async def test_numeric_response_parsed(self, pipeline: RAGPipeline):
        """A numeric response is parsed as the answerability score."""
        pipeline._llm.generate = AsyncMock(return_value="0.85")

        score = await pipeline._score_answerability("What is the price?", "The price is $10.")

        assert score == pytest.approx(0.85)

    async def test_score_clamped_to_range(self, pipeline: RAGPipeline):
        """Answerability score is clamped to [0.0, 1.0]."""
        pipeline._llm.generate = AsyncMock(return_value="1.5")

        score = await pipeline._score_answerability("test query", "test passage")

        assert score <= 1.0

    async def test_malformed_response_returns_default(self, pipeline: RAGPipeline):
        """Non-numeric response returns the fallback score of 0.5."""
        pipeline._llm.generate = AsyncMock(return_value="not a number")

        score = await pipeline._score_answerability("test", "test")

        assert score == pytest.approx(0.5)

    async def test_response_with_extra_text(self, pipeline: RAGPipeline):
        """Response with text after the number uses only the first token."""
        pipeline._llm.generate = AsyncMock(return_value="0.7 - the passage partially answers")

        score = await pipeline._score_answerability("test", "test")

        assert score == pytest.approx(0.7)


# ---------------------------------------------------------------------------
# Confidence badge assignment
# ---------------------------------------------------------------------------


class TestConfidenceBadge:
    """Tests for confidence badge thresholds in synthesize."""

    def _make_retrieval_result(self, synthesis_confidence: float) -> RetrievalResult:
        """Build a RetrievalResult with given synthesis confidence."""
        return RetrievalResult(
            passages=[{
                "chunk_id": str(uuid4()),
                "document_id": str(uuid4()),
                "text": "test passage text",
                "similarity_score": 0.8,
                "bm25_score": 0.5,
                "combined_score": 0.7,
                "answerability": synthesis_confidence,
                "final_score": 0.7 * synthesis_confidence,
            }],
            retrieval_confidence=0.7,
            synthesis_confidence=synthesis_confidence,
            answerability_scores=[synthesis_confidence],
        )

    async def test_high_confidence_badge(self, pipeline: RAGPipeline):
        """Confidence >= 0.9 and hallucination passed produces 'high' badge."""
        retrieval = self._make_retrieval_result(synthesis_confidence=0.95)
        pipeline._llm.generate = AsyncMock(return_value="The answer is $10.")
        # Mock hallucination check to return passed=True
        pipeline._check_hallucination = AsyncMock(
            return_value={"passed": True, "uncited_claims": 0}
        )

        result = await pipeline.synthesize(uuid4(), "What is the price?", retrieval)

        assert result.confidence_badge == "high"
        assert result.confidence >= 0.9

    async def test_moderate_confidence_badge(self, pipeline: RAGPipeline):
        """Confidence >= 0.6 and < 0.9 produces 'moderate' badge."""
        retrieval = self._make_retrieval_result(synthesis_confidence=0.75)
        pipeline._llm.generate = AsyncMock(return_value="The answer might be $10.")
        pipeline._check_hallucination = AsyncMock(
            return_value={"passed": True, "uncited_claims": 0}
        )

        result = await pipeline.synthesize(uuid4(), "What is the price?", retrieval)

        assert result.confidence_badge == "moderate"

    async def test_low_confidence_badge(self, pipeline: RAGPipeline):
        """Confidence >= 0.4 and < 0.6 produces 'low' badge."""
        retrieval = self._make_retrieval_result(synthesis_confidence=0.5)
        pipeline._llm.generate = AsyncMock(return_value="I think maybe...")
        pipeline._check_hallucination = AsyncMock(
            return_value={"passed": True, "uncited_claims": 0}
        )

        result = await pipeline.synthesize(uuid4(), "What is the price?", retrieval)

        assert result.confidence_badge == "low"

    async def test_uncertain_confidence_badge(self, pipeline: RAGPipeline):
        """Confidence < 0.4 produces 'uncertain' badge."""
        retrieval = self._make_retrieval_result(synthesis_confidence=0.3)
        pipeline._llm.generate = AsyncMock(return_value="I'm not sure...")
        pipeline._check_hallucination = AsyncMock(
            return_value={"passed": True, "uncited_claims": 0}
        )

        result = await pipeline.synthesize(uuid4(), "What is the price?", retrieval)

        assert result.confidence_badge == "uncertain"

    async def test_hallucination_failure_halves_confidence(self, pipeline: RAGPipeline):
        """Failed hallucination check multiplies confidence by 0.5."""
        retrieval = self._make_retrieval_result(synthesis_confidence=0.95)
        pipeline._llm.generate = AsyncMock(return_value="Some answer.")
        pipeline._check_hallucination = AsyncMock(
            return_value={"passed": False, "uncited_claims": 2}
        )

        result = await pipeline.synthesize(uuid4(), "test query", retrieval)

        # Confidence should be 0.95 * 0.5 = 0.475 (badge: low)
        assert result.confidence == pytest.approx(0.475, rel=0.01)
        assert result.hallucination_check_passed is False


# ---------------------------------------------------------------------------
# No passages edge case
# ---------------------------------------------------------------------------


async def test_synthesize_no_passages(pipeline: RAGPipeline):
    """Synthesize with no passages returns a safe fallback response."""
    retrieval = RetrievalResult(
        passages=[],
        retrieval_confidence=0.0,
        synthesis_confidence=0.0,
        answerability_scores=[],
    )

    result = await pipeline.synthesize(uuid4(), "test query", retrieval)

    assert result.confidence == 0.0
    assert result.confidence_badge == "uncertain"
    assert result.hallucination_check_passed is True
    assert "forwarded" in result.answer.lower() or "don't have" in result.answer.lower()


async def test_synthesize_llm_failure_returns_error_response(pipeline: RAGPipeline):
    """LLM failure during synthesis returns an error SynthesisResult."""
    retrieval = RetrievalResult(
        passages=[{
            "chunk_id": str(uuid4()),
            "document_id": str(uuid4()),
            "text": "test passage",
            "similarity_score": 0.8,
            "bm25_score": 0.5,
            "combined_score": 0.7,
            "answerability": 0.8,
            "final_score": 0.56,
        }],
        retrieval_confidence=0.7,
        synthesis_confidence=0.8,
        answerability_scores=[0.8],
    )
    pipeline._llm.generate = AsyncMock(side_effect=RuntimeError("LLM error"))

    result = await pipeline.synthesize(uuid4(), "test query", retrieval)

    assert result.confidence_badge == "low"
    assert result.hallucination_check_passed is False
    assert "error" in result.answer.lower()
