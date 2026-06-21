"""
Rate Limiter
============

Enforces request rate limits using a sliding window algorithm.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .exceptions import RateLimitExceededError


@dataclass
class RateLimitRule:
    """Rate limit configuration rule."""

    key: str  # e.g., 'ip', 'user_id', 'global'
    limit: int  # maximum requests
    window_seconds: int  # sliding window size in seconds


class RateLimiter:
    """
    In-memory Sliding Window Rate Limiter.

    Usage:
        limiter = RateLimiter()
        rule = RateLimitRule(key="api", limit=100, window_seconds=60)
        limiter.add_rule("api_rule", rule)
        
        # Will raise RateLimitExceededError if rate limit is exceeded
        limiter.check_rate_limit("api_rule", "user_123")
    """

    def __init__(self) -> None:
        self.rules: Dict[str, RateLimitRule] = {}
        # Stores timestamps of requests: (rule_name, identifier) -> list of float timestamps
        self.history: Dict[Tuple[str, str], List[float]] = {}

    def add_rule(self, name: str, rule: RateLimitRule) -> None:
        """Register a new rate limiting rule."""
        self.rules[name] = rule

    def is_rate_limited(self, rule_name: str, identifier: str) -> bool:
        """Check if request for identifier is rate limited under specified rule."""
        rule = self.rules.get(rule_name)
        if rule is None:
            return False

        now = time.time()
        window_start = now - rule.window_seconds
        key = (rule_name, identifier)

        # Retrieve request history
        timestamps = self.history.get(key, [])

        # Filter out timestamps older than the sliding window
        timestamps = [t for t in timestamps if t > window_start]
        self.history[key] = timestamps

        return len(timestamps) >= rule.limit

    def check_rate_limit(self, rule_name: str, identifier: str) -> None:
        """Check rate limit, recording the attempt and raising if exceeded."""
        rule = self.rules.get(rule_name)
        if rule is None:
            return

        now = time.time()
        window_start = now - rule.window_seconds
        key = (rule_name, identifier)

        # Retrieve request history
        timestamps = self.history.get(key, [])

        # Filter out old timestamps
        timestamps = [t for t in timestamps if t > window_start]

        if len(timestamps) >= rule.limit:
            # Save timestamps back first
            self.history[key] = timestamps
            raise RateLimitExceededError(
                f"Rate limit exceeded for rule '{rule_name}' and identifier '{identifier}'. "
                f"Limit: {rule.limit}/{rule.window_seconds}s."
            )

        # Add current request timestamp
        timestamps.append(now)
        self.history[key] = timestamps

    def get_status(self, rule_name: str, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status (limit, remaining, reset_in_seconds)."""
        rule = self.rules.get(rule_name)
        if rule is None:
            return {}

        now = time.time()
        window_start = now - rule.window_seconds
        key = (rule_name, identifier)

        timestamps = self.history.get(key, [])
        timestamps = [t for t in timestamps if t > window_start]

        remaining = max(0, rule.limit - len(timestamps))
        reset_in = 0.0
        if timestamps:
            reset_in = max(0.0, (timestamps[0] + rule.window_seconds) - now)

        return {
            "limit": rule.limit,
            "remaining": remaining,
            "reset_in_seconds": reset_in,
            "window_seconds": rule.window_seconds,
        }

    def reset_limit(self, rule_name: str, identifier: str) -> None:
        """Reset request history for identifier."""
        key = (rule_name, identifier)
        if key in self.history:
            del self.history[key]
