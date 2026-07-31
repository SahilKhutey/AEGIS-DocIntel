"""Sliding-window correctness."""

from __future__ import annotations

import pytest

from amdi.security.rate_limit import InMemoryBackend, RateLimiter


@pytest.mark.asyncio
async def test_allows_under_limit() -> None:
    rl = RateLimiter(limit=3, window_s=60, backend="memory")
    d1 = await rl.check("u1"); d2 = await rl.check("u1"); d3 = await rl.check("u1")
    assert all(d.allowed for d in (d1, d2, d3))
    assert d3.remaining == 0


@pytest.mark.asyncio
async def test_denies_over_limit() -> None:
    rl = RateLimiter(limit=2, window_s=60, backend="memory")
    await rl.check("u1"); await rl.check("u1")
    denied = await rl.check("u1")
    assert denied.allowed is False
    assert denied.retry_after_s > 0


@pytest.mark.asyncio
async def test_separate_identities_have_separate_buckets() -> None:
    rl = RateLimiter(limit=1, window_s=60, backend="memory")
    a1 = await rl.check("user-a"); b1 = await rl.check("user-b")
    assert a1.allowed and b1.allowed


@pytest.mark.asyncio
async def test_backend_in_memory_basic() -> None:
    b = InMemoryBackend()
    now = 1_700_000_000_000
    ok1, c1 = await b.check_and_consume(key="k", window_ms=1000, limit=2, now_ms=now)
    ok2, c2 = await b.check_and_consume(key="k", window_ms=1000, limit=2, now_ms=now)
    ok3, _ = await b.check_and_consume(key="k", window_ms=1000, limit=2, now_ms=now)
    assert ok1 and ok2 and not ok3
    assert c2 == 2
