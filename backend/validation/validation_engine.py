"""
Validation Engine
==================

Main orchestrator class running the Validation Framework across all 6 test levels.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .exceptions import ValidationError, CoverageThresholdError
from .unit_test_runner import UnitTestRunner, UnitTestResult
from .integration_test_runner import IntegrationTestRunner, IntegrationTestResult
from .e2e_test_runner import E2ETestRunner, E2ETestResult
from .stress_test_runner import StressTestRunner, StressTestResult, LoadProfile
from .robustness_test_runner import RobustnessTestRunner, RobustnessTestResult, Perturbation
from .ablation_runner import AblationRunner, AblationResult, AblationStudy
from .validation_report import ValidationReport, ValidationMetrics


@dataclass
class ValidationResult:
    """Consolidated result of a Validation Engine run."""

    suite_name: str
    passed: bool
    metrics: ValidationMetrics
    report: ValidationReport
    report_json_path: Optional[str] = None
    report_markdown_path: Optional[str] = None


class ValidationSuite:
    """A suite defining tests to execute across validation levels."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.unit_test_modules: List[str] = []
        self.unit_tests_explicit: List[Dict[str, Any]] = []
        self.integration_tests: List[Dict[str, Any]] = []
        self.e2e_tests: List[Dict[str, Any]] = []
        self.stress_tests: List[Dict[str, Any]] = []
        self.robustness_tests: List[Dict[str, Any]] = []
        self.ablation_studies: List[Dict[str, Any]] = []

    def add_unit_module(self, module_path: str) -> None:
        self.unit_test_modules.append(module_path)

    def add_unit_test(self, test_fn: Callable, test_name: str, component: str = "unknown") -> None:
        self.unit_tests_explicit.append({
            "test_fn": test_fn,
            "test_name": test_name,
            "component": component
        })

    def add_integration_test(
        self,
        test_name: str,
        components_tested: List[str],
        integration_fn: Callable[[], Dict[str, Any]],
        contract_checks: Optional[List[tuple]] = None,
    ) -> None:
        self.integration_tests.append({
            "test_name": test_name,
            "components_tested": components_tested,
            "integration_fn": integration_fn,
            "contract_checks": contract_checks,
        })

    def add_e2e_test(
        self,
        test_name: str,
        pipeline_fn: Callable,
        input_document: Any,
        query: str,
        expected_answer: Optional[str] = None,
        accuracy_fn: Optional[Callable[[str, str], float]] = None,
    ) -> None:
        self.e2e_tests.append({
            "test_name": test_name,
            "pipeline_fn": pipeline_fn,
            "input_document": input_document,
            "query": query,
            "expected_answer": expected_answer,
            "accuracy_fn": accuracy_fn,
        })

    def add_stress_test(
        self,
        load_fn: Callable,
        profile: LoadProfile,
    ) -> None:
        self.stress_tests.append({
            "load_fn": load_fn,
            "profile": profile,
        })

    def add_robustness_test(
        self,
        pipeline_fn: Callable,
        original_input: Any,
        expected_output: Any,
        perturbation: Perturbation,
        perturbation_params: Optional[Dict[str, Any]] = None,
    ) -> None:
        self.robustness_tests.append({
            "pipeline_fn": pipeline_fn,
            "original_input": original_input,
            "expected_output": expected_output,
            "perturbation": perturbation,
            "perturbation_params": perturbation_params,
        })

    def add_ablation_study(
        self,
        study: AblationStudy,
        original_input: Any,
        expected_output: Any,
    ) -> None:
        self.ablation_studies.append({
            "study": study,
            "original_input": original_input,
            "expected_output": expected_output,
        })


