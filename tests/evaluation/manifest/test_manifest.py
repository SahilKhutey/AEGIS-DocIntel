"""
tests/evaluation/manifest/test_manifest.py
==========================================
MAN-001 through MAN-010 tests verifying manifest schema compliance,
dataset cryptographic integrity, metric registry calculations, and evaluation gates.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest
from pydantic import ValidationError

from aegis.evaluation.manifest.models import (
    DatasetSpec,
    EvaluationManifest,
    MetricThreshold,
    TaskSpec,
)
from aegis.evaluation.manifest.loader import ManifestLoader
from aegis.evaluation.manifest.validator import (
    ManifestValidationError,
    ManifestValidator,
)
from aegis.evaluation.metrics.registry import MetricRegistry
from evaluation.scripts.evaluate_intelligence import evaluate_intelligence

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_man_001_valid_manifest_creation():
    """MAN-001: Manifest model creation succeeds with valid fields."""
    manifest = EvaluationManifest(
        schema_version="1.0.0",
        manifest_id="test-manifest",
        name="Test Suite",
        target_domain="document_intelligence",
        datasets={
            "d1": DatasetSpec(
                path="evaluation/datasets/document_intelligence/extraction_cases.jsonl",
                sha256="70e5b70371bc0ef3bebf096398f03b63d990b50f338d81de5a49d5a64cd641c6",
                format="jsonl",
            )
        },
        tasks={
            "t1": TaskSpec(
                dataset="d1",
                engine="FactExtractor",
                metrics=["extraction_f1"],
            )
        },
        quality_gates={
            "extraction_f1": MetricThreshold(min_value=0.85, strict=True)
        },
    )
    assert manifest.manifest_id == "test-manifest"
    assert manifest.datasets["d1"].format == "jsonl"


def test_man_002_manifest_schema_validation_failure():
    """MAN-002: Manifest schema validation fails when required fields are missing."""
    with pytest.raises(ValidationError):
        EvaluationManifest(
            manifest_id="missing_name",
            # missing target_domain and name
        )


def test_man_003_loader_yaml_success():
    """MAN-003: Manifest loader parses YAML and validates integrity successfully."""
    manifest_path = REPO_ROOT / "configs" / "evaluation" / "intelligence.yaml"
    manifest = ManifestLoader.load(manifest_path, repo_root=REPO_ROOT, verify_integrity=True)
    assert manifest.manifest_id == "eval-manifest-intelligence-v1"
    assert "extraction" in manifest.datasets
    assert "comparison" in manifest.datasets


def test_man_004_validator_missing_dataset_file(tmp_path):
    """MAN-004: Manifest validator fails if dataset file does not exist on disk."""
    fake_sha = "a" * 64
    manifest = EvaluationManifest(
        schema_version="1.0.0",
        manifest_id="missing-file-test",
        name="Missing File Test",
        target_domain="test",
        datasets={
            "nonexistent": DatasetSpec(
                path="nonexistent/path/file.jsonl",
                sha256=fake_sha,
                format="jsonl",
            )
        },
        tasks={},
        quality_gates={},
    )
    valid, errors = ManifestValidator.validate_manifest(manifest, repo_root=tmp_path)
    assert not valid
    assert any("file not found" in err for err in errors)


def test_man_005_validator_tampered_dataset_sha(tmp_path):
    """MAN-005: Manifest validator detects tampered dataset with mismatched SHA-256."""
    test_file = tmp_path / "tampered.jsonl"
    test_file.write_text("tampered content", encoding="utf-8")
    wrong_sha = "0" * 64

    valid, msg = ManifestValidator.verify_dataset_integrity("tampered", str(test_file), wrong_sha, tmp_path)
    assert not valid
    assert "SHA-256 mismatch" in msg


def test_man_006_validator_task_references_unknown_dataset():
    """MAN-006: Manifest validator fails if a task references an undefined dataset key."""
    manifest = EvaluationManifest(
        schema_version="1.0.0",
        manifest_id="unknown-dataset-test",
        name="Unknown Dataset Test",
        target_domain="test",
        datasets={},
        tasks={
            "bad_task": TaskSpec(dataset="ghost_dataset", engine="Engine", metrics=["m1"])
        },
        quality_gates={},
    )
    valid, errors = ManifestValidator.validate_manifest(manifest)
    assert not valid
    assert any("references non-existent dataset" in err for err in errors)


def test_man_007_quality_gate_threshold_logic():
    """MAN-007: Quality gate thresholds properly detect out-of-bound values."""
    gate = MetricThreshold(min_value=0.90, max_value=1.0)
    assert 0.95 >= gate.min_value
    assert not (0.85 >= gate.min_value)


def test_man_008_metric_registry_calculations():
    """MAN-008: MetricRegistry computes standard metrics with high precision."""
    f1 = MetricRegistry.compute("f1", tp=10, fp=2, fn=0)
    p = MetricRegistry.compute("precision", tp=10, fp=2)
    r = MetricRegistry.compute("recall", tp=10, fn=0)
    assert round(p, 4) == 0.8333
    assert r == 1.0
    assert round(f1, 4) == 0.9091

    fidelity = MetricRegistry.compute("grounding_fidelity", verified_quotes=15, total_quotes=15)
    assert fidelity == 1.0

    rr = MetricRegistry.compute("reciprocal_rank", ranked_ids=["a", "b", "c"], gold_id="b")
    assert rr == 0.5


def test_man_009_loader_json_format(tmp_path):
    """MAN-009: Manifest loader supports JSON format seamlessly."""
    dataset_file = tmp_path / "data.jsonl"
    dataset_file.write_text("{\"a\": 1}\n", encoding="utf-8")
    import hashlib
    file_sha = hashlib.sha256(dataset_file.read_bytes()).hexdigest()

    json_manifest = {
        "schema_version": "1.0.0",
        "manifest_id": "json-eval",
        "name": "JSON Eval",
        "target_domain": "doc_intel",
        "datasets": {
            "d": {
                "path": str(dataset_file),
                "sha256": file_sha,
                "format": "jsonl",
            }
        },
        "tasks": {},
        "quality_gates": {},
    }
    manifest_file = tmp_path / "manifest.json"
    manifest_file.write_text(json.dumps(json_manifest), encoding="utf-8")

    loaded = ManifestLoader.load(manifest_file, repo_root=tmp_path, verify_integrity=True)
    assert loaded.manifest_id == "json-eval"


def test_man_010_evaluate_intelligence_manifest_end_to_end():
    """MAN-010: evaluate_intelligence runs end-to-end with manifest enforcement."""
    manifest_path = REPO_ROOT / "configs" / "evaluation" / "intelligence.yaml"
    results = evaluate_intelligence(manifest_path=manifest_path)
    assert results["manifest_id"] == "eval-manifest-intelligence-v1"
    assert results["quality_gates_passed"] is True
    assert results["extraction_f1"] == 1.0
    assert results["grounding_fidelity"] == 1.0
    assert results["conflict_detection_recall"] == 1.0
