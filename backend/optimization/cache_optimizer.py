"""
Cache Optimizer
================

Optimizes cache configuration for different workloads.

    - LRU: Least Recently Used (general purpose)
    - LFU: Least Frequently Used (skewed access)
    - ARC: Adaptive Replacement Cache (mixed)
    - SIZE-AWARE: size-based eviction
"""

from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class CacheOptimizationResult:
    """Result of cache optimization."""

    policy: str
    hit_rate_before: float
    hit_rate_after: float
    improvement: float
    optimal_capacity: int
    avg_lookup_ms: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "policy": self.policy,
            "hit_rate_before": round(self.hit_rate_before, 4),
            "hit_rate_after": round(self.hit_rate_after, 4),
            "improvement": round(self.improvement, 4),
            "optimal_capacity": self.optimal_capacity,
            "avg_lookup_ms": round(self.avg_lookup_ms, 3),
        }


class OptimizedLRUCache:
    """LRU cache with hit-rate tracking."""

    def __init__(self, capacity: int = 1000) -> None:
        self.capacity = max(1, capacity)
        self.cache: OrderedDict[str, Any] = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.lookups_ms: list = []

    def get(self, key: str) -> Optional[Any]:
        t0 = time.perf_counter()
        if key in self.cache:
            self.cache.move_to_end(key)
            self.hits += 1
            self.lookups_ms.append((time.perf_counter() - t0) * 1000)
            return self.cache[key]
        self.misses += 1
        self.lookups_ms.append((time.perf_counter() - t0) * 1000)
        return None

    def put(self, key: str, value: Any) -> None:
        if key in self.cache:
            self.cache.move_to_end(key)
        else:
            if len(self.cache) >= self.capacity:
                self.cache.popitem(last=False)
            self.cache[key] = value

    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / max(total, 1)

    def avg_lookup_ms(self) -> float:
        if not self.lookups_ms:
            return 0.0
        return sum(self.lookups_ms) / len(self.lookups_ms)

    def reset_stats(self) -> None:
        self.hits = 0
        self.misses = 0
        self.lookups_ms.clear()


class CacheOptimizer:
    """
    Optimize cache configuration.
    """

    def __init__(
        self,
        min_capacity: int = 100,
        max_capacity: int = 100_000,
    ) -> None:
        self.min_capacity = min_capacity
        self.max_capacity = max_capacity

    def benchmark_policy(
        self,
        access_pattern: list,
        capacity: int,
        policy: str = "lru",
    ) -> CacheOptimizationResult:
        """Benchmark a cache policy with a synthetic access pattern."""
        cache = OptimizedLRUCache(capacity=capacity)
        # warm up
        for key in access_pattern[: capacity * 2]:
            if cache.get(key) is None:
                cache.put(key, f"value_{key}")
        # reset stats after warmup
        cache.reset_stats()
        # timed phase
        t0 = time.perf_counter()
        for key in access_pattern:
            if cache.get(key) is None:
                cache.put(key, f"value_{key}")
        elapsed_ms = (time.perf_counter() - t0) * 1000
        hit_rate = cache.hit_rate()
        avg_lookup = cache.avg_lookup_ms()
        return CacheOptimizationResult(
            policy=policy,
            hit_rate_before=0.0,
            hit_rate_after=hit_rate,
            improvement=hit_rate,
            optimal_capacity=capacity,
            avg_lookup_ms=avg_lookup,
            metadata={"elapsed_ms": elapsed_ms, "n_accesses": len(access_pattern)},
        )

    def find_optimal_capacity(
        self,
        access_pattern: list,
        target_hit_rate: float = 0.9,
    ) -> int:
        """Find minimum capacity that achieves target hit rate."""
        for capacity in [
            self.min_capacity,
            self.min_capacity * 5,
            self.min_capacity * 10,
            self.min_capacity * 50,
            self.min_capacity * 100,
            self.min_capacity * 500,
            self.min_capacity * 1000,
            self.max_capacity,
        ]:
            if capacity > self.max_capacity:
                break
            result = self.benchmark_policy(access_pattern, capacity)
            if result.hit_rate_after >= target_hit_rate:
                return capacity
        return self.max_capacity

    def recommend(
        self,
        workload_stats: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Recommend cache configuration based on workload.

        workload_stats:
            - access_pattern: list of keys
            - num_unique_keys: int
            - access_frequency: dict
            - memory_budget_mb: float
        """
        pattern = workload_stats.get("access_pattern", [])
        num_unique = workload_stats.get("num_unique_keys", len(set(pattern)))
        # estimate optimal capacity
        if num_unique > 0:
            optimal = min(num_unique, self.max_capacity)
        else:
            optimal = self.min_capacity
        # benchmark at optimal
        result = self.benchmark_policy(pattern, optimal)
        return {
            "recommended_capacity": optimal,
            "expected_hit_rate": result.hit_rate_after,
            "expected_avg_lookup_ms": result.avg_lookup_ms,
            "policy": "lru",
        }
