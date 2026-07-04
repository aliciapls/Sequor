"""Redteam eval-harness — security regression probes (offline, behavioral).

One probe per closed security defect from redteam rounds R1/R2/R3. Each probe is
behavioral (construct input, call the real code, assert the closed behavior) or a
structural code-shape assertion — never regex/keyword scoring of model prose
(rules/probe-driven-verification.md). A failing probe = HIGH: the defect regressed.

Accretion rule: NEVER prune a probe when its defect closes; the probe is the
tripwire that catches a future refactor re-opening it.
"""

import json

import pytest


# ── R1 — CRITICAL auth bypass: decode_token pins the algorithm ──────────────
class TestR1AuthBypass:
    def test_valid_token_round_trips(self):
        from sequor.auth import create_access_token, decode_token

        token = create_access_token({"operator_id": "op1", "tenant_id": "t1", "role": "member"})
        payload = decode_token(token)
        assert payload is not None and payload["operator_id"] == "op1"

    def test_tampered_signature_rejected(self):
        from sequor.auth import create_access_token, decode_token

        token = create_access_token({"operator_id": "op1", "role": "member"})
        head, body, sig = token.split(".")
        forged = f"{head}.{body}.{sig[:-3]}xyz"  # corrupt the signature
        assert decode_token(forged) is None

    def test_alg_none_forgery_rejected(self):
        """A hand-crafted alg=none token must not authenticate (the R1 bypass class).

        Built manually because a safe JWT lib refuses to *encode* alg=none — the
        attack is an attacker assembling the bytes directly; decode_token must
        reject it because it pins algorithms=[HS256].
        """
        import base64

        from sequor.auth import decode_token

        def _b64url(obj):
            import json

            return base64.urlsafe_b64encode(json.dumps(obj).encode()).rstrip(b"=").decode()

        forged = (
            _b64url({"alg": "none", "typ": "JWT"})
            + "."
            + _b64url({"operator_id": "attacker", "role": "admin"})
            + "."
        )
        assert decode_token(forged) is None


# ── R2 — fail-closed encryption/env default ─────────────────────────────────
class TestR2FailClosedDefault:
    def test_app_env_defaults_to_production(self):
        """Unset APP_ENV must resolve to production (fail-closed), not development."""
        from sequor.config import Settings

        assert Settings.model_fields["app_env"].default == "production"


# ── R3 N3 — rate limiter fails CLOSED at capacity (no fail-open bypass) ──────
class TestR3N3RateLimiterFailClosed:
    def test_new_key_still_enforced_at_capacity(self):
        from sequor.onboarding import rate_limiter as rl

        limiter = rl.IPRateLimiter(max_requests=2, window_seconds=3600)
        # Fill the tracked-key map to capacity with distinct keys.
        for i in range(rl._MAX_TRACKED_KEYS):
            limiter.is_allowed(f"filler-{i}")

        # A brand-new key at capacity must STILL be enforced, not auto-allowed.
        assert limiter.is_allowed("attacker") is True  # 1st within limit
        assert limiter.is_allowed("attacker") is True  # 2nd within limit
        assert limiter.is_allowed("attacker") is False  # 3rd exceeds -> enforced


# ── R3 N2 — DNS endpoint hostname validation is strict ──────────────────────
class TestR3N2DnsDomainValidation:
    @pytest.mark.parametrize("good", ["example.com", "mail.sub.example.co.uk", "a-b.example.io"])
    def test_valid_domains_accepted(self, good):
        from sequor.onboarding.app import _DNS_DOMAIN_RE

        assert _DNS_DOMAIN_RE.match(good)

    @pytest.mark.parametrize(
        "bad",
        ["nodot", "", "http://example.com", "exa mple.com", "-bad.com", "bad-.com", "a" * 300],
    )
    def test_malformed_domains_rejected(self, bad):
        from sequor.onboarding.app import _DNS_DOMAIN_RE

        assert not _DNS_DOMAIN_RE.match(bad)


# ── R3 N4 — inbound rejects anything it cannot verify in production ──────────
class TestR3N4InboundUnverifiableRejected:
    @pytest.mark.asyncio
    async def test_empty_body_rejected_in_production(self, monkeypatch):
        import sequor.email.inbound as inbound

        monkeypatch.setattr(inbound.settings, "app_env", "production")
        processor = inbound.InboundEmailProcessor.__new__(inbound.InboundEmailProcessor)
        result = await inbound.InboundEmailProcessor.process_sendgrid_payload(
            processor, payload={}, raw_body=None, signature=None
        )
        assert result["status"] == "rejected"


# ── R3 NEW-5 — hallucination rejection uses the per-CLAIM denominator ────────
class TestR3New5HallucinationPerClaim:
    @pytest.mark.asyncio
    async def test_high_claim_ratio_rejects(self):
        from unittest.mock import AsyncMock

        from sequor.ai.rag_pipeline import RAGPipeline

        pipe = RAGPipeline.__new__(RAGPipeline)
        pipe._llm = AsyncMock()
        pipe._llm.generate = AsyncMock(
            return_value=json.dumps({"passed": True, "total_claims": 4, "uncited_claims": 3})
        )
        out = await pipe._check_hallucination(query="q", answer="a", passages=[{"text": "p"}])
        assert out["passed"] is False  # 3/4 > 0.5

    @pytest.mark.asyncio
    async def test_low_claim_ratio_over_one_passage_does_not_reject(self):
        from unittest.mock import AsyncMock

        from sequor.ai.rag_pipeline import RAGPipeline

        pipe = RAGPipeline.__new__(RAGPipeline)
        pipe._llm = AsyncMock()
        pipe._llm.generate = AsyncMock(
            return_value=json.dumps({"passed": True, "total_claims": 10, "uncited_claims": 1})
        )
        # Old passage-count denominator (1 > 1*0.5) would have WRONGLY rejected.
        out = await pipe._check_hallucination(query="q", answer="a", passages=[{"text": "p"}])
        assert out["passed"] is True  # 1/10 < 0.5
