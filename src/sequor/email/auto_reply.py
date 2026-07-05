"""Auto-reply service that orchestrates the full message pipeline.

Combines:
1. Message classification
2. RAG retrieval and synthesis
3. Learning loop (for learned answers)
4. Response generation with confidence
5. Email auto-reply when confidence is high enough
6. Escalation routing when needed
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import structlog

from sequor.ai.classifier import ClassificationResult, MessageClassifier
from sequor.ai.learning import LearningLoop
from sequor.ai.rag_pipeline import RAGPipeline
from sequor.ai.response import ResponseGenerator, ResponseResult
from sequor.email.sender import SendGridEmailSender
from sequor.protocols import EmailSender
from sequor.email.utils import mask_email as _mask_email


logger = structlog.get_logger()


@dataclass
class MessageContext:
    """Context for processing a message."""

    tenant_id: UUID
    account_id: UUID
    contact_email: str
    message_id: UUID
    subject: str | None
    body_text: str
    channel: str
    external_message_id: str | None
    in_reply_to: str | None


@dataclass
class AutoReplyResult:
    """Result of auto-reply processing."""

    response_recorded: bool
    email_sent: bool
    escalated: bool
    escalation_id: UUID | None
    response_id: UUID | None
    confidence_badge: str
    confidence_score: float
    routing_target: str
    error: str | None


class AutoReplyService:
    """Orchestrates the full auto-reply pipeline.

    Flow:
    1. Classify message (routine/semi_routine/complex/high_stakes)
    2. If confidence > 0.6 and not high_stakes → RAG retrieval
    3. Generate response with confidence
    4. If high confidence and routine/semi_routine → send auto-reply
    5. Otherwise → escalate to backup contact
    6. If learning loop available, store for future reference
    """

    CONFIDENCE_THRESHOLD_AUTO_REPLY = 0.90
    CONFIDENCE_THRESHOLD_RAG = 0.60

    def __init__(
        self,
        classifier: MessageClassifier,
        rag_pipeline: RAGPipeline,
        email_sender: EmailSender,
        response_generator: ResponseGenerator | None = None,
        learning_loop: LearningLoop | None = None,
    ) -> None:
        """Initialize the auto-reply service.

        Args:
            classifier: MessageClassifier for intent detection
            rag_pipeline: RAGPipeline for document retrieval
            email_sender: EmailSender for outbound emails
            response_generator: Optional ResponseGenerator (created if not provided)
            learning_loop: Optional LearningLoop for learned answers
        """
        self._classifier = classifier
        self._rag = rag_pipeline
        self._email = email_sender
        self._learning = learning_loop
        self._response_gen = response_generator or ResponseGenerator(
            rag_pipeline=rag_pipeline,
            learning_loop=learning_loop,
        )

    async def process_message(
        self,
        context: MessageContext,
        confidence_threshold: float | None = None,
    ) -> AutoReplyResult:
        """Process an incoming message through the full pipeline.

        Args:
            context: Message context with tenant, contact, content
            confidence_threshold: Optional override for auto-reply threshold

        Returns:
            AutoReplyResult with processing outcome
        """
        threshold = confidence_threshold or self.CONFIDENCE_THRESHOLD_AUTO_REPLY

        logger.info(
            "auto_reply.process.start",
            tenant_id=str(context.tenant_id),
            message_id=str(context.message_id),
            channel=context.channel,
        )

        try:
            classification = await self._classifier.classify(
                tenant_id=context.tenant_id,
                message_text=context.body_text,
                channel=context.channel,
            )

            learned_answers = None
            if self._learning and self._should_use_learning(classification):
                learned_answers = await self._learning.search_learned_answers(
                    tenant_id=context.tenant_id,
                    query=context.body_text,
                    account_id=context.account_id,
                )

            response_result = await self._response_gen.generate(
                tenant_id=context.tenant_id,
                message_text=context.body_text,
                classification=classification,
                learned_answers=learned_answers,
            )

            response_record = await self._record_response(
                context=context,
                response_result=response_result,
                classification=classification,
            )

            escalation_id = None
            email_sent = False

            if response_result.escalation_needed:
                escalation_id = await self._create_escalation(
                    context=context,
                    response_id=response_record,
                    classification=classification,
                )
                logger.info(
                    "auto_reply.escalated",
                    tenant_id=str(context.tenant_id),
                    message_id=str(context.message_id),
                    escalation_id=str(escalation_id),
                )

            elif response_result.was_auto_sent and classification.confidence >= threshold:
                email_sent = await self._send_auto_reply(
                    context=context,
                    response_result=response_result,
                )
                logger.info(
                    "auto_reply.sent",
                    tenant_id=str(context.tenant_id),
                    message_id=str(context.message_id),
                    badge=response_result.confidence_badge,
                )

            return AutoReplyResult(
                response_recorded=True,
                email_sent=email_sent,
                escalated=response_result.escalation_needed,
                escalation_id=escalation_id,
                response_id=response_record,
                confidence_badge=response_result.confidence_badge,
                confidence_score=response_result.confidence_score,
                routing_target=response_result.routing_target,
                error=None,
            )

        except Exception as e:
            logger.error(
                "auto_reply.process.error",
                tenant_id=str(context.tenant_id),
                message_id=str(context.message_id),
                error=str(e),
            )
            return AutoReplyResult(
                response_recorded=False,
                email_sent=False,
                escalated=True,
                escalation_id=None,
                response_id=None,
                confidence_badge="uncertain",
                confidence_score=0.0,
                routing_target="escalation_queue",
                error=str(e),
            )

    def _should_use_learning(self, classification: ClassificationResult) -> bool:
        """Check if learning loop should be used for this classification."""
        return (
            classification.category.value in ["routine", "semi_routine"]
            and classification.confidence >= 0.6
        )

    async def _record_response(
        self,
        context: MessageContext,
        response_result: ResponseResult,
        classification: ClassificationResult,
    ) -> UUID:
        """Record the response in the database via SessionCrud."""
        from sequor.db.crud import SessionCrud
        from sequor.db.database import get_engine
        from sequor.db.models import ConfidenceBadge
        from sqlalchemy.ext.asyncio import AsyncSession
        from datetime import timezone

        now = datetime.now(timezone.utc)
        badge = ConfidenceBadge(response_result.confidence_badge)

        async with AsyncSession(get_engine()) as session:
            from sequor.db.tenant_context import bind_tenant

            await bind_tenant(session, context.tenant_id)
            crud = SessionCrud(session)
            record = await crud.create(
                "responses",
                {
                    "tenant_id": context.tenant_id,
                    "message_id": context.message_id,
                    "content": response_result.content,
                    "confidence_badge": badge.value,
                    "confidence_score": response_result.confidence_score,
                    "was_auto_sent": response_result.was_auto_sent,
                    "sent_at": now if response_result.was_auto_sent else None,
                },
            )
            await session.commit()

        resp_id = record.get("id")
        return UUID(str(resp_id)) if resp_id else context.message_id

    async def _create_escalation(
        self,
        context: MessageContext,
        response_id: UUID,
        classification: ClassificationResult,
    ) -> UUID:
        """Create an escalation via EscalationService (sends email, writes audit).

        Delegates to EscalationService.create_escalation which handles:
        backup contact lookup, escalation email with AI context, audit trail,
        and SLA deadline tracking.
        """
        from sequor.db.crud import SessionCrud
        from sequor.db.database import get_engine
        from sequor.db.models import EscalationPriority
        from sequor.escalation.service import EscalationService
        from sqlalchemy.ext.asyncio import AsyncSession

        urgency_map = {
            "low": EscalationPriority.low,
            "medium": EscalationPriority.medium,
            "high": EscalationPriority.high,
            "critical": EscalationPriority.critical,
        }
        priority = urgency_map.get(classification.urgency.value, EscalationPriority.medium)

        engine = get_engine()
        async with AsyncSession(engine) as session:
            from sequor.db.tenant_context import bind_tenant

            await bind_tenant(session, context.tenant_id)
            crud = SessionCrud(session)
            svc = EscalationService(db_express=crud, email_sender=self._email)

            record = await svc.create_escalation(
                message_id=context.message_id,
                tenant_id=context.tenant_id,
                account_id=context.account_id,
                priority=priority,
                ai_summary=classification.reasoning or "Classification-based escalation",
                routing_reason=f"AI confidence {classification.confidence:.0%}, category {classification.category.value}",
                suggested_response=getattr(classification, "suggested_response", None),
                confidence_score=classification.confidence,
            )
            await session.commit()

        esc_id = record.get("id")
        return UUID(esc_id) if isinstance(esc_id, str) else esc_id or context.message_id

    async def _send_auto_reply(
        self,
        context: MessageContext,
        response_result: ResponseResult,
    ) -> bool:
        """Send an auto-reply email.

        Args:
            context: Message context
            response_result: Generated response

        Returns:
            True if email was sent successfully
        """
        if not isinstance(self._email, (SendGridEmailSender, EmailSender)):
            logger.warning("auto_reply.email_sender_incompatible")
            return False

        try:
            from sequor.email.templates import build_auto_reply_email

            html, text = build_auto_reply_email(
                response_content=response_result.content,
                confidence_badge=response_result.confidence_badge,
            )
            await self._email.send_email(
                to=context.contact_email,
                subject=f"Re: {context.subject or '(No Subject)'}",
                body_html=html,
                body_text=text,
                in_reply_to=context.external_message_id,
            )
            return True
        except Exception as e:
            logger.error(
                "auto_reply.send_failed",
                to=_mask_email(context.contact_email),
                error=str(e),
            )
            return False


_auto_reply_service: AutoReplyService | None = None


def get_auto_reply_service() -> AutoReplyService:
    """Get or create the global AutoReplyService instance."""
    global _auto_reply_service
    if _auto_reply_service is None:
        from sequor.ai.client import get_ollama_client
        from sequor.ai.vector_store import VectorStore
        from sequor.db.database import get_engine

        engine = get_engine()
        llm = get_ollama_client()
        vector_store = VectorStore(engine)
        rag = RAGPipeline(vector_store=vector_store, llm_client=llm)
        classifier = MessageClassifier(llm_client=llm)
        learning = LearningLoop(llm_client=llm, engine=engine)
        email_sender = SendGridEmailSender()

        _auto_reply_service = AutoReplyService(
            classifier=classifier,
            rag_pipeline=rag,
            email_sender=email_sender,
            learning_loop=learning,
        )

    return _auto_reply_service
