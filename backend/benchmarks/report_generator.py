"""
Report Generator
================

Generates benchmark reports in Markdown and JSON.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .baseline import BaselineResult
from .metrics_aggregator import AggregatedMetrics
from .statistical_tests import SignificanceResult


@dataclass
class BenchmarkReport:
    """Benchmark suite execution report."""

    suite_name: str
    timestamp: str
    aggregated: AggregatedMetrics
    significance: Dict[str, SignificanceResult] = field(default_factory=dict)
    baselines: Dict[str, BaselineResult] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp,
            "aggregated": self.aggregated.to_dict(),
            "significance": {k: v.to_dict() for k, v in self.significance.items()},
            "baselines": {k: v.to_dict() for k, v in self.baselines.items()},
            "metadata": self.metadata,
        }

    def to_markdown(self) -> str:
        md = f"# AMDI-OS Benchmark Report: {self.suite_name}\n"
        md += f"Generated at: {self.timestamp}\n\n"
        
        md += "## Aggregated Performance Metrics\n"
        md += "| Metric | Value |\n"
        md += "| --- | --- |\n"
        md += f"| Accuracy | {self.aggregated.accuracy:.4f} |\n"
        md += f"| Precision | {self.aggregated.precision:.4f} |\n"
        md += f"| Recall | {self.aggregated.recall:.4f} |\n"
        md += f"| F1 Score | {self.aggregated.f1:.4f} |\n"
        md += f"| Mean Latency | {self.aggregated.latency_mean_ms:.2f} ms |\n"
        md += f"| Peak Memory | {self.aggregated.memory_peak_mb:.2f} MB |\n"
        md += f"| Total Tokens | {self.aggregated.total_tokens} |\n"
        md += f"| Total Cost | ${self.aggregated.total_cost_usd:.6f} |\n\n"

        if self.baselines:
            md += "## Baseline Comparisons\n"
            for name, res in self.baselines.items():
                md += f"### vs {name}\n"
                md += f"- **Accuracy Improvement**: {res.accuracy_improvement:+.4f} ({res.relative_improvement:+.2%})\n"
                md += f"- **Latency Change**: {res.latency_change_pct:+.2f}%\n"
                md += f"- **Token Reduction**: {res.token_reduction_pct:+.2f}%\n"
                md += f"- **Cost Reduction**: {res.cost_reduction_pct:+.2f}%\n\n"

        if self.significance:
            md += "## Statistical Significance\n"
            for test, res in self.significance.items():
                md += f"- **{test}**: p-value = {res.p_value:.6f} (Significant: {res.significant})\n"
        return md


class ReportGenerator:
    """Generates structured benchmarking reports."""

    def __init__(self) -> None:
        pass

    def generate(
        self,
        suite_name: str,
        aggregated: AggregatedMetrics,
        significance: Optional[Dict[str, SignificanceResult]] = None,
        baselines: Optional[Dict[str, BaselineResult]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> BenchmarkReport:
        return BenchmarkReport(
            suite_name=suite_name,
            timestamp=datetime.now(timezone.utc).isoformat(),
            aggregated=aggregated,
            significance=significance or {},
            baselines=baselines or {},
            metadata=metadata or {},
        )
