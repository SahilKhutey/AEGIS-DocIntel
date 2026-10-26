"""
AEGIS-DocIntel — Evaluation Dataset Contract Tests
==================================================
Ensures the evaluation dataset matches its manifest contract and that
drift in slice definitions, case counts, or schema identifiers is rejected.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "validate_mvp_dataset.py"


def test_repository_evaluation_dataset_matches_manifest():
    """Verify that the repository's evaluation dataset matches the declared manifest contract."""
    result = subprocess.run(
        [sys.executable, str(SCRIPT)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, f"Validator failed:\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    assert "MVP DATASET CONTRACT: PASSED" in result.stdout


def test_validator_detects_count_drift(tmp_path: Path):
    """Verify that the validator flags count drift between manifest and dataset."""
    manifest = {
        "manifest_version": "1.0.0",
        "slices": {
            "extraction": {"test_cases_count": 2},
            "packing": {"test_cases_count": 1},
            "privacy": {"test_cases_count": 1},
            "retrieval": {"test_cases_count": 1},
        },
        "quality_gates": {},
    }
    dataset = {
        "extraction_cases": [
            {"case_id": "ext_01", "expected_order": ["b1"]}
        ],
        "packing_cases": [
            {"case_id": "pack_01", "budget": 10, "costs": [5], "weights": [0.5]}
        ],
        "privacy_cases": [
            {"id": "priv_01", "text": "Clean", "expected_pii": []}
        ],
        "retrieval_cases": [
            {"query_id": "q01", "query": "Test query?", "corpus": []}
        ],
    }

    manifest_file = tmp_path / "manifest.json"
    dataset_file = tmp_path / "dataset.json"

    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    dataset_file.write_text(json.dumps(dataset), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest_file), "--dataset", str(dataset_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "Count drift in slice 'extraction'" in result.stdout


def test_validator_detects_duplicate_id(tmp_path: Path):
    """Verify that the validator flags duplicate IDs in any slice."""
    manifest = {
        "manifest_version": "1.0.0",
        "slices": {
            "extraction": {"test_cases_count": 2},
            "packing": {"test_cases_count": 1},
            "privacy": {"test_cases_count": 1},
            "retrieval": {"test_cases_count": 1},
        },
        "quality_gates": {},
    }
    dataset = {
        "extraction_cases": [
            {"case_id": "dup_01", "expected_order": ["b1"]},
            {"case_id": "dup_01", "expected_order": ["b2"]},
        ],
        "packing_cases": [
            {"case_id": "pack_01", "budget": 10, "costs": [5], "weights": [0.5]}
        ],
        "privacy_cases": [
            {"id": "priv_01", "text": "Clean", "expected_pii": []}
        ],
        "retrieval_cases": [
            {"query_id": "q01", "query": "Test query?", "corpus": []}
        ],
    }

    manifest_file = tmp_path / "manifest.json"
    dataset_file = tmp_path / "dataset.json"

    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
    dataset_file.write_text(json.dumps(dataset), encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--manifest", str(manifest_file), "--dataset", str(dataset_file)],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 1
    assert "duplicate identifier" in result.stdout
