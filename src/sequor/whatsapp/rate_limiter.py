"""Token-bucket rate limiter for outbound WhatsApp sends."""

import asyncio
import time

import structlog

logger = structlog.get_logger()

_MAX_WAIT_SECONDS = 60


class WhatsAppRateLimitExceededError(Exception):
    """Local rate limiter blocked the send after maximum wait."""


class WhatsAppRateLimiter:
    """Token-bucket rate limiter for outbound WhatsApp messages.

    Allows up to `max_per_minute` sends per minute. Acquiring a token
    beyond the budget waits for refill. If the wait would exceed 60
    seconds, raises WhatsAppRateLimitExceededError instead of blocking.

    Enforces a minimum interval between acquisitions to prevent burst
    exhaustion of accumulated tokens (which would violate Meta's sustained
    rate limit even if the burst itself is technically within the bucket).
    """

    def __init__(self, max_per_minute: int) -> None:
        if max_per_minute <= 0:
            raise ValueError("max_per_minute must be positive")
        self._max = max_per_minute
        self._tokens: float = float(max_per_minute)
        self._last_refill: float = time.monotonic()
        self._last_acquire: float = 0.0

    async def acquire(self) -> None:
        """Wait until a token is available, then consume it."""
        self._refill()

        # Minimum interval between sends (seconds per token at sustained rate)
        min_interval = 60.0 / self._max

        if self._tokens >= 1.0:
            now = time.monotonic()
            elapsed_since_last = now - self._last_acquire
            if elapsed_since_last < min_interval:
                delay = min_interval - elapsed_since_last
                await asyncio.sleep(delay)
                self._refill()
            self._tokens -= 1.0
            self._last_acquire = time.monotonic()
            return

        needed = 1.0 - self._tokens
        wait_seconds = needed / (self._max / 60.0)

        if wait_seconds >= _MAX_WAIT_SECONDS:
            raise WhatsAppRateLimitExceededError(
                f"WhatsApp rate limit wait ({wait_seconds:.1f}s) exceeds maximum "
                f"({_MAX_WAIT_SECONDS}s). Queue the message for later."
            )

        logger.warning("whatsapp.rate_limited", wait_seconds=round(wait_seconds, 2))
        await asyncio.sleep(wait_seconds)

        self._refill()
        self._tokens -= 1.0
        self._last_acquire = time.monotonic()

    def _refill(self) -> None:
        now = time.monotonic()
        elapsed = now - self._last_refill
        added = elapsed * (self._max / 60.0)
        self._tokens = min(self._tokens + added, float(self._max))
        self._last_refill = now
