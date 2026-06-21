"""
Integration Test Runner
========================

Tests interactions between components.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

from .exceptions import TestFailureError
from .unit_test_runner import UnitTestResult


@dataclass
class IntegrationTestResult:
    """Result of integration test."""

    test_name: str
    components_tested: List[str]
    passed: bool
    duration_ms: float
    data_flow_validated: bool = False
    contract_violations: List[str] = field(default_factory=list)
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "components_tested": self.components_tested,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 3),
            "data_flow_validated": self.data_flow_validated,
            "contract_violations": self.contract_violations,
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class IntegrationTestRunner:
    """
    Run integration tests across multiple components.

    Verifies:
        - Data flows correctly between components
        - Interfaces / contracts are respected
        - State is preserved across handoffs
        - Error handling is consistent
    """

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast
        self.results: List[IntegrationTestResult] = []

    def run_integration(
        self,
        test_name: str,
        components_tested: List[str],
        integration_fn: Callable[[], Dict[str, Any]],
        contract_checks: Optional[List[Tuple[str, Any, Callable]]] = None,
    ) -> IntegrationTestResult:
        """
        Run an integration test.

        Parameters
        ----------
        test_name : str
        components_tested : List[str]
            Names of components being tested together.
        integration_fn : Callable
            Function that runs the integration and returns results.
        contract_checks : Optional[List[Tuple[str, Any, Callable]]]
            List of (name, expected_value, actual_extractor) checks.
        """
        import time as _time
        t0 = _time.perf_counter()
        contract_violations: List[str] = []
        data_flow_validated = True
        try:
            result = integration_fn()
            duration = (_time.perf_counter() - t0) * 1000
            # run contract checks
            if contract_checks:
                for name, expected, actual_fn in contract_checks:
                    actual = actual_fn(result)
                    if not self._check_contract(name, expected, actual):
                        contract_violations.append(
                            f"{name}: expected {expected}, got {actual}"
                        )
                        data_flow_validated = False
            r = IntegrationTestResult(
                test_name=test_name,
                components_tested=components_tested,
                passed=len(contract_violations) == 0,
                duration_ms=duration,
                data_flow_validated=data_flow_validated,
                contract_violations=contract_violations,
                metadata=result if isinstance(result, dict) else {},
            )
            self.results.append(r)
            return r
        except Exception as exc:
            duration = (_time.perf_counter() - t0) * 1000
            r = IntegrationTestResult(
                test_name=test_name,
                components_tested=components_tested,
                passed=False,
                duration_ms=duration,
                error_message=str(exc),
            )
            self.results.append(r)
            if self.fail_fast:
                raise TestFailureError(f"{test_name}: {exc}")
            return r

    def test_data_flow(
        self,
        test_name: str,
        source_output: Any,
        target_input_schema: Dict[str, type],
        target_fn: Callable,
    ) -> IntegrationTestResult:
        """Test that source output is accepted by target."""
        if not isinstance(source_output, dict):
            missing = ["not_a_dict"]
        else:
            missing = [
                k for k, t in target_input_schema.items()
                if k not in source_output
                or not isinstance(source_output[k], t)
            ]
        if missing:
            return IntegrationTestResult(
                test_name=test_name,
                components_tested=["source", "target"],
                passed=False,
                duration_ms=0,
                contract_violations=[f"missing_keys:{missing}"],
            )
        try:
            result = target_fn(source_output)
            return IntegrationTestResult(
                test_name=test_name,
                components_tested=["source", "target"],
                passed=True,
                duration_ms=0,
                data_flow_validated=True,
                metadata={"result_type": type(result).__name__},
            )
        except Exception as exc:
            return IntegrationTestResult(
                test_name=test_name,
                components_tested=["source", "target"],
                passed=False,
                duration_ms=0,
                error_message=str(exc),
            )

    def summary(self) -> Dict[str, Any]:
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        return {
            "total": total,
            "passed": passed,
            "failed": total - passed,
            "pass_rate": passed / max(total, 1),
            "contract_violations": sum(
                len(r.contract_violations) for r in self.results
            ),
        }

    @staticmethod
    def _check_contract(name: str, expected: Any, actual: Any) -> bool:
        if callable(expected):
            return bool(expected(actual))
        if isinstance(expected, type):
            return isinstance(actual, expected)
        return actual == expected
