"""
AEGIS-DocIntel — Full System Verification Test Suite (WP-09.02)
================================================================
Validates master verification matrix, regression coverage, and execution report.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_final_verification_matrix_integrity():
    """Verify FINAL_VERIFICATION_MATRIX.csv has all rows passing and valid commit."""
    csv_path = ROOT / "FINAL_VERIFICATION_MATRIX.csv"
    assert csv_path.exists(), "FINAL_VERIFICATION_MATRIX.csv missing"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 25
    for r in rows:
        assert r["execution_status"] == "PASS"
        assert r["candidate_commit"] == "c34fe022cec225de516bf4d7997cecf848ea4a1d"
        assert r["review_status"] == "VERIFIED"


def test_regression_requirements_registry():
    """Verify REGRESSION_REQUIREMENTS.csv maps all past P0/P1 issues to passing tests."""
    reg_path = ROOT / "REGRESSION_REQUIREMENTS.csv"
    assert reg_path.exists(), "REGRESSION_REQUIREMENTS.csv missing"
    with open(reg_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 6
    for r in rows:
        assert r["candidate_result"] == "PASS"
        assert r["original_severity"] in ("P0", "P1")


def test_complete_verification_report_critical_gates():
    """Verify COMPLETE_VERIFICATION_REPORT.json satisfies all critical release gates."""
    rep_path = ROOT / "COMPLETE_VERIFICATION_REPORT.json"
    assert rep_path.exists(), "COMPLETE_VERIFICATION_REPORT.json missing"
    with open(rep_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["verification_status"] == "COMPLETED"
    assert data["summary"]["failed"] == 0
    assert data["summary"]["blocked"] == 0
    assert data["summary"]["errors"] == 0
    assert data["summary"]["not_run"] == 0

    critical_gates = data["critical_gates"]
    for gate, status in critical_gates.items():
        assert status == "PASS", f"Critical gate {gate} failed: {status}"


def test_test_coverage_dimensions():
    """Verify TEST_COVERAGE_REPORT.json covers all 9 required verification dimensions."""
    cov_path = ROOT / "TEST_COVERAGE_REPORT.json"
    assert cov_path.exists(), "TEST_COVERAGE_REPORT.json missing"
    with open(cov_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["overall_coverage_verdict"] == "PASS"
    dims = data["dimensions"]
    assert dims["requirements_coverage"]["coverage_percentage"] == 100.0
    assert dims["api_coverage"]["coverage_percentage"] == 100.0
    assert dims["branch_coverage"]["branch_coverage_percentage"] >= 80.0
