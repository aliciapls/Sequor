"""Learning loop for capturing human answers.

Captures human answers from escalations and indexes them for future retrieval.
Enables the system to learn from human resolutions without upfront document preparation.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

from sequor.ai.client import OllamaClient, get_ollama_client

logger = structlog.get_logger()


@dataclass
class LearnedAnswerRecord:
    """A learned answer record."""

    id: UUID
    tenant_id: UUID
    account_id: UUID
    question_text: str
    answer_text: str
    source_type: str
    source_escalation_id: UUID | None
    created_at: datetime


class LearningLoop:
    """Learning loop that captures human answers from escalations.

    When a human resolves an escalation by replying to the escalation email,
    the system captures that knowledge and indexes it for future retrieval.
    """

    def __init__(
        self,
        llm_client: OllamaClient | None = None,
        engine: AsyncEngine | None = None,
    ) -> None:
        """Initialize the learning loop.

        Args:
            llm_client: Ollama client for embedding generation
            engine: SQLAlchemy async engine
        """
        self._llm = llm_client or get_ollama_client()
        self._engine = engine

    async def capture_human_answer(
        self,
        tenant_id: UUID,
        account_id: UUID,
        escalation_id: UUID,
        original_query: str,
        human_reply: str,
    ) -> UUID:
        """Capture a human's answer from an escalation resolution.

        When a backup contact resolves an escalation by replying to the email,
        this method captures the question-answer pair and indexes it.

        Args:
            tenant_id: Tenant ID
            account_id: Account ID
            escalation_id: ID of the resolved escalation
            original_query: The original client question that was escalated
            human_reply: The human's reply that resolved the escalation

        Returns:
            UUID of the created learned answer record
        """
        logger.info(
            "learning.capture.start",
            tenant_id=str(tenant_id),
            escalation_id=str(escalation_id),
            query_length=len(original_query),
            reply_length=len(human_reply),
        )

        if not human_reply or not human_reply.strip():
            raise ValueError("Human reply cannot be empty")

        if len(human_reply.strip()) < 10:
            logger.warning(
                "learning.capture.too_short",
                escalation_id=str(escalation_id),
                reply_length=len(human_reply),
            )
            raise ValueError(
                "Human reply is too short to be a meaningful answer (minimum 10 characters)"
            )

        combined_text = f"Q: {original_query}\nA: {human_reply}"
        embeddings = await self._llm.generate_embeddings([combined_text])
        embedding = embeddings[0] if embeddings else None

        if self._engine:
            doc_id = await self._store_learned_answer(
                tenant_id=tenant_id,
                account_id=account_id,
                question_text=original_query,
                answer_text=human_reply,
                source_escalation_id=escalation_id,
                embedding=embedding,
            )
        else:
            from uuid import uuid4

            doc_id = uuid4()

        logger.info(
            "learning.capture.complete",
            learned_answer_id=str(doc_id),
            escalation_id=str(escalation_id),
        )

        return doc_id

    async def _store_learned_answer(
        self,
        tenant_id: UUID,
        account_id: UUID,
        question_text: str,
        answer_text: str,
        source_escalation_id: UUID | None,
        embedding: list[float] | None,
    ) -> UUID:
        """Store a learned answer in the database."""
        from sqlalchemy.ext.asyncio import AsyncSession

        from sequor.db.models import SourceType

        async with AsyncSession(self._engine) as session:
            await session.execute(
                """
                INSERT INTO learned_answers
                (id, tenant_id, account_id, question_text, answer_text, source_type,
                 source_escalation_id, embedding, created_at)
                VALUES (gen_random_uuid(), :tenant_id, :account_id, :question_text, :answer_text,
                        :source_type, :source_escalation_id, :embedding, NOW())
                """,
                {
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "question_text": question_text,
                    "answer_text": answer_text,
                    "source_type": SourceType.human_answer.value,
                    "source_escalation_id": source_escalation_id,
                    "embedding": embedding,
                },
            )
            await session.commit()

            result = await session.execute(
                "SELECT id FROM learned_answers WHERE tenant_id = :tenant_id ORDER BY created_at DESC LIMIT 1",
                {"tenant_id": tenant_id},
            )
            row = result.fetchone()
            return row[0] if row else tenant_id

    async def search_learned_answers(
        self,
        tenant_id: UUID,
        query: str,
        account_id: UUID | None = None,
        top_k: int = 3,
    ) -> list[dict]:
        """Search learned answers for a query."""
        from sqlalchemy.ext.asyncio import AsyncSession

        query_embedding = await self._llm.generate_embeddings([query])
        if not query_embedding:
            return []

        async with AsyncSession(self._engine) as session:
            if account_id:
                result = await session.execute(
                    """
                    SELECT id, question_text, answer_text, source_type,
                           source_escalation_id, created_at, embedding
                    FROM learned_answers
                    WHERE tenant_id = :tenant_id AND account_id = :account_id
                    """,
                    {"tenant_id": tenant_id, "account_id": account_id},
                )
            else:
                result = await session.execute(
                    """
                    SELECT id, question_text, answer_text, source_type,
                           source_escalation_id, created_at, embedding
                    FROM learned_answers
                    WHERE tenant_id = :tenant_id
                    """,
                    {"tenant_id": tenant_id},
                )
            rows = result.fetchall()

        if not rows:
            return []

        results = []
        for row in rows:
            if row.embedding:
                similarity = self._cosine_similarity(
                    query_embedding[0],
                    list(row.embedding),
                )
                if similarity > 0.5:
                    results.append(
                        {
                            "id": row.id,
                            "question_text": row.question_text,
                            "answer_text": row.answer_text,
                            "source_type": row.source_type,
                            "source_escalation_id": row.source_escalation_id,
                            "created_at": row.created_at,
                            "similarity": similarity,
                        }
                    )

        results.sort(key=lambda x: x["similarity"], reverse=True)
        return results[:top_k]

    async def delete_learned_answer(
        self,
        tenant_id: UUID,
        learned_answer_id: UUID,
    ) -> bool:
        """Delete a learned answer."""
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(self._engine) as session:
            result = await session.execute(
                """
                DELETE FROM learned_answers
                WHERE id = :id AND tenant_id = :tenant_id
                """,
                {"id": learned_answer_id, "tenant_id": tenant_id},
            )
            await session.commit()
            deleted = result.rowcount > 0

        if deleted:
            logger.info(
                "learning.delete.ok",
                learned_answer_id=str(learned_answer_id),
            )
        else:
            logger.warning(
                "learning.delete.not_found",
                learned_answer_id=str(learned_answer_id),
            )

        return deleted

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        import math

        if len(a) != len(b):
            return 0.0

        dot_product = sum(x * y for x, y in zip(a, b, strict=True))
        magnitude_a = math.sqrt(sum(x * x for x in a))
        magnitude_b = math.sqrt(sum(x * x for x in b))

        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0

        return dot_product / (magnitude_a * magnitude_b)
