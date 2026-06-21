"""

Latency Benchmark

==================



Measures response time across multiple runs and computes

distribution statistics (mean, median, p50, p95, p99).



Mathematical Foundation:

    μ = mean(latencies)

    σ = std(latencies)

    p_q = q-th percentile

    CV = σ / μ   (coefficient of variation)

"""



from __future__ import annotations



import time

from dataclasses import dataclass, field

from typing import Any, Callable, Dict, List, Optional



import numpy as np





@dataclass

class LatencyStats:

    """Latency distribution statistics."""



    mean_ms: float

    median_ms: float

    std_ms: float

    min_ms: float

    max_ms: float

    p50_ms: float

    p90_ms: float

    p95_ms: float

    p99_ms: float

    coefficient_of_variation: float

    throughput_per_sec: float



    def to_dict(self) -> dict:

        return {

            "mean_ms": round(self.mean_ms, 3),

            "median_ms": round(self.median_ms, 3),

            "std_ms": round(self.std_ms, 3),

            "min_ms": round(self.min_ms, 3),

            "max_ms": round(self.max_ms, 3),

            "p50_ms": round(self.p50_ms, 3),

            "p90_ms": round(self.p90_ms, 3),

            "p95_ms": round(self.p95_ms, 3),

            "p99_ms": round(self.p99_ms, 3),

            "coefficient_of_variation": round(self.coefficient_of_variation, 4),

            "throughput_per_sec": round(self.throughput_per_sec, 4),

        }





@dataclass

class LatencyResult:

    """Latency benchmark result."""



    operation: str

    num_runs: int

    total_time_ms: float

    stats: LatencyStats

    raw_latencies_ms: List[float] = field(default_factory=list)



    def to_dict(self) -> dict:

        return {

            "operation": self.operation,

            "num_runs": self.num_runs,

            "total_time_ms": round(self.total_time_ms, 3),

            "stats": self.stats.to_dict(),

        }





class LatencyBenchmark:

    """Run latency benchmarks."""



    def __init__(

        self,

        num_runs: int = 10,

        warmup_runs: int = 2,

    ) -> None:

        self.num_runs = max(1, num_runs)

        self.warmup_runs = max(0, warmup_runs)



    def benchmark(

        self,

        operation: Callable[[], Any],

        operation_name: str = "operation",

    ) -> LatencyResult:

        """Benchmark `operation` over multiple runs."""

        # warmup

        for _ in range(self.warmup_runs):

            operation()

        # timed runs

        latencies: List[float] = []

        for _ in range(self.num_runs):

            t0 = time.perf_counter()

            operation()

            latencies.append((time.perf_counter() - t0) * 1000)

        # stats

        arr = np.array(latencies)

        stats = LatencyStats(

            mean_ms=float(arr.mean()),

            median_ms=float(np.median(arr)),

            std_ms=float(arr.std()),

            min_ms=float(arr.min()),

            max_ms=float(arr.max()),

            p50_ms=float(np.percentile(arr, 50)),

            p90_ms=float(np.percentile(arr, 90)),

            p95_ms=float(np.percentile(arr, 95)),

            p99_ms=float(np.percentile(arr, 99)),

            coefficient_of_variation=(

                float(arr.std() / arr.mean()) if arr.mean() > 0 else 0.0

            ),

            throughput_per_sec=(

                1000.0 / float(arr.mean()) if arr.mean() > 0 else 0.0

            ),

        )

        return LatencyResult(

            operation=operation_name,

            num_runs=self.num_runs,

            total_time_ms=float(arr.sum()),

            stats=stats,

            raw_latencies_ms=latencies,

        )



    def benchmark_async(

        self,

        operation: Callable[[], Any],

        operation_name: str = "async_operation",

    ) -> LatencyResult:

        """Benchmark with concurrent execution."""

        import concurrent.futures

        latencies: List[float] = []

        # warmup

        for _ in range(self.warmup_runs):

            operation()

        with concurrent.futures.ThreadPoolExecutor() as executor:

            futures_list = []

            t0_all = time.perf_counter()

            for _ in range(self.num_runs):

                f = executor.submit(_timed_call, operation)

                futures_list.append(f)

            for f in concurrent.futures.as_completed(futures_list):

                latencies.append(f.result())

            total = (time.perf_counter() - t0_all) * 1000

        arr = np.array(latencies)

        stats = LatencyStats(

            mean_ms=float(arr.mean()),

            median_ms=float(np.median(arr)),

            std_ms=float(arr.std()),

            min_ms=float(arr.min()),

            max_ms=float(arr.max()),

            p50_ms=float(np.percentile(arr, 50)),

            p90_ms=float(np.percentile(arr, 90)),

            p95_ms=float(np.percentile(arr, 95)),

            p99_ms=float(np.percentile(arr, 99)),

            coefficient_of_variation=(

                float(arr.std() / arr.mean()) if arr.mean() > 0 else 0.0

            ),

            throughput_per_sec=(

                1000.0 / (total / max(self.num_runs, 1))

            ),

        )

        return LatencyResult(

            operation=operation_name,

            num_runs=self.num_runs,

            total_time_ms=total,

            stats=stats,

            raw_latencies_ms=latencies,

        )





def _timed_call(operation: Callable[[], Any]) -> float:

    t0 = time.perf_counter()

    operation()

    return (time.perf_counter() - t0) * 1000
