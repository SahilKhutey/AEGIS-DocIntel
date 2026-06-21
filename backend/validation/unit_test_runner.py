"""
Unit Test Runner
=================

Runs individual component tests.
"""

from __future__ import annotations

import importlib
import inspect
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import TestFailureError


@dataclass
class UnitTestResult:
    """Result of a single unit test."""

    test_name: str
    component: str
    passed: bool
    duration_ms: float
    error_message: Optional[str] = None
    traceback: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "component": self.component,
            "passed": self.passed,
            "duration_ms": round(self.duration_ms, 3),
            "error_message": self.error_message,
            "metadata": self.metadata,
        }


class UnitTestRunner:
    """
    Run unit tests on individual components.

    Tests should be functions or methods that:
        - Take no arguments (or fixed arguments)
        - Raise AssertionError or TestFailureError on failure
        - Return None or a metadata dict on success
    """

    def __init__(self, fail_fast: bool = False) -> None:
        self.fail_fast = fail_fast
        self.results: List[UnitTestResult] = []

    def run_test(
        self,
        test_fn: Callable,
        test_name: str,
        component: str = "unknown",
        timeout_s: float = 30.0,
    ) -> UnitTestResult:
        """Run a single unit test."""
        import time as _time
        t0 = _time.perf_counter()
        try:
            import signal
            # optional timeout via signal
            result = test_fn()
            duration = (_time.perf_counter() - t0) * 1000
            r = UnitTestResult(
                test_name=test_name,
                component=component,
                passed=True,
                duration_ms=duration,
                metadata=result if isinstance(result, dict) else {},
            )
            self.results.append(r)
            return r
        except AssertionError as exc:
            duration = (_time.perf_counter() - t0) * 1000
            r = UnitTestResult(
                test_name=test_name,
                component=component,
                passed=False,
                duration_ms=duration,
                error_message=str(exc),
            )
            self.results.append(r)
            if self.fail_fast:
                raise TestFailureError(f"{test_name}: {exc}")
            return r
        except Exception as exc:
            duration = (_time.perf_counter() - t0) * 1000
            r = UnitTestResult(
                test_name=test_name,
                component=component,
                passed=False,
                duration_ms=duration,
                error_message=str(exc),
                traceback=traceback.format_exc(),
            )
            self.results.append(r)
            if self.fail_fast:
                raise TestFailureError(f"{test_name}: {exc}")
            return r

    def run_tests(
        self,
        tests: List[Dict[str, Any]],
    ) -> List[UnitTestResult]:
        """
        Run a batch of unit tests.

        Parameters
        ----------
        tests : List[Dict]
            Each dict: {test_fn, test_name, component}.
        """
        return [
            self.run_test(
                test_fn=t["test_fn"],
                test_name=t["test_name"],
                component=t.get("component", "unknown"),
            )
            for t in tests
        ]

    def discover_and_run(
        self,
        module_path: str,
        pattern: str = "test_",
    ) -> List[UnitTestResult]:
        """Discover and run all test_* functions in a module."""
        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise TestFailureError(f"Cannot import {module_path}: {exc}")
        results = []
        for name, func in inspect.getmembers(module, inspect.isfunction):
            if name.startswith(pattern):
                results.append(
                    self.run_test(
                        test_fn=func,
                        test_name=name,
                        component=module_path,
                    )
                )
        return results

    def coverage_report(self) -> Dict[str, Any]:
        """Generate test coverage report."""
        total = len(self.results)
        passed = sum(1 for r in self.results if r.passed)
        failed = total - passed
        by_component: Dict[str, Dict[str, int]] = {}
        for r in self.results:
            by_component.setdefault(r.component, {"passed": 0, "failed": 0})
            if r.passed:
                by_component[r.component]["passed"] += 1
            else:
                by_component[r.component]["failed"] += 1
        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / max(total, 1),
            "by_component": by_component,
        }

    def assert_coverage(
        self,
        min_pass_rate: float = 0.95,
        min_tests: int = 0,
    ) -> None:
        """Assert that coverage meets threshold."""
        report = self.coverage_report()
        if report["total"] < min_tests:
            raise TestFailureError(
                f"Not enough tests: {report['total']} < {min_tests}"
            )
        if report["pass_rate"] < min_pass_rate:
            raise TestFailureError(
                f"Pass rate {report['pass_rate']:.2%} below "
                f"threshold {min_pass_rate:.2%}"
            )
