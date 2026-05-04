"""Unit tests for sequor.email.auto_reply.

Tests the AutoReplyService orchestration with all mocks, covering the full
pipeline (classify -> generate -> auto-reply / escalate) and the _mask_email
helper.
"""

from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from sequor.ai.classifier import ClassificationResult, MessageCategory, MessageUrgency
from sequor.ai.rag_pipeline import SynthesisResult
from sequor.ai.response import ResponseResult
from sequor.email.auto_reply import (
    AutoReplyResult,
    AutoReplyService,
    MessageContext,
    _mask_email,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _context(body_text: str = "What are your hours?") -> MessageContext:
    """Build a MessageContext for testing."""
    return MessageContext(
        tenant_id=uuid4(),
        account_id=uuid4(),
        contact_email="john@example.com",
        message_id=uuid4(),
        subject="Inquiry",
        body_text=body_text,
        channel="email",
        external_message_id="msg-123",
        in_reply_to=None,
    )


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


def _response(
    was_auto_sent: bool = True,
    escalation_needed: bool = False,
    confidence: float = 0.92,
    badge: str = "high",
) -> ResponseResult:
    """Build a ResponseResult for testing."""
    return ResponseResult(
        content="Our hours are 9am to 5pm.",
        confidence_badge=badge,
        confidence_score=confidence,
        was_auto_sent=was_auto_sent,
        sources=[],
        routing_target="auto_respond" if was_auto_sent else "escalation_queue",
        escalation_needed=escalation_needed,
    )


@pytest.fixture
def mock_classifier():
    """Create a mock MessageClassifier."""
    classifier = AsyncMock()
    classifier.classify = AsyncMock(return_value=_classification())
    return classifier


@pytest.fixture
def mock_rag():
    """Create a mock RAGPipeline."""
    return AsyncMock()


@pytest.fixture
def mock_email_sender():
    """Create a mock EmailSender that satisfies the runtime_checkable Protocol."""
    from sequor.protocols import EmailSender

    sender = AsyncMock(spec=EmailSender)
    sender.send_email = AsyncMock(return_value="sent-msg-id")
    sender.send_escalation_email = AsyncMock(return_value="sent-esc-id")
    return sender


@pytest.fixture
def mock_response_gen():
    """Create a mock ResponseGenerator."""
    gen = AsyncMock()
    gen.generate = AsyncMock(return_value=_response())
    return gen


@pytest.fixture
def service(mock_classifier, mock_rag, mock_email_sender, mock_response_gen):
    """Create an AutoReplyService with all mock dependencies."""
    return AutoReplyService(
        classifier=mock_classifier,
        rag_pipeline=mock_rag,
        email_sender=mock_email_sender,
        response_generator=mock_response_gen,
    )


# ---------------------------------------------------------------------------
# Full pipeline: high confidence -> auto-reply
# ---------------------------------------------------------------------------


async def test_high_confidence_auto_reply(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
    mock_email_sender,
):
    """High confidence routine message triggers auto-reply email."""
    mock_classifier.classify.return_value = _classification(
        category="routine", confidence=0.95
    )
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=True,
        escalation_needed=False,
        confidence=0.92,
        badge="high",
    )

    # Patch _record_response to avoid database
    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
        mock_record.return_value = uuid4()

        result = await service.process_message(_context())

    assert result.response_recorded is True
    assert result.email_sent is True
    assert result.escalated is False
    assert result.confidence_badge == "high"
    mock_email_sender.send_email.assert_called_once()


# ---------------------------------------------------------------------------
# Full pipeline: low confidence -> escalation
# ---------------------------------------------------------------------------


async def test_low_confidence_escalation(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
    mock_email_sender,
):
    """Low confidence message triggers escalation without auto-reply."""
    mock_classifier.classify.return_value = _classification(
        category="complex", confidence=0.4
    )
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=False,
        escalation_needed=True,
        confidence=0.3,
        badge="uncertain",
    )

    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record, \
         patch.object(service, "_create_escalation", new_callable=AsyncMock) as mock_escalation:
        mock_record.return_value = uuid4()
        mock_escalation.return_value = uuid4()

        result = await service.process_message(_context())

    assert result.response_recorded is True
    assert result.escalated is True
    assert result.email_sent is False
    mock_email_sender.send_email.assert_not_called()


# ---------------------------------------------------------------------------
# High stakes -> forced escalation
# ---------------------------------------------------------------------------


async def test_high_stakes_forced_escalation(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
    mock_email_sender,
):
    """High-stakes messages always escalate regardless of confidence."""
    mock_classifier.classify.return_value = _classification(
        category="high_stakes", confidence=0.99
    )
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=False,
        escalation_needed=True,
        confidence=0.0,
        badge="uncertain",
    )

    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record, \
         patch.object(service, "_create_escalation", new_callable=AsyncMock) as mock_escalation:
        mock_record.return_value = uuid4()
        mock_escalation.return_value = uuid4()

        result = await service.process_message(_context("I need a legal review."))

    assert result.escalated is True
    assert result.email_sent is False


# ---------------------------------------------------------------------------
# Pipeline exception handling
# ---------------------------------------------------------------------------


