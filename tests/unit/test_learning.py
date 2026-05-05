"""Unit tests for sequor.ai.learning.

Tests the LearningLoop's cosine similarity, input validation for
capture_human_answer, and search with empty results.
"""

import math
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from sequor.ai.learning import LearningLoop


@pytest.fixture
def mock_llm():
    """Create a mock OllamaClient."""
    llm = AsyncMock()
    llm.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
    return llm


@pytest.fixture
def learning_loop(mock_llm):
    """Create a LearningLoop with a mock LLM and no engine."""
    return LearningLoop(llm_client=mock_llm, engine=None)


# ---------------------------------------------------------------------------
# _cosine_similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    """Tests for cosine similarity on LearningLoop (same algorithm as VectorStore)."""

    def test_identical_vectors(self, learning_loop: LearningLoop):
        """Identical vectors have similarity 1.0."""
        result = learning_loop._cosine_similarity([1.0, 0.0], [1.0, 0.0])
        assert result == pytest.approx(1.0)

    def test_orthogonal_vectors(self, learning_loop: LearningLoop):
        """Orthogonal vectors have similarity 0.0."""
        result = learning_loop._cosine_similarity([1.0, 0.0], [0.0, 1.0])
        assert result == pytest.approx(0.0)

    def test_known_value(self, learning_loop: LearningLoop):
        """Known vector pair produces the expected similarity."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        expected = 32.0 / (math.sqrt(14) * math.sqrt(77))
        result = learning_loop._cosine_similarity(a, b)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_zero_vector(self, learning_loop: LearningLoop):
        """Zero vector returns 0.0."""
        result = learning_loop._cosine_similarity([0.0, 0.0], [1.0, 1.0])
        assert result == 0.0

    def test_mismatched_lengths(self, learning_loop: LearningLoop):
        """Vectors of different lengths return 0.0."""
        result = learning_loop._cosine_similarity([1.0], [1.0, 2.0])
        assert result == 0.0

    def test_opposite_directions(self, learning_loop: LearningLoop):
        """Opposite vectors return -1.0."""
        result = learning_loop._cosine_similarity([1.0, 0.0], [-1.0, 0.0])
        assert result == pytest.approx(-1.0)


# ---------------------------------------------------------------------------
# capture_human_answer validation
# ---------------------------------------------------------------------------


class TestCaptureHumanAnswerValidation:
    """Tests for input validation in capture_human_answer."""

    async def test_empty_reply_raises(self, learning_loop: LearningLoop):
        """Empty human reply raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await learning_loop.capture_human_answer(
                tenant_id=uuid4(),
                account_id=uuid4(),
                escalation_id=uuid4(),
                original_query="What is the price?",
                human_reply="",
            )

    async def test_whitespace_only_reply_raises(self, learning_loop: LearningLoop):
        """Whitespace-only reply raises ValueError."""
        with pytest.raises(ValueError, match="cannot be empty"):
            await learning_loop.capture_human_answer(
                tenant_id=uuid4(),
                account_id=uuid4(),
                escalation_id=uuid4(),
                original_query="What is the price?",
                human_reply="   \n\t  ",
            )

    async def test_too_short_reply_raises(self, learning_loop: LearningLoop):
        """Reply shorter than 10 characters raises ValueError."""
        with pytest.raises(ValueError, match="too short"):
            await learning_loop.capture_human_answer(
                tenant_id=uuid4(),
                account_id=uuid4(),
                escalation_id=uuid4(),
                original_query="What is the price?",
                human_reply="Yes",
            )

    async def test_valid_reply_returns_uuid(self, learning_loop: LearningLoop):
        """A valid reply produces a UUID return value."""
        result = await learning_loop.capture_human_answer(
            tenant_id=uuid4(),
            account_id=uuid4(),
            escalation_id=uuid4(),
            original_query="What is the price?",
            human_reply="Our pricing starts at $10 per month for the basic plan.",
        )

        # With engine=None, a uuid4 is generated locally
        assert result is not None

    async def test_embedding_generated_for_reply(self, learning_loop: LearningLoop, mock_llm):
        """capture_human_answer calls generate_embeddings with the combined text."""
        await learning_loop.capture_human_answer(
            tenant_id=uuid4(),
            account_id=uuid4(),
            escalation_id=uuid4(),
            original_query="What are your hours?",
            human_reply="We are open from 9am to 5pm Monday through Friday.",
        )

        mock_llm.generate_embeddings.assert_called_once()
        call_args = mock_llm.generate_embeddings.call_args[0][0]
        assert len(call_args) == 1
        assert "What are your hours?" in call_args[0]
        assert "9am to 5pm" in call_args[0]


# ---------------------------------------------------------------------------
# search_learned_answers with empty results
# ---------------------------------------------------------------------------


class TestSearchLearnedAnswers:
    """Tests for search_learned_answers behavior."""

    async def test_no_embedding_returns_empty(self, mock_llm):
        """When embedding generation fails, returns empty list."""
        mock_llm.generate_embeddings = AsyncMock(return_value=[])
        loop = LearningLoop(llm_client=mock_llm, engine=None)

        # search_learned_answers requires an engine for DB queries,
        # but with empty embeddings it returns early before the DB call
        # However, the method still tries to use the engine for session,
        # so we need a mock engine for this test.
        mock_engine = MagicMock()
        loop._engine = mock_engine

        results = await loop.search_learned_answers(
            tenant_id=uuid4(),
            query="test query",
        )

        assert results == []

    async def test_search_with_engine_returns_results(self, learning_loop: LearningLoop):
        """Search with a mock engine returns sorted results."""
        from types import SimpleNamespace
        from uuid import uuid4

        # Create mock row objects
        doc_id = uuid4()
        mock_row = SimpleNamespace(
            id=doc_id,
            question_text="What is the price?",
            answer_text="$10 per month.",
            source_type="human_answer",
            source_escalation_id=None,
            created_at=None,
            embedding=[0.1, 0.2, 0.3],
            similarity=0.95,
        )

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        mock_engine = MagicMock()
        learning_loop._engine = mock_engine

        with patch("sqlalchemy.ext.asyncio.AsyncSession", return_value=mock_session):
            results = await learning_loop.search_learned_answers(
                tenant_id=uuid4(),
                query="What is the price?",
            )

        # The embedding [0.1, 0.2, 0.3] is identical to the query embedding,
        # so similarity should be 1.0, which is > 0.5 threshold
        assert len(results) >= 1
        assert results[0]["question_text"] == "What is the price?"

    async def test_search_filters_low_similarity(self, learning_loop: LearningLoop):
        """Results with similarity <= 0.5 are excluded."""
        from types import SimpleNamespace

        doc_id = uuid4()
        mock_row = SimpleNamespace(
            id=doc_id,
            question_text="Unrelated",
            answer_text="Unrelated answer.",
            source_type="human_answer",
            source_escalation_id=None,
            created_at=None,
            embedding=[3.0, 0.0, -1.0],
            similarity=0.2,
        )

        mock_result = MagicMock()
        mock_result.fetchall.return_value = [mock_row]

        mock_session = AsyncMock()
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        learning_loop._engine = MagicMock()

        with patch("sqlalchemy.ext.asyncio.AsyncSession", return_value=mock_session):
            results = await learning_loop.search_learned_answers(
                tenant_id=uuid4(),
                query="What is the price?",
            )

        assert len(results) == 0
