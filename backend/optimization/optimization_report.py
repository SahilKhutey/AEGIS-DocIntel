"""
Optimization Report
====================

Consolidates all optimization results and calculates overall pipeline performance metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .token_optimizer import TokenOptimizationResult
from .memory_optimizer import MemoryOptimizationResult
from .latency_optimizer import LatencyOptimizationResult
from .retrieval_optimizer import RetrievalOptimizationResult


@dataclass
class OptimizationMetrics:
    """Consolidated metrics for an optimization suite run."""

    token_reduction_pct: float
    memory_reduction_pct: float
    latency_reduction_pct: float
    retrieval_speedup: float
    overall_quality_score: float
    status: str  # "OPTIMIZED" or "FAILED"

    def to_dict(self) -> dict:
        return {
            "token_reduction_pct": round(self.token_reduction_pct, 4),
            "memory_reduction_pct": round(self.memory_reduction_pct, 4),
            "latency_reduction_pct": round(self.latency_reduction_pct, 4),
            "retrieval_speedup": round(self.retrieval_speedup, 4),
            "overall_quality_score": round(self.overall_quality_score, 4),
            "status": self.status,
        }


class OptimizationReport:
    """Consolidates results across all 4 optimization categories."""

    def __init__(self, suite_name: str) -> None:
        self.suite_name = suite_name
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.token_results: List[TokenOptimizationResult] = []
        self.memory_results: List[MemoryOptimizationResult] = []
        self.latency_results: List[LatencyOptimizationResult] = []
        self.retrieval_results: List[RetrievalOptimizationResult] = []

    def add_token_result(self, result: TokenOptimizationResult) -> None:
        self.token_results.append(result)

    def add_memory_result(self, result: MemoryOptimizationResult) -> None:
        self.memory_results.append(result)

    def add_latency_result(self, result: LatencyOptimizationResult) -> None:
        self.latency_results.append(result)

    def add_retrieval_result(self, result: RetrievalOptimizationResult) -> None:
        self.retrieval_results.append(result)

    def compute_metrics(self) -> OptimizationMetrics:
        """
        Compute consolidated optimization metrics.
        """
        # Token metrics
        if self.token_results:
            total_orig_tokens = sum(r.original_tokens for r in self.token_results)
            total_opt_tokens = sum(r.optimized_tokens for r in self.token_results)
            token_red = (total_orig_tokens - total_opt_tokens) / max(total_orig_tokens, 1)
            quality = sum(r.quality_score for r in self.token_results) / len(self.token_results)
        else:
            token_red = 0.0
            quality = 1.0

        # Memory metrics
        if self.memory_results:
            total_orig_bytes = sum(r.original_bytes for r in self.memory_results)
            total_opt_bytes = sum(r.optimized_bytes for r in self.memory_results)
            mem_red = (total_orig_bytes - total_opt_bytes) / max(total_orig_bytes, 1)
        else:
            mem_red = 0.0

        # Latency metrics
        if self.latency_results:
            total_base_lat = sum(r.baseline_ms for r in self.latency_results)
            total_opt_lat = sum(r.optimized_ms for r in self.latency_results)
            lat_red = (total_base_lat - total_opt_lat) / max(total_base_lat, 1)
        else:
            lat_red = 0.0

        # Retrieval metrics
        if self.retrieval_results:
            total_base_ret = sum(r.baseline_latency_ms for r in self.retrieval_results)
            total_opt_ret = sum(r.optimized_latency_ms for r in self.retrieval_results)
            ret_speedup = total_base_ret / max(total_opt_ret, 1e-9)
        else:
            ret_speedup = 1.0

        status = "OPTIMIZED" if (token_red > 0.0 or mem_red > 0.0 or lat_red > 0.0 or ret_speedup > 1.0) else "baseline"

        return OptimizationMetrics(
            token_reduction_pct=token_red,
            memory_reduction_pct=mem_red,
            latency_reduction_pct=lat_red,
            retrieval_speedup=ret_speedup,
            overall_quality_score=quality,
            status=status,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp,
            "metrics": self.compute_metrics().to_dict(),
            "results": {
                "token_optimizations": [r.to_dict() for r in self.token_results],
                "memory_optimizations": [r.to_dict() for r in self.memory_results],
                "latency_optimizations": [r.to_dict() for r in self.latency_results],
                "retrieval_optimizations": [r.to_dict() for r in self.retrieval_results],
            },
        }

    def to_json(self) -> str:
        """Serialize report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """Generate a formatted markdown report."""
        metrics = self.compute_metrics()
        
        md = []
        md.append(f"# Optimization Report: {self.suite_name}")
        md.append(f"Generated at: `{self.timestamp}`\n")
        
        md.append("## Summary Metrics")
        md.append("| Metric | Reduction Rate / Speedup | Status |")
        md.append("| --- | --- | --- |")
        md.append(f"| **Token Reduction** | `{metrics.token_reduction_pct:.2%}` | |")
        md.append(f"| **Memory Reduction** | `{metrics.memory_reduction_pct:.2%}` | |")
        md.append(f"| **Latency Reduction** | `{metrics.latency_reduction_pct:.2%}` | |")
        md.append(f"| **Retrieval Speedup** | `{metrics.retrieval_speedup:.2f}x` | |")
        md.append(f"| **Overall Status** | `{metrics.status}` | |")
        md.append("")

        if self.token_results:
            md.append("## Token Optimization Results")
            md.append("| Strategy | Original Tokens | Optimized Tokens | Saved | Reduction % | Quality |")
            md.append("| --- | --- | --- | --- | --- | --- |")
            for r in self.token_results:
                md.append(f"| {r.strategy} | {r.original_tokens} | {r.optimized_tokens} | {r.tokens_saved} | {r.reduction_pct:.2%} | {r.quality_score:.2f} |")
            md.append("")

        if self.memory_results:
            md.append("## Memory Optimization Results")
            md.append("| Strategy | Original Bytes | Optimized Bytes | Saved | Reduction % |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.memory_results:
                md.append(f"| {r.strategy} | {r.original_bytes} | {r.optimized_bytes} | {r.bytes_saved} | {r.reduction_pct:.2%} |")
            md.append("")

        if self.latency_results:
            md.append("## Latency Optimization Results")
            md.append("| Strategy | Baseline (ms) | Optimized (ms) | Speedup | Reduction % |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.latency_results:
                md.append(f"| {r.strategy} | {r.baseline_ms:.1f} | {r.optimized_ms:.1f} | {r.speedup:.2f}x | {r.reduction_pct:.2%} |")
            md.append("")

        if self.retrieval_results:
            md.append("## Retrieval Optimization Results")
            md.append("| Strategy | Baseline Latency (ms) | Optimized Latency (ms) | Speedup | Recall@K |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.retrieval_results:
                md.append(f"| {r.strategy} | {r.baseline_latency_ms:.1f} | {r.optimized_latency_ms:.1f} | {r.speedup:.2f}x | {r.recall_at_k:.2%} |")
            md.append("")

        return "\n".join(md)
