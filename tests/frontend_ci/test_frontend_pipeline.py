"""
tests/frontend_ci/test_frontend_pipeline.py
===========================================
FCI-001 through FCI-008 tests verifying frontend CI workflow configuration,
scripts definitions, TypeScript configuration, and pipeline integrity.
"""

from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WORKFLOW_FILE = REPO_ROOT / ".github" / "workflows" / "frontend-ci.yml"
WEB_DIR = REPO_ROOT / "web"


def _get_workflow_data():
    with open(WORKFLOW_FILE, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data


def test_fci_001_workflow_file_exists_and_valid_yaml():
    """FCI-001: .github/workflows/frontend-ci.yml exists and is valid YAML."""
    assert WORKFLOW_FILE.exists(), f"Missing workflow at {WORKFLOW_FILE}"
    data = _get_workflow_data()
    assert data is not None
    assert "name" in data
    assert "jobs" in data


def test_fci_002_workflow_triggers_on_web_paths():
    """FCI-002: Workflow triggers on push/PR for paths under web/**."""
    data = _get_workflow_data()
    on_block = data.get("on") or data.get(True) or {}
    push_paths = on_block.get("push", {}).get("paths", [])
    pr_paths = on_block.get("pull_request", {}).get("paths", [])
    assert "web/**" in push_paths
    assert "web/**" in pr_paths


def test_fci_003_workflow_working_directory():
    """FCI-003: Workflow specifies working directory 'web'."""
    data = _get_workflow_data()
    job = data.get("jobs", {}).get("frontend-quality", {})
    working_dir = job.get("defaults", {}).get("run", {}).get("working-directory")
    assert working_dir == "web"


def test_fci_004_workflow_steps_coverage():
    """FCI-004: Workflow contains dependency install, typecheck, test, and build steps."""
    data = _get_workflow_data()
    job = data.get("jobs", {}).get("frontend-quality", {})
    steps = job.get("steps", [])
    step_runs = [s.get("run", "") for s in steps]

    assert any("npm ci" in r for r in step_runs)
    assert any("tsc --noEmit" in r for r in step_runs)
    assert any("npm test" in r for r in step_runs)
    assert any("npm run build" in r for r in step_runs)


def test_fci_005_package_json_scripts():
    """FCI-005: web/package.json contains required scripts."""
    pkg_json = WEB_DIR / "package.json"
    assert pkg_json.exists()
    with open(pkg_json, "r", encoding="utf-8") as f:
        data = json.load(f)
    scripts = data.get("scripts", {})
    assert "build" in scripts
    assert "test" in scripts
    assert "lint" in scripts


def test_fci_006_tsconfig_valid():
    """FCI-006: web/tsconfig.json exists and is valid JSON."""
    tsconfig = WEB_DIR / "tsconfig.json"
    assert tsconfig.exists()
    with open(tsconfig, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "compilerOptions" in data


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed on system")
def test_fci_007_local_typecheck_clean():
    """FCI-007: Local TypeScript check passes with exit code 0."""
    result = subprocess.run(
        ["npx", "tsc", "--noEmit"],
        cwd=str(WEB_DIR),
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0, f"TypeScript check failed: {result.stderr or result.stdout}"


@pytest.mark.skipif(shutil.which("npm") is None, reason="npm not installed on system")
def test_fci_008_local_test_suite_passes():
    """FCI-008: Local Vitest test suite runs and passes all tests."""
    result = subprocess.run(
        ["npm", "test"],
        cwd=str(WEB_DIR),
        capture_output=True,
        text=True,
        shell=True,
    )
    assert result.returncode == 0, f"Vitest tests failed: {result.stderr or result.stdout}"
    assert "passed" in result.stdout.lower()
