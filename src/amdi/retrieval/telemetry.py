"""Per-method latency + counters."""

from __future__ import annotations

import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncIterator


class Telemetry:
    def __init__(self) -> None:
        self.latencies_ms: dict[str, list[float]] = defaultdict(list)
        self.counters: dict[str, int] = defaultdict(int)

    @asynccontextmanager
    async def time(self, label: str) -> AsyncIterator[None]:
        t0 = time.perf_counter()
        try:
            yield
        finally:
            self.latencies_ms[label].append((time.perf_counter() - t0) * 1000.0)

    def incr(self, label: str, by: int = 1) -> None:
        self.counters[label] += by

    def snapshot(self) -> dict[str, float | int]:
        out: dict[str, float | int] = {}
        for label, values in self.latencies_ms.items():
            out[f"{label}.p50_ms"] = _pct(values, 50)
            out[f"{label}.p95_ms"] = _pct(values, 95)
            out[f"{label}.count"] = len(values)
        for label, n in self.counters.items():
            out[f"counter.{label}"] = n
        return out


def _pct(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))
    return round(s[idx], 3)


__all__ = ["Telemetry"]
