"""
Unit tests for AuditPlanner and AuditResultNormalizer (RUN-009, RUN-010, RUN-011, RUN-012).
"""

import pytest
from aegis.audit.runner.exceptions import SuiteNotFoundError
from aegis.audit.runner.planner import AuditPlanner
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.runner.result_normalizer import AuditResultNormalizer
from aegis.audit.suites.base import BaseAuditSuite


class MockSuiteA(BaseAuditSuite):
    suite_id = "suite_a"
    def validate(self, ctx): pass
    def execute(self, ctx): return {"status": "PASSED"}


class MockSuiteB(BaseAuditSuite):
    suite_id = "suite_b"
    def validate(self, ctx): pass
    def execute(self, ctx): return {"status": "PASSED"}


def test_planner_configured_suites():
    reg = AuditRegistry()
    reg.register(MockSuiteA())
    reg.register(MockSuiteB())

    config = {
        "audit": {
            "execution": {"suite_timeout_seconds": 60},
            "suites": [
                {"id": "suite_a", "enabled": True, "required": True},
                {"id": "suite_b", "enabled": False, "required": False},
            ]
        }
    }

    plan = AuditPlanner.build_plan(config, reg)
    assert len(plan) == 2
    assert plan[0].suite_id == "suite_a"
    assert plan[0].enabled is True
    assert plan[1].suite_id == "suite_b"
    assert plan[1].enabled is False


def test_planner_requested_suite_unknown():
    reg = AuditRegistry()
    reg.register(MockSuiteA())
    config = {"audit": {"suites": [{"id": "suite_a"}]}}

    with pytest.raises(SuiteNotFoundError):
        AuditPlanner.build_plan(config, reg, requested_suites=["non_existent"])


def test_result_normalizer_mathematical_consistency():
    # If total does not match passed+failed+skipped+errors, it should correct total
    res = AuditResultNormalizer.normalize(
        suite_id="test",
        suite_version="1.0.0",
        raw_result={
            "status": "PASSED",
            "statistics": {
                "total": 999,  # Intentionally inconsistent declared total
                "passed": 5,
                "failed": 2,
                "skipped": 1,
                "errors": 0,
            }
        }
    )
    assert res["statistics"]["total"] == 8  # Corrected: 5 + 2 + 1 + 0 = 8
    assert res["status"] == "PASSED"
