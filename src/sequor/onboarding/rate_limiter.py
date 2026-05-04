"""IP-based sliding window rate limiter for onboarding endpoints.

Uses an in-memory defaultdict + deque of timestamps. Expired entries are
pruned on every check to prevent unbounded memory growth.
"""

import time
import structlog
from collections import defaultdict, deque


_logger = structlog.get_logger()


def _mask_ip(ip: str) -> str:
    """Mask the last octet of an IPv4 address for logging.

    For non-IPv4 inputs (IPv6, unknown), returns a safe placeholder.
    """
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "***.***.***.***"


class IPRateLimiter:
    """Sliding-window rate limiter keyed by client IP.

    Parameters
    ----------
    max_requests:
        Maximum number of requests allowed within the window.
    window_seconds:
        Duration of the sliding window in seconds.
    """

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._windows: defaultdict[str, deque] = defaultdict(deque)

    def is_allowed(self, key: str) -> bool:
        """Check whether a request from *key* is allowed.

        Prunes expired timestamps before checking. Returns True if the
        request is within the limit, False otherwise.
        """
        now = time.monotonic()
        window = self._windows[key]
        cutoff = now - self._window_seconds

        # Prune expired entries
        while window and window[0] <= cutoff:
            window.popleft()

        if len(window) >= self._max_requests:
            return False

        window.append(now)
        return True

    @property
    def max_requests(self) -> int:
        return self._max_requests

    @property
    def window_seconds(self) -> int:
        return self._window_seconds


def get_client_ip(request) -> str:
    """Extract the client IP from a FastAPI Request.

    Checks X-Forwarded-For first (leftmost value), then falls back to
    the direct client address.
    """
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "unknown"
