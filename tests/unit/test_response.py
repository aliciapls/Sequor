"""Unit tests for sequor.ai.response.

Tests response generation routing: auto-reply for high-confidence routine
messages, escalation for low-confidence, and forced escalation for high_stakes.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from sequor.ai.classifier import ClassificationResult, MessageCategory, MessageUrgency
from sequor.ai.rag_pipeline import SynthesisResult
from sequor.ai.response import ResponseGenerator, ResponseResult


def _classification(
    category: str = "routine",
    urgency: str = "low",
    confidence: float = 0.95,
) -> ClassificationResult:
    """Build a ClassificationResult for testing."""
    return ClassificationResult(
        category=MessageCategory(category),
        urgency=MessageUrgency(urgency),
        confidence=confidence,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )


def _synthesis(
    answer: str = "Here is the answer.",
    confidence: float = 0.92,
    badge: str = "high",
    hallucination_passed: bool = True,
) -> SynthesisResult:
    """Build a SynthesisResult for testing."""
    return SynthesisResult(
        answer=answer,
        sources=[{"chunk_id": str(uuid4()), "document_id": str(uuid4())}],
        confidence=confidence,
        confidence_badge=badge,
        hallucination_check_passed=hallucination_passed,
        uncited_claims=0,
    )


@pytest.fixture
def mock_rag():
    """Create a mock RAGPipeline."""
    rag = AsyncMock()
    rag.query = AsyncMock(return_value=_synthesis())
    return rag


@pytest.fixture
def generator(mock_rag):
    """Create a ResponseGenerator with a mock RAG pipeline."""
    return ResponseGenerator(rag_pipeline=mock_rag)


# ---------------------------------------------------------------------------
# High confidence + routine -> auto-reply
# ---------------------------------------------------------------------------


async def test_routine_high_confidence_auto_reply(generator: ResponseGenerator, mock_rag):
    """Routine message with confidence >= 0.9 and good synthesis is auto-replied."""
    classification = _classification(category="routine", confidence=0.95)
    mock_rag.query.return_value = _synthesis(badge="high", confidence=0.92)

    result = await generator.generate(uuid4(), "What are your hours?", classification)

    assert result.was_auto_sent is True
    assert result.routing_target == "auto_respond"
    assert result.escalation_needed is False


async def test_semi_routine_high_confidence_auto_reply(generator: ResponseGenerator, mock_rag):
    """Semi-routine with high unified confidence (both classifier AND synthesis >= threshold)
    is auto-replied — A3 unification requires the weaker of the two to clear the gate."""
    classification = _classification(category="semi_routine", confidence=0.92)
    mock_rag.query.return_value = _synthesis(badge="moderate", confidence=0.92)

    result = await generator.generate(uuid4(), "Can you help with X?", classification)

    assert result.was_auto_sent is True
    assert result.routing_target == "auto_respond"


# ---------------------------------------------------------------------------
# Low confidence -> escalation
# ---------------------------------------------------------------------------


async def test_low_confidence_escalation(generator: ResponseGenerator, mock_rag):
    """Low classification confidence triggers escalation without AI draft."""
    classification = _classification(category="routine", confidence=0.3)
    mock_rag.query.return_value = _synthesis(badge="uncertain", confidence=0.2)

    result = await generator.generate(uuid4(), "Unclear question", classification)

    assert result.was_auto_sent is False
    assert result.escalation_needed is True
    assert result.routing_target == "escalation_queue"


async def test_moderate_confidence_escalation_with_draft(generator: ResponseGenerator, mock_rag):
    """Moderate confidence triggers escalation WITH an AI draft for review."""
    classification = _classification(category="semi_routine", confidence=0.7)
    mock_rag.query.return_value = _synthesis(badge="moderate", confidence=0.75)

    result = await generator.generate(uuid4(), "A question", classification)

    assert result.was_auto_sent is False
    assert result.escalation_needed is True
    assert result.routing_target == "escalation_queue"
    # The AI draft should be available for review
    assert result.content != ""


# ---------------------------------------------------------------------------
# High stakes -> always escalate
# ---------------------------------------------------------------------------


async def test_high_stakes_forces_escalation(generator: ResponseGenerator):
    """High-stakes messages are ALWAYS escalated regardless of confidence."""
    classification = _classification(category="high_stakes", confidence=0.99)

    result = await generator.generate(uuid4(), "I need a refund for $5000", classification)

    assert result.was_auto_sent is False
    assert result.escalation_needed is True
    assert result.escalation_has_ai_draft is False
    assert result.routing_target == "escalation_queue"
    assert "personal attention" in result.content.lower()


# ---------------------------------------------------------------------------
# Urgent messages
# ---------------------------------------------------------------------------


async def test_high_urgency_escalation(generator: ResponseGenerator):
    """High urgency messages are escalated with priority."""
    classification = _classification(urgency="high", confidence=0.8)

    result = await generator.generate(uuid4(), "Urgent issue", classification)

    assert result.escalation_needed is True
    assert result.was_auto_sent is False
    assert "urgent" in result.content.lower() or "prioritized" in result.content.lower()


async def test_critical_urgency_escalation(generator: ResponseGenerator):
    """Critical urgency messages are escalated immediately."""
    classification = _classification(urgency="critical", confidence=0.85)

    result = await generator.generate(uuid4(), "Emergency", classification)

    assert result.escalation_needed is True
    assert result.was_auto_sent is False


# ---------------------------------------------------------------------------
# Complex category
# ---------------------------------------------------------------------------


async def test_complex_category_never_auto_sent(generator: ResponseGenerator, mock_rag):
    """Complex messages are never auto-sent, even with high confidence."""
    classification = _classification(category="complex", confidence=0.95)
    mock_rag.query.return_value = _synthesis(badge="high", confidence=0.92)

    result = await generator.generate(uuid4(), "Complex question", classification)

    assert result.was_auto_sent is False


# ---------------------------------------------------------------------------
# Learned answers
# ---------------------------------------------------------------------------


async def test_learned_answers_used(generator: ResponseGenerator):
    """When learned answers are available, they are used for response."""
    classification = _classification(category="routine", confidence=0.9)
    learned = [
        {
            "id": uuid4(),
            "answer_text": "The answer from human is 42.",
            "similarity": 0.9,
        }
    ]

    result = await generator.generate(
        uuid4(), "What is the answer?", classification, learned_answers=learned
    )

    assert "42" in result.content


async def test_learned_answer_high_similarity_auto_sent(generator: ResponseGenerator):
    """Learned answer with high similarity and routine category triggers auto-reply."""
    classification = _classification(category="routine", confidence=0.9)
    learned = [
        {
            "id": uuid4(),
            "answer_text": "Our hours are 9-5.",
            "similarity": 0.9,
        }
    ]

    result = await generator.generate(
        uuid4(), "What are your hours?", classification, learned_answers=learned
    )

    assert result.was_auto_sent is True


async def test_learned_answer_low_classifier_high_similarity_auto_sent(
    generator: ResponseGenerator,
):
    """Security-review H1: learned-answer path intentionally uses similarity alone
    (not min(classifier, similarity)) because a human-verified answer is more
    trustworthy than an uncertain classifier. A message with classifier=0.2 +
    similarity=0.92 auto-sends — the human already approved this answer."""
    classification = _classification(category="routine", confidence=0.2)
    learned = [
        {
            "id": uuid4(),
            "answer_text": "Human-verified answer.",
            "similarity": 0.92,
        }
    ]

    result = await generator.generate(
        uuid4(), "matching query", classification, learned_answers=learned
    )

    # similarity 0.92 >= 0.90 → auto-send; classifier's 0.2 is intentionally
    # not factored in (human-verified answer trumps uncertain classifier)
    assert result.was_auto_sent is True


async def test_learned_answer_badge_assignment_high(generator: ResponseGenerator):
    """Learned answer with similarity >= 0.95 gets 'high' badge (A3 spec-table thresholds:
    >=0.95 high, >=0.80 moderate, >=0.60 low)."""
    classification = _classification(category="routine", confidence=0.95)
    learned = [
        {
            "id": uuid4(),
            "answer_text": "Confirmed answer.",
            "similarity": 0.96,
        }
    ]

    result = await generator.generate(uuid4(), "test", classification, learned_answers=learned)

    assert result.confidence_badge == "high"


async def test_learned_answer_badge_moderate(generator: ResponseGenerator):
    """Learned answer with similarity >= 0.80 gets 'moderate' badge (A3 spec-table)."""
    classification = _classification(category="routine", confidence=0.85)
    learned = [
        {
            "id": uuid4(),
            "answer_text": "Partial answer.",
            "similarity": 0.85,
        }
    ]

    result = await generator.generate(uuid4(), "test", classification, learned_answers=learned)

    assert result.confidence_badge == "moderate"


# ---------------------------------------------------------------------------
# Low synthesis score
# ---------------------------------------------------------------------------


async def test_uncertain_synthesis_prevents_auto_reply(generator: ResponseGenerator, mock_rag):
    """Uncertain synthesis confidence prevents auto-reply even with high classification."""
    classification = _classification(category="routine", confidence=0.95)
    mock_rag.query.return_value = _synthesis(badge="uncertain", confidence=0.2)

    result = await generator.generate(uuid4(), "Unclear question", classification)

    assert result.was_auto_sent is False


# ---------------------------------------------------------------------------
# A3 unification regression — the core bug (plan §2.5a)
# ---------------------------------------------------------------------------


async def test_confident_classifier_uncertain_synthesis_not_auto_sent(
    generator: ResponseGenerator, mock_rag
):
    """A3 core bug: classifier 0.95 + synthesis 0.3 MUST NOT auto-send.
    Pre-A3 the gate keyed off classification.confidence (0.95 >= 0.90 → send),
    while the badge showed synthesis 0.3 → uncertain. The unified quantity
    min(0.95, 0.3) = 0.3 < 0.90 correctly blocks the send."""
    classification = _classification(category="routine", confidence=0.95)
    mock_rag.query.return_value = _synthesis(badge="uncertain", confidence=0.3)

    result = await generator.generate(uuid4(), "risky question", classification)

    assert result.was_auto_sent is False
    assert result.escalation_needed is True
    assert result.routing_target == "escalation_queue"


async def test_unified_confidence_0_92_auto_sends_with_moderate_badge(
    generator: ResponseGenerator, mock_rag
):
    """Plan §2.5b: unified 0.92 >= 0.90 → auto-send with 'moderate' badge
    (0.92 < 0.95 so badge is moderate, not high)."""
    classification = _classification(category="routine", confidence=0.92)
    mock_rag.query.return_value = _synthesis(badge="moderate", confidence=0.92)

    result = await generator.generate(uuid4(), "hours question", classification)

    assert result.was_auto_sent is True
    assert result.confidence_badge == "moderate"
    assert result.routing_target == "auto_respond"


async def test_account_confidence_threshold_0_95_blocks_0_92(
    generator: ResponseGenerator, mock_rag
):
    """Plan §2.5d: Account.confidence_threshold=0.95 blocks unified 0.92."""
    classification = _classification(category="routine", confidence=0.92)
    mock_rag.query.return_value = _synthesis(badge="moderate", confidence=0.92)

    result = await generator.generate(
        uuid4(), "hours question", classification, confidence_threshold=0.95
    )

    assert result.was_auto_sent is False
    assert result.escalation_needed is True


# ---------------------------------------------------------------------------
# ResponseResult structure
# ---------------------------------------------------------------------------


def test_response_result_fields():
    """ResponseResult has all expected fields."""
    result = ResponseResult(
        content="Test answer",
        confidence_badge="high",
        confidence_score=0.92,
        was_auto_sent=True,
        sources=[{"type": "doc"}],
        routing_target="auto_respond",
        escalation_needed=False,
    )

    assert result.content == "Test answer"
    assert result.confidence_badge == "high"
    assert result.was_auto_sent is True
    assert result.escalation_needed is False
    assert result.escalation_has_ai_draft is False  # default
