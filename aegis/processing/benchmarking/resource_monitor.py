"""
aegis.processing.benchmarking.resource_monitor
==============================================
Performance profiling for document processing: latency (median, p95, p99),
throughput (pages/sec), and memory tracking.
"""

from __future__ import annotations

import statistics
import time
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class PerformanceMetrics(BaseModel):
    total_documents: int
    total_pages: int
    total_elapsed_seconds: float
    throughput_pages_per_sec: float
    latency_per_doc_median_ms: float
    latency_per_doc_p95_ms: float
    latency_per_doc_p99_ms: float
    latency_per_page_median_ms: float
    latency_per_page_p95_ms: float
    latency_per_page_p99_ms: float
    peak_memory_mb: Optional[float] = None


class ResourceMonitor:
    """Profiles latency distributions and throughput across document processing batches."""

    @staticmethod
    def calculate_percentiles(values: List[float]) -> Tuple[float, float, float]:
        """Compute median, p95, and p99 from a list of measurements."""
        if not values:
            return 0.0, 0.0, 0.0
        sorted_vals = sorted(values)
        n = len(sorted_vals)
        median_val = statistics.median(sorted_vals)

        # p95 and p99 indices
        idx_95 = min(int(n * 0.95), n - 1)
        idx_99 = min(int(n * 0.99), n - 1)

        p95_val = sorted_vals[idx_95]
        p99_val = sorted_vals[idx_99]

        return round(median_val, 2), round(p95_val, 2), round(p99_val, 2)

    @classmethod
    def summarize(
        cls,
        doc_latencies_ms: List[float],
        page_latencies_ms: List[float],
        total_pages: int,
        total_elapsed_seconds: float,
        peak_memory_mb: Optional[float] = None
    ) -> PerformanceMetrics:
        """Aggregate performance statistics."""
        d_med, d_95, d_99 = cls.calculate_percentiles(doc_latencies_ms)
        p_med, p_95, p_99 = cls.calculate_percentiles(page_latencies_ms)

        throughput = (total_pages / total_elapsed_seconds) if total_elapsed_seconds > 0 else 0.0

        return PerformanceMetrics(
            total_documents=len(doc_latencies_ms),
            total_pages=total_pages,
            total_elapsed_seconds=round(total_elapsed_seconds, 4),
            throughput_pages_per_sec=round(throughput, 2),
            latency_per_doc_median_ms=d_med,
            latency_per_doc_p95_ms=d_95,
            latency_per_doc_p99_ms=d_99,
            latency_per_page_median_ms=p_med,
            latency_per_page_p95_ms=p_95,
            latency_per_page_p99_ms=p_99,
            peak_memory_mb=peak_memory_mb,
        )
