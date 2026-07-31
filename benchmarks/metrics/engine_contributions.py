"""Per-method contribution analysis on retrieval results."""

from __future__ import annotations

from typing import Iterable


def evaluate(result_samples: Iterable[dict]) -> dict[str, float]:
    counts: dict[str, int] = {}
    total_ms: dict[str, float] = {}

    for r in result_samples:
        for k, v in (r.get("counters") or {}).items():
            counts[k] = counts.get(k, 0) + int(v)
        for k, v in (r.get("timings_ms") or {}).items():
            total_ms[k] = total_ms.get(k, 0.0) + float(v)

    total_items = sum(v for k, v in counts.items() if k.startswith("results.")) or 1
    return {
        **{f"contrib.{k}": round(v / total_items, 4) for k, v in counts.items()},
        **{f"latency_share_ms.{k}": round(v, 3) for k, v in total_ms.items()},
    }


__all__ = ["evaluate"]
