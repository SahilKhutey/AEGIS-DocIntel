"""
AEGIS-DocIntel Rate Limiting Service (PROT-04 WP-04.06)
Enforces sliding-window rate limits across Evaluator, License, IP, and Endpoint scopes.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from typing import Dict, List, Optional


class RateLimitExceededException(Exception):
    def __init__(
        self,
        scope_key: str,
        current_count: int,
        limit: int,
        window_seconds: float,
        retry_after_seconds: int = 30,
        message: Optional[str] = None,
    ):
        self.scope_key = scope_key
        self.current_count = current_count
        self.limit = limit
        self.window_seconds = window_seconds
        self.retry_after_seconds = retry_after_seconds
        msg = (
            message
            or f"Rate limit exceeded for scope '{scope_key}': {current_count}/{limit} in {window_seconds}s. Retry after {retry_after_seconds}s."
        )
        super().__init__(msg)


class RateLimitService:
    def __init__(self):
        # Key: scope_key -> list of float timestamps
        self._timestamps: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.Lock()

    def _prune(self, ts_list: List[float], cutoff: float) -> List[float]:
        return [t for t in ts_list if t >= cutoff]

    def check_rate_limit(
        self,
        scope_key: str,
        limit: int,
        window_seconds: float = 60.0,
    ) -> None:
        """
        Records an event and raises RateLimitExceededException if frequency threshold is exceeded.
        """
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            ts_list = self._prune(self._timestamps[scope_key], cutoff)
            if len(ts_list) >= limit:
                # Compute retry-after based on oldest timestamp within window
                oldest_in_window = min(ts_list) if ts_list else cutoff
                retry_after = max(1, int((oldest_in_window + window_seconds) - now))
                self._timestamps[scope_key] = ts_list
                raise RateLimitExceededException(
                    scope_key=scope_key,
                    current_count=len(ts_list),
                    limit=limit,
                    window_seconds=window_seconds,
                    retry_after_seconds=retry_after,
                )
            ts_list.append(now)
            self._timestamps[scope_key] = ts_list

    def get_utilization(self, scope_key: str, window_seconds: float = 60.0) -> int:
        now = time.time()
        cutoff = now - window_seconds
        with self._lock:
            ts_list = self._prune(self._timestamps[scope_key], cutoff)
            self._timestamps[scope_key] = ts_list
            return len(ts_list)

    def reset_scope(self, scope_key: str) -> None:
        with self._lock:
            self._timestamps.pop(scope_key, None)


default_rate_limit_service = RateLimitService()
