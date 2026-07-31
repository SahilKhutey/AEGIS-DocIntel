"""Sliding-window rate limiter."""

from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass

from amdi.config import get_settings

logger = logging.getLogger("amdi.security.rate_limit")


@dataclass
class RateDecision:
    allowed: bool
    limit: int
    remaining: int
    retry_after_s: float
    reset_at_ms: int

    def headers(self) -> dict[str, str]:
        return {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(self.remaining, 0)),
            "X-RateLimit-Reset": str(self.reset_at_ms),
            "Retry-After": ("" if self.allowed else str(int(math.ceil(self.retry_after_s)))),
        }


class InMemoryBackend:
    """Cheap, process-local sliding window for dev/single-instance."""

    def __init__(self) -> None:
        self._buckets: dict[str, list[float]] = {}
        self._lock = asyncio.Lock()

    async def check_and_consume(
        self, *, key: str, window_ms: int, limit: int, now_ms: int,
    ) -> tuple[bool, int]:
        cutoff = now_ms / 1000.0 - window_ms / 1000.0
        async with self._lock:
            stamps = [t for t in self._buckets.get(key, ()) if t >= cutoff]
            allowed = len(stamps) < limit
            if allowed:
                stamps.append(now_ms / 1000.0)
            self._buckets[key] = stamps
            return allowed, len(stamps)


class RedisBackend:
    """Production-grade sliding window via Redis sorted sets."""

    def __init__(self, url: str) -> None:
        self._url = url
        self._client = None

    async def _ensure(self):
        if self._client is not None:
            return self._client
        try:
            import redis.asyncio as aioredis  # type: ignore
        except ImportError as exc:  # pragma: no cover
            raise RuntimeError(
                "redis package missing. pip install 'redis>=5'"
            ) from exc
        self._client = aioredis.from_url(self._url, decode_responses=True)
        return self._client

    async def check_and_consume(
        self, *, key: str, window_ms: int, limit: int, now_ms: int,
    ) -> tuple[bool, int]:
        client = await self._ensure()
        cutoff_ms = now_ms - window_ms
        member = f"{now_ms}-{now_ms * 1_000_000 % 1_000_000}"
        async with client.pipeline(transaction=False) as pipe:
            pipe.zremrangebyscore(key, 0, cutoff_ms)
            pipe.zcard(key)
            pipe.zadd(key, {member: now_ms})
            pipe.expire(key, window_ms // 1000 + 2)
            _, count_before, _, _ = await pipe.execute()

        count_after = int(count_before) + 1
        return count_after <= limit, count_after


class RateLimiter:
    """Public façade."""

    def __init__(self, *, limit: int, window_s: int, backend: str | None = None) -> None:
        self.limit = limit
        self.window_ms = window_s * 1000
        s = get_settings()
        backend_choice = backend or ("redis" if s.queue_backend == "arq" else "memory")
        self._redis_backend = RedisBackend(s.redis_url) if backend_choice == "redis" else None
        self._mem_backend = InMemoryBackend()

    async def check(self, identity: str) -> RateDecision:
        now_ms = int(time.time() * 1000)
        key = f"ratelimit:{identity}"
        allowed, count = True, 0
        if self._redis_backend is not None:
            try:
                allowed, count = await self._redis_backend.check_and_consume(
                    key=key, window_ms=self.window_ms, limit=self.limit, now_ms=now_ms,
                )
            except Exception:
                allowed, count = await self._mem_backend.check_and_consume(
                    key=key, window_ms=self.window_ms, limit=self.limit, now_ms=now_ms,
                )
        else:
            allowed, count = await self._mem_backend.check_and_consume(
                key=key, window_ms=self.window_ms, limit=self.limit, now_ms=now_ms,
            )
        reset_at_ms = now_ms + self.window_ms
        return RateDecision(
            allowed=allowed,
            limit=self.limit,
            remaining=max(self.limit - count, 0),
            retry_after_s=(self.window_ms / 1000.0) if not allowed else 0.0,
            reset_at_ms=reset_at_ms,
        )


__all__ = [
    "RateDecision", "RateLimiter",
    "InMemoryBackend", "RedisBackend",
]
