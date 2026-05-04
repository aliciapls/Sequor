"""Unit tests for sequor.ai.classifier.

Tests message classification with a mock LLM client, covering all categories,
urgency levels, confidence scoring, and fallback behavior.
"""

import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest

from sequor.ai.classifier import (
    ClassificationResult,
    MessageCategory,
    MessageClassifier,
    MessageUrgency,
)


def _make_mock_llm(response_text: str) -> AsyncMock:
    """Create a mock LLM client that returns the given response."""
    mock = AsyncMock()
    mock.generate = AsyncMock(return_value=response_text)
    return mock


def _classification_json(
    category: str = "routine",
    urgency: str = "low",
    confidence: float = 0.85,
    reasoning: str = "Test reasoning",
) -> str:
    """Build a valid classification JSON response string."""
    return json.dumps({
        "category": category,
        "urgency": urgency,
        "confidence": confidence,
        "reasoning": reasoning,
    })


# ---------------------------------------------------------------------------
# Parsing and category coverage
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "category",
    ["routine", "semi_routine", "complex", "high_stakes"],
)
async def test_classify_all_categories(category: str):
    """All four message categories are parsed correctly."""
    llm = _make_mock_llm(_classification_json(category=category))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")

    assert result.category == MessageCategory(category)


@pytest.mark.parametrize(
    "urgency",
    ["low", "medium", "high", "critical"],
)
async def test_classify_all_urgency_levels(urgency: str):
    """All four urgency levels are parsed correctly."""
    llm = _make_mock_llm(_classification_json(urgency=urgency))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")

    assert result.urgency == MessageUrgency(urgency)


# ---------------------------------------------------------------------------
# Confidence score clamping
# ---------------------------------------------------------------------------


async def test_confidence_clamped_to_range():
    """Confidence values outside [0.0, 1.0] are clamped."""
    llm = _make_mock_llm(_classification_json(confidence=1.5))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.confidence <= 1.0

    llm_neg = _make_mock_llm(_classification_json(confidence=-0.3))
    classifier_neg = MessageClassifier(llm_client=llm_neg)

    result_neg = await classifier_neg.classify(uuid4(), "test message")
    assert result_neg.confidence >= 0.0


async def test_confidence_valid_values():
    """Valid confidence values in [0.0, 1.0] pass through unchanged."""
    llm = _make_mock_llm(_classification_json(confidence=0.75))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.confidence == pytest.approx(0.75)


# ---------------------------------------------------------------------------
# Fallback behavior when LLM fails
# ---------------------------------------------------------------------------


async def test_fallback_on_llm_exception():
    """When the LLM raises an exception, the classifier falls back to semi_routine/medium."""
    llm = AsyncMock()
    llm.generate = AsyncMock(side_effect=RuntimeError("LLM unavailable"))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")

    assert result.category == MessageCategory.SEMI_ROUTINE
    assert result.urgency == MessageUrgency.MEDIUM
    assert result.confidence == 0.0
    assert "Classification failed" in result.reasoning


async def test_fallback_on_invalid_category():
    """When the LLM returns an unknown category, it defaults to semi_routine."""
    llm = _make_mock_llm(_classification_json(category="unknown_category"))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.category == MessageCategory.SEMI_ROUTINE


async def test_fallback_on_invalid_urgency():
    """When the LLM returns an unknown urgency, it defaults to medium."""
    llm = _make_mock_llm(_classification_json(urgency="immediate"))
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.urgency == MessageUrgency.MEDIUM


# ---------------------------------------------------------------------------
# Malformed response parsing
# ---------------------------------------------------------------------------


async def test_parse_malformed_json_with_regex_fallback():
    """When JSON is malformed, the parser uses regex extraction."""
    # Response with no valid JSON wrapper but extractable fields
    malformed = (
        'Here is my classification:\n'
        '"category": "complex", "urgency": "high", '
        '"confidence": 0.6, "reasoning": "Needs human review"'
    )
    llm = _make_mock_llm(malformed)
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.category == MessageCategory.COMPLEX
    assert result.urgency == MessageUrgency.HIGH


