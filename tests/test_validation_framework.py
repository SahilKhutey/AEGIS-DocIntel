import os
import sys
import tempfile
from pathlib import Path
import numpy as np
import pytest
from unittest.mock import MagicMock

# Configure Python path to find backend.validation
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))


def test_validation_imports():
    """Verify that all components can be imported from backend.validation."""
    from backend.validation import (
        ValidationEngine,
        ValidationSuite,
        ValidationResult,
        UnitTestRunner,
        UnitTestResult,
        IntegrationTestRunner,
        IntegrationTestResult,
        E2ETestRunner,
        E2ETestResult,
        StressTestRunner,
        StressTestResult,
        LoadProfile,
        RobustnessTestRunner,
        RobustnessTestResult,
        Perturbation,
        AblationRunner,
        AblationResult,
        AblationStudy,
        ValidationReport,
        ValidationMetrics,
        AMDIAssertions,
        assert_valid_output,
        assert_within_tolerance,
        sample_document,
        sample_pdf_text,
        sample_ground_truth,
        ValidationError,
        TestFailureError,
        CoverageThresholdError,
    )
    assert True


def test_exceptions():
    """Verify custom exceptions can be raised and caught."""
    from backend.validation.exceptions import (
        ValidationError,
        TestFailureError,
        CoverageThresholdError,
        StressTestFailure,
        AblationError,
        RobustnessError,
    )
    
    with pytest.raises(ValidationError):
        raise TestFailureError("Failure")
        
    with pytest.raises(CoverageThresholdError):
        raise CoverageThresholdError("Low coverage")

    with pytest.raises(StressTestFailure):
        raise StressTestFailure("Slowing down")


def test_assertions():
    """Verify AMDIAssertions validation logic."""
    from backend.validation.assertions import AMDIAssertions
    
    # Valid output structure
    AMDIAssertions.assert_valid_output({"a": 1, "b": 2}, ["a", "b"])
    with pytest.raises(Exception):
        AMDIAssertions.assert_valid_output({"a": 1}, ["a", "b"])
    with pytest.raises(Exception):
        AMDIAssertions.assert_valid_output(None, allow_none=False)

    # Within tolerance
    AMDIAssertions.assert_within_tolerance(10.1, 10.0, tolerance=0.02)
    with pytest.raises(Exception):
        AMDIAssertions.assert_within_tolerance(10.5, 10.0, tolerance=0.02)

    # Latency, memory, token budgets
    AMDIAssertions.assert_latency_below(200.0, 500.0)
    with pytest.raises(Exception):
        AMDIAssertions.assert_latency_below(600.0, 500.0)

    AMDIAssertions.assert_memory_below(150.0, 300.0)
    with pytest.raises(Exception):
        AMDIAssertions.assert_memory_below(400.0, 300.0)

    AMDIAssertions.assert_token_within_budget(120, 200)
    with pytest.raises(Exception):
        AMDIAssertions.assert_token_within_budget(250, 200)

    # Array closeness
    a = np.array([1.0, 2.0, 3.0])
    b = np.array([1.0001, 2.0001, 2.9999])
    AMDIAssertions.assert_arrays_close(a, b, rtol=1e-3)
    with pytest.raises(Exception):
        AMDIAssertions.assert_arrays_close(a, b, rtol=1e-6)

    # Conservation law
    # Input = output + compressed + discarded
    AMDIAssertions.assert_conservation(100.0, 40.0, 50.0, 10.0)
    with pytest.raises(Exception):
        AMDIAssertions.assert_conservation(100.0, 40.0, 50.0, 5.0)


