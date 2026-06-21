"""
Stress Test Runner
====================

Tests system behavior under high load.
"""

from __future__ import annotations

import concurrent.futures
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np

from .exceptions import StressTestFailure


@dataclass
class LoadProfile:
    """Stress test load profile."""

    name: str
    num_requests: int
    concurrency: int = 1
    duration_seconds: Optional[float] = None
    ramp_up_seconds: float = 0.0


@dataclass
class StressTestResult:
    """Result of stress test."""

    profile_name: str
    total_requests: int
    successful_requests: int
    failed_requests: int
    duration_seconds: float
    throughput_rps: float
    latency_p50_ms: float
    latency_p95_ms: float
    latency_p99_ms: float
    latency_max_ms: float
    errors: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "profile_name": self.profile_name,
            "total_requests": self.total_requests,
            "successful_requests": self.successful_requests,
            "failed_requests": self.failed_requests,
            "duration_seconds": round(self.duration_seconds, 3),
            "throughput_rps": round(self.throughput_rps, 4),
            "latency_p50_ms": round(self.latency_p50_ms, 2),
            "latency_p95_ms": round(self.latency_p95_ms, 2),
            "latency_p99_ms": round(self.latency_p99_ms, 2),
            "latency_max_ms": round(self.latency_max_ms, 2),
            "errors": self.errors,
        }


class StressTestRunner:
    """
    Run stress tests on the AMDI-OS pipeline.

    Tests:
        - High concurrency
        - Sustained load
        - Burst load
        - Resource exhaustion
    """

    def __init__(
        self,
        max_error_rate: float = 0.05,
        max_latency_p99_ms: float = 30_000,
    ) -> None:
        self.max_error_rate = max_error_rate
        self.max_latency_p99_ms = max_latency_p99_ms
        self.results: List[StressTestResult] = []

    def run_load_test(
        self,
        load_fn: Callable,
        profile: LoadProfile,
    ) -> StressTestResult:
        """
        Run a load test.

        Parameters
        ----------
        load_fn : Callable
            Function to invoke (with no arguments).
        profile : LoadProfile
            Load configuration.
        """
        latencies: List[float] = []
        errors: Dict[str, int] = {}
        successful = 0
        failed = 0
        t0 = time.perf_counter()
        # ramp up
        if profile.ramp_up_seconds > 0:
            time.sleep(profile.ramp_up_seconds)
        with concurrent.futures.ThreadPoolExecutor(
            max_workers=profile.concurrency
        ) as executor:
            futures = []
            for i in range(profile.num_requests):
                if (
                    profile.duration_seconds is not None
                    and (time.perf_counter() - t0) >= profile.duration_seconds
                ):
                    break
                futures.append(executor.submit(_timed_call, load_fn, i))
            for future in concurrent.futures.as_completed(futures):
                try:
                    latency, success, error = future.result()
                    latencies.append(latency)
                    if success:
                        successful += 1
                    else:
                        failed += 1
                        if error:
                            errors[error] = errors.get(error, 0) + 1
                except Exception as exc:
                    failed += 1
                    errors[str(exc)] = errors.get(str(exc), 0) + 1
        total_time = time.perf_counter() - t0
        if not latencies:
            return StressTestResult(
                profile_name=profile.name,
                total_requests=0,
                successful_requests=0,
                failed_requests=0,
                duration_seconds=total_time,
                throughput_rps=0.0,
                latency_p50_ms=0,
                latency_p95_ms=0,
                latency_p99_ms=0,
                latency_max_ms=0,
                errors=errors,
            )
        arr = np.array(latencies)
        total = successful + failed
        rps = total / max(total_time, 1e-9)
        result = StressTestResult(
            profile_name=profile.name,
            total_requests=total,
            successful_requests=successful,
            failed_requests=failed,
            duration_seconds=total_time,
            throughput_rps=rps,
            latency_p50_ms=float(np.percentile(arr, 50)),
            latency_p95_ms=float(np.percentile(arr, 95)),
            latency_p99_ms=float(np.percentile(arr, 99)),
            latency_max_ms=float(arr.max()),
            errors=errors,
        )
        self.results.append(result)
        self._validate(result)
        return result

    def _validate(self, result: StressTestResult) -> None:
        """Validate stress test result against thresholds."""
        error_rate = result.failed_requests / max(result.total_requests, 1)
        if error_rate > self.max_error_rate:
            raise StressTestFailure(
                f"Error rate {error_rate:.2%} exceeds threshold "
                f"{self.max_error_rate:.2%}"
            )
        if result.latency_p99_ms > self.max_latency_p99_ms:
            raise StressTestFailure(
                f"p99 latency {result.latency_p99_ms:.0f}ms exceeds "
                f"threshold {self.max_latency_p99_ms:.0f}ms"
            )

    def find_breaking_point(
        self,
        load_fn: Callable,
        start_concurrency: int = 1,
        max_concurrency: int = 100,
        step: int = 5,
        num_requests_per_step: int = 50,
    ) -> Dict[str, Any]:
        """Find the concurrency level where the system breaks."""
        results = []
        for c in range(start_concurrency, max_concurrency + 1, step):
            profile = LoadProfile(
                name=f"ramp_{c}",
                num_requests=num_requests_per_step,
                concurrency=c,
            )
            try:
                r = self.run_load_test(load_fn, profile)
                results.append({
                    "concurrency": c,
                    "throughput_rps": r.throughput_rps,
                    "latency_p95_ms": r.latency_p95_ms,
                    "error_rate": r.failed_requests / max(r.total_requests, 1),
                })
            except StressTestFailure as exc:
                return {
                    "breaking_point": c,
                    "last_successful": results[-1] if results else None,
                    "reason": str(exc),
                    "history": results,
                }
        return {
            "breaking_point": None,
            "max_tested": max_concurrency,
            "history": results,
        }


def _timed_call(fn: Callable, index: int) -> tuple:
    """Time a function call."""
    t0 = time.perf_counter()
    try:
        fn()
        return (time.perf_counter() - t0) * 1000, True, None
    except Exception as exc:
        return (time.perf_counter() - t0) * 1000, False, str(exc)
