"""
Latency Optimizer
===================

Strategies to reduce pipeline latency:

    - PARALLELIZE: run independent operations concurrently
    - CACHE: memoize expensive calls
    - PRECOMPUTE: precompute expensive values
    - STREAM: stream results incrementally
    - INDEX: use faster data structures
    - BATCH: batch small operations
    - ASYNC: use async I/O

Mathematical Foundation:
    Speedup S = T_baseline / T_optimized

    Amdahl's law:
        S_max = 1 / ((1 - P) + P / N)
    where P = parallelizable fraction, N = # parallel workers
"""

from __future__ import annotations

import concurrent.futures
import functools
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class LatencyStrategy(Enum):
    """Latency optimization strategies."""

    PARALLELIZE = "parallelize"
    CACHE = "cache"
    PRECOMPUTE = "precompute"
    STREAM = "stream"
    INDEX = "index"
    BATCH = "batch"
    ASYNC = "async"


@dataclass
class LatencyOptimizationResult:
    """Result of latency optimization."""

    strategy: str
    baseline_ms: float
    optimized_ms: float
    speedup: float
    reduction_pct: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "baseline_ms": round(self.baseline_ms, 3),
            "optimized_ms": round(self.optimized_ms, 3),
            "speedup": round(self.speedup, 4),
            "reduction_pct": round(self.reduction_pct, 4),
        }


class LatencyOptimizer:
    """
    Apply latency optimization strategies.
    """

    def __init__(self) -> None:
        self._cache: Dict[str, Any] = {}
        self._precomputed: Dict[str, Any] = {}

    def parallelize(
        self,
        operations: List[Callable[[], Any]],
        max_workers: int = 4,
    ) -> tuple:
        """Run operations in parallel."""
        # baseline: sequential
        t0 = time.perf_counter()
        sequential_results = [op() for op in operations]
        baseline_ms = (time.perf_counter() - t0) * 1000
        # optimized: parallel
        t0 = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Using list comprehension to execute tasks concurrently
            futures = [executor.submit(op) for op in operations]
            parallel_results = [f.result() for f in futures]
        optimized_ms = (time.perf_counter() - t0) * 1000
        speedup = baseline_ms / max(optimized_ms, 1e-9)
        return parallel_results, LatencyOptimizationResult(
            strategy="parallelize",
            baseline_ms=baseline_ms,
            optimized_ms=optimized_ms,
            speedup=speedup,
            reduction_pct=(baseline_ms - optimized_ms) / max(baseline_ms, 1),
            metadata={"max_workers": max_workers, "num_ops": len(operations)},
        )

    def cached_call(
        self,
        key: str,
        func: Callable[[], Any],
    ) -> tuple:
        """Memoized call."""
        if key in self._cache:
            return self._cache[key], LatencyOptimizationResult(
                strategy="cache",
                baseline_ms=0.0,
                optimized_ms=0.0,
                speedup=float("inf"),
                reduction_pct=1.0,
                metadata={"cache_hit": True, "key": key},
            )
        t0 = time.perf_counter()
        result = func()
        elapsed_ms = (time.perf_counter() - t0) * 1000
        self._cache[key] = result
        return result, LatencyOptimizationResult(
            strategy="cache",
            baseline_ms=elapsed_ms,
            optimized_ms=elapsed_ms,
            speedup=1.0,
            reduction_pct=0.0,
            metadata={"cache_hit": False, "key": key, "first_call_ms": elapsed_ms},
        )

    def precompute(
        self,
        key: str,
        func: Callable[[], Any],
        use_cached: bool = True,
    ) -> Any:
        """Precompute and cache a value."""
        if use_cached and key in self._precomputed:
            return self._precomputed[key]
        result = func()
        self._precomputed[key] = result
        return result

    def batch_operations(
        self,
        items: List[Any],
        batch_fn: Callable[[List[Any]], Any],
        batch_size: int = 32,
    ) -> tuple:
        """Batch small operations into larger ones."""
        # baseline: one-at-a-time
        t0 = time.perf_counter()
        sequential_results = [batch_fn([item])[0] if batch_fn([item]) else None for item in items]
        baseline_ms = (time.perf_counter() - t0) * 1000
        # optimized: batched
        t0 = time.perf_counter()
        batched_results: List[Any] = []
        for i in range(0, len(items), batch_size):
            batch = items[i : i + batch_size]
            result = batch_fn(batch)
            if isinstance(result, list):
                batched_results.extend(result)
            else:
                batched_results.append(result)
        optimized_ms = (time.perf_counter() - t0) * 1000
        speedup = baseline_ms / max(optimized_ms, 1e-9)
        return batched_results, LatencyOptimizationResult(
            strategy="batch",
            baseline_ms=baseline_ms,
            optimized_ms=optimized_ms,
            speedup=speedup,
            reduction_pct=(baseline_ms - optimized_ms) / max(baseline_ms, 1),
            metadata={"batch_size": batch_size, "num_items": len(items)},
        )

    def clear_cache(self) -> None:
        self._cache.clear()
        self._precomputed.clear()


def memoize(profiler: Optional[Any] = None):
    """Decorator for memoization."""
    cache: Dict[Any, Any] = {}

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            key = (args, tuple(sorted(kwargs.items())))
            if key not in cache:
                cache[key] = func(*args, **kwargs)
            return cache[key]
        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {"size": len(cache)}
        return wrapper
    return decorator
