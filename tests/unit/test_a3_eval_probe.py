"""A3 eval probe — adversarial verification of the unified confidence gate.

Probe: "confident classifier + uncertain synthesis must not auto-send"
Schema: JSON-structured, mechanically scored (NOT regex-on-prose).
Pre-A3 the gate keyed off classification.confidence alone, so a message
with classifier=0.95 + synthesis=0.3 would auto-send while displaying an
"uncertain" badge. Post-A3 the unified quantity min(classifier, synthesis)
= 0.3 < 0.90 correctly blocks the send.

This probe exercises the ResponseGenerator.generate() path with the exact
failure-mode inputs and asserts the response.escalation_needed outcome.
It would have FAILED pre-fix (was_auto_sent=True) and PASSES post-fix
(was_auto_sent=False) — the regression-detection property.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from unittest.mock import AsyncMock
from uuid import uuid4

from sequor.ai.classifier import ClassificationResult, MessageCategory, MessageUrgency
from sequor.ai.rag_pipeline import SynthesisResult
from sequor.ai.response import ResponseGenerator


@dataclass
class ProbeResult:
    """Structured probe answer — mechanically scored, never regex-matched."""

    passed: bool
    was_auto_sent: bool
    unified_confidence: float
    badge: str
    escalation_needed: bool
    evidence: str


def _classification(confidence: float = 0.95) -> ClassificationResult:
    return ClassificationResult(
        category=MessageCategory.ROUTINE,
        urgency=MessageUrgency.LOW,
        confidence=confidence,
        reasoning="test",
        classifier_version="1.0.0",
        classified_at=datetime.now(timezone.utc),
    )


def _synthesis(confidence: float) -> SynthesisResult:
    return SynthesisResult(
        answer="Here is the answer.",
        sources=[{"chunk_id": str(uuid4()), "document_id": str(uuid4())}],
        confidence=confidence,
        confidence_badge="uncertain" if confidence < 0.6 else "moderate",
        hallucination_check_passed=True,
        uncited_claims=0,
    )


async def _run_probe(
    classifier_confidence: float,
    synthesis_confidence: float,
    confidence_threshold: float = 0.90,
) -> ProbeResult:
    """Run the probe — the single executable verification of the A3 gate.

    Returns a structured ProbeResult (schema-conformant, mechanically scored).
    The scoring rule is: passed = (was_auto_sent is False) when the unified
    confidence min(classifier, synthesis) < threshold.
    """
    mock_rag = AsyncMock()
    mock_rag.query = AsyncMock(return_value=_synthesis(synthesis_confidence))

    generator = ResponseGenerator(rag_pipeline=mock_rag)
    classification = _classification(confidence=classifier_confidence)

    result = await generator.generate(
        uuid4(),
        "probe: confident classifier + uncertain synthesis",
        classification,
        confidence_threshold=confidence_threshold,
    )

    unified = min(classifier_confidence, synthesis_confidence)
    expected_auto_send = unified >= confidence_threshold

    return ProbeResult(
        passed=(result.was_auto_sent == expected_auto_send),
        was_auto_sent=result.was_auto_sent,
        unified_confidence=unified,
        badge=result.confidence_badge,
        escalation_needed=result.escalation_needed,
        evidence=(
            f"classifier={classifier_confidence}, synthesis={synthesis_confidence}, "
            f"unified={unified}, threshold={confidence_threshold}, "
            f"was_auto_sent={result.was_auto_sent}, "
            f"badge={result.confidence_badge}"
        ),
    )


# ---------------------------------------------------------------------------
# Probe battery — each is an independent verification case
# ---------------------------------------------------------------------------


async def probe_a3_core_bug() -> ProbeResult:
    """The exact pre-A3 failure: classifier-high + synthesis-low → NOT auto-sent."""
    return await _run_probe(
        classifier_confidence=0.95,
        synthesis_confidence=0.3,
    )


async def probe_a3_unified_pass() -> ProbeResult:
    """Both signals strong → auto-send."""
    return await _run_probe(
        classifier_confidence=0.92,
        synthesis_confidence=0.92,
    )


async def probe_a3_custom_threshold() -> ProbeResult:
    """Per-account threshold=0.95 blocks unified=0.92."""
    return await _run_probe(
        classifier_confidence=0.92,
        synthesis_confidence=0.92,
        confidence_threshold=0.95,
    )


async def probe_a3_badge_agreement() -> ProbeResult:
    """Badge and gate read the SAME quantity — badge=moderate at 0.85."""
    return await _run_probe(
        classifier_confidence=0.85,
        synthesis_confidence=0.85,
    )


# ---------------------------------------------------------------------------
# Scoring (mechanical, NOT regex — per probe-driven-verification.md MUST-1/2)
# ---------------------------------------------------------------------------


async def run_all_probes() -> dict[str, Any]:
    """Run the full probe battery and return scored results."""
    probes = {
        "a3_core_bug": probe_a3_core_bug,
        "a3_unified_pass": probe_a3_unified_pass,
        "a3_custom_threshold": probe_a3_custom_threshold,
        "a3_badge_agreement": probe_a3_badge_agreement,
    }

    results: dict[str, Any] = {}
    all_passed = True

    for name, probe_fn in probes.items():
        result = await probe_fn()
        results[name] = {
            "passed": result.passed,
            "was_auto_sent": result.was_auto_sent,
            "unified_confidence": result.unified_confidence,
            "badge": result.badge,
            "escalation_needed": result.escalation_needed,
            "evidence": result.evidence,
        }
        if not result.passed:
            all_passed = False

    results["_all_passed"] = all_passed
    return results


# ---------------------------------------------------------------------------
# pytest integration — run as part of the unit suite
# ---------------------------------------------------------------------------


import pytest


@pytest.mark.asyncio
async def test_probe_a3_core_bug():
    """Probe: classifier 0.95 + synthesis 0.3 → NOT auto-sent (the core bug fix)."""
    r = await probe_a3_core_bug()
    assert r.passed, r.evidence
    assert r.was_auto_sent is False
    assert r.escalation_needed is True


@pytest.mark.asyncio
async def test_probe_a3_unified_pass():
    """Probe: both signals >= 0.90 → auto-send."""
    r = await probe_a3_unified_pass()
    assert r.passed, r.evidence
    assert r.was_auto_sent is True


@pytest.mark.asyncio
async def test_probe_a3_custom_threshold():
    """Probe: custom threshold 0.95 blocks unified 0.92."""
    r = await probe_a3_custom_threshold()
    assert r.passed, r.evidence
    assert r.was_auto_sent is False


@pytest.mark.asyncio
async def test_probe_a3_badge_agreement():
    """Probe: badge and gate agree — unified 0.85 → moderate badge, no auto-send."""
    r = await probe_a3_badge_agreement()
    assert r.passed, r.evidence
    assert r.was_auto_sent is False  # 0.85 < 0.90
    assert r.badge == "moderate"


@pytest.mark.asyncio
async def test_probe_battery_all_pass():
    """The full probe battery must pass — regression-detection property."""
    results = await run_all_probes()
    assert results[
        "_all_passed"
    ], f"Probe battery failure: { {k: v for k, v in results.items() if k != '_all_passed' and not v['passed']} }"
