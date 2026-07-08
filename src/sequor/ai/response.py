"""Response generation with confidence scoring.

Generates AI responses using RAG retrieval and synthesizes with confidence badges.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

from sequor.ai.classifier import (
    ClassificationResult,
    MessageCategory,
    MessageClassifier,
    MessageUrgency,
)
from sequor.ai.learning import LearningLoop
from sequor.ai.rag_pipeline import RAGPipeline

logger = structlog.get_logger()


def _badge_for(confidence: float) -> str:
    """Map a unified response confidence to the spec badge level
    (``response-accuracy.md`` §Badge Levels): >=0.95 high, >=0.80 moderate,
    >=0.60 low, else uncertain. Both the auto-send gate and the rendered badge
    read the SAME ``response_confidence`` (A3 unification) — this function fixes
    the badge-render side of that agreement."""
    if confidence >= 0.95:
        return "high"
    if confidence >= 0.80:
        return "moderate"
    if confidence >= 0.60:
        return "low"
    return "uncertain"


@dataclass
class ResponseResult:
    """Result of response generation."""

    content: str
    confidence_badge: str
    confidence_score: float
    was_auto_sent: bool
    sources: list[dict]
    routing_target: str
    escalation_needed: bool
    escalation_has_ai_draft: bool = False


class ResponseGenerator:
    """Generates AI responses with confidence scoring.

    Combines:
    - RAG retrieval and synthesis
    - Learned answers from human escalations
    - Classification-based routing decisions
    """

    def __init__(
        self,
        rag_pipeline: RAGPipeline,
        learning_loop: LearningLoop | None = None,
        llm_client: Any | None = None,
    ) -> None:
        """Initialize the response generator.

        Args:
            rag_pipeline: RAGPipeline for document retrieval
            learning_loop: Optional LearningLoop for learned answers
            llm_client: OllamaClient for direct LLM calls
        """
        self._rag = rag_pipeline
        self._learning = learning_loop
        self._llm = llm_client

    async def generate(
        self,
        tenant_id: UUID,
        message_text: str,
        classification: ClassificationResult,
        learned_answers: list[dict] | None = None,
        system_instructions: str | None = None,
        confidence_threshold: float = 0.90,
    ) -> ResponseResult:
        """Generate a response for a classified message.

        Args:
            tenant_id: Tenant ID
            message_text: The user's message
            classification: Classification result
            learned_answers: Optional pre-fetched learned answers
            system_instructions: Optional system prompt additions

        Returns:
            ResponseResult with content, confidence, and routing decision
        """
        logger.info(
            "response.generate.start",
            tenant_id=str(tenant_id),
            category=classification.category.value,
            confidence=classification.confidence,
        )

        if classification.category == MessageCategory.HIGH_STAKES:
            return await self._handle_high_stakes(tenant_id, message_text, classification)

        if classification.urgency in [MessageUrgency.HIGH, MessageUrgency.CRITICAL]:
            return await self._handle_urgent(tenant_id, message_text, classification)

        if learned_answers and len(learned_answers) > 0:
            return await self._generate_from_learned(
                tenant_id, message_text, classification, learned_answers, confidence_threshold
            )

        synthesis = await self._rag.query(
            tenant_id=tenant_id,
            query=message_text,
            top_k=5,
        )

        # A3 unification: ONE response confidence drives BOTH the auto-send gate
        # and the rendered badge. The response is only as confident as its weakest
        # link — the classifier verdict AND the RAG synthesis chain (retrieval ×
        # hallucination, already combined in synthesis.confidence). Pre-A3 the gate
        # keyed off classification.confidence while the badge showed
        # synthesis.confidence, so a high-classifier / low-synthesis message could
        # auto-send while its badge read "uncertain".
        response_confidence = min(classification.confidence, synthesis.confidence)
        is_complex = classification.category == MessageCategory.COMPLEX

        was_auto_sent = MessageClassifier.should_auto_respond(
            classification, response_confidence, confidence_threshold
        )

        escalation_needed = not was_auto_sent
        # Escalate WITH an AI draft when the (unified) confidence is mid-band: the
        # synthesis is usable enough to offer the operator a starting point but not
        # confident enough to auto-send. Below 0.6 / uncertain / complex → no draft.
        badge = _badge_for(response_confidence)
        escalation_has_ai_draft = (
            escalation_needed
            and response_confidence >= 0.6
            and badge != "uncertain"
            and not is_complex
        )

        logger.info(
            "response.generate.ok",
            tenant_id=str(tenant_id),
            badge=badge,
            confidence=response_confidence,
            was_auto_sent=was_auto_sent,
            escalation_needed=escalation_needed,
            escalation_has_ai_draft=escalation_has_ai_draft,
        )

        return ResponseResult(
            content=synthesis.answer,
            confidence_badge=badge,
            confidence_score=response_confidence,
            was_auto_sent=was_auto_sent,
            sources=synthesis.sources,
            routing_target="auto_respond" if was_auto_sent else "escalation_queue",
            escalation_needed=escalation_needed,
            escalation_has_ai_draft=escalation_has_ai_draft,
        )

    async def _handle_high_stakes(
        self,
        tenant_id: UUID,
        message_text: str,
        classification: ClassificationResult,
    ) -> ResponseResult:
        """Handle high-stakes messages - route to human immediately."""
        logger.info(
            "response.high_stakes",
            tenant_id=str(tenant_id),
        )

        return ResponseResult(
            content=(
                "Thank you for your message. This type of inquiry requires "
                "personal attention and will be reviewed by our team shortly. "
                "We aim to respond within the SLA commitment for your plan."
            ),
            confidence_badge="uncertain",
            confidence_score=0.0,
            was_auto_sent=False,
            sources=[],
            routing_target="escalation_queue",
            escalation_needed=True,
            escalation_has_ai_draft=False,
        )

    async def _handle_urgent(
        self,
        tenant_id: UUID,
        message_text: str,
        classification: ClassificationResult,
    ) -> ResponseResult:
        """Handle urgent messages - escalate with priority."""
        logger.info(
            "response.urgent",
            tenant_id=str(tenant_id),
            urgency=classification.urgency.value,
        )

        return ResponseResult(
            content=(
                "Thank you for your message. This is marked as urgent and "
                "will be prioritized for immediate review by our team."
            ),
            confidence_badge="low",
            confidence_score=0.3,
            was_auto_sent=False,
            sources=[],
            routing_target="escalation_queue",
            escalation_needed=True,
            escalation_has_ai_draft=False,
        )

    async def _generate_from_learned(
        self,
        tenant_id: UUID,
        message_text: str,
        classification: ClassificationResult,
        learned_answers: list[dict],
        confidence_threshold: float = 0.90,
    ) -> ResponseResult:
        """Generate response using learned answers (human escalation data).

        The learned-answer match similarity IS the unified response confidence
        here — a human-verified answer matched by vector similarity. This is an
        INTENTIONAL exception to the RAG-path ``min(classifier, synthesis)``
        unification: a human-verified answer is more trustworthy than an
        uncertain classifier, so the classifier confidence is NOT factored in
        (the human already approved this answer). Both the gate and the badge
        read the similarity directly (A3 unification — the learned path uses
        the similarity as the single quantity, analogous to how the RAG path
        uses ``min(classifier, synthesis)``)."""
        if not learned_answers:
            return await self._generate_from_rag(
                tenant_id, message_text, classification, confidence_threshold
            )

        best_answer = learned_answers[0]
        response_confidence = best_answer.get("similarity", 0.5)

        was_auto_sent = MessageClassifier.should_auto_respond(
            classification, response_confidence, confidence_threshold
        )

        answer_text = best_answer.get("answer_text", "")
        sources = [
            {
                "source_type": "human_answer",
                "answer_id": str(best_answer.get("id")),
                "similarity": response_confidence,
            }
        ]

        badge = _badge_for(response_confidence)

        logger.info(
            "response.from_learned.ok",
            tenant_id=str(tenant_id),
            badge=badge,
            answer_id=str(best_answer.get("id")),
        )

        return ResponseResult(
            content=answer_text,
            confidence_badge=badge,
            confidence_score=response_confidence,
            was_auto_sent=was_auto_sent,
            sources=sources,
            routing_target="auto_respond" if was_auto_sent else "escalation_queue",
            escalation_needed=not was_auto_sent,
            escalation_has_ai_draft=False,
        )

    async def _generate_from_rag(
        self,
        tenant_id: UUID,
        message_text: str,
        classification: ClassificationResult,
        confidence_threshold: float = 0.90,
    ) -> ResponseResult:
        """Generate response using RAG pipeline (unified confidence: the weaker of
        classifier + synthesis, per A3)."""
        synthesis = await self._rag.query(
            tenant_id=tenant_id,
            query=message_text,
            top_k=5,
        )

        response_confidence = min(classification.confidence, synthesis.confidence)
        was_auto_sent = MessageClassifier.should_auto_respond(
            classification, response_confidence, confidence_threshold
        )
        badge = _badge_for(response_confidence)
        is_complex = classification.category == MessageCategory.COMPLEX
        escalation_needed = not was_auto_sent

        return ResponseResult(
            content=synthesis.answer,
            confidence_badge=badge,
            confidence_score=response_confidence,
            was_auto_sent=was_auto_sent,
            sources=synthesis.sources,
            routing_target="auto_respond" if was_auto_sent else "escalation_queue",
            escalation_needed=escalation_needed,
            escalation_has_ai_draft=(
                escalation_needed
                and response_confidence >= 0.6
                and badge != "uncertain"
                and not is_complex
            ),
        )
