"""
Unit tests for configuration validation (CFG-001 through CFG-010, CFG-T01 through CFG-T12).
"""

import pytest
from aegis.audit.config.fingerprint import compute_configuration_hash
from aegis.audit.config.validator import AuditConfigValidator
from aegis.audit.runner.registry import AuditRegistry
from aegis.audit.suites.base import BaseAuditSuite


class MockSuite(BaseAuditSuite):
    suite_id = "unit"
    def validate(self, ctx): pass
    def execute(self, ctx): return {"status": "PASSED"}


def test_valid_configuration():
    reg = AuditRegistry()
    reg.register(MockSuite())

    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test Audit",
            "enabled": True,
            "execution": {"timeout_seconds": 600, "strict": False, "retries": 1},
            "suites": [{"id": "unit", "enabled": True, "required": True}],
            "evidence": {"enabled": True}
        }
    }
    rep = AuditConfigValidator.validate(cfg, registry=reg)
    assert rep["configuration_status"] == "VALID"
    assert rep["schema_validation"] == "PASS"
    assert rep["semantic_validation"] == "PASS"
    assert len(rep["configuration_hash"]) == 64


def test_cfg_001_unsupported_version():
    cfg = {
        "version": "99.0",
        "audit": {"name": "Test", "enabled": True, "execution": {"timeout_seconds": 10}, "suites": [{"id": "unit"}], "evidence": {"enabled": True}}
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-001" for e in rep["errors"])


def test_cfg_002_duplicate_suites():
    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test",
            "enabled": True,
            "execution": {"timeout_seconds": 10},
            "suites": [{"id": "unit"}, {"id": "unit"}],
            "evidence": {"enabled": True}
        }
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-002" for e in rep["errors"])


def test_cfg_004_negative_timeout():
    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test",
            "enabled": True,
            "execution": {"timeout_seconds": -10},
            "suites": [{"id": "unit"}],
            "evidence": {"enabled": True}
        }
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-004" for e in rep["errors"])


def test_cfg_007_required_suite_disabled_contradiction():
    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test",
            "enabled": True,
            "execution": {"timeout_seconds": 60},
            "suites": [{"id": "unit", "required": True, "enabled": False}],
            "evidence": {"enabled": True}
        }
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-007" for e in rep["errors"])


def test_cfg_008_strict_mode_evidence_disabled():
    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test",
            "enabled": True,
            "execution": {"timeout_seconds": 60, "strict": True},
            "suites": [{"id": "unit", "required": True, "enabled": True}],
            "evidence": {"enabled": False}
        }
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-008" for e in rep["errors"])


def test_cfg_009_path_traversal():
    cfg = {
        "version": "1.0",
        "audit": {
            "name": "Test",
            "enabled": True,
            "execution": {"timeout_seconds": 60},
            "suites": [{"id": "unit", "required": True, "enabled": True}],
            "evidence": {"enabled": True, "output_dir": "../../etc/passwd"}
        }
    }
    rep = AuditConfigValidator.validate(cfg)
    assert rep["configuration_status"] == "INVALID"
    assert any(e["code"] == "CFG-009" for e in rep["errors"])


def test_configuration_hash_strips_secrets():
    cfg1 = {"version": "1.0", "secret_token": "super_secret_123", "value": 42}
    cfg2 = {"version": "1.0", "secret_token": "different_secret_456", "value": 42}
    # Both should have identical configuration hash because secrets are sanitized
    assert compute_configuration_hash(cfg1) == compute_configuration_hash(cfg2)
