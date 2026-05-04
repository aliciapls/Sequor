"""Message classification engine using Kaizen agents.

Classifies incoming messages into categories and urgency levels.
This is the "brain" that determines routing and response strategy.
"""

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import StrEnum
from typing import Any
from uuid import UUID

import structlog

logger = structlog.get_logger()


class MessageCategory(StrEnum):
    """Message classification categories."""

    ROUTINE = "routine"
    SEMI_ROUTINE = "semi_routine"
    COMPLEX = "complex"
    HIGH_STAKES = "high_stakes"


class MessageUrgency(StrEnum):
    """Message urgency levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ClassificationResult:
    """Result of message classification."""

    category: MessageCategory
    urgency: MessageUrgency
    confidence: float
    reasoning: str
    classifier_version: str
    classified_at: datetime


class MessageClassifier:
    """Classifies incoming messages using LLM reasoning.

    Determines:
    - Category: routine, semi_routine, complex, high_stakes
    - Urgency: low, medium, high, critical
    - Confidence score (0.0 - 1.0)

    Uses LLM-first reasoning per agent-reasoning.md rules.
    """

    CLASSIFIER_VERSION = "1.0.0"

    CATEGORY_DESCRIPTIONS = {
        "routine": "Common questions with standard answers (FAQ, pricing, availability, simple requests). Can be handled by AI with high confidence.",
        "semi_routine": "Questions requiring some context or interpretation. AI can handle with moderate confidence, may need human review.",
        "complex": "Questions requiring nuanced understanding, multiple pieces of information, or professional judgment. Human review recommended.",
        "high_stakes": "Sensitive matters involving money, legal issues, personnel, or significant consequences. Must be routed to human immediately.",
    }

    URGENCY_DESCRIPTIONS = {
        "low": "No time pressure. Response can wait 24-48 hours.",
        "medium": "Response expected within 4-8 hours.",
        "high": "Response needed within 1-2 hours.",
        "critical": "Immediate attention required. Escalate now.",
    }

    def __init__(
        self,
        llm_client: Any | None = None,
    ) -> None:
        """Initialize the classifier.

        Args:
            llm_client: OllamaClient instance for LLM calls
        """
        self._llm = llm_client

    async def classify(
        self,
        tenant_id: UUID,
        message_text: str,
        channel: str = "email",
        context: dict[str, Any] | None = None,
    ) -> ClassificationResult:
        """Classify an incoming message.

        Args:
            tenant_id: Tenant ID
            message_text: The message content to classify
            channel: Communication channel (email, whatsapp)
            context: Optional additional context (contact history, account info)

        Returns:
            ClassificationResult with category, urgency, confidence, and reasoning
        """
        logger.info(
            "classifier.classify.start",
            tenant_id=str(tenant_id),
            message_length=len(message_text),
            channel=channel,
        )

        prompt = self._build_classification_prompt(
            message_text=message_text,
            channel=channel,
            context=context,
        )

        try:
            response = await self._llm.generate(prompt, temperature=0.1)
            result = self._parse_classification_response(response)

            classification = ClassificationResult(
                category=MessageCategory(result["category"]),
                urgency=MessageUrgency(result["urgency"]),
                confidence=float(result["confidence"]),
                reasoning=result["reasoning"],
                classifier_version=self.CLASSIFIER_VERSION,
                classified_at=datetime.now(timezone.utc),
            )

            logger.info(
                "classifier.classify.ok",
                tenant_id=str(tenant_id),
                category=classification.category.value,
                urgency=classification.urgency.value,
                confidence=classification.confidence,
            )

            return classification

        except Exception as e:
            logger.error(
                "classifier.classify.error",
                tenant_id=str(tenant_id),
                error=str(e),
            )
            return ClassificationResult(
                category=MessageCategory.SEMI_ROUTINE,
                urgency=MessageUrgency.MEDIUM,
                confidence=0.0,
                reasoning=f"Classification failed: {str(e)}. Defaulting to semi_routine/medium.",
                classifier_version=self.CLASSIFIER_VERSION,
                classified_at=datetime.now(timezone.utc),
            )

    def _build_classification_prompt(
        self,
        message_text: str,
        channel: str,
        context: dict[str, Any] | None,
    ) -> str:
        """Build the classification prompt for the LLM.

        Args:
            message_text: Message content
            channel: Communication channel
            context: Optional context

        Returns:
            Formatted prompt string
        """
        context_str = ""
        if context:
            context_parts = []
            if context.get("contact_history"):
                history = context["contact_history"]
                context_parts.append(f"Contact history ({len(history)} previous messages)")
            if context.get("account_type"):
                context_parts.append(f"Account type: {context['account_type']}")
            if context.get("document_types"):
                docs = ", ".join(context["document_types"])
                context_parts.append(f"Available documents: {docs}")
            if context_parts:
                context_str = "\n\nContext:\n" + "\n".join(f"- {c}" for c in context_parts)

        prompt = f"""Classify this incoming message from a client.