class ValidationEngine:
    """Orchestrates tests across the validation framework."""

    def __init__(
        self,
        fail_fast: bool = False,
        min_coverage_pct: float = 90.0,
        accuracy_fn: Optional[Callable[[Any, Any], float]] = None,
    ) -> None:
        self.fail_fast = fail_fast
        self.min_coverage_pct = min_coverage_pct
        self.accuracy_fn = accuracy_fn

    def run_suite(
        self,
        suite: ValidationSuite,
        output_dir: Optional[str] = None,
    ) -> ValidationResult:
        """Run the registered validation suite across all modules."""
        report = ValidationReport(suite.name)
        
        # 1. Run Unit Tests
        unit_runner = UnitTestRunner(fail_fast=self.fail_fast)
        for module in suite.unit_test_modules:
            unit_runner.discover_and_run(module)
        if suite.unit_tests_explicit:
            unit_runner.run_tests(suite.unit_tests_explicit)
        report.add_unit_results(unit_runner.results)

        # 2. Run Integration Tests
        int_runner = IntegrationTestRunner(fail_fast=self.fail_fast)
        for t in suite.integration_tests:
            int_runner.run_integration(
                test_name=t["test_name"],
                components_tested=t["components_tested"],
                integration_fn=t["integration_fn"],
                contract_checks=t["contract_checks"],
            )
        report.add_integration_results(int_runner.results)

        # 3. Run End-to-End Tests
        e2e_runner = E2ETestRunner()
        for t in suite.e2e_tests:
            e2e_runner.run_e2e(
                test_name=t["test_name"],
                pipeline_fn=t["pipeline_fn"],
                input_document=t["input_document"],
                query=t["query"],
                expected_answer=t["expected_answer"],
                accuracy_fn=t["accuracy_fn"],
            )
        report.add_e2e_results(e2e_runner.results)

        # 4. Run Stress Tests
        stress_runner = StressTestRunner()
        for t in suite.stress_tests:
            try:
                stress_runner.run_load_test(
                    load_fn=t["load_fn"],
                    profile=t["profile"],
                )
            except Exception:
                # Keep running other tests in suite
                pass
        report.add_stress_results(stress_runner.results)

        # 5. Run Robustness Tests
        # Use suite-level or engine-level accuracy_fn
        robustness_acc_fn = self.accuracy_fn
        if not robustness_acc_fn:
            # simple Jaccard fallback
            def fallback_acc(out: Any, exp: Any) -> float:
                p = str(out.get("answer", out) if isinstance(out, dict) else out).split()
                e = str(exp.get("expected_answer", exp) if isinstance(exp, dict) else exp).split()
                if not p or not e:
                    return 0.0
                return len(set(p) & set(e)) / len(set(p) | set(e))
            robustness_acc_fn = fallback_acc

        robustness_runner = RobustnessTestRunner(accuracy_fn=robustness_acc_fn)
        for t in suite.robustness_tests:
            robustness_runner.run_robustness(
                pipeline_fn=t["pipeline_fn"],
                original_input=t["original_input"],
                expected_output=t["expected_output"],
                perturbation=t["perturbation"],
                perturbation_params=t["perturbation_params"],
            )
        report.add_robustness_results(robustness_runner.results)

        # 6. Run Ablation Studies
        ablation_runner = AblationRunner(
            pipeline_fn=lambda inp, disabled_components=None: suite.e2e_tests[0]["pipeline_fn"](inp, disabled_components) if suite.e2e_tests else (lambda x: {}),
            accuracy_fn=self.accuracy_fn
        )
        for t in suite.ablation_studies:
            # Override pipeline_fn inside ablation runner to support disabled components properly
            ablation_runner.pipeline_fn = t["study"].config_modifications.get("pipeline_fn", ablation_runner.pipeline_fn)
            ablation_runner.run_study(
                study=t["study"],
                original_input=t["original_input"],
                expected_output=t["expected_output"],
            )
        report.add_ablation_results(ablation_runner.results)

        # Compute metrics & determine final status
        metrics = report.compute_metrics()
        
        # Check thresholds
        if metrics.coverage_pct < self.min_coverage_pct:
            # We don't necessarily crash here, but we set passed to False
            passed = False
        else:
            passed = metrics.status == "PASSED"

        # Output reports to disk if directory provided
        json_path = None
        md_path = None
        if output_dir:
            os.makedirs(output_dir, exist_ok=True)
            json_path = os.path.join(output_dir, "validation_report.json")
            md_path = os.path.join(output_dir, "validation_report.md")
            
            with open(json_path, "w", encoding="utf-8") as f:
                f.write(report.to_json())
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(report.to_markdown())

        return ValidationResult(
            suite_name=suite.name,
            passed=passed,
            metrics=metrics,
            report=report,
            report_json_path=json_path,
            report_markdown_path=md_path,
        )
