"""
AEGIS-DocIntel Gateway Rate Limiter
PROT-FINAL-05: Workstream DEP-02 & DEP-08

Provides sliding-window rate limiting per client IP, evaluator session,
and tenant boundary to protect the evaluation platform from denial-of-service
and unmetered scraping attempts.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Dict, List, Tuple


class RateLimiter:
    """
    Sliding window in-memory rate limiter for the public gateway.
    """

    def __init__(self, default_rpm: int = 60, default_burst: int = 15):
        self._default_rpm = default_rpm
        self._default_burst = default_burst
        # key -> list of timestamps
        self._history: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(
        self,
        identifier: str,
        limit_per_minute: int = 60,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        Checks whether the identifier is within limits.
        Returns: (is_allowed, remaining, retry_after_seconds)
        """
        now = time.time()
        window_start = now - window_seconds

        # Prune older entries
        timestamps = [ts for ts in self._history[identifier] if ts > window_start]
        self._history[identifier] = timestamps

        current_count = len(timestamps)
        if current_count >= limit_per_minute:
            oldest_ts = timestamps[0] if timestamps else now
            retry_after = max(1, int(oldest_ts + window_seconds - now))
            return False, 0, retry_after

        # Record this request
        self._history[identifier].append(now)
        remaining = limit_per_minute - (current_count + 1)
        return True, remaining, 0

    def reset(self) -> None:
        """Clears all tracking state."""
        self._history.clear()


rate_limiter = RateLimiter()
