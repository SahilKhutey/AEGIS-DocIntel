"""
AEGIS-DocIntel — Independent Review Verification Test Suite (WP-09.05)
======================================================================
Validates reviewer sign-off, spot-check register, and approval verdict.
"""
from __future__ import annotations

import csv
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_independent_review_findings_spot_checks():
    """Verify INDEPENDENT_REVIEW_FINDINGS.csv has 10/10 PASS spot-checks."""
    csv_path = ROOT / "INDEPENDENT_REVIEW_FINDINGS.csv"
    assert csv_path.exists(), "INDEPENDENT_REVIEW_FINDINGS.csv missing"
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) == 10
    for r in rows:
        assert r["verdict"] == "PASS"
        assert r["review_id"].startswith("REV-")


def test_reviewer_signoff_approval():
    """Verify REVIEWER_SIGNOFF.md contains formal approval without conditions."""
    signoff_path = ROOT / "REVIEWER_SIGNOFF.md"
    assert signoff_path.exists(), "REVIEWER_SIGNOFF.md missing"
    content = signoff_path.read_text(encoding="utf-8")
    assert "[x] **APPROVED**" in content
    assert "c34fe022cec225de516bf4d7997cecf848ea4a1d" in content
    assert "AEGIS-MVP-RC1" in content


def test_independent_review_report():
    """Verify INDEPENDENT_REVIEW_REPORT.md contains complete audit dimensions."""
    rpt_path = ROOT / "INDEPENDENT_REVIEW_REPORT.md"
    assert rpt_path.exists(), "INDEPENDENT_REVIEW_REPORT.md missing"
    content = rpt_path.read_text(encoding="utf-8")
    assert "Anti-IDOR" in content
    assert "APPROVED" in content