def test_unit_test_runner():
    """Verify UnitTestRunner behavior."""
    from backend.validation.unit_test_runner import UnitTestRunner
    
    def dummy_pass():
        return {"metric": 0.99}
        
    def dummy_fail():
        raise AssertionError("Failed assertion")
        
    def dummy_error():
        raise ValueError("Oops")

    runner = UnitTestRunner(fail_fast=False)
    
    # Run a passing test
    res_pass = runner.run_test(dummy_pass, "test_pass", "component_a")
    assert res_pass.passed is True
    assert res_pass.metadata["metric"] == 0.99
    
    # Run a failing test
    res_fail = runner.run_test(dummy_fail, "test_fail", "component_a")
    assert res_fail.passed is False
    assert "Failed assertion" in res_fail.error_message

    # Run error test
    res_err = runner.run_test(dummy_error, "test_err", "component_b")
    assert res_err.passed is False
    assert "Oops" in res_err.error_message
    
    # Coverage verification
    report = runner.coverage_report()
    assert report["total"] == 3
    assert report["passed"] == 1
    assert report["failed"] == 2
    assert report["pass_rate"] == 1 / 3
    
    with pytest.raises(Exception):
        runner.assert_coverage(min_pass_rate=0.90)


def test_integration_test_runner():
    """Verify IntegrationTestRunner functionality."""
    from backend.validation.integration_test_runner import IntegrationTestRunner
    
    def mock_flow():
        return {"status": "ok", "value": 42}
        
    runner = IntegrationTestRunner()
    
    # Run with contract checks
    res = runner.run_integration(
        test_name="component_handshake",
        components_tested=["L1", "L2"],
        integration_fn=mock_flow,
        contract_checks=[
            ("status_is_str", str, lambda r: r["status"]),
            ("value_is_42", 42, lambda r: r["value"]),
            ("value_is_even", lambda v: v % 2 == 0, lambda r: r["value"])
        ]
    )
    assert res.passed is True
    assert res.data_flow_validated is True
    assert len(res.contract_violations) == 0

    # Run failing contract checks
    res_fail = runner.run_integration(
        test_name="component_handshake_fail",
        components_tested=["L1", "L2"],
        integration_fn=mock_flow,
        contract_checks=[
            ("value_is_99", 99, lambda r: r["value"])
        ]
    )
    assert res_fail.passed is False
    assert res_fail.data_flow_validated is False
    assert len(res_fail.contract_violations) == 1
    
    # Test schema check helper
    res_schema = runner.test_data_flow(
        test_name="schema_validation",
        source_output={"name": "Alice", "age": 30},
        target_input_schema={"name": str, "age": int},
        target_fn=lambda inp: f"Hello {inp['name']}"
    )
    assert res_schema.passed is True

    res_schema_fail = runner.test_data_flow(
        test_name="schema_validation_fail",
        source_output={"name": "Alice", "age": "thirty"},
        target_input_schema={"name": str, "age": int},
        target_fn=lambda inp: f"Hello {inp['name']}"
    )
    assert res_schema_fail.passed is False
    assert "missing_keys" in res_schema_fail.contract_violations[0]


def test_e2e_test_runner():
    """Verify E2ETestRunner correctness."""
    from backend.validation.e2e_test_runner import E2ETestRunner
    
    def mock_pipeline(doc, query, ablated_components=None):
        return {
            "answer": "Quantum mechanics describes the physics of atoms.",
            "citations": ["page 1"],
            "tokens": 150,
            "stage_times": {"ingestion": 10.0, "llm": 50.0}
        }
        
    runner = E2ETestRunner(
        accuracy_threshold=0.6,
        latency_threshold_ms=1000.0,
        token_budget=500,
        require_citations=True
    )
    
    res = runner.run_e2e(
        test_name="quantum_e2e",
        pipeline_fn=mock_pipeline,
        input_document="some doc",
        query="Explain quantum mechanics",
        expected_answer="quantum mechanics describes atoms"
    )
    
    assert res.passed is True
    assert res.citation_count == 1
    assert res.token_count == 150
    assert res.accuracy > 0.6
    
    # Check failure case (low accuracy)
    res_fail = runner.run_e2e(
        test_name="quantum_e2e_fail",
        pipeline_fn=mock_pipeline,
        input_document="some doc",
        query="Explain quantum mechanics",
        expected_answer="completely unrelated target text"
    )
    assert res_fail.passed is False
    assert "accuracy" in res_fail.error_message


