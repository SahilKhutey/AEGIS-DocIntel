"""
Validation Report
==================

Consolidates all validation results and calculates overall framework metrics.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from .unit_test_runner import UnitTestResult
from .integration_test_runner import IntegrationTestResult
from .e2e_test_runner import E2ETestResult
from .stress_test_runner import StressTestResult
from .robustness_test_runner import RobustnessTestResult
from .ablation_runner import AblationResult


@dataclass
class ValidationMetrics:
    """Consolidated metrics for a validation suite run."""

    total_tests: int
    passed_tests: int
    failed_tests: int
    coverage_pct: float  # C = (T_passing / T_total) * 100
    robustness_score: float  # R = (1/N) * sum(avg_accuracy_i) * 100
    avg_latency_ms: float
    max_memory_mb: float
    total_token_usage: int
    status: str  # "PASSED" or "FAILED"

    def to_dict(self) -> dict:
        return {
            "total_tests": self.total_tests,
            "passed_tests": self.passed_tests,
            "failed_tests": self.failed_tests,
            "coverage_pct": round(self.coverage_pct, 2),
            "robustness_score": round(self.robustness_score, 2),
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "max_memory_mb": round(self.max_memory_mb, 2),
            "total_token_usage": self.total_token_usage,
            "status": self.status,
        }


class ValidationReport:
    """Consolidates results across all 6 validation test categories."""

    def __init__(self, suite_name: str) -> None:
        self.suite_name = suite_name
        self.timestamp = datetime.now(timezone.utc).isoformat()
        self.unit_results: List[UnitTestResult] = []
        self.integration_results: List[IntegrationTestResult] = []
        self.e2e_results: List[E2ETestResult] = []
        self.stress_results: List[StressTestResult] = []
        self.robustness_results: List[RobustnessTestResult] = []
        self.ablation_results: List[AblationResult] = []

    def add_unit_results(self, results: List[UnitTestResult]) -> None:
        self.unit_results.extend(results)

    def add_integration_results(self, results: List[IntegrationTestResult]) -> None:
        self.integration_results.extend(results)

    def add_e2e_results(self, results: List[E2ETestResult]) -> None:
        self.e2e_results.extend(results)

    def add_stress_results(self, results: List[StressTestResult]) -> None:
        self.stress_results.extend(results)

    def add_robustness_results(self, results: List[RobustnessTestResult]) -> None:
        self.robustness_results.extend(results)

    def add_ablation_results(self, results: List[AblationResult]) -> None:
        self.ablation_results.extend(results)

    def compute_metrics(self) -> ValidationMetrics:
        """
        Compute consolidated validation metrics.
        """
        total = (
            len(self.unit_results)
            + len(self.integration_results)
            + len(self.e2e_results)
            + len(self.stress_results)
            + len(self.robustness_results)
            + len(self.ablation_results)
        )
        
        passed = (
            sum(1 for r in self.unit_results if r.passed)
            + sum(1 for r in self.integration_results if r.passed)
            + sum(1 for r in self.e2e_results if r.passed)
            + sum(1 for r in self.stress_results if r.failed_requests == 0)
            + sum(1 for r in self.robustness_results if r.success_rate >= 0.5)
            + sum(1 for r in self.ablation_results if r.passed)
        )
        # Note: adjust pass calculation to be robust
        passed_strict = (
            sum(1 for r in self.unit_results if r.passed)
            + sum(1 for r in self.integration_results if r.passed)
            + sum(1 for r in self.e2e_results if r.passed)
            # For stress tests, let's check if there are no errors or if it's considered passed
            + sum(1 for r in self.stress_results if r.failed_requests == 0)
            + sum(1 for r in self.robustness_results if r.success_rate >= 0.5)
            + sum(1 for r in self.ablation_results if r.passed)
        )

        coverage_pct = (passed_strict / max(total, 1)) * 100.0

        # Calculate robustness score: R = (1/N) * sum(avg_accuracy_i) * 100
        if self.robustness_results:
            robustness_score = (
                sum(r.avg_accuracy for r in self.robustness_results)
                / len(self.robustness_results)
            ) * 100.0
        else:
            robustness_score = 100.0

        # Latency average (from e2e tests)
        latencies = [r.duration_ms for r in self.e2e_results]
        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0

        # Max memory observed (from stress test metadata or custom tracking)
        memories = []
        for r in self.stress_results:
            if "peak_memory_mb" in r.metadata:
                memories.append(r.metadata["peak_memory_mb"])
        max_mem = max(memories) if memories else 0.0

        # Token usage
        tokens = sum(r.token_count for r in self.e2e_results)

        status = "PASSED" if coverage_pct >= 90.0 else "FAILED"

        return ValidationMetrics(
            total_tests=total,
            passed_tests=passed_strict,
            failed_tests=total - passed_strict,
            coverage_pct=coverage_pct,
            robustness_score=robustness_score,
            avg_latency_ms=avg_latency,
            max_memory_mb=max_mem,
            total_token_usage=tokens,
            status=status,
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary format."""
        return {
            "suite_name": self.suite_name,
            "timestamp": self.timestamp,
            "metrics": self.compute_metrics().to_dict(),
            "results": {
                "unit_tests": [r.to_dict() for r in self.unit_results],
                "integration_tests": [r.to_dict() for r in self.integration_results],
                "e2e_tests": [r.to_dict() for r in self.e2e_results],
                "stress_tests": [r.to_dict() for r in self.stress_results],
                "robustness_tests": [r.to_dict() for r in self.robustness_results],
                "ablation_studies": [r.to_dict() for r in self.ablation_results],
            },
        }

    def to_json(self) -> str:
        """Serialize report to JSON string."""
        return json.dumps(self.to_dict(), indent=2)

    def to_markdown(self) -> str:
        """Generate a formatted markdown report."""
        metrics = self.compute_metrics()
        
        md = []
        md.append(f"# Validation Report: {self.suite_name}")
        md.append(f"Generated at: `{self.timestamp}`\n")
        
        md.append("## Summary Metrics")
        md.append("| Metric | Value |")
        md.append("| --- | --- |")
        md.append(f"| **Overall Status** | `{metrics.status}` |")
        md.append(f"| **Test Coverage** | `{metrics.coverage_pct:.2f}%` ({metrics.passed_tests}/{metrics.total_tests} passed) |")
        md.append(f"| **Robustness Score** | `{metrics.robustness_score:.2f}%` |")
        md.append(f"| **Average Latency** | `{metrics.avg_latency_ms:.2f}ms` |")
        md.append(f"| **Tokens Used** | `{metrics.total_token_usage}` |")
        md.append("")

        if self.unit_results:
            md.append("## Unit Test Results")
            md.append("| Test Name | Component | Status | Duration (ms) |")
            md.append("| --- | --- | --- | --- |")
            for r in self.unit_results:
                status = "PASSED" if r.passed else "FAILED"
                md.append(f"| {r.test_name} | `{r.component}` | `{status}` | {r.duration_ms:.1f} |")
            md.append("")

        if self.integration_results:
            md.append("## Integration Test Results")
            md.append("| Test Name | Components Tested | Status | Data Flow Validated | Duration (ms) |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.integration_results:
                status = "PASSED" if r.passed else "FAILED"
                comps = ", ".join(r.components_tested)
                md.append(f"| {r.test_name} | `{comps}` | `{status}` | {r.data_flow_validated} | {r.duration_ms:.1f} |")
            md.append("")

        if self.e2e_results:
            md.append("## End-to-End Test Results")
            md.append("| Test Name | Status | Accuracy | Tokens | Latency (ms) |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.e2e_results:
                status = "PASSED" if r.passed else "FAILED"
                acc_val = f"{r.accuracy:.2%}" if r.accuracy is not None else "N/A"
                md.append(f"| {r.test_name} | `{status}` | {acc_val} | {r.token_count} | {r.duration_ms:.1f} |")
            md.append("")

        if self.stress_results:
            md.append("## Stress Test Results")
            md.append("| Load Profile | Concurrency | RPS | Latency p95 (ms) | Error Rate |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.stress_results:
                err_rate = r.failed_requests / max(r.total_requests, 1)
                md.append(f"| {r.profile_name} | {r.total_requests} | {r.throughput_rps:.2f} | {r.latency_p95_ms:.1f} | {err_rate:.2%} |")
            md.append("")

        if self.robustness_results:
            md.append("## Robustness Test Results")
            md.append("| Perturbation | Trials | Success Rate | Avg Accuracy | Degradation |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.robustness_results:
                md.append(f"| {r.perturbation} | {r.num_trials} | {r.success_rate:.2%} | {r.avg_accuracy:.2%} | {r.degradation:.2%} |")
            md.append("")

        if self.ablation_results:
            md.append("## Ablation Study Results")
            md.append("| Component | Status | Full Acc | Ablated Acc | Impact (Δ_accuracy) |")
            md.append("| --- | --- | --- | --- | --- |")
            for r in self.ablation_results:
                status = "PASSED" if r.passed else "FAILED"
                md.append(f"| {r.ablated_component} | `{status}` | {r.full_accuracy:.2%} | {r.ablated_accuracy:.2%} | {r.impact_accuracy:.2%} |")
            md.append("")

        return "\n".join(md)
