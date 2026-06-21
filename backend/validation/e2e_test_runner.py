"""
End-to-End Test Runner
========================

Runs full pipeline tests with real documents.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import TestFailureError


@dataclass
class E2ETestResult:
    """Result of an end-to-end test."""

    test_name: str
    passed: bool
    duration_ms: float
    input_document: Optional[str] = None
    query: Optional[str] = None
    answer: Optional[str] = None
    expected_answer: Optional[str] = None
    accuracy: Optional[float] = None
    citation_count: int = 0
    token_count: int = 0
    error_message: Optional[str] = None
    pipeline_stages: Dict[str, float] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 3),
            "input_document": self.input_document,
            "query": self.query,
            "answer": self.answer[:200] if self.answer else None,
            "expected_answer": self.expected_answer[:200] if self.expected_answer else None,
            "accuracy": round(self.accuracy, 4) if self.accuracy else None,
            "citation_count": self.citation_count,
            "token_count": self.token_count,
            "error_message": self.error_message,
            "pipeline_stages": {k: round(v, 2) for k, v in self.pipeline_stages.items()},
        }


class E2ETestRunner:
    """
    End-to-end test runner.

    Validates:
        - Full pipeline runs successfully
        - Output matches expected answer (when provided)
        - Citations are present and valid
        - Token usage is within budget
        - Latency is acceptable
    """

    def __init__(
        self,
        accuracy_threshold: float = 0.7,
        latency_threshold_ms: float = 30_000,
        token_budget: int = 8000,
        require_citations: bool = False,
    ) -> None:
        self.accuracy_threshold = accuracy_threshold
        self.latency_threshold_ms = latency_threshold_ms
        self.token_budget = token_budget
        self.require_citations = require_citations
        self.results: List[E2ETestResult] = []

    def run_e2e(
        self,
        test_name: str,
        pipeline_fn: Callable,
        input_document: Any,
        query: str,
        expected_answer: Optional[str] = None,
        accuracy_fn: Optional[Callable[[str, str], float]] = None,
    ) -> E2ETestResult:
        """
        Run an end-to-end test.

        Parameters
        ----------
        test_name : str
        pipeline_fn : Callable
            Function that takes (input_document, query) and returns Dict with
            keys: answer, citations, tokens, metadata.
        input_document : Any
        query : str
        expected_answer : Optional[str]
        accuracy_fn : Optional[Callable]
            Function (predicted, expected) → accuracy in [0, 1].
        """
        t0 = time.perf_counter()
        try:
            output = pipeline_fn(input_document, query)
            duration_ms = (time.perf_counter() - t0) * 1000
            answer = output.get("answer", "")
            citations = output.get("citations", [])
            tokens = output.get("tokens", 0)
            stages = output.get("stage_times", {})
            # accuracy
            accuracy = None
            if expected_answer is not None:
                if accuracy_fn:
                    accuracy = accuracy_fn(answer, expected_answer)
                else:
                    accuracy = _default_accuracy(answer, expected_answer)
            # validation
            passed = True
            error_message = None
            if accuracy is not None and accuracy < self.accuracy_threshold:
                passed = False
                error_message = f"accuracy {accuracy:.2%} below threshold"
            if duration_ms > self.latency_threshold_ms:
                passed = False
                error_message = (
                    f"latency {duration_ms:.0f}ms exceeds "
                    f"threshold {self.latency_threshold_ms:.0f}ms"
                )
            if tokens > self.token_budget:
                passed = False
                error_message = f"tokens {tokens} exceed budget {self.token_budget}"
            if self.require_citations and len(citations) == 0:
                passed = False
                error_message = "no citations provided"
            r = E2ETestResult(
                test_name=test_name,
                passed=passed,
                duration_ms=duration_ms,
                input_document=str(input_document)[:100],
                query=query,
                answer=answer,
                expected_answer=expected_answer,
                accuracy=accuracy,
                citation_count=len(citations),
                token_count=tokens,
                error_message=error_message,
                pipeline_stages=stages,
                metadata=output.get("metadata", {}),
            )
            self.results.append(r)
            return r
        except Exception as exc:
            duration_ms = (time.perf_counter() - t0) * 1000
            r = E2ETestResult(
                test_name=test_name,
                passed=False,
                duration_ms=duration_ms,
                input_document=str(input_document)[:100],
                query=query,
                error_message=str(exc),
            )
            self.results.append(r)
            return r

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        avg_accuracy = (
            sum(r.accuracy for r in self.results if r.accuracy is not None)
            / max(sum(1 for r in self.results if r.accuracy is not None), 1)
        )
        avg_latency = (
            sum(r.duration_ms for r in self.results) / max(total, 1)
        )
        avg_tokens = (
            sum(r.token_count for r in self.results) / max(total, 1)
        )
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / max(total, 1),
            "avg_accuracy": round(avg_accuracy, 4),
            "avg_latency_ms": round(avg_latency, 2),
            "avg_tokens": round(avg_tokens, 2),
        }


def _default_accuracy(predicted: str, expected: str) -> float:
    """Default accuracy via token F1."""
    import re
    pred_tokens = set(re.findall(r"\w+", predicted.lower()))
    exp_tokens = set(re.findall(r"\w+", expected.lower()))
    if not pred_tokens or not exp_tokens:
        return 0.0
    common = pred_tokens & exp_tokens
    p = len(common) / len(pred_tokens)
    r = len(common) / len(exp_tokens)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)