def test_stress_test_runner():
    """Verify StressTestRunner behavior under mock load."""
    from backend.validation.stress_test_runner import StressTestRunner, LoadProfile
    
    call_count = 0
    def mock_load_fn():
        nonlocal call_count
        call_count += 1
        # Mock some light latency
        import time
        time.sleep(0.005)
        
    runner = StressTestRunner(max_error_rate=0.1, max_latency_p99_ms=1000.0)
    profile = LoadProfile(name="light_load", num_requests=10, concurrency=2)
    
    res = runner.run_load_test(mock_load_fn, profile)
    
    assert res.total_requests == 10
    assert res.successful_requests == 10
    assert res.failed_requests == 0
    assert res.throughput_rps > 0.0
    assert res.latency_p50_ms > 0.0
    
    # Finding breaking point
    def breaking_fn():
        # Fail if call_count exceeds some limit to simulate crash under load
        if call_count > 15:
            raise RuntimeError("Exceeded threshold")
        mock_load_fn()
        
    runner_break = StressTestRunner(max_error_rate=0.01)
    break_res = runner_break.find_breaking_point(
        load_fn=breaking_fn,
        start_concurrency=1,
        max_concurrency=5,
        step=1,
        num_requests_per_step=5
    )
    # The system should break when concurrency ramps up and triggers errors
    assert break_res["breaking_point"] is not None


def test_robustness_test_runner():
    """Verify RobustnessTestRunner perturbation modifications."""
    from backend.validation.robustness_test_runner import RobustnessTestRunner, Perturbation
    
    def dummy_accuracy(predicted, expected):
        return 1.0 if predicted == expected else 0.5
        
    runner = RobustnessTestRunner(accuracy_fn=dummy_accuracy, success_threshold=0.8, num_trials=3)
    
    # Pipeline that just returns input
    pipeline_fn = lambda x: x
    
    # Test NOISE perturbation
    res_noise = runner.run_robustness(
        pipeline_fn=pipeline_fn,
        original_input="abcdefgh",
        expected_output="abcdefgh",
        perturbation=Perturbation.NOISE,
        perturbation_params={"level": 0.2}
    )
    assert res_noise.success_rate < 1.0  # Noise should change characters, lowering accuracy
    
    # Test EMPTY perturbation
    res_empty = runner.run_robustness(
        pipeline_fn=pipeline_fn,
        original_input="test",
        expected_output="test",
        perturbation=Perturbation.EMPTY
    )
    # Empty perturbation returns empty string, pipeline returns empty string, accuracy evaluates to 0.5 < 0.8
    assert res_empty.success_rate == 0.0

    # Test perturbation functions directly
    from backend.validation.robustness_test_runner import RobustnessTestRunner
    
    assert len(RobustnessTestRunner._add_special_chars("abc")) > 3
    assert len(RobustnessTestRunner._duplicate("abc", 2)) == 6
    assert "日本語" in RobustnessTestRunner._add_unicode("abc")
    assert "中文" in RobustnessTestRunner._add_mixed_languages("abc")


def test_ablation_runner():
    """Verify AblationRunner metrics comparisons."""
    from backend.validation.ablation_runner import AblationRunner, AblationStudy
    
    def mock_pipeline(doc, disabled_components=None):
        disabled = disabled_components or []
        # Disabling memory drops accuracy, disabling geometry drops latency
        accuracy = 0.95
        tokens = 200
        if "memory" in disabled:
            accuracy -= 0.3
        if "geometry" in disabled:
            accuracy -= 0.1
            
        return {
            "answer": "Predict",
            "accuracy": accuracy,
            "tokens": tokens
        }
        
    def mock_accuracy_fn(predicted_res, expected_res):
        return predicted_res["accuracy"]
        
    runner = AblationRunner(pipeline_fn=mock_pipeline, accuracy_fn=mock_accuracy_fn)
    study = AblationStudy(
        name="Engine Importance",
        components=["memory", "geometry"]
    )
    
    results = runner.run_study(
        study=study,
        original_input="document",
        expected_output="ground_truth"
    )
    
    assert len(results) == 2
    # Memory drop: 0.95 - 0.65 = 0.3
    assert abs(results[0].impact_accuracy - 0.3) < 1e-5
    # Geometry drop: 0.95 - 0.85 = 0.1
    assert abs(results[1].impact_accuracy - 0.1) < 1e-5
    assert results[0].passed is True


