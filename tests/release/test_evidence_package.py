"""
AEGIS-DocIntel — Evidence Package Verification Test Suite (WP-09.04)
====================================================================
Validates evidence manifest, SHA-256 checksums, and package validation report.
"""
from __future__ import annotations

import csv
import hashlib
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_evidence_package_validation_report():
    """Verify EVIDENCE_PACKAGE_VALIDATION_REPORT.json has 0 failures and verdict PASS."""
    val_path = ROOT / "EVIDENCE_PACKAGE_VALIDATION_REPORT.json"
    assert val_path.exists(), "EVIDENCE_PACKAGE_VALIDATION_REPORT.json missing"
    with open(val_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["validation_verdict"] == "PASS"
    assert data["failed_checks"] == 0
    assert data["total_checks"] == 10
    for chk in data["checks"]:
        assert chk["result"] == "PASS"


def test_requirements_traceability_100_percent():
    """Verify REQUIREMENTS_TRACEABILITY.csv has all rows PASS and mapped to candidate SHA."""
    tr_path = ROOT / "REQUIREMENTS_TRACEABILITY.csv"
    assert tr_path.exists(), "REQUIREMENTS_TRACEABILITY.csv missing"
    with open(tr_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 20
    for r in rows:
        assert r["status"] == "PASS"
        assert r["commit_sha"] == "c34fe022cec225de516bf4d7997cecf848ea4a1d"
        assert len(r["evidence_path"]) > 0


def test_final_verification_report_critical_gates():
    """Verify FINAL_VERIFICATION_REPORT.json has release_verdict GO and 0 blockers."""
    rep_path = ROOT / "FINAL_VERIFICATION_REPORT.json"
    assert rep_path.exists(), "FINAL_VERIFICATION_REPORT.json missing"
    with open(rep_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["release_verdict"] == "GO"
    assert data["open_blockers"] == 0
    for wp, status in data["work_packages"].items():
        assert status == "PASS", f"WP failed: {wp}"
    for gate, status in data["critical_gates"].items():
        assert status == "PASS", f"Gate failed: {gate}"
