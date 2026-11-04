"""
tests/integration/frontend_ci/test_frontend_ci_suite.py
======================================================
Tests verifying Frontend CI scenarios FE-CI-001 through FE-CI-010.
"""

import json
from pathlib import Path
import pytest
from aegis.integration.frontend_ci.runner import FrontendCIRunner


@pytest.fixture
def runner():
    root = Path(__file__).resolve().parents[3]
    return FrontendCIRunner(root_dir=root)


def test_fe_ci_001_valid_frontend_pipeline(runner):
    tc = runner.run_type_check()
    assert tc["status"] == "PASS", f"Typecheck failed: {tc.get('output')}"
    lc = runner.run_lint_check()
    assert lc["status"] == "PASS", f"Lint check failed: {lc.get('output')}"
    ut = runner.run_unit_tests()
    assert ut["status"] == "PASS", f"Unit tests failed: {ut.get('output')}"


def test_fe_ci_006_lockfile_integrity(runner):
    res = runner.verify_lockfile_integrity()
    assert res["status"] == "PASS"
    assert res["dependencies_count"] > 0


def test_fe_ci_007_secret_scanning(runner):
    sec = runner.scan_for_secrets()
    assert sec["status"] == "PASS"
    assert sec["secrets_detected"] == 0


def test_fe_ci_008_and_009_workflow_triggers(runner):
    wf_path = runner.root_dir / ".github" / "workflows" / "frontend-ci.yml"
    assert wf_path.exists()
    content = wf_path.read_text(encoding="utf-8")
    assert "web/**" in content
    assert "pull_request" in content
    assert "npm run lint" in content
    assert "npm test" in content
    assert "npm run build" in content


def test_fe_ci_010_full_benchmark_suite(runner):
    res = runner.evaluate_ci_scenarios()
    assert res["pass_rate"] == 1.0
    assert res["failed_scenarios"] == 0
    assert len(res["scenarios"]) == 10

    # Ensure artifacts were written
    report_file = runner.artifacts_dir / "FRONTEND_CI_TEST_REPORT.json"
    build_file = runner.artifacts_dir / "FRONTEND_BUILD_REPORT.json"
    findings_file = runner.artifacts_dir / "FRONTEND_CI_FINDINGS.md"

    assert report_file.exists()
    assert build_file.exists()
    assert findings_file.exists()
