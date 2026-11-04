"""
tests/integration/deployment/test_deployment_suite.py
=====================================================
Tests verifying Deployment Configuration, Security Controls, and Smoke Drills for WP-08.05.
"""

from pathlib import Path
import pytest
from aegis.integration.deployment.runner import DeploymentRunner


@pytest.fixture
def runner():
    root = Path(__file__).resolve().parents[3]
    return DeploymentRunner(root_dir=root)


def test_dep_001_container_security(runner):
    res = runner.verify_container_security()
    assert res["status"] == "PASS"
    for check_name, check_val in res["security_checks"].items():
        assert check_val is True, f"Failed container security check: {check_name}"


def test_dep_002_health_probes(runner):
    res = runner.verify_health_probes()
    assert res["status"] == "PASS"
    assert res["liveness_probe"]["healthy"] is True
    assert res["readiness_probe"]["all_ready"] is True


def test_dep_003_staging_smoke_and_rollback(runner):
    res = runner.evaluate_deployment_gates()
    assert res["overall_status"] == "PASS"
    assert res["staging_smoke_test"]["status"] == "PASS"
    assert res["rollback_drill"]["status"] == "PASS"

    # Verify generated evidence
    verif_file = runner.artifacts_dir / "DEPLOYMENT_VERIFICATION_REPORT.json"
    smoke_file = runner.artifacts_dir / "STAGING_SMOKE_TEST_REPORT.json"
    rollback_file = runner.root_dir / "DEPLOYMENT_ROLLBACK_REPORT.md"
    prod_file = runner.root_dir / "PRODUCTION_READINESS_REPORT.md"

    assert verif_file.exists()
    assert smoke_file.exists()
    assert rollback_file.exists()
    assert prod_file.exists()
