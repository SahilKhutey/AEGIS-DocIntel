"""
Integration and End-to-End tests for the complete Audit Infrastructure.
"""

import tempfile
from pathlib import Path
import pytest
from aegis.audit.evidence.store import EvidenceStore
from aegis.audit.runner.engine import AuditRunner
from aegis.audit.runner.exceptions import ConfigurationError


def test_e2e_full_lifecycle_passing():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = EvidenceStore(base_artifacts_dir=Path(tmp_dir))
        runner = AuditRunner(
            config={
                "version": "1.0",
                "audit": {
                    "name": "E2E Test Run",
                    "enabled": True,
                    "execution": {"timeout_seconds": 60, "strict": False},
                    "suites": [
                        {"id": "integration", "enabled": True, "required": True},
                        {"id": "security", "enabled": True, "required": True}
                    ],
                    "evidence": {"enabled": True}
                }
            },
            evidence_store=store,
        )

        res = runner.run()
        assert res["status"] == "PASSED"
        run_id = res["run_id"]
        
        # Verify persistence and retrieval
        retrieved = store.get_run(run_id)
        assert retrieved is not None
        assert retrieved["execution"]["status"] == "PASSED"

        # Verify integrity
        integrity = store.verify_integrity(run_id)
        assert integrity["status"] == "PASS"


def test_e2e_invalid_configuration_rejected_before_execution():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = EvidenceStore(base_artifacts_dir=Path(tmp_dir))
        runner = AuditRunner(
            config={
                "version": "1.0",
                "audit": {
                    "name": "Invalid Config",
                    "enabled": True,
                    "execution": {"timeout_seconds": -100},  # Negative timeout!
                    "suites": [{"id": "unit"}],
                    "evidence": {"enabled": True}
                }
            },
            evidence_store=store,
        )

        with pytest.raises(ConfigurationError):
            runner.run()


def test_e2e_dry_run_mode():
    runner = AuditRunner(
        config={
            "version": "1.0",
            "audit": {
                "name": "Dry Run Test",
                "enabled": True,
                "execution": {"timeout_seconds": 60},
                "suites": [{"id": "integration"}],
                "evidence": {"enabled": True}
            }
        }
    )
    res = runner.run(dry_run=True)
    assert res["status"] == "DRY_RUN"
    assert res["planned_suites_count"] == 1
    assert "integration" in res["planned_suites"]
