"""Redteam eval-harness — spec-compliance regression probes (offline, behavioral).

Probes for shipped comms-wedge spec criteria whose code was corrected in a redteam
round. Behavioral (call real code, assert the spec-mandated behavior). Never regex on
model prose (rules/probe-driven-verification.md).
"""

from dataclasses import dataclass
from unittest.mock import AsyncMock
from uuid import uuid4

import pytest


@dataclass
class _Result:
    chunk_id: object
    document_id: object
    chunk_text: str
    similarity_score: float
    bm25_score: float
    combined_score: float


# ── R3 NEW-3 — answerability floor: low-answerability passages EXCLUDED ──────
class TestNew3AnswerabilityFloor:
    def test_floor_constant(self):
        from sequor.ai.rag_pipeline import _ANSWERABILITY_FLOOR

        assert _ANSWERABILITY_FLOOR == 0.3

    @pytest.mark.asyncio
    async def test_low_answerability_passage_excluded_despite_high_similarity(self):
        """Spec rag-pipeline.md:89 — a passage below the answerability floor is
        excluded from synthesis even when its vector similarity is high."""
        from sequor.ai.rag_pipeline import RAGPipeline

        pipe = RAGPipeline.__new__(RAGPipeline)
        pipe._llm = AsyncMock()
        pipe._llm.generate_embeddings = AsyncMock(return_value=[[0.1, 0.2, 0.3]])
        pipe._vector_store = AsyncMock()

        keep = _Result(uuid4(), uuid4(), "answerable-passage", 0.80, 0.80, 0.80)
        drop = _Result(uuid4(), uuid4(), "high-similarity-unanswerable", 0.99, 0.99, 0.99)
        pipe._vector_store.search = AsyncMock(return_value=[keep, drop])
        # keep -> answerability 0.9 (>= floor); drop -> 0.1 (< 0.3 floor)
        pipe._score_answerability = AsyncMock(side_effect=[0.9, 0.1])

        result = await pipe.retrieve(tenant_id=uuid4(), query="q")
        texts = [p["text"] for p in result.passages]
        assert "answerable-passage" in texts
        assert "high-similarity-unanswerable" not in texts  # excluded despite 0.99 similarity


# ── D1 — digest api: format_digest_email contract ───────────────────────────
class TestD1DigestFormat:
    def test_api_symbols_exist(self):
        from sequor.digest.service import (  # noqa: F401
            format_digest_email,
            gather_digest_data,
            send_digest,
        )

    def test_subject_uses_account_name_and_body_flags_breaches(self):
        from sequor.digest.service import format_digest_email

        data = {
            "account_name": "Front Desk",
            "pending": 2,
            "escalated": 3,
            "breached_sla": 1,
            "oldest_unresolved_hours": 5.2,
            "auto_resolved": 4,
            "resolved_by_rag": 3,
            "resolved_by_learned": 1,
            "learned_count": 2,
            "learned_topics": ["refund policy", "shipping timelines"],
        }
        subject, body = format_digest_email(data)
        assert "[COVERAGE DIGEST]" in subject
        assert "Front Desk" in subject
        assert "Breached SLA:" in body and "need attention" in body
        assert "refund policy" in body

    def test_no_breach_line_when_zero(self):
        from sequor.digest.service import format_digest_email

        data = {
            "account_name": "X",
            "pending": 0,
            "escalated": 0,
            "breached_sla": 0,
            "oldest_unresolved_hours": None,
            "auto_resolved": 0,
            "resolved_by_rag": 0,
            "resolved_by_learned": 0,
            "learned_count": 0,
            "learned_topics": [],
        }
        _, body = format_digest_email(data)
        assert "Breached SLA:" not in body


# ── Online probes (deferred — need live infra; never regex-fallback) ─────────
@pytest.mark.skip(
    reason="probe-unavailable: requires postgres (Tier-2 gather_digest_data execution)"
)
class TestOnlineDigestExecution:
    """gather_digest_data execution + encryption round-trip through the ORM need a
    real Postgres session; enumerated here so the gap is visible, not silently absent."""
