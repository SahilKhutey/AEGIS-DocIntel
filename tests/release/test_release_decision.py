"""
AEGIS-DocIntel — Release Decision Verification Test Suite (WP-09.06)
====================================================================
Validates release readiness scorecard, release decision JSON/MD, and GO verdict.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path
import pytest

ROOT = Path(__file__).resolve().parent.parent.parent


def test_release_readiness_scorecard():
    """Verify RELEASE_READINESS_SCORECARD.json meets minimum 95% threshold."""
    sc_path = ROOT / "RELEASE_READINESS_SCORECARD.json"
    assert sc_path.exists(), "RELEASE_READINESS_SCORECARD.json missing"
    with open(sc_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["verdict"] == "PASS"
    assert data["overall_score"] >= 95.0
    assert len(data["categories"]) == 5
    for cat in data["categories"]:
        assert cat["status"] == "PASS"


def test_release_decision_verdict_go():
    """Verify RELEASE_DECISION.json issues formal GO decision with 0 blockers."""
    dec_path = ROOT / "RELEASE_DECISION.json"
    assert dec_path.exists(), "RELEASE_DECISION.json missing"
    with open(dec_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["decision"] == "GO"
    assert data["open_blockers"] == 0
    assert data["candidate_commit"] == "c34fe022cec225de516bf4d7997cecf848ea4a1d"
    assert len(data["authorizations"]) >= 2


def test_release_decision_markdown():
    """Verify RELEASE_DECISION.md has all required decision sections."""
    md_path = ROOT / "RELEASE_DECISION.md"
    assert md_path.exists(), "RELEASE_DECISION.md missing"
    content = md_path.read_text(encoding="utf-8")
    assert "[x] **GO**" in content
    assert "Critical Release Gate Assessment" in content
    assert "Independent Reviewer Assessment" in content


def test_release_conditions_register():
    """Verify RELEASE_CONDITIONS_REGISTER.csv contains only non-blocking conditions."""
    cond_path = ROOT / "RELEASE_CONDITIONS_REGISTER.csv"
    assert cond_path.exists(), "RELEASE_CONDITIONS_REGISTER.csv missing"
    with open(cond_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    assert len(rows) >= 2
    for r in rows:
        assert r["severity"] in ("LOW", "P3", "P4")
        assert r["status"] == "CONTROLLED"


def test_release_audit_history_jsonl():
    """Verify RELEASE_AUDIT_HISTORY.jsonl contains valid JSON Lines entries."""
    hist_path = ROOT / "RELEASE_AUDIT_HISTORY.jsonl"
    assert hist_path.exists(), "RELEASE_AUDIT_HISTORY.jsonl missing"
    with open(hist_path, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]

    assert len(lines) >= 1
    last_entry = json.loads(lines[-1])
    assert last_entry["decision"] == "GO"
    assert last_entry["commit_sha"] == "c34fe022cec225de516bf4d7997cecf848ea4a1d"
