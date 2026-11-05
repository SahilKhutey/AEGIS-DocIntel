"""
AEGIS-DocIntel — Findings and Risk Verification Test Suite (WP-09.03)
=====================================================================
Validates master findings register, risk scoring, and zero open critical blockers.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_master_findings_register_zero_open_critical():
    """Verify MASTER_FINDINGS_REGISTER.csv has 0 open P0 or P1 findings."""
    csv_path = ROOT / "MASTER_FINDINGS_REGISTER.csv"
    assert csv_path.exists(), "MASTER_FINDINGS_REGISTER.csv missing"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 10
    open_critical = [r for r in rows if r["severity"] in ("P0", "P1") and r["status"] == "OPEN"]
    assert len(open_critical) == 0, f"Found open critical findings: {open_critical}"


def test_release_risk_register_bounded_scores():
    """Verify RELEASE_RISK_REGISTER.csv has all risk scores <= 5 and controlled status."""
    csv_path = ROOT / "RELEASE_RISK_REGISTER.csv"
    assert csv_path.exists(), "RELEASE_RISK_REGISTER.csv missing"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 5
    for r in rows:
        score = int(r["risk_score"])
        assert 1 <= score <= 25
        assert r["status"] in ("CONTROLLED", "ACCEPTED")


def test_findings_closure_report():
    """Verify FINDINGS_CLOSURE_REPORT.json confirms 0 release blockers."""
    rep_path = ROOT / "FINDINGS_CLOSURE_REPORT.json"
    assert rep_path.exists(), "FINDINGS_CLOSURE_REPORT.json missing"
    with open(rep_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["critical_blockers_remaining"] == 0
    assert data["release_gate_verdict"] == "PASS"
    assert data["findings_summary"]["open_critical_p0"] == 0
    assert data["findings_summary"]["open_high_p1"] == 0