async def test_pipeline_exception_returns_error_result(
    service: AutoReplyService,
    mock_classifier,
):
    """When the pipeline throws, the result indicates failure with escalation."""
    mock_classifier.classify.side_effect = RuntimeError("Service unavailable")

    result = await service.process_message(_context())

    assert result.response_recorded is False
    assert result.escalated is True
    assert result.error is not None
    assert "Service unavailable" in result.error


# ---------------------------------------------------------------------------
# Auto-reply email send failure
# ---------------------------------------------------------------------------


async def test_auto_reply_email_send_failure(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
    mock_email_sender,
):
    """When email send fails, email_sent is False but response is recorded."""
    mock_classifier.classify.return_value = _classification(confidence=0.95)
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=True, escalation_needed=False
    )
    mock_email_sender.send_email.side_effect = RuntimeError("SMTP error")

    # _send_auto_reply catches the exception and returns False
    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
        mock_record.return_value = uuid4()

        result = await service.process_message(_context())

    # Email was attempted but failed, so email_sent should be False
    assert result.email_sent is False


# ---------------------------------------------------------------------------
# Confidence threshold override
# ---------------------------------------------------------------------------


async def test_custom_confidence_threshold(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
    mock_email_sender,
):
    """A higher custom threshold can prevent auto-reply even with high confidence."""
    mock_classifier.classify.return_value = _classification(confidence=0.92)
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=True, escalation_needed=False, confidence=0.92, badge="high"
    )

    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
        mock_record.return_value = uuid4()

        # Default threshold is 0.90; setting 0.99 should prevent sending
        result = await service.process_message(_context(), confidence_threshold=0.99)

    assert result.email_sent is False


# ---------------------------------------------------------------------------
# _mask_email helper
# ---------------------------------------------------------------------------


class TestMaskEmail:
    """Tests for the _mask_email helper function."""

    def test_normal_email(self):
        """Standard email masks the middle of the local part."""
        assert _mask_email("john@example.com") == "j***@example.com"

    def test_short_local_part(self):
        """Short local part (<= 2 chars) masks everything."""
        assert _mask_email("ab@example.com") == "***@example.com"

    def test_single_char_local(self):
        """Single-character local part masks everything."""
        assert _mask_email("a@example.com") == "***@example.com"

    def test_no_at_sign(self):
        """String without @ returns '***'."""
        assert _mask_email("notanemail") == "***"

    def test_empty_string(self):
        """Empty string returns '***'."""
        assert _mask_email("") == "***"

    def test_long_email(self):
        """Long email masks only the middle."""
        result = _mask_email("longusername@company.org")
        assert result.startswith("l")
        assert "***@" in result
        assert "company.org" in result


# ---------------------------------------------------------------------------
# _should_use_learning
# ---------------------------------------------------------------------------


def test_should_use_learning_routine_high_confidence(service: AutoReplyService):
    """Learning is used for routine messages with confidence >= 0.6."""
    classification = _classification(category="routine", confidence=0.7)
    assert service._should_use_learning(classification) is True


def test_should_use_learning_complex_blocked(service: AutoReplyService):
    """Learning is not used for complex messages."""
    classification = _classification(category="complex", confidence=0.8)
    assert service._should_use_learning(classification) is False


def test_should_use_learning_low_confidence_blocked(service: AutoReplyService):
    """Learning is not used when confidence < 0.6."""
    classification = _classification(category="routine", confidence=0.5)
    assert service._should_use_learning(classification) is False


# ---------------------------------------------------------------------------
# Learning loop integration in process_message
# ---------------------------------------------------------------------------


async def test_learning_loop_queried_when_available(
    mock_classifier, mock_rag, mock_email_sender, mock_response_gen,
):
    """When a LearningLoop is provided, search_learned_answers is called."""
    mock_learning = AsyncMock()
    mock_learning.search_learned_answers = AsyncMock(return_value=[])

    service = AutoReplyService(
        classifier=mock_classifier,
        rag_pipeline=mock_rag,
        email_sender=mock_email_sender,
        response_generator=mock_response_gen,
        learning_loop=mock_learning,
    )

    mock_classifier.classify.return_value = _classification(
        category="routine", confidence=0.8
    )
    mock_response_gen.generate.return_value = _response(
        was_auto_sent=True, escalation_needed=False
    )

    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
        mock_record.return_value = uuid4()
        await service.process_message(_context())

    mock_learning.search_learned_answers.assert_called_once()


async def test_learning_loop_not_queried_when_none(
    service: AutoReplyService,
    mock_classifier,
    mock_response_gen,
):
    """When no LearningLoop is provided, learned answers are not queried."""
    assert service._learning is None

    with patch.object(service, "_record_response", new_callable=AsyncMock) as mock_record:
        mock_record.return_value = uuid4()
        await service.process_message(_context())

    # No errors, just skipped learning


# ---------------------------------------------------------------------------
# AutoReplyResult structure
# ---------------------------------------------------------------------------


def test_auto_reply_result_defaults():
    """AutoReplyResult has correct default values."""
    result = AutoReplyResult(
        response_recorded=True,
        email_sent=True,
        escalated=False,
        escalation_id=None,
        response_id=None,
        confidence_badge="high",
        confidence_score=0.92,
        routing_target="auto_respond",
        error=None,
    )

    assert result.response_recorded is True
    assert result.email_sent is True
    assert result.escalated is False
    assert result.error is None
