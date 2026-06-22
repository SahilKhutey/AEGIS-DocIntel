"""
Verification Report Structures
==============================

Data structures representing the results and metrics of the verification pipeline.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class VerificationMetrics:
    """Metrics compiled across all verifiers."""

    citation_accuracy: float
    fact_accuracy: float
    hallucination_rate: float
    consistency_score: float
    source_reliability: float
    composite_confidence: float

    def to_dict(self) -> dict:
        return {
            "citation_accuracy": round(self.citation_accuracy, 4),
            "fact_accuracy": round(self.fact_accuracy, 4),
            "hallucination_rate": round(self.hallucination_rate, 4),
            "consistency_score": round(self.consistency_score, 4),
            "source_reliability": round(self.source_reliability, 4),
            "composite_confidence": round(self.composite_confidence, 4),
        }


@dataclass
class VerificationReportData:
    """Complete container for verification results."""

    response_text: str
    metrics: VerificationMetrics
    citation_result: Any
    fact_result: Any
    hallucination_result: Any
    consistency_result: Any
    source_result: Any
    passed: bool
    grade: str
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "grade": self.grade,
            "metrics": self.metrics.to_dict(),
            "citation_result": self.citation_result.to_dict(),
            "fact_result": self.fact_result.to_dict(),
            "hallucination_result": self.hallucination_result.to_dict(),
            "consistency_result": self.consistency_result.to_dict(),
            "source_result": self.source_result.to_dict(),
            "issues": self.issues,
        }
