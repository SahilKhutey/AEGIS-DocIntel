"""
Baseline Comparator
====================

Compares AMDI-OS against baseline pipelines:

    1. Vanilla RAG: PDF → OCR → Chunk → Embed → VectorDB → LLM
    2. Direct LLM: PDF text → LLM (no retrieval)
    3. AMDI-OS: full pipeline

Outputs improvement metrics (AMDI - baseline).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BaselineResult:
    """Comparison result between AMDI-OS and a baseline."""

    baseline_name: str
    baseline_accuracy: float
    amdi_accuracy: float
    accuracy_improvement: float  # AMDI - baseline
    relative_improvement: float  # (AMDI - baseline) / baseline
    baseline_latency_ms: float
    amdi_latency_ms: float
    latency_change_pct: float
    baseline_tokens: int
    amdi_tokens: int
    token_reduction_pct: float
    baseline_cost_usd: float
    amdi_cost_usd: float
    cost_reduction_pct: float
    num_questions: int

    def to_dict(self) -> dict:
        return {
            "baseline_name": self.baseline_name,
            "baseline_accuracy": round(self.baseline_accuracy, 4),
            "amdi_accuracy": round(self.amdi_accuracy, 4),
            "accuracy_improvement": round(self.accuracy_improvement, 4),
            "relative_improvement": round(self.relative_improvement, 4),
            "baseline_latency_ms": round(self.baseline_latency_ms, 2),
            "amdi_latency_ms": round(self.amdi_latency_ms, 2),
            "latency_change_pct": round(self.latency_change_pct, 2),
            "baseline_tokens": self.baseline_tokens,
            "amdi_tokens": self.amdi_tokens,
            "token_reduction_pct": round(self.token_reduction_pct, 2),
            "baseline_cost_usd": round(self.baseline_cost_usd, 6),
            "amdi_cost_usd": round(self.amdi_cost_usd, 6),
            "cost_reduction_pct": round(self.cost_reduction_pct, 2),
            "num_questions": self.num_questions,
        }


class BaselineComparator:
    """Compare AMDI-OS performance against baseline runs."""

    def __init__(self) -> None:
        pass

    def compare(
        self,
        baseline_name: str,
        baseline_metrics: Dict[str, Any],
        amdi_metrics: Dict[str, Any],
        num_questions: int,
    ) -> BaselineResult:
        # Accuracy improvement
        b_acc = baseline_metrics.get("accuracy", 0.0)
        a_acc = amdi_metrics.get("accuracy", 0.0)
        acc_imp = a_acc - b_acc
        rel_imp = acc_imp / b_acc if b_acc > 0 else 0.0

        # Latency change
        b_lat = baseline_metrics.get("latency_ms", 1.0)
        a_lat = amdi_metrics.get("latency_ms", 1.0)
        lat_change = ((a_lat - b_lat) / b_lat) * 100 if b_lat > 0 else 0.0

        # Token reduction
        b_tokens = baseline_metrics.get("tokens", 0)
        a_tokens = amdi_metrics.get("tokens", 0)
        token_red = ((b_tokens - a_tokens) / b_tokens) * 100 if b_tokens > 0 else 0.0

        # Cost reduction
        b_cost = baseline_metrics.get("cost_usd", 0.0)
        a_cost = amdi_metrics.get("cost_usd", 0.0)
        cost_red = ((b_cost - a_cost) / b_cost) * 100 if b_cost > 0.0 else 0.0

        return BaselineResult(
            baseline_name=baseline_name,
            baseline_accuracy=b_acc,
            amdi_accuracy=a_acc,
            accuracy_improvement=acc_imp,
            relative_improvement=rel_imp,
            baseline_latency_ms=b_lat,
            amdi_latency_ms=a_lat,
            latency_change_pct=lat_change,
            baseline_tokens=b_tokens,
            amdi_tokens=a_tokens,
            token_reduction_pct=token_red,
            baseline_cost_usd=b_cost,
            amdi_cost_usd=a_cost,
            cost_reduction_pct=cost_red,
            num_questions=num_questions,
        )
