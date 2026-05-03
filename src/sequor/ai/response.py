"""Response generation with confidence scoring.

Generates AI responses using RAG retrieval and synthesizes with confidence badges.
"""

from dataclasses import dataclass
from typing import Any
from uuid import UUID

import structlog

from sequor.ai.classifier import ClassificationResult, MessageCategory, MessageUrgency
from sequor.ai.learning import LearningLoop
from sequor.ai.rag_pipeline import RAGPipeline

logger = structlog.get_logger()


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
                tenant_id, message_text, classification, learned_answers
            )

        synthesis = await self._rag.query(
            tenant_id=tenant_id,
            query=message_text,
            top_k=5,
        )

        # Three-tier confidence routing per spec:
        # - > 90%: auto-reply to contact
        # - 60-90%: escalate WITH AI draft for review
        # - < 60%: escalate WITHOUT AI draft
        confidence = classification.confidence
        is_routine = classification.category in [
            MessageCategory.ROUTINE,
            MessageCategory.SEMI_ROUTINE,
        ]
        has_good_synthesis = synthesis.confidence_badge in ["high", "moderate"]
        low_synthesis = (
            synthesis.confidence_badge == "uncertain" or synthesis.confidence_score < 0.3
        )
        is_complex = classification.category == MessageCategory.COMPLEX

        was_auto_sent = confidence >= 0.9 and is_routine and has_good_synthesis and not is_complex

        escalation_needed = not was_auto_sent
        escalation_has_ai_draft = (
            escalation_needed and confidence >= 0.6 and not low_synthesis and not is_complex
        )

        logger.info(
            "response.generate.ok",
            tenant_id=str(tenant_id),
            badge=synthesis.confidence_badge,
            confidence=confidence,
            was_auto_sent=was_auto_sent,
            escalation_needed=escalation_needed,
            escalation_has_ai_draft=escalation_has_ai_draft,
        )

        return ResponseResult(
            content=synthesis.answer,
            confidence_badge=synthesis.confidence_badge,
            confidence_score=synthesis.confidence,
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
    ) -> ResponseResult:
        """Generate response using learned answers (human escalation data)."""
        if not learned_answers:
            return await self._generate_from_rag(tenant_id, message_text, classification)

        best_answer = learned_answers[0]
        confidence = best_answer.get("similarity", 0.5)

        was_auto_sent = confidence >= 0.85 and classification.category in [
            MessageCategory.ROUTINE,
            MessageCategory.SEMI_ROUTINE,
        ]

        answer_text = best_answer.get("answer_text", "")
        sources = [
            {
                "source_type": "human_answer",
                "answer_id": str(best_answer.get("id")),
                "similarity": confidence,
            }
        ]

        if confidence >= 0.8:
            badge = "high"
        elif confidence >= 0.6:
            badge = "moderate"
        elif confidence >= 0.4:
            badge = "low"
        else:
            badge = "uncertain"

        logger.info(
            "response.from_learned.ok",
            tenant_id=str(tenant_id),
            badge=badge,
            answer_id=str(best_answer.get("id")),
        )

        return ResponseResult(
            content=answer_text,
            confidence_badge=badge,
            confidence_score=confidence,
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
    ) -> ResponseResult:
        """Generate response using RAG pipeline."""
        synthesis = await self._rag.query(
            tenant_id=tenant_id,
            query=message_text,
            top_k=5,
        )

        was_auto_sent = classification.confidence >= 0.9 and synthesis.confidence_badge in [
            "high",
            "moderate",
        ]

        escalation_needed = (
            synthesis.confidence_badge == "uncertain" or synthesis.confidence_score < 0.3
        )

        return ResponseResult(
            content=synthesis.answer,
            confidence_badge=synthesis.confidence_badge,
            confidence_score=synthesis.confidence,
            was_auto_sent=was_auto_sent,
            sources=synthesis.sources,
            routing_target="auto_respond"
            if was_auto_sent and not escalation_needed
            else "escalation_queue",
            escalation_needed=escalation_needed,
            escalation_has_ai_draft=False,
        )
