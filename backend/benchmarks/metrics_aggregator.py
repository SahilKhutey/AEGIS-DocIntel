"""
Metrics Aggregator
==================

Aggregates multiple benchmark results.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

import numpy as np


@dataclass
class AggregatedMetrics:
    """Aggregated benchmark metrics."""

    accuracy: float = 0.0
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    latency_mean_ms: float = 0.0
    memory_peak_mb: float = 0.0
    total_tokens: int = 0
    total_cost_usd: float = 0.0
    num_runs: int = 0

    def to_dict(self) -> dict:
        return {
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "latency_mean_ms": round(self.latency_mean_ms, 2),
            "memory_peak_mb": round(self.memory_peak_mb, 2),
            "total_tokens": self.total_tokens,
            "total_cost_usd": round(self.total_cost_usd, 6),
            "num_runs": self.num_runs,
        }


class MetricsAggregator:
    """Aggregate performance scores across multiple document benchmarks."""

    def __init__(self) -> None:
        self.accuracies: List[float] = []
        self.precisions: List[float] = []
        self.recalls: List[float] = []
        self.f1s: List[float] = []
        self.latencies: List[float] = []
        self.memories: List[float] = []
        self.tokens: List[int] = []
        self.costs: List[float] = []

    def add_result(self, result: Any) -> None:
        if hasattr(result, "accuracy"):
            self.accuracies.append(result.accuracy.accuracy)
        if hasattr(result, "precision_recall"):
            self.precisions.append(result.precision_recall.precision)
            self.recalls.append(result.precision_recall.recall)
            self.f1s.append(result.precision_recall.f1)
        if hasattr(result, "latency"):
            self.latencies.append(result.latency.stats.mean_ms)
        if hasattr(result, "memory"):
            self.memories.append(result.memory.peak_mb)
        if hasattr(result, "tokens"):
            self.tokens.append(result.tokens.total_tokens)
        if hasattr(result, "cost"):
            self.costs.append(result.cost.total_cost_usd)

    def aggregate(self) -> AggregatedMetrics:
        if not self.accuracies and not self.latencies:
            return AggregatedMetrics()

        return AggregatedMetrics(
            accuracy=float(np.mean(self.accuracies)) if self.accuracies else 0.0,
            precision=float(np.mean(self.precisions)) if self.precisions else 0.0,
            recall=float(np.mean(self.recalls)) if self.recalls else 0.0,
            f1=float(np.mean(self.f1s)) if self.f1s else 0.0,
            latency_mean_ms=float(np.mean(self.latencies)) if self.latencies else 0.0,
            memory_peak_mb=float(np.max(self.memories)) if self.memories else 0.0,
            total_tokens=int(np.sum(self.tokens)) if self.tokens else 0,
            total_cost_usd=float(np.sum(self.costs)) if self.costs else 0.0,
            num_runs=max(len(self.accuracies), len(self.latencies)),
        )
