"""Unit tests for sequor.ai.vector_store.

Tests the pure computation methods (_cosine_similarity, _compute_bm25,
_tokenize) and the search method's empty-results path. No database required.
"""

import math
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from sequor.ai.vector_store import VectorStore


@pytest.fixture
def store():
    """Create a VectorStore with a mock engine (no database calls in these tests)."""
    mock_engine = MagicMock()
    return VectorStore(engine=mock_engine)


# ---------------------------------------------------------------------------
# _cosine_similarity
# ---------------------------------------------------------------------------


class TestCosineSimilarity:
    """Tests for the cosine similarity computation."""

    def test_identical_vectors(self, store: VectorStore):
        """Identical unit vectors have similarity 1.0."""
        a = [1.0, 0.0, 0.0]
        b = [1.0, 0.0, 0.0]
        result = store._cosine_similarity(a, b)
        assert result == pytest.approx(1.0)

    def test_orthogonal_vectors(self, store: VectorStore):
        """Orthogonal vectors have similarity 0.0."""
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        result = store._cosine_similarity(a, b)
        assert result == pytest.approx(0.0)

    def test_opposite_vectors(self, store: VectorStore):
        """Opposite vectors have similarity -1.0."""
        a = [1.0, 0.0]
        b = [-1.0, 0.0]
        result = store._cosine_similarity(a, b)
        assert result == pytest.approx(-1.0)

    def test_known_similarity(self, store: VectorStore):
        """Known vectors produce the expected similarity value."""
        a = [1.0, 2.0, 3.0]
        b = [4.0, 5.0, 6.0]
        # dot = 4+10+18=32, mag_a = sqrt(14), mag_b = sqrt(77)
        expected = 32.0 / (math.sqrt(14) * math.sqrt(77))
        result = store._cosine_similarity(a, b)
        assert result == pytest.approx(expected, rel=1e-6)

    def test_zero_vector_returns_zero(self, store: VectorStore):
        """Zero vector has similarity 0.0 with any vector."""
        result = store._cosine_similarity([0.0, 0.0], [1.0, 1.0])
        assert result == 0.0

    def test_mismatched_lengths_returns_zero(self, store: VectorStore):
        """Vectors of different lengths return 0.0."""
        result = store._cosine_similarity([1.0, 2.0], [1.0, 2.0, 3.0])
        assert result == 0.0

    def test_single_element_vectors(self, store: VectorStore):
        """Single-element vectors work correctly."""
        result = store._cosine_similarity([3.0], [4.0])
        assert result == pytest.approx(1.0)  # same direction


# ---------------------------------------------------------------------------
# _tokenize
# ---------------------------------------------------------------------------


class TestTokenize:
    """Tests for the tokenization helper."""

    def test_simple_text(self, store: VectorStore):
        """Simple lowercase text is tokenized into words."""
        tokens = store._tokenize("hello world test")
        assert tokens == ["hello", "world", "test"]

    def test_uppercase_converted(self, store: VectorStore):
        """Uppercase text is lowercased."""
        tokens = store._tokenize("HELLO World")
        assert tokens == ["hello", "world"]

    def test_special_characters_stripped(self, store: VectorStore):
        """Punctuation and special characters are removed."""
        tokens = store._tokenize("hello, world! how's it going?")
        assert "hello" in tokens
        assert "world" in tokens
        assert "how" in tokens
        assert "s" in tokens  # "how's" splits into "how" and "s"

    def test_numbers_preserved(self, store: VectorStore):
        """Numbers are preserved as tokens."""
        tokens = store._tokenize("order 123 and item 456")
        assert "123" in tokens
        assert "456" in tokens

    def test_empty_string(self, store: VectorStore):
        """Empty string produces no tokens."""
        tokens = store._tokenize("")
        assert tokens == []

    def test_only_special_chars(self, store: VectorStore):
        """Text with only special characters produces no tokens."""
        tokens = store._tokenize("!@#$%^&*()")
        assert tokens == []


# ---------------------------------------------------------------------------
# _compute_bm25
# ---------------------------------------------------------------------------


class TestComputeBM25:
    """Tests for BM25 scoring."""

    def _make_chunk(self, text: str):
        """Create a chunk-like object for BM25 testing."""
        return SimpleNamespace(
            id=uuid4(),
            chunk_text=text,
        )

    def test_empty_chunks_returns_empty(self, store: VectorStore):
        """Empty chunk list returns empty scores."""
        scores = store._compute_bm25([], "test query")
        assert scores == {}

    def test_matching_query_scores_higher(self, store: VectorStore):
        """Chunks containing query terms score higher than unrelated ones."""
        matching = self._make_chunk("pricing information about our plans")
        unrelated = self._make_chunk("weather forecast for today")
        scores = store._compute_bm25([matching, unrelated], "pricing plans")

        match_score = scores[str(matching.id)]
        unrel_score = scores[str(unrelated.id)]
        assert match_score > unrel_score

    def test_scores_normalized(self, store: VectorStore):
        """BM25 scores are normalized (max score = 1.0 when there are differences)."""
        good = self._make_chunk("the quick brown fox jumps over the lazy dog")
        bad = self._make_chunk("completely unrelated text about nothing relevant")
        scores = store._compute_bm25([good, bad], "quick brown fox")

        # At least one score should be > 0; max should be 1.0
        if max(scores.values()) > 0:
            assert max(scores.values()) == pytest.approx(1.0)

    def test_no_query_terms_returns_zero(self, store: VectorStore):
        """Query terms not in any chunk produce zero scores."""
        chunk = self._make_chunk("alpha beta gamma")
        scores = store._compute_bm25([chunk], "delta epsilon")
        assert all(v == pytest.approx(0.0) for v in scores.values())


# ---------------------------------------------------------------------------
# search with empty results
# ---------------------------------------------------------------------------


class TestSearchEmptyResults:
    """Tests for the search method when no chunks exist."""

    async def test_search_returns_empty_when_no_chunks(self, store: VectorStore):
        """Search with no stored chunks returns an empty list."""
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_session.execute = AsyncMock(return_value=mock_result)
        mock_session.__aenter__ = AsyncMock(return_value=mock_session)
        mock_session.__aexit__ = AsyncMock(return_value=False)

        with patch("sqlalchemy.ext.asyncio.AsyncSession", return_value=mock_session):
            results = await store.search(
                tenant_id=uuid4(),
                query_embedding=[0.1, 0.2, 0.3],
                query_text="test query",
            )

        assert results == []