Message channel: {channel}
{context_str}

Message content:
---
{message_text}
---

Classify the message on two dimensions:

**Category** (one of):
- routine: Common questions with standard answers. AI can handle confidently.
- semi_routine: Questions requiring some context or interpretation. AI can handle with moderate confidence.
- complex: Questions requiring nuanced understanding or professional judgment. Human review recommended.
- high_stakes: Sensitive matters involving money, legal, personnel, or significant consequences. Must route to human immediately.

**Urgency** (one of):
- low: No time pressure. Response can wait 24-48 hours.
- medium: Response expected within 4-8 hours.
- high: Response needed within 1-2 hours.
- critical: Immediate attention required.

Respond in this exact JSON format:
{{"category": "routine|semi_routine|complex|high_stakes", "urgency": "low|medium|high|critical", "confidence": 0.0-1.0, "reasoning": "brief explanation of classification decision"}}

Confidence guidelines:
- 0.9-1.0: Very clear-cut case
- 0.7-0.9: Clear classification
- 0.5-0.7: Some uncertainty, borderline case
- Below 0.5: Very uncertain, lean toward human review"""

        return prompt

    def _parse_classification_response(self, response: str) -> dict:
        """Parse LLM classification response.

        Args:
            response: Raw LLM response

        Returns:
            Parsed classification dict
        """
        import json
        import re

        response = response.strip()

        json_match = re.search(r"\{[^{}]*\}", response, re.DOTALL)
        if json_match:
            response = json_match.group(0)

        try:
            result = json.loads(response)
        except json.JSONDecodeError:
            json_pattern = r"\"category\":\s*\"(\w+)\""
            cat_match = re.search(json_pattern, response)
            cat = cat_match.group(1) if cat_match else "semi_routine"

            urg_pattern = r"\"urgency\":\s*\"(\w+)\""
            urg_match = re.search(urg_pattern, response)
            urgency = urg_match.group(1) if urg_match else "medium"

            conf_pattern = r"\"confidence\":\s*([0-9.]+)"
            conf_match = re.search(conf_pattern, response)
            confidence = float(conf_match.group(1)) if conf_match else 0.5

            reason_pattern = r"\"reasoning\":\s*\"([^\"]+)\""
            reason_match = re.search(reason_pattern, response)
            reasoning = reason_match.group(1) if reason_match else "Could not parse reasoning"

            result = {
                "category": cat,
                "urgency": urgency,
                "confidence": confidence,
                "reasoning": reasoning,
            }

        if result["category"] not in ["routine", "semi_routine", "complex", "high_stakes"]:
            result["category"] = "semi_routine"
        if result["urgency"] not in ["low", "medium", "high", "critical"]:
            result["urgency"] = "medium"
        result["confidence"] = max(0.0, min(1.0, result.get("confidence", 0.5)))

        return result

    def should_use_rag(self, classification: ClassificationResult) -> bool:
        """Determine if RAG should be used for this classification.

        RAG is triggered when:
        - Confidence > 0.6
        - Category is NOT high_stakes

        Args:
            classification: Classification result

        Returns:
            True if RAG should be used
        """
        return (
            classification.confidence > 0.6
            and classification.category != MessageCategory.HIGH_STAKES
        )

    def should_auto_respond(
        self,
        classification: ClassificationResult,
        confidence_threshold: float = 0.90,
    ) -> bool:
        """Determine if the message should be auto-responded.

        Args:
            classification: Classification result
            confidence_threshold: Minimum confidence for auto-response

        Returns:
            True if safe to auto-respond
        """
        return (
            classification.category in [MessageCategory.ROUTINE, MessageCategory.SEMI_ROUTINE]
            and classification.urgency in [MessageUrgency.LOW, MessageUrgency.MEDIUM]
            and classification.confidence >= confidence_threshold
        )