def test_validation_report_generation():
    """Verify ValidationReport serialization and metrics calculations."""
    from backend.validation.validation_report import ValidationReport
    from backend.validation.unit_test_runner import UnitTestResult
    from backend.validation.e2e_test_runner import E2ETestResult
    
    report = ValidationReport("Checkup")
    
    report.add_unit_results([
        UnitTestResult("t1", "c1", passed=True, duration_ms=5.0),
        UnitTestResult("t2", "c2", passed=False, duration_ms=10.0)
    ])
    
    report.add_e2e_results([
        E2ETestResult("e1", passed=True, duration_ms=120.0, token_count=100, accuracy=0.85)
    ])
    
    metrics = report.compute_metrics()
    # Coverage: 2 passed out of 3 = 66.67%
    assert abs(metrics.coverage_pct - 66.67) < 0.1
    assert metrics.status == "FAILED"  # because coverage < 90%
    assert metrics.total_token_usage == 100
    
    # Test JSON and Markdown exports
    json_data = report.to_json()
    assert '"suite_name": "Checkup"' in json_data
    
    md_data = report.to_markdown()
    assert "# Validation Report: Checkup" in md_data
    assert "Overall Status" in md_data


def test_validation_engine():
    """Verify ValidationEngine run_suite coordinating all elements."""
    from backend.validation import ValidationEngine, ValidationSuite, LoadProfile, Perturbation, AblationStudy
    
    suite = ValidationSuite("Whole System")
    
    # Add dummy unit test
    suite.add_unit_test(lambda: {"ok": True}, "dummy_unit", "c1")
    
    # Add dummy E2E test
    def mock_pipeline_fn(doc, disabled_components=None):
        return {"answer": "Target answer", "tokens": 10}
    suite.add_e2e_test(
        test_name="dummy_e2e",
        pipeline_fn=mock_pipeline_fn,
        input_document="doc",
        query="query",
        expected_answer="Target answer"
    )
    
    # Add dummy stress test
    suite.add_stress_test(
        load_fn=lambda: mock_pipeline_fn("doc"),
        profile=LoadProfile("dummy_profile", num_requests=2, concurrency=1)
    )
    
    # Add dummy robustness test
    suite.add_robustness_test(
        pipeline_fn=lambda doc: mock_pipeline_fn(doc),
        original_input="text",
        expected_output="Target answer",
        perturbation=Perturbation.DUPLICATE,
        perturbation_params={"copies": 2}
    )
    
    # Add dummy ablation study
    study = AblationStudy(
        name="ablate_memory",
        components=["memory"],
        config_modifications={"pipeline_fn": mock_pipeline_fn}
    )
    suite.add_ablation_study(
        study=study,
        original_input="doc",
        expected_output="Target answer"
    )
    
    # Run validation engine with file output
    with tempfile.TemporaryDirectory() as tmp_dir:
        engine = ValidationEngine(fail_fast=False, min_coverage_pct=50.0)
        res = engine.run_suite(suite, output_dir=tmp_dir)
        
        assert res.suite_name == "Whole System"
        assert res.passed is True
        assert res.metrics.coverage_pct > 50.0
        
        # Verify files written
        assert os.path.exists(os.path.join(tmp_dir, "validation_report.json"))
        assert os.path.exists(os.path.join(tmp_dir, "validation_report.md"))
