"""IP-based sliding window rate limiter for onboarding endpoints.

Uses an in-memory defaultdict + deque of timestamps. Expired entries are
pruned on every check. Empty keys are removed to prevent unbounded memory.
"""

import re
import time
import structlog
from collections import defaultdict, deque


_logger = structlog.get_logger()

_MAX_TRACKED_KEYS = 10_000
_IPV4_RE = re.compile(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$")


def _mask_ip(ip: str) -> str:
    """Mask the last octet of an IPv4 address for logging."""
    parts = ip.split(".")
    if len(parts) == 4:
        return f"{parts[0]}.{parts[1]}.{parts[2]}.***"
    return "***.***.***.***"


class IPRateLimiter:
    """Sliding-window rate limiter keyed by client IP."""

    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self._max_requests = max_requests
        self._window_seconds = window_seconds
        self._windows: dict[str, deque] = {}

    def is_allowed(self, key: str) -> bool:
        """Check whether a request from *key* is allowed.

        Prunes expired timestamps and removes empty keys to bound memory.
        """
        now = time.monotonic()
        cutoff = now - self._window_seconds

        window = self._windows.get(key)
        if window is None:
            if len(self._windows) >= _MAX_TRACKED_KEYS:
                # Fail CLOSED with LRU eviction, NOT open. Returning True here
                # let an attacker who first fills the map with _MAX_TRACKED_KEYS
                # distinct keys (many source IPs / spoofed X-Forwarded-For)
                # bypass every throttle for all subsequent new keys. Instead,
                # evict the oldest-inserted key and keep enforcing this one.
                self._windows.pop(next(iter(self._windows)), None)
                _logger.warning("rate_limiter.max_keys_evicted")
            window = deque()
            self._windows[key] = window
        else:
            while window and window[0] <= cutoff:
                window.popleft()
            if not window:
                del self._windows[key]
                window = deque()
                self._windows[key] = window

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

    Only trusts X-Forwarded-For when behind a known reverse proxy
    (TRUSTED_PROXY_HEADER env var). Otherwise uses the direct client address.
    """
    from sequor.config import settings

    if getattr(settings, "trust_x_forwarded_for", False):
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
            if _IPV4_RE.match(ip):
                return ip

    if request.client:
        return request.client.host
    return "unknown"
