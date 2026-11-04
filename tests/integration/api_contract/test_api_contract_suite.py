"""
tests/integration/api_contract/test_api_contract_suite.py
=========================================================
Tests verifying API contract scenarios API-001 through API-015.
"""

from pathlib import Path
import pytest
from aegis.integration.api_contract.runner import APIContractRunner


@pytest.fixture
def runner():
    root = Path(__file__).resolve().parents[3]
    return APIContractRunner(root_dir=root)


def test_api_001_openapi_conformance(runner):
    conf = runner.validate_openapi_conformance()
    assert conf["status"] == "PASS"
    assert conf["endpoints_count"] >= 50
    assert conf["schemas_count"] >= 30
    assert conf["key_endpoints_verified"]["upload"] is True
    assert conf["key_endpoints_verified"]["answers"] is True


def test_api_002_schema_compatibility(runner):
    compat = runner.validate_schema_compatibility()
    assert compat["status"] == "PASS"
    assert compat["compatibility_rate"] == 1.0
    for check in compat["checks"]:
        assert check["compatible"] is True, f"Incompatible schema: {check}"


def test_api_003_endpoint_inventory_exists(runner):
    csv_file = runner.root_dir / "contracts" / "API_ENDPOINT_INVENTORY.csv"
    assert csv_file.exists()
    lines = csv_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) >= 70  # header + endpoints


def test_api_004_full_contract_scenario_suite(runner):
    res = runner.evaluate_api_scenarios()
    assert res["pass_rate"] == 1.0
    assert res["failed_scenarios"] == 0
    assert len(res["scenarios"]) == 15

    # Check evidence artifacts generated
    report_file = runner.artifacts_dir / "API_CONTRACT_TEST_REPORT.json"
    compat_file = runner.artifacts_dir / "API_COMPATIBILITY_REPORT.json"
    schema_file = runner.artifacts_dir / "API_SCHEMA_VALIDATION_REPORT.json"

    assert report_file.exists()
    assert compat_file.exists()
    assert schema_file.exists()
