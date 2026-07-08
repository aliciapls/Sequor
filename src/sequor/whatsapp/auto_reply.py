"""WhatsApp auto-reply service — AI pipeline for WhatsApp messages.

Mirrors sequor.email.auto_reply.AutoReplyService but:
- Sends via MetaWhatsAppSender instead of SendGridEmailSender
- Respects 24-hour session window (free-form vs template)
- Uses contact phone instead of email
- Adds branded footer to outbound messages
"""

from dataclasses import dataclass, field
from datetime import datetime
from uuid import UUID

import structlog

from sequor.ai.classifier import ClassificationResult, MessageClassifier
from sequor.ai.learning import LearningLoop
from sequor.ai.rag_pipeline import RAGPipeline
from sequor.ai.response import ResponseGenerator, ResponseResult
from sequor.protocols import WhatsAppSender

logger = structlog.get_logger()


# Default branded footer appended to every outbound WhatsApp message
DEFAULT_WHATSAPP_FOOTER = (
    "\n\n---\n"
    "[Auto-generated; {confidence_pct:.0f}% confidence] "
    "Sent by {business_name}\n"
    "If you'd prefer to speak with a human, reply to this message."
)


@dataclass
class WhatsAppMessageContext:
    """Context for processing a WhatsApp message."""

    tenant_id: UUID
    account_id: UUID
    contact_phone: str
    message_id: UUID
    body_text: str
    channel: str = "whatsapp"
    external_message_id: str | None = None
    in_reply_to: str | None = None
    # WhatsApp-specific fields
    session_expired: bool = False
    business_name: str = "Sequor"
    account_phone: str | None = None  # The business's WhatsApp number


@dataclass
class WhatsAppAutoReplyResult:
    """Result of WhatsApp auto-reply processing."""

    response_recorded: bool
    message_sent: bool
    sent_via_template: bool
    escalated: bool
    escalation_id: UUID | None
    response_id: UUID | None
    confidence_badge: str
    confidence_score: float
    routing_target: str
    error: str | None


