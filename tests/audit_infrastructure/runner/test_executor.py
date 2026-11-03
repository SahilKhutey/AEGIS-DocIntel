"""
Unit tests for AuditExecutor and TimeoutManager (RUN-004, RUN-005, RUN-006, RUN-007, RUN-008).
"""

import time
import pytest
from aegis.audit.runner.exceptions import SuiteValidationError, TimeoutException
from aegis.audit.runner.executor import AuditExecutor
from aegis.audit.runner.planner import PlannedSuite
from aegis.audit.runner.timeout_manager import TimeoutManager
from aegis.audit.suites.base import BaseAuditSuite


class MockContext:
    def __init__(self):
        self.cleanup_calls = []

    def record_cleanup_error(self, suite_id, exc):
        self.cleanup_calls.append((suite_id, exc))


class PassingSuite(BaseAuditSuite):
    suite_id = "pass_test"
    suite_version = "1.0.0"
    def validate(self, ctx): pass
    def execute(self, ctx):
        return {"status": "PASSED", "statistics": {"total": 2, "passed": 2, "failed": 0, "skipped": 0, "errors": 0}}
    def cleanup(self, ctx):
        ctx.cleanup_calls.append("PassingSuite.cleanup")


class FailingSuite(BaseAuditSuite):
    suite_id = "fail_test"
    suite_version = "1.0.0"
    def validate(self, ctx): pass
    def execute(self, ctx):
        return {"status": "FAILED", "statistics": {"total": 1, "passed": 0, "failed": 1, "skipped": 0, "errors": 0}}
    def cleanup(self, ctx):
        ctx.cleanup_calls.append("FailingSuite.cleanup")


class ExceptionSuite(BaseAuditSuite):
    suite_id = "exc_test"
    suite_version = "1.0.0"
    def validate(self, ctx): pass
    def execute(self, ctx):
        raise RuntimeError("Catastrophic error inside suite execution")
    def cleanup(self, ctx):
        ctx.cleanup_calls.append("ExceptionSuite.cleanup")


class TimeoutSuite(BaseAuditSuite):
    suite_id = "timeout_test"
    suite_version = "1.0.0"
    def validate(self, ctx): pass
    def execute(self, ctx):
        time.sleep(2.0)
        return {"status": "PASSED"}
    def cleanup(self, ctx):
        ctx.cleanup_calls.append("TimeoutSuite.cleanup")


def test_execute_passing_suite():
    ctx = MockContext()
    executor = AuditExecutor()
    planned = PlannedSuite(suite_id="pass_test", suite=PassingSuite(), timeout_seconds=5.0)
    res = executor.execute_suite(planned, ctx)
    assert res["status"] == "PASSED"
    assert "PassingSuite.cleanup" in ctx.cleanup_calls


def test_execute_failing_suite():
    ctx = MockContext()
    executor = AuditExecutor()
    planned = PlannedSuite(suite_id="fail_test", suite=FailingSuite(), timeout_seconds=5.0)
    res = executor.execute_suite(planned, ctx)
    assert res["status"] == "FAILED"
    assert "FailingSuite.cleanup" in ctx.cleanup_calls


def test_execute_exception_suite():
    ctx = MockContext()
    executor = AuditExecutor()
    planned = PlannedSuite(suite_id="exc_test", suite=ExceptionSuite(), timeout_seconds=5.0)
    res = executor.execute_suite(planned, ctx)
    assert res["status"] == "ERROR"
    assert res["error_type"] == "RuntimeError"
    assert "ExceptionSuite.cleanup" in ctx.cleanup_calls


def test_execute_timeout_suite():
    ctx = MockContext()
    executor = AuditExecutor()
    planned = PlannedSuite(suite_id="timeout_test", suite=TimeoutSuite(), timeout_seconds=0.2)
    res = executor.execute_suite(planned, ctx)
    assert res["status"] == "TIMEOUT"
    assert "TimeoutSuite.cleanup" in ctx.cleanup_calls


def test_timeout_manager_standalone():
    def fast_fn():
        return 42

    def slow_fn():
        time.sleep(0.5)
        return 99

    assert TimeoutManager.execute(fast_fn, timeout_seconds=1.0) == 42
    with pytest.raises(TimeoutException):
        TimeoutManager.execute(slow_fn, timeout_seconds=0.1)
