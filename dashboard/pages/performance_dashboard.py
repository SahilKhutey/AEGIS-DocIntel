"""
Performance Dashboard
======================

Engine-level metrics: latency, memory, throughput.
"""

from __future__ import annotations

import time
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class EngineMetric:
    """Performance metric for a single engine."""

    engine_name: str
    latency_ms: float
    memory_mb: float
    cpu_percent: float
    throughput: float  # docs/sec
    error_rate: float
    last_updated: float

    def to_dict(self) -> dict:
        return {
            "engine_name": self.engine_name,
            "latency_ms": round(self.latency_ms, 2),
            "memory_mb": round(self.memory_mb, 2),
            "cpu_percent": round(self.cpu_percent, 2),
            "throughput": round(self.throughput, 4),
            "error_rate": round(self.error_rate, 4),
            "last_updated": self.last_updated,
        }


@dataclass
class PerformanceViewData:
    """Performance dashboard data."""

    engine_metrics: List[EngineMetric] = field(default_factory=list)
    system_latency_p50: float = 0.0
    system_latency_p95: float = 0.0
    system_latency_p99: float = 0.0
    total_memory_mb: float = 0.0
    total_cpu_percent: float = 0.0
    requests_per_second: float = 0.0
    error_rate: float = 0.0
    uptime_seconds: float = 0.0

    def to_dict(self) -> dict:
        return {
            "engine_metrics": [e.to_dict() for e in self.engine_metrics],
            "system_latency_p50": round(self.system_latency_p50, 2),
            "system_latency_p95": round(self.system_latency_p95, 2),
            "system_latency_p99": round(self.system_latency_p99, 2),
            "total_memory_mb": round(self.total_memory_mb, 2),
            "total_cpu_percent": round(self.total_cpu_percent, 2),
            "requests_per_second": round(self.requests_per_second, 4),
            "error_rate": round(self.error_rate, 4),
            "uptime_seconds": round(self.uptime_seconds, 2),
        }


class PerformanceTracker:
    """Track per-call performance metrics."""

    def __init__(self, window_size: int = 1000) -> None:
        self.window_size = window_size
        self.latencies: Dict[str, deque] = {}
        self.errors: Dict[str, deque] = {}
        self.throughput: Dict[str, deque] = {}
        self.start_time = time.time()

    def record(
        self,
        engine_name: str,
        latency_ms: float,
        success: bool = True,
    ) -> None:
        if engine_name not in self.latencies:
            self.latencies[engine_name] = deque(maxlen=self.window_size)
            self.errors[engine_name] = deque(maxlen=self.window_size)
            self.throughput[engine_name] = deque(maxlen=self.window_size)
        self.latencies[engine_name].append(latency_ms)
        self.errors[engine_name].append(0 if success else 1)
        self.throughput[engine_name].append(time.time())

    def get_engine_metrics(self) -> List[EngineMetric]:
        metrics: List[EngineMetric] = []
        for name, latencies in self.latencies.items():
            errors = self.errors[name]
            throughput = self.throughput[name]
            error_rate = sum(errors) / max(len(errors), 1)
            tput = 0.0
            if len(throughput) >= 2:
                window = throughput[-1] - throughput[0]
                tput = (len(throughput) - 1) / max(window, 1e-9)
            metrics.append(
                EngineMetric(
                    engine_name=name,
                    latency_ms=float(np_mean(list(latencies))),
                    memory_mb=0.0,
                    cpu_percent=0.0,
                    throughput=tput,
                    error_rate=error_rate,
                    last_updated=time.time(),
                )
            )
        return metrics


def np_mean(values: List[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


class PerformanceDashboard:
    """Performance dashboard backend API."""

    def __init__(self, tracker: PerformanceTracker) -> None:
        self.tracker = tracker

    def get_view(self) -> PerformanceViewData:
        engine_metrics = self.tracker.get_engine_metrics()
        all_latencies: List[float] = []
        total_errors = 0
        total_requests = 0
        for m in engine_metrics:
            all_latencies.append(m.latency_ms)
            total_errors += int(m.error_rate * 100)
            total_requests += 100
        all_latencies.sort()
        p50 = _percentile(all_latencies, 50)
        p95 = _percentile(all_latencies, 95)
        p99 = _percentile(all_latencies, 99)
        error_rate = total_errors / max(total_requests, 1)
        uptime = time.time() - self.tracker.start_time
        return PerformanceViewData(
            engine_metrics=engine_metrics,
            system_latency_p50=p50,
            system_latency_p95=p95,
            system_latency_p99=p99,
            error_rate=error_rate,
            uptime_seconds=uptime,
        )


def _percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    k = (len(values) - 1) * (p / 100.0)
    f = int(k)
    c = min(f + 1, len(values) - 1)
    if f == c:
        return values[f]
    return values[f] + (values[c] - values[f]) * (k - f)
