"""
Unit tests for Evidence validation, models, and stores (EVD-001 through EVD-012).
"""

import tempfile
from pathlib import Path
import pytest
from aegis.audit.evidence.hashing import hash_bytes, hash_file
from aegis.audit.evidence.models import AuditArtifact, AuditRun, AuditSuiteResult
from aegis.audit.evidence.store import EvidenceStore
from aegis.audit.evidence.validator import EvidenceValidator


def test_valid_evidence_run():
    run_dict = {
        "schema_version": "1.0",
        "run_id": "AG-20261103-120000-TEST",
        "baseline_id": "AEGIS-BASELINE-001",
        "project": "AEGIS-DocIntel",
        "execution": {"status": "PASSED", "started_at": "2026-11-03T12:00:00Z"},
        "source": {"branch": "master", "commit_sha": "a" * 40, "working_tree": "CLEAN"},
        "configuration": {"profile": "default", "hash": "b" * 64},
        "environment": {"python_version": "3.12.10", "platform": "Windows"},
        "suites": [
            {
                "suite_id": "unit",
                "suite_version": "1.0.0",
                "status": "PASSED",
                "started_at": "2026-11-03T12:00:00Z",
                "completed_at": "2026-11-03T12:00:01Z",
                "duration_seconds": 1.0,
                "statistics": {"total": 1, "passed": 1, "failed": 0, "skipped": 0, "errors": 0},
                "findings": [],
                "artifacts": []
            }
        ],
        "findings": [],
        "artifacts": []
    }
    errors = EvidenceValidator.validate_run(run_dict)
    assert len(errors) == 0


def test_evd_002_missing_run_id():
    run_dict = {
        "schema_version": "1.0",
        "baseline_id": "AEGIS-BASELINE-001",
        "execution": {"status": "PASSED"},
        "source": {},
        "configuration": {},
        "environment": {},
        "suites": []
    }
    errors = EvidenceValidator.validate_run(run_dict)
    assert any("run_id" in err for err in errors)


def test_evd_003_invalid_suite_status():
    run_dict = {
        "schema_version": "1.0",
        "run_id": "AG-20261103-120000-TEST",
        "baseline_id": "AEGIS-BASELINE-001",
        "execution": {"status": "PASSED"},
        "source": {},
        "configuration": {},
        "environment": {},
        "suites": [{"suite_id": "unit", "status": "NON_STANDARD_STATUS", "statistics": {"total": 0, "passed": 0, "failed": 0, "skipped": 0, "errors": 0}}]
    }
    errors = EvidenceValidator.validate_run(run_dict)
    assert any("status" in err for err in errors)


def test_evd_007_statistics_mismatch():
    run_dict = {
        "schema_version": "1.0",
        "run_id": "AG-20261103-120000-TEST",
        "baseline_id": "AEGIS-BASELINE-001",
        "execution": {"status": "PASSED"},
        "source": {},
        "configuration": {},
        "environment": {},
        "suites": [{
            "suite_id": "unit",
            "status": "PASSED",
            "statistics": {"total": 10, "passed": 2, "failed": 1, "skipped": 0, "errors": 0}  # 10 != 3
        }]
    }
    errors = EvidenceValidator.validate_run(run_dict)
    assert any("statistics mismatch" in err for err in errors)


def test_evd_009_artifact_integrity_verification():
    with tempfile.TemporaryDirectory() as tmp_dir:
        store = EvidenceStore(base_artifacts_dir=Path(tmp_dir))
        
        # Save an artifact
        art = store.save_artifact_file(
            run_id="AG-20261103-120000-INTEG",
            artifact_id="ART-001",
            filename="output.txt",
            content="Original uncorrupted log",
            created_at="2026-11-03T12:00:00Z"
        )
        assert len(art.sha256) == 64

        # Save run
        run_obj = AuditRun(
            run_id="AG-20261103-120000-INTEG",
            baseline_id="AEGIS-BASELINE-001",
            project="AEGIS-DocIntel",
            execution={"status": "PASSED", "started_at": "2026-11-03T12:00:00Z"},
            source={"branch": "master", "commit_sha": "a" * 40, "working_tree": "CLEAN"},
            configuration={"profile": "default", "hash": "b" * 64},
            environment={"python_version": "3.12.10", "platform": "Windows"},
            suites=[],
            findings=[],
            artifacts=[art.to_dict()]
        )
        run_dir = store.save_run(run_obj)

        # Integrity should pass initially
        ver1 = store.verify_integrity("AG-20261103-120000-INTEG")
        assert ver1["status"] == "PASS"

        # Tamper with the physical artifact
        tampered_file = run_dir / "artifacts" / "output.txt"
        tampered_file.write_text("TAMPERED CONTENT CORRUPTION")

        # Integrity verification must catch tampering
        ver2 = store.verify_integrity("AG-20261103-120000-INTEG")
        assert ver2["status"] == "INTEGRITY_FAILURE"
