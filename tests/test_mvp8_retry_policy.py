"""
tests/test_mvp8_retry_policy.py
===============================
Unit tests for deterministic retry policy with exponential backoff and jitter.
"""

from __future__ import annotations

import pytest

from src.operations.retry_policy import RetryPolicy


def test_transient_error_is_retried_before_limit():
    policy = RetryPolicy(max_attempts=4)
    result = policy.decide(
        attempt=1,
        retryable=True,
        random_value=0.5,
    )
    assert result.should_retry is True
    assert result.delay_seconds == 1.0  # 2.0 * 2^0 * 0.5


def test_retry_is_refused_after_attempt_limit():
    policy = RetryPolicy(max_attempts=4)
    result = policy.decide(
        attempt=4,
        retryable=True,
        random_value=0.5,
    )
    assert result.should_retry is False
    assert result.reason == "attempts_exhausted"


def test_permanent_error_is_not_retried():
    result = RetryPolicy().decide(
        attempt=1,
        retryable=False,
    )
    assert result.should_retry is False
    assert result.reason == "permanent_error"


def test_attempt_below_one_raises_error():
    with pytest.raises(ValueError, match="attempt must be >= 1"):
        RetryPolicy().decide(attempt=0, retryable=True)


def test_exponential_backoff_and_max_ceiling():
    policy = RetryPolicy(max_attempts=10, base_delay_seconds=2.0, max_delay_seconds=30.0)

    # Attempt 1: ceiling = min(30, 2 * 2^0) = 2.0 -> with 1.0 jitter = 2.0
    r1 = policy.decide(attempt=1, retryable=True, random_value=1.0)
    assert r1.delay_seconds == 2.0

    # Attempt 2: ceiling = min(30, 2 * 2^1) = 4.0
    r2 = policy.decide(attempt=2, retryable=True, random_value=1.0)
    assert r2.delay_seconds == 4.0

    # Attempt 3: ceiling = min(30, 2 * 2^2) = 8.0
    r3 = policy.decide(attempt=3, retryable=True, random_value=1.0)
    assert r3.delay_seconds == 8.0

    # Attempt 6: 2 * 2^5 = 64.0 > 30.0 ceiling -> capped at 30.0
    r6 = policy.decide(attempt=6, retryable=True, random_value=1.0)
    assert r6.delay_seconds == 30.0
