"""
tests/test_mvp4_security.py
===========================
Adversarial security, rate limiting, and tenant boundary regression tests.
"""

from __future__ import annotations

import time
import pytest
from src.core.rate_limiter import LocalSlidingWindowLimiter
from src.api.error_handlers import RateLimitExceededError


def test_rate_limiter_allows_under_limit():
    limiter = LocalSlidingWindowLimiter(limit=5, window_seconds=60)
    for _ in range(5):
        assert limiter.allow("tenant-1") is True


def test_rate_limiter_blocks_over_limit():
    limiter = LocalSlidingWindowLimiter(limit=3, window_seconds=60)
    assert limiter.allow("tenant-1") is True
    assert limiter.allow("tenant-1") is True
    assert limiter.allow("tenant-1") is True
    assert limiter.allow("tenant-1") is False

    with pytest.raises(RateLimitExceededError):
        limiter.check_rate_limit("tenant-1")


def test_rate_limiter_keys_are_isolated():
    limiter = LocalSlidingWindowLimiter(limit=2, window_seconds=60)
    assert limiter.allow("tenant-1") is True
    assert limiter.allow("tenant-1") is True
    assert limiter.allow("tenant-1") is False

    # tenant-2 should still have fresh quota
    assert limiter.allow("tenant-2") is True
    assert limiter.allow("tenant-2") is True


def test_rate_limiter_invalid_parameters():
    with pytest.raises(ValueError, match="positive integers"):
        LocalSlidingWindowLimiter(limit=0, window_seconds=60)

    with pytest.raises(ValueError, match="positive integers"):
        LocalSlidingWindowLimiter(limit=10, window_seconds=0)
