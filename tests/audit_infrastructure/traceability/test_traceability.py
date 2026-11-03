"""
Unit tests for Traceability, Git Collector, Provenance, and Finding Fingerprints (TRC-001 through TRC-015).
"""

import pytest
from aegis.audit.traceability.finding_fingerprint import FindingFingerprint
from aegis.audit.traceability.git_collector import GitCollector
from aegis.audit.traceability.historical_comparison import HistoricalComparison
from aegis.audit.traceability.provenance_builder import ProvenanceBuilder
from aegis.audit.traceability.provenance_validator import ProvenanceValidator
from aegis.audit.traceability.run_identity import RunIdentity


def test_trc_001_run_identity_generation():
    id1 = RunIdentity.generate()
    id2 = RunIdentity.generate()
    assert id1["run_id"] != id2["run_id"]
    assert id1["run_id"].startswith("AG-")
    assert len(id1["run_uuid"]) == 36


def test_trc_002_git_collector_clean_state():
    collector = GitCollector()
    state = collector.collect()
    assert len(state["commit_sha"]) == 40
    assert "repository" in state
    assert isinstance(state["working_tree_clean"], bool)


def test_trc_008_trc_010_provenance_validation():
    prov = ProvenanceBuilder.build(
        run_identity={"run_id": "AG-20261103-120000-TEST", "run_uuid": "abc", "baseline_id": "BASE-001", "trigger": "CLI"},
        git_snapshot={"repository": "repo", "commit_sha": "a" * 40, "working_tree_clean": True},
        config_snapshot={"profile": "default", "sha256": "b" * 64},
        env_snapshot={"os": "Windows"},
        started_at="2026-11-03T12:00:00Z",
        completed_at="2026-11-03T12:00:01Z"
    )
    errors = ProvenanceValidator.validate(prov, strict_mode=True)
    assert len(errors) == 0


def test_trc_009_dirty_working_tree_strict_mode():
    prov = ProvenanceBuilder.build(
        run_identity={"run_id": "AG-20261103-120000-TEST", "run_uuid": "abc", "baseline_id": "BASE-001"},
        git_snapshot={"repository": "repo", "commit_sha": "a" * 40, "working_tree_clean": False, "modified_files_count": 2},
        config_snapshot={"profile": "default", "sha256": "b" * 64},
        env_snapshot={"os": "Windows"},
        started_at="2026-11-03T12:00:00Z",
        completed_at="2026-11-03T12:00:01Z"
    )
    errors = ProvenanceValidator.validate(prov, strict_mode=True)
    assert any("Dirty working tree rejected in strict release mode" in err for err in errors)


def test_trc_012_trc_013_finding_fingerprint_line_invariance():
    # Fingerprint must be identical regardless of line movements
    fp1 = FindingFingerprint.compute(
        suite_id="security",
        rule_id="SEC-001",
        file_path="src/api/auth.py",
        identity="Missing token expiration"
    )
    fp2 = FindingFingerprint.compute(
        suite_id="security",
        rule_id="SEC-001",
        file_path="src/api/auth.py",
        identity="Missing token expiration"
    )
    assert fp1 == fp2
    assert len(fp1) == 64


def test_trc_014_historical_comparison():
    base_run = {
        "run_id": "RUN-BASE",
        "suites": [{"suite_id": "unit", "status": "PASSED"}],
        "findings": [
            {"finding_id": "F1", "fingerprint": "fp1", "title": "Old defect"},
            {"finding_id": "F2", "fingerprint": "fp2", "title": "Persistent defect"}
        ]
    }
    curr_run = {
        "run_id": "RUN-CURR",
        "suites": [{"suite_id": "unit", "status": "FAILED"}],  # Regression!
        "findings": [
            {"finding_id": "F2", "fingerprint": "fp2", "title": "Persistent defect"},
            {"finding_id": "F3", "fingerprint": "fp3", "title": "Brand new defect"}
        ]
    }

    comp = HistoricalComparison.compare(base_run, curr_run)
    assert comp["new_findings_count"] == 1
    assert comp["resolved_findings_count"] == 1
    assert comp["persistent_findings_count"] == 1
    assert comp["suite_regressions_count"] == 1
    assert comp["suite_regressions"][0]["suite_id"] == "unit"