async def test_parse_json_wrapped_in_markdown():
    """Classification JSON wrapped in markdown code fences is extracted."""
    response = '```json\n{"category": "routine", "urgency": "low", "confidence": 0.9, "reasoning": "FAQ"}\n```'
    llm = _make_mock_llm(response)
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")
    assert result.category == MessageCategory.ROUTINE
    assert result.urgency == MessageUrgency.LOW


# ---------------------------------------------------------------------------
# Response metadata
# ---------------------------------------------------------------------------


async def test_classification_result_metadata():
    """ClassificationResult includes version and timestamp."""
    llm = _make_mock_llm(_classification_json())
    classifier = MessageClassifier(llm_client=llm)

    result = await classifier.classify(uuid4(), "test message")

    assert result.classifier_version == "1.0.0"
    assert isinstance(result.classified_at, datetime)
    assert result.classified_at.tzinfo is not None


# ---------------------------------------------------------------------------
# Routing helpers
# ---------------------------------------------------------------------------


def test_should_use_rag_high_confidence_routine():
    """RAG is used when confidence > 0.6 and category is not high_stakes."""
    classification = ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.LOW,
        confidence=0.8,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_use_rag(classification) is True


def test_should_use_rag_high_stakes_blocked():
    """RAG is NOT used for high_stakes messages regardless of confidence."""
    classification = ClassificationResult(
        category=MessageCategory.HIGH_STAKES,
        urgency=MessageUrgency.LOW,
        confidence=0.95,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_use_rag(classification) is False


def test_should_use_rag_low_confidence_blocked():
    """RAG is NOT used when confidence <= 0.6."""
    classification = ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.LOW,
        confidence=0.5,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_use_rag(classification) is False


def test_should_auto_respond_routine_high_confidence():
    """Auto-respond is True for routine + low urgency + confidence >= 0.9."""
    classification = ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.LOW,
        confidence=0.95,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_auto_respond(classification) is True


def test_should_auto_respond_high_stakes_blocked():
    """Auto-respond is blocked for high_stakes even with high confidence."""
    classification = ClassificationResult(
        category=MessageCategory.HIGH_STAKES,
        urgency=MessageUrgency.LOW,
        confidence=0.95,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_auto_respond(classification) is False


def test_should_auto_respond_critical_urgency_blocked():
    """Auto-respond is blocked for critical urgency even when routine."""
    classification = ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.CRITICAL,
        confidence=0.95,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_auto_respond(classification) is False


def test_should_auto_respond_below_threshold():
    """Auto-respond is blocked when confidence < threshold."""
    classification = ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.LOW,
        confidence=0.85,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )
    classifier = MessageClassifier(llm_client=AsyncMock())
    assert classifier.should_auto_respond(classification) is False


# ---------------------------------------------------------------------------
# Prompt building
# ---------------------------------------------------------------------------


def test_build_classification_prompt_includes_context():
    """The classification prompt includes context when provided."""
    classifier = MessageClassifier(llm_client=AsyncMock())

    prompt = classifier._build_classification_prompt(
        message_text="What are your hours?",
        channel="email",
        context={
            "contact_history": ["msg1", "msg2"],
            "account_type": "premium",
            "document_types": ["faq.pdf", "policy.docx"],
        },
    )

    assert "2 previous messages" in prompt
    assert "premium" in prompt
    assert "faq.pdf" in prompt
    assert "email" in prompt


def test_build_classification_prompt_no_context():
    """The classification prompt works without context."""
    classifier = MessageClassifier(llm_client=AsyncMock())

    prompt = classifier._build_classification_prompt(
        message_text="Hello",
        channel="whatsapp",
        context=None,
    )

    assert "whatsapp" in prompt
    assert "Hello" in prompt
