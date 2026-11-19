"""
Tests for Work Packages PH-10, PH-11, PH-12, and PH-13:
Campaign Planning, Launch Day Runbook, Incident Escalation, and Launch Signoff Gates.
"""

from pathlib import Path
import json
import re
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CAMPAIGN_DIR = REPO_ROOT / "launch" / "product-hunt" / "campaign"
RELEASE_DIR = REPO_ROOT / "launch" / "product-hunt" / "release"
AUDIT_PH = REPO_ROOT / "audit" / "prot-final-09" / "product-hunt"


def test_four_week_campaign_structure():
    """Verify four-week launch campaign milestones."""
    plan_file = CAMPAIGN_DIR / "FOUR_WEEK_PLAN.md"
    assert plan_file.exists()
    content = plan_file.read_text(encoding="utf-8")

    assert "Week 1: Positioning Freeze" in content
    assert "Week 2: Visual Asset Production" in content
    assert "Week 3: Product Hunt Draft" in content
    assert "Week 4: Final Launch Rehearsal" in content


def test_launch_day_runbook_timezone_conversions():
    """Verify Pacific Time to Indian Standard Time schedule conversion."""
    runbook_file = CAMPAIGN_DIR / "LAUNCH_DAY_RUNBOOK.md"
    assert runbook_file.exists()
    content = runbook_file.read_text(encoding="utf-8")

    assert "12:01 AM Pacific Time" in content or "00:01 PT" in content
    assert "1:31 PM Indian Standard Time" in content or "13:31 IST" in content

    # Check incident tiers
    assert "P0 (Critical)" in content
    assert "P1 (High)" in content
    assert "P2 (Medium)" in content
    assert "P3 (Low)" in content


def test_all_15_launch_gates_passed():
    """Verify that all 15 mandatory launch gates in LAUNCH_CHECKLIST.md are marked passed."""
    checklist_file = RELEASE_DIR / "LAUNCH_CHECKLIST.md"
    assert checklist_file.exists()
    content = checklist_file.read_text(encoding="utf-8")

    gates = re.findall(r"- \[(x)\] \*\*GATE-(\d\d)", content)
    assert len(gates) == 15, f"Expected 15 checked gates, found {len(gates)}"

    gate_numbers = [int(num) for _, num in gates]
    assert sorted(gate_numbers) == list(range(1, 16)), "All gates 1 to 15 must be present and checked"


def test_launch_signoff_verdict():
    """Verify LAUNCH_SIGNOFF.md contains an explicit unconditional GO verdict."""
    signoff_file = RELEASE_DIR / "LAUNCH_SIGNOFF.md"
    assert signoff_file.exists()
    content = signoff_file.read_text(encoding="utf-8")

    assert "- [x] **GO**" in content, "Launch decision must be checked as GO"
    assert "Sahil Khutey" in content
    assert "AEGIS-DocIntel" in content
    assert "0.1.0-evaluation" in content


def test_audit_directories_and_registries():
    """Verify that all 7 audit subdirectories and registries exist and are valid JSON."""
    subdirs = [
        "baseline", "assets", "landing-page", "analytics",
        "launch-tests", "launch-day", "reports"
    ]

    for sd in subdirs:
        dir_path = AUDIT_PH / sd
        assert dir_path.exists(), f"Audit directory {sd} must exist"
        json_files = list(dir_path.glob("*.json"))
        assert len(json_files) > 0, f"Audit directory {sd} must contain JSON evidence"

        for jf in json_files:
            with jf.open("r", encoding="utf-8") as f:
                data = json.load(f)
                assert isinstance(data, (dict, list)), f"Registry {jf.name} must contain valid JSON root"
