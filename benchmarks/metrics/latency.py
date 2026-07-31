"""Per-stage latency summary."""

from __future__ import annotations

import statistics
from dataclasses import dataclass


@dataclass
class Latency:
    p50_ms: float
    p95_ms: float
    p99_ms: float
    mean_ms: float


def evaluate(per_question_ms: list[float]) -> Latency:
    if not per_question_ms:
        return Latency(0.0, 0.0, 0.0, 0.0)
    s = sorted(per_question_ms)
    return Latency(
        p50_ms=round(float(statistics.median(s)), 3),
        p95_ms=round(float(_pct(s, 95)), 3),
        p99_ms=round(float(_pct(s, 99)), 3),
        mean_ms=round(float(sum(s) / len(s)), 3),
    )


def _pct(s, p):
    return s[max(0, min(len(s) - 1, int(round((p / 100.0) * (len(s) - 1)))))]


__all__ = ["evaluate", "Latency"]