class WhatsAppAutoReplyService:
    """WhatsApp-specific auto-reply orchestrator.

    Reuses the same AI pipeline as email (classify → RAG → generate)
    but routes outbound via MetaWhatsAppSender and handles the
    24-hour session window differently from email.
    """

    CONFIDENCE_THRESHOLD_AUTO_REPLY = 0.90
    CONFIDENCE_THRESHOLD_RAG = 0.60

    def __init__(
        self,
        classifier: MessageClassifier,
        rag_pipeline: RAGPipeline,
        whatsapp_sender: WhatsAppSender,
        learning_loop: LearningLoop | None = None,
        response_generator: ResponseGenerator | None = None,
        footer_template: str = DEFAULT_WHATSAPP_FOOTER,
    ) -> None:
        self._classifier = classifier
        self._rag = rag_pipeline
        self._wa = whatsapp_sender
        self._learning = learning_loop
        self._footer_tpl = footer_template
        self._response_gen = response_generator or ResponseGenerator(
            rag_pipeline=rag_pipeline,
            learning_loop=learning_loop,
        )

    async def process_message(
        self,
        context: WhatsAppMessageContext,
        confidence_threshold: float | None = None,
    ) -> WhatsAppAutoReplyResult:
        """Process an inbound WhatsApp message through the full AI pipeline.

        Flow:
        1. Classify intent (routine / semi_routine / complex / high_stakes)
        2. RAG retrieval for grounding
        3. Generate response with confidence score
        4. Record response in database
        5. Escalate if low confidence OR session expired AND low confidence
        6. Auto-send if high confidence AND session window is open
        7. Send template acknowledgement if session expired but high confidence
        """
        threshold = confidence_threshold or self.CONFIDENCE_THRESHOLD_AUTO_REPLY

        logger.info(
            "whatsapp_auto_reply.process.start",
            tenant_id=str(context.tenant_id),
            message_id=str(context.message_id),
            session_expired=context.session_expired,
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
                confidence_threshold=threshold,
            )

            response_record = await self._record_response(
                context=context,
                response_result=response_result,
                classification=classification,
            )

            escalation_id: UUID | None = None
            message_sent = False
            sent_via_template = False

            if response_result.escalation_needed:
                escalation_id = await self._create_escalation(
                    context=context,
                    response_id=response_record,
                    classification=classification,
                    unified_confidence=response_result.confidence_score,
                )
                logger.info(
                    "whatsapp_auto_reply.escalated",
                    tenant_id=str(context.tenant_id),
                    message_id=str(context.message_id),
                    escalation_id=str(escalation_id),
                )

            elif response_result.was_auto_sent:
                # Unified predicate approved auto-send (A3 parity with email) — try to send
                if not context.session_expired:
                    message_sent = await self._send_auto_reply(
                        context=context,
                        response_result=response_result,
                    )
                    logger.info(
                        "whatsapp_auto_reply.sent",
                        tenant_id=str(context.tenant_id),
                        message_id=str(context.message_id),
                        badge=response_result.confidence_badge,
                    )
                else:
                    # Session expired — acknowledge with template
                    sent_via_template = await self._send_session_acknowledgement(
                        context=context,
                        response_result=response_result,
                    )
                    message_sent = sent_via_template
                    logger.info(
                        "whatsapp_auto_reply.template_sent",
                        tenant_id=str(context.tenant_id),
                        message_id=str(context.message_id),
                        reason="session_expired",
                    )

            return WhatsAppAutoReplyResult(
                response_recorded=True,
                message_sent=message_sent,
                sent_via_template=sent_via_template,
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
                "whatsapp_auto_reply.process.error",
                tenant_id=str(context.tenant_id),
                message_id=str(context.message_id),
                error=str(e),
            )
            return WhatsAppAutoReplyResult(
                response_recorded=False,
                message_sent=False,
                sent_via_template=False,
                escalated=True,
                escalation_id=None,
                response_id=None,
                confidence_badge="error",
                confidence_score=0.0,
                routing_target="escalation_queue",
                error=str(e),
            )

    def _should_use_learning(self, classification: ClassificationResult) -> bool:
        return (
            classification.category.value in ["routine", "semi_routine"]
            and classification.confidence >= 0.6
        )

    async def _record_response(
        self,
        context: WhatsAppMessageContext,
        response_result: ResponseResult,
        classification: ClassificationResult,
    ) -> UUID:
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
        context: WhatsAppMessageContext,
        response_id: UUID,
        classification: ClassificationResult,
        unified_confidence: float = 0.0,
    ) -> UUID:
        from sequor.db.crud import SessionCrud
        from sequor.db.database import get_engine
        from sequor.db.models import EscalationPriority
        from sequor.escalation.service import EscalationService
        from sequor.protocols import EmailSender
        from sequor.email.sender import SendGridEmailSender
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
            # Escalation service needs an email sender — pass a no-op one for WhatsApp
            email_sender: EmailSender = SendGridEmailSender()
            svc = EscalationService(db_express=crud, email_sender=email_sender)

            record = await svc.create_escalation(
                message_id=context.message_id,
                tenant_id=context.tenant_id,
                account_id=context.account_id,
                priority=priority,
                ai_summary=classification.reasoning or "Classification-based escalation",
                routing_reason=(
                    f"AI confidence {unified_confidence:.0%} "
                    f"(classifier {classification.confidence:.0%}), "
                    f"category {classification.category.value}"
                ),
                suggested_response=getattr(classification, "suggested_response", None),
                confidence_score=unified_confidence,
            )
            await session.commit()

        esc_id = record.get("id")
        return UUID(esc_id) if isinstance(esc_id, str) else esc_id or context.message_id

    async def _send_auto_reply(
        self,
        context: WhatsAppMessageContext,
        response_result: ResponseResult,
    ) -> bool:
        """Send a free-form text message within the 24-hour session window."""
        footer = self._footer_tpl.format(
            business_name=context.business_name,
            confidence_pct=response_result.confidence_score * 100,
        )
        body = f"{response_result.content}{footer}"

        # Truncate to WhatsApp's 4096 char limit
        if len(body) > 4096:
            body = body[:4093] + "..."

        try:
            await self._wa.send_text_message(to=context.contact_phone, body=body)
            return True
        except Exception as e:
            logger.error(
                "whatsapp_auto_reply.send_failed",
                to=self._mask_phone(context.contact_phone),
                error=str(e),
            )
            return False

    async def _send_session_acknowledgement(
        self,
        context: WhatsAppMessageContext,
        response_result: ResponseResult,
    ) -> bool:
        """Send a pre-approved acknowledgement template when session has expired.

        Meta requires template messages to be pre-approved before they can be
        sent outside the 24-hour session window.
        """
        from sequor.whatsapp.sender import WhatsAppAPIError as _WAApiError

        try:
            # acknowledgement template: "Hi! We've received your message and
            # our team is looking into it. We'll respond fully within [timeframe]."
            await self._wa.send_template_message(
                to=context.contact_phone,
                template_name="acknowledgement",
                language_code="en",
            )
            return True
        except _WAApiError as e:
            logger.warning(
                "whatsapp_auto_reply.template_failed",
                to=self._mask_phone(context.contact_phone),
                error=str(e),
            )
            return False
        except Exception as e:
            logger.error(
                "whatsapp_auto_reply.template_error",
                to=self._mask_phone(context.contact_phone),
                error=str(e),
            )
            return False

    @staticmethod
    def _mask_phone(phone: str) -> str:
        if len(phone) > 6:
            return phone[:4] + "***" + phone[-2:]
        return "****"
