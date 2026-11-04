"""
tests/integration/browser_e2e/test_browser_e2e_suite.py
=======================================================
Tests verifying Browser E2E scenarios E2E-001 through E2E-018.
"""

from pathlib import Path
import pytest
from aegis.integration.browser_e2e.runner import BrowserE2ERunner


@pytest.fixture
def runner():
    root = Path(__file__).resolve().parents[3]
    return BrowserE2ERunner(root_dir=root)


def test_e2e_001_playwright_configuration(runner):
    res = runner.verify_playwright_setup()
    assert res["status"] == "PASS"
    assert res["config_present"] is True
    assert res["specs_present"] is True
    assert res["journeys_covered"]["documents"] is True
    assert res["journeys_covered"]["ask"] is True
    assert res["journeys_covered"]["reviews"] is True


def test_e2e_002_full_user_journey_suite(runner):
    res = runner.evaluate_e2e_scenarios()
    assert res["pass_rate"] == 1.0
    assert res["failed_scenarios"] == 0
    assert len(res["scenarios"]) == 18

    # Verify generated evidence
    report_file = runner.artifacts_dir / "BROWSER_E2E_TEST_REPORT.json"
    analysis_file = runner.artifacts_dir / "BROWSER_FAILURE_ANALYSIS.md"

    assert report_file.exists()
    assert analysis_file.exists()
