"""
tests/corpus/test_corpus_integration.py
=======================================
Integration tests INT-CORPUS-001 through INT-CORPUS-010 validating complete
public corpus governance, WP-02 audit runner integration, WP-03 manifest
evaluation integration, and CLI execution.
"""

import json
from pathlib import Path
import pytest

from aegis.audit.runner.engine import AuditRunner
from aegis.corpus.adapters.registry import AdapterRegistry
from aegis.corpus.cli import (
    cmd_manifest_verify,
    cmd_partition_verify,
    cmd_registry_validate,
    cmd_report,
)
from aegis.corpus.partition import HoldoutAccessGuard, PartitionManifest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_int_corpus_001_audit_engine_corpus_suite():
    """INT-CORPUS-001: Verify CorpusAuditSuite is registered and executes through AuditRunner."""
    engine = AuditRunner(repo_path=REPO_ROOT)
    assert engine.registry.has("corpus") is True

    result = engine.run(suite_ids=["corpus"])
    assert result["status"] == "PASSED"
    assert result["summary"]["passed_suites"] >= 1
    assert result["summary"]["failed_suites"] == 0


def test_int_corpus_002_audit_evidence_capture():
    """INT-CORPUS-002: Verify execution produces traceable audit evidence with captured commit and environment."""
    engine = AuditRunner(repo_path=REPO_ROOT)
    result = engine.run(suite_ids=["corpus"])
    
    assert result["status"] == "PASSED"
    assert "run_id" in result
    assert "run_dir" in result

    run_dir = Path(result["run_dir"])
    assert run_dir.exists()
    prov_file = run_dir / "provenance.json"
    if prov_file.exists():
        with open(prov_file, "r", encoding="utf-8") as f:
            prov = json.load(f)
        assert "commit" in prov or "git" in prov or "environment" in prov


def test_int_corpus_003_cli_registry_validate():
    """INT-CORPUS-003: Test CLI registry validate command execution."""
    class DummyArgs:
        pass
    
    exit_code = cmd_registry_validate(DummyArgs())
    assert exit_code == 0


def test_int_corpus_004_cli_manifest_verify():
    """INT-CORPUS-004: Test CLI manifest verify command execution."""
    class DummyArgs:
        manifest = str(REPO_ROOT / "artifacts" / "corpus" / "manifests" / "checksum_manifest.json")
    
    exit_code = cmd_manifest_verify(DummyArgs())
    assert exit_code == 0


def test_int_corpus_005_cli_partition_verify():
    """INT-CORPUS-005: Test CLI partition verify command confirms zero leakage."""
    class DummyArgs:
        manifest = str(REPO_ROOT / "artifacts" / "corpus" / "manifests" / "partition_manifest.json")
    
    exit_code = cmd_partition_verify(DummyArgs())
    assert exit_code == 0


def test_int_corpus_006_cli_report():
    """INT-CORPUS-006: Test CLI report prints full corpus status."""
    class DummyArgs:
        pass
    
    exit_code = cmd_report(DummyArgs())
    assert exit_code == 0


def test_int_corpus_007_adapter_normalization_pipeline(tmp_path):
    """INT-CORPUS-007: Normalize dataset using adapter and verify canonical schema output."""
    sample_funsd = {
        "form": [
            {"id": 0, "text": "Invoice Number", "box": [10, 10, 100, 30], "label": "question"},
            {"id": 1, "text": "INV-2026-99", "box": [110, 10, 200, 30], "label": "answer"},
        ]
    }
    input_file = tmp_path / "sample_funsd.json"
    input_file.write_text(json.dumps(sample_funsd), encoding="utf-8")

    adapter = AdapterRegistry.get_adapter("funsd")
    assert adapter is not None
    docs, annos, evals, report = adapter.convert(input_file, dataset_id="FUNSD_INVOICES")

    assert report.success is True
    assert len(docs) == 1
    assert docs[0].rights.licence_id == "LIC-FUNSD-ACAD-001"
    assert len(annos) == 1
    assert len(evals) == 1


def test_int_corpus_008_holdout_manifest_compatibility():
    """INT-CORPUS-008: Verify partition manifest supplies compliant partitions to evaluation setups."""
    p_manifest_file = REPO_ROOT / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
    assert p_manifest_file.exists()

    with open(p_manifest_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    manifest = PartitionManifest(**data)

    assert len(manifest.partitions.development) == 150
    assert len(manifest.partitions.validation) == 50
    assert len(manifest.partitions.holdout) == 50

    # Ensure mutual exclusivity across all three partitions
    dev_set = set(manifest.partitions.development)
    val_set = set(manifest.partitions.validation)
    hold_set = set(manifest.partitions.holdout)

    assert len(dev_set.intersection(val_set)) == 0
    assert len(dev_set.intersection(hold_set)) == 0
    assert len(val_set.intersection(hold_set)) == 0


def test_int_corpus_009_holdout_sealing_security():
    """INT-CORPUS-009: Verify HoldoutAccessGuard blocks accidental holdout answers access."""
    p_manifest_file = REPO_ROOT / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
    with open(p_manifest_file, "r", encoding="utf-8") as f:
        manifest = PartitionManifest(**json.load(f))

    guard = HoldoutAccessGuard(manifest)
    assert guard.verify_holdout_access_permission("unauthorized_user") is False
    assert guard.verify_holdout_access_permission("audit_final_runner", "WRONG_TOKEN") is False
    assert guard.verify_holdout_access_permission("audit_final_runner", "AEGIS-HOLDOUT-AUTH-2026") is True


def test_int_corpus_010_complete_governance_traceability():
    """INT-CORPUS-010: Complete pipeline audit verifying all 250 documents have valid licence and source bindings."""
    inv_file = REPO_ROOT / "artifacts" / "corpus" / "manifests" / "document_inventory.jsonl"
    with open(inv_file, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    assert len(lines) == 250
    for doc in lines:
        assert doc["source_id"].startswith("SRC-")
        assert doc["licence_id"].startswith("LIC-")
        assert doc["rights_status"] in ["APPROVED", "CONDITIONAL"]
        assert len(doc["sha256"]) == 64
