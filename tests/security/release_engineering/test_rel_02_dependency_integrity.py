"""
Release Engineering Test Suite — Dependency Integrity (REL-003, GATE-05)
PROT-FINAL-04: Workstream REL-03
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
NPM_LOCK = REPO_ROOT / "web" / "package-lock.json"
REQ_CORE = REPO_ROOT / "requirements-core.txt"
DEP_REPORT = REPO_ROOT / "release" / "reports" / "dependency-report.json"


def test_rel_021_lockfiles_exist():
    """REL-003.1: Confirms presence of authoritative dependency lockfiles."""
    assert NPM_LOCK.exists(), "NPM lockfile missing"
    assert REQ_CORE.exists(), "Core requirements missing"


def test_rel_022_npm_lockfile_integrity():
    """REL-003.2: Confirms NPM lockfile is valid JSON with locked package versions."""
    lock_data = json.loads(NPM_LOCK.read_text(encoding="utf-8"))
    assert lock_data.get("lockfileVersion") in (2, 3), f"Unexpected lockfile version: {lock_data.get('lockfileVersion')}"
    packages = lock_data.get("packages", {})
    assert len(packages) > 50, "NPM lockfile has insufficient package records"


def test_rel_023_python_pinned_requirements():
    """REL-003.3: Confirms python requirements have explicitly constrained dependency bounds."""
    lines = [line.strip() for line in REQ_CORE.read_text(encoding="utf-8").splitlines() if line.strip() and not line.startswith("#")]
    assert len(lines) >= 20
    for line in lines:
        assert ">=" in line or "==" in line, f"Floating unpinned dependency: {line}"


def test_rel_024_dependency_scan_report_clean():
    """GATE-05: Confirms dependency vulnerability scan report exists and reports 0 critical/high unmitigated CVEs."""
    assert DEP_REPORT.exists(), f"Dependency report missing: {DEP_REPORT}"
    report = json.loads(DEP_REPORT.read_text(encoding="utf-8"))
    assert report.get("status") == "PASS"
    npm_metrics = report.get("ecosystems", {}).get("npm", {})
    assert npm_metrics.get("critical_vulnerabilities") == 0
    assert npm_metrics.get("high_vulnerabilities") == 0
