"""Learning loop for capturing human answers.

Captures human answers from escalations and indexes them for future retrieval.
Enables the system to learn from human resolutions without upfront document preparation.
"""

from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

import structlog
from sqlalchemy.ext.asyncio import AsyncEngine

from sequor.ai.client import MiniMaxClient, OllamaClient, get_ollama_client

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
        llm_client: OllamaClient | MiniMaxClient | None = None,
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
        from sqlalchemy import text
        from sqlalchemy.ext.asyncio import AsyncSession

        from sequor.db.encrypted_column import encrypt_field, get_tenant_key
        from sequor.db.models import SourceType
        from sequor.db.tenant_context import bind_tenant

        async with AsyncSession(self._engine) as session:
            # This raw INSERT bypasses the EncryptedString TypeDecorator, so the
            # PII text MUST be encrypted here with the SAME field_names the ORM
            # column declares (learned_question / learned_answer). Otherwise the
            # ORM digest read (select(LearnedAnswer)) would try to decrypt
            # plaintext and raise InvalidTag. bind_tenant loads the per-tenant
            # key; without a master key it no-ops and we store plaintext,
            # matching the ORM's dev fail-open.
            await bind_tenant(session, tenant_id)
            key = get_tenant_key()
            enc_question = (
                encrypt_field(key, "learned_question", question_text) if key else question_text
            )
            enc_answer = encrypt_field(key, "learned_answer", answer_text) if key else answer_text
            result = await session.execute(
                text(
                    """
                INSERT INTO learned_answers
                (id, tenant_id, account_id, question_text, answer_text, source_type,
                 source_escalation_id, embedding, created_at)
                VALUES (gen_random_uuid(), :tenant_id, :account_id, :question_text, :answer_text,
                        :source_type, :source_escalation_id, :embedding, NOW())
                RETURNING id
                """
                ),
                {
                    "tenant_id": tenant_id,
                    "account_id": account_id,
                    "question_text": enc_question,
                    "answer_text": enc_answer,
                    "source_type": SourceType.human_answer.value,
                    "source_escalation_id": source_escalation_id,
                    "embedding": embedding,
                },
            )
            row = result.fetchone()
            await session.commit()
            return row[0] if row else tenant_id

    async def search_learned_answers(
        self,
        tenant_id: UUID,
        query: str,
        account_id: UUID | None = None,
        top_k: int = 3,
    ) -> list[dict]:
        """Search learned answers using pgvector cosine distance."""
        from sqlalchemy.ext.asyncio import AsyncSession
        from sqlalchemy import text

        query_embedding = await self._llm.generate_embeddings([query])
        if not query_embedding:
            return []

        emb_str = "[" + ",".join(str(v) for v in query_embedding[0]) + "]"

        async with AsyncSession(self._engine) as session:
            # Bind so the per-tenant key is loaded; the raw-selected PII text is
            # decrypted with the SAME field_names the ORM column declares.
            # No-op without a master key (dev fail-open → plaintext passthrough).
            from sequor.db.encrypted_column import decrypt_field, get_tenant_key
            from sequor.db.tenant_context import bind_tenant

            await bind_tenant(session, tenant_id)
            key = get_tenant_key()
            account_filter = "AND account_id = :account_id" if account_id else ""
            params: dict = {"tenant_id": tenant_id, "emb": emb_str, "limit": top_k}
            if account_id:
                params["account_id"] = account_id

            result = await session.execute(
                text(
                    f"""
                SELECT id, question_text, answer_text, source_type,
                       source_escalation_id, created_at,
                       1 - (embedding <=> CAST(:emb AS vector)) AS similarity
                FROM learned_answers
                WHERE tenant_id = :tenant_id
                  AND embedding IS NOT NULL
                  {account_filter}
                ORDER BY embedding <=> CAST(:emb AS vector)
                LIMIT :limit
                """
                ),
                params,
            )
            rows = result.fetchall()

        results = []
        for row in rows:
            sim = getattr(row, "similarity", None)
            if sim is None:
                continue
            sim = float(sim)
            if sim <= 0.5:
                continue
            raw_q = getattr(row, "question_text", "") or ""
            raw_a = getattr(row, "answer_text", "") or ""
            results.append(
                {
                    "id": getattr(row, "id", None),
                    "question_text": (
                        decrypt_field(key, "learned_question", raw_q) if key and raw_q else raw_q
                    ),
                    "answer_text": (
                        decrypt_field(key, "learned_answer", raw_a) if key and raw_a else raw_a
                    ),
                    "source_type": getattr(row, "source_type", ""),
                    "source_escalation_id": getattr(row, "source_escalation_id", None),
                    "created_at": getattr(row, "created_at", None),
                    "similarity": sim,
                }
            )
        return results

    async def delete_learned_answer(
        self,
        tenant_id: UUID,
        learned_answer_id: UUID,
    ) -> bool:
        """Delete a learned answer."""
        from sqlalchemy.ext.asyncio import AsyncSession

        async with AsyncSession(self._engine) as session:
            from sqlalchemy import text

            from sequor.db.tenant_context import bind_tenant

            # Bind the RLS GUC (app.current_tenant). learned_answers is
            # tenant-scoped under the no-FORCE RLS policy: without the GUC the
            # row is invisible to DELETE → rowcount=0 → silent no-op (False).
            # Mirrors _store_learned_answer / search_learned_answers.
            await bind_tenant(session, tenant_id)

            result = await session.execute(
                text(
                    """
                DELETE FROM learned_answers
                WHERE id = :id AND tenant_id = :tenant_id
                """
                ),
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
