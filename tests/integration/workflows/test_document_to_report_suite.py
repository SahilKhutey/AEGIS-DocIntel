"""
tests/integration/workflows/test_document_to_report_suite.py
===========================================================
Tests verifying Document-to-Report Workflow scenarios WF-001 through WF-010.
"""

from pathlib import Path
import pytest
from aegis.integration.workflows.runner import DocumentToReportRunner


@pytest.fixture
def runner():
    root = Path(__file__).resolve().parents[3]
    return DocumentToReportRunner(root_dir=root)


def test_wf_001_to_010_workflow_execution(runner):
    res = runner.execute_all_scenarios()
    assert res["pass_rate"] == 1.0
    assert res["failed_scenarios"] == 0
    assert len(res["scenarios"]) == 10

    # Verify generated evidence
    report_file = runner.artifacts_dir / "DOCUMENT_TO_REPORT_TEST_REPORT.json"
    perf_file = runner.artifacts_dir / "DOCUMENT_TO_REPORT_PERFORMANCE.json"
    failure_file = runner.artifacts_dir / "END_TO_END_FAILURE_ANALYSIS.md"
    reg_file = runner.root_dir / "WP08_INTEGRATION_FAILURE_REGISTRY.md"

    assert report_file.exists()
    assert perf_file.exists()
    assert failure_file.exists()
    assert reg_file.exists()


def test_wf_schema_manifest_validity(runner):
    schema_path = runner.root_dir / "schemas" / "integration" / "workflow_run_manifest.schema.json"
    assert schema_path.exists()
