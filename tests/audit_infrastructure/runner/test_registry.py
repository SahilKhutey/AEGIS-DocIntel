"""
Unit tests for AuditRegistry (RUN-001, RUN-002, RUN-003).
"""

import pytest
from aegis.audit.runner.exceptions import DuplicateSuiteError, SuiteNotFoundError
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.suites.base import BaseAuditSuite


class DummyPassingSuite(BaseAuditSuite):
    suite_id = "dummy_pass"
    suite_name = "Dummy Passing Suite"
    suite_version = "1.0.0"

    def validate(self, context):
        pass

    def execute(self, context):
        return {"status": "PASSED"}


def test_register_valid_suite():
    reg = AuditRegistry()
    suite = DummyPassingSuite()
    reg.register(suite)
    assert "dummy_pass" in reg.list_suites()
    assert reg.get("dummy_pass") is suite
    assert reg.get("DUMMY_PASS") is suite  # Case-insensitive


def test_register_duplicate_suite():
    reg = AuditRegistry()
    reg.register(DummyPassingSuite())
    with pytest.raises(DuplicateSuiteError):
        reg.register(DummyPassingSuite())


def test_get_unknown_suite():
    reg = AuditRegistry()
    with pytest.raises(SuiteNotFoundError):
        reg.get("non_existent_suite")


def test_register_invalid_object():
    reg = AuditRegistry()
    with pytest.raises(TypeError):
        reg.register("not_a_suite")  # type: ignore


def test_register_empty_id():
    class EmptyIdSuite(BaseAuditSuite):
        suite_id = ""
        def validate(self, context): pass
        def execute(self, context): return {}

    reg = AuditRegistry()
    with pytest.raises(ValueError):
        reg.register(EmptyIdSuite())
