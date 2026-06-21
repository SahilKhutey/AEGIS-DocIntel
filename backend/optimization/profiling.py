"""
Profiling Utilities
====================

Lightweight profiling decorators and context managers.
"""

from __future__ import annotations

import functools
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class ProfileResult:
    """Result of profiling a function."""

    name: str
    total_calls: int
    total_time_ms: float
    mean_time_ms: float
    median_time_ms: float
    min_time_ms: float
    max_time_ms: float
    p95_time_ms: float
    p99_time_ms: float
    last_peak_memory_mb: float = 0.0

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "total_calls": self.total_calls,
            "total_time_ms": round(self.total_time_ms, 3),
            "mean_time_ms": round(self.mean_time_ms, 3),
            "median_time_ms": round(self.median_time_ms, 3),
            "min_time_ms": round(self.min_time_ms, 3),
            "max_time_ms": round(self.max_time_ms, 3),
            "p95_time_ms": round(self.p95_time_ms, 3),
            "p99_time_ms": round(self.p99_time_ms, 3),
            "last_peak_memory_mb": round(self.last_peak_memory_mb, 3),
        }


class Profiler:
    """
    Lightweight function profiler.

    Usage:
        profiler = Profiler()
        with profiler.profile("operation"):
            do_something()
        print(profiler.get_results())
    """

    def __init__(self, history_size: int = 1000) -> None:
        self.history_size = history_size
        self.timings: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )
        self.memory: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=history_size)
        )

    @contextmanager
    def profile(self, name: str):
        """Context manager for profiling."""
        t0 = time.perf_counter()
        try:
            import psutil
            import os
            process = psutil.Process(os.getpid())
            mem_before = process.memory_info().rss / (1024 * 1024)
        except ImportError:
            mem_before = 0.0
        try:
            yield
        finally:
            elapsed = (time.perf_counter() - t0) * 1000
            self.timings[name].append(elapsed)
            try:
                import psutil
                import os
                process = psutil.Process(os.getpid())
                mem_after = process.memory_info().rss / (1024 * 1024)
                self.memory[name].append(max(mem_after - mem_before, 0.0))
            except ImportError:
                pass

    def get_results(self) -> Dict[str, ProfileResult]:
        """Get aggregated results."""
        import numpy as np
        results: Dict[str, ProfileResult] = {}
        for name, timings in self.timings.items():
            arr = np.array(list(timings))
            mems = list(self.memory.get(name, []))
            results[name] = ProfileResult(
                name=name,
                total_calls=len(arr),
                total_time_ms=float(arr.sum()),
                mean_time_ms=float(arr.mean()),
                median_time_ms=float(np.median(arr)),
                min_time_ms=float(arr.min()),
                max_time_ms=float(arr.max()),
                p95_time_ms=float(np.percentile(arr, 95)),
                p99_time_ms=float(np.percentile(arr, 99)),
                last_peak_memory_mb=float(mems[-1]) if mems else 0.0,
            )
        return results

    def reset(self) -> None:
        self.timings.clear()
        self.memory.clear()


def profile(profiler: Profiler, name: str):
    """Decorator to profile a function."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            with profiler.profile(name):
                return func(*args, **kwargs)
        return wrapper
    return decorator
