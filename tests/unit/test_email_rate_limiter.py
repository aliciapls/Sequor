"""Unit tests for the email rate limiter."""

import asyncio
import time

import pytest

from sequor.email.rate_limiter import EmailRateLimiter, RateLimitExceededError


class TestEmailRateLimiter:
    def test_rejects_zero_rate(self):
        with pytest.raises(ValueError, match="positive"):
            EmailRateLimiter(max_per_minute=0)

    def test_rejects_negative_rate(self):
        with pytest.raises(ValueError, match="positive"):
            EmailRateLimiter(max_per_minute=-5)

    async def test_acquire_within_limit(self):
        limiter = EmailRateLimiter(max_per_minute=10)
        await limiter.acquire()

    async def test_tokens_depleted_after_burst(self):
        limiter = EmailRateLimiter(max_per_minute=3)
        for _ in range(3):
            await limiter.acquire()
        assert limiter._tokens < 1.0

    def test_refill_cannot_exceed_max(self):
        limiter = EmailRateLimiter(max_per_minute=10)
        limiter._tokens = 5.0
        limiter._last_refill = time.monotonic() - 3600
        limiter._refill()
        assert limiter._tokens <= 10.0

    async def test_acquire_raises_after_extended_wait(self):
        limiter = EmailRateLimiter(max_per_minute=1)
        await limiter.acquire()
        # Need more tokens than 60s can refill — set tokens negative
        limiter._tokens = -1.0
        limiter._last_refill = time.monotonic()
        with pytest.raises(RateLimitExceededError):
            await limiter.acquire()

    async def test_refill_restores_tokens_over_time(self):
        limiter = EmailRateLimiter(max_per_minute=60)
        limiter._tokens = 0.0
        limiter._last_refill = time.monotonic() - 1.0
        limiter._refill()
        assert limiter._tokens >= 1.0
