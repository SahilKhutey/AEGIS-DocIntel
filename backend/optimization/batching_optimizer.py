"""
Batching Optimizer
====================

Batch small operations for higher throughput.

Mathematical Foundation:
    Throughput_gain = batch_size / per_item_overhead

    Latency:
        T_batch = T_setup + (n / batch_size) · T_per_batch
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np


@dataclass
class BatchResult:
    """Result of batch operation."""

    batch_size: int
    num_batches: int
    total_items: int
    total_time_ms: float
    avg_batch_time_ms: float
    throughput_items_per_sec: float
    results: List[Any] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "batch_size": self.batch_size,
            "num_batches": self.num_batches,
            "total_items": self.total_items,
            "total_time_ms": round(self.total_time_ms, 3),
            "avg_batch_time_ms": round(self.avg_batch_time_ms, 3),
            "throughput_items_per_sec": round(self.throughput_items_per_sec, 2),
        }


class BatchingOptimizer:
    """
    Find optimal batch size and process in batches.
    """

    def __init__(
        self,
        min_batch: int = 1,
        max_batch: int = 256,
    ) -> None:
        self.min_batch = max(1, min_batch)
        self.max_batch = max(self.min_batch, max_batch)

    def find_optimal_batch_size(
        self,
        items: List[Any],
        process_fn: Callable[[List[Any]], List[Any]],
        target_time_ms: float = 100.0,
    ) -> int:
        """Find the batch size that minimizes total processing time."""
        best_batch = self.min_batch
        best_time = float("inf")
        for batch_size in [1, 2, 4, 8, 16, 32, 64, 128, 256]:
            if batch_size < self.min_batch or batch_size > self.max_batch:
                continue
            t0 = time.perf_counter()
            for i in range(0, len(items), batch_size):
                batch = items[i : i + batch_size]
                process_fn(batch)
            elapsed = (time.perf_counter() - t0) * 1000
            if elapsed < best_time:
                best_time = elapsed
                best_batch = batch_size
            if elapsed < target_time_ms:
                break
        return best_batch

    def batch_process(
        self,
        items: List[Any],
        process_fn: Callable[[List[Any]], List[Any]],
        batch_size: int = 32,
    ) -> BatchResult:
        """Process items in batches."""
        t0 = time.perf_counter()
        results: List[Any] = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            batch_result = process_fn(batch)
            if isinstance(batch_result, list):
                results.extend(batch_result)
            else:
                results.append(batch_result)
        total_ms = (time.perf_counter() - t0) * 1000
        num_batches = (len(items) + batch_size - 1) // batch_size
        throughput = len(items) / max(total_ms / 1000.0, 1e-9)
        return BatchResult(
            batch_size=batch_size,
            num_batches=num_batches,
            total_items=len(items),
            total_time_ms=total_ms,
            avg_batch_time_ms=total_ms / max(num_batches, 1),
            throughput_items_per_sec=throughput,
            results=results,
        )
