"""
src/core/rate_limiter.py
========================
AEGIS-DocIntel — In-Memory Sliding Window Rate Limiter.
Provides thread-safe request rate regulation per authenticated principal or tenant.
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from threading import Lock
from src.api.error_handlers import RateLimitExceededError


class LocalSlidingWindowLimiter:
    """
    Sliding window rate limiter for development and single-process deployments.
    Tracks timestamps per key and prunes events older than window_seconds.
    """

    def __init__(self, limit: int = 60, window_seconds: int = 60) -> None:
        if limit < 1 or window_seconds < 1:
            raise ValueError("limit and window_seconds must be positive integers")
        self.limit = limit
        self.window_seconds = window_seconds
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def allow(self, key: str) -> bool:
        """Atomically test if request is within rate limit; appends timestamp if allowed."""
        now = time.monotonic()
        cutoff = now - self.window_seconds
        with self._lock:
            events = self._events[key]
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= self.limit:
                return False
            events.append(now)
            return True

    def check_rate_limit(self, key: str) -> None:
        """Check rate limit; raises RateLimitExceededError if limit is breached."""
        if not self.allow(key):
            raise RateLimitExceededError(
                f"Rate limit of {self.limit} requests per {self.window_seconds}s exceeded."
            )

    def reset(self) -> None:
        """Clear all active counters (primarily used for test isolation)."""
        with self._lock:
            self._events.clear()
