"""Base contract for a retrieval method."""

from __future__ import annotations

import abc
import time

from amdi.retrieval.schemas import Evidence, Query


class BaseRetrievalMethod(abc.ABC):
    name: str = "base"

    def __init__(self) -> None:
        self._calls = 0
        self._total_ms = 0.0

    @abc.abstractmethod
    async def search(self, query: Query, k: int) -> list[Evidence]:
        """Return up to k Evidence items, in ranked order (highest first)."""

    async def warmup(self) -> None:
        """Optional eager-load hook; default no-op."""
        return None

    async def aclose(self) -> None:
        """Optional cleanup hook; default no-op."""
        return None

    async def timed_search(self, q: Query, k: int) -> list[Evidence]:
        t0 = time.perf_counter()
        try:
            return await self.search(q, k)
        finally:
            dt = (time.perf_counter() - t0) * 1000.0
            self._calls += 1
            self._total_ms += dt

    def telemetry(self) -> dict[str, float]:
        return {
            "calls": float(self._calls),
            "total_ms": round(self._total_ms, 3),
            "avg_ms": round(self._total_ms / self._calls, 3) if self._calls else 0.0,
        }


__all__ = ["BaseRetrievalMethod"]
