"""
src/operations/retry_policy.py
==============================
Deterministic retry policy with exponential backoff, full jitter, and permanent error classification.
"""

from __future__ import annotations

import random
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class RetryDecision:
    should_retry: bool
    delay_seconds: float
    reason: str


@dataclass(frozen=True, slots=True)
class RetryPolicy:
    max_attempts: int = 4
    base_delay_seconds: float = 2.0
    max_delay_seconds: float = 120.0

    def decide(
        self,
        *,
        attempt: int,
        retryable: bool,
        random_value: float | None = None,
    ) -> RetryDecision:
        """
        Decide whether to retry a failed job execution attempt.

        - attempt: 1-indexed attempt number (1 for the first execution).
        - retryable: False for permanent validation errors; True for transient errors.
        - random_value: Optional float in [0.0, 1.0] for deterministic testing of jitter.
        """
        if attempt < 1:
            raise ValueError("attempt must be >= 1")
        if not retryable:
            return RetryDecision(False, 0.0, "permanent_error")
        if attempt >= self.max_attempts:
            return RetryDecision(False, 0.0, "attempts_exhausted")

        # Exponential backoff with full jitter
        ceiling = min(self.max_delay_seconds, self.base_delay_seconds * (2 ** (attempt - 1)))
        jitter = random_value if random_value is not None else random.random()
        delay = ceiling * jitter
        return RetryDecision(True, delay, "retryable_failure")
