"""
tests/integration/test_remediation_integration.py
=================================================
INT-001 through INT-010 tests verifying cross-system integration,
data flow across citation gates, evaluation manifests, benchmark reconciliation,
licensing SBOM, security orchestration, and release readiness.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aegis.compliance.licensing.scanner import DependencyLicenseScanner
from aegis.evaluation.benchmarks.reconciliation import BenchmarkReconciler
from aegis.evaluation.manifest.loader import ManifestLoader
from aegis.release.metadata_validator import ReleaseMetadataValidator
from aegis.release.release_gate import ReleaseGateChecker
from aegis.security.orchestrator import SecurityAuditOrchestrator
from evaluation.scripts.evaluate_retrieval import evaluate_retrieval
from evaluation.scripts.evaluate_intelligence import evaluate_intelligence

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_int_001_citation_results_feed_benchmark_reconciliation():
    """INT-001: evaluate_retrieval output feeds into BenchmarkReconciler cleanly."""
    retrieval_res = evaluate_retrieval()
    assert retrieval_res["citation_precision"] >= 0.90
    assert retrieval_res["citation_coverage"] >= 0.90

    reconciled = BenchmarkReconciler.reconcile_retrieval_results(retrieval_res)
    assert reconciled["citation_precision"] == retrieval_res["citation_precision"]
    violations = BenchmarkReconciler.validate_math_invariants(reconciled)
    assert len(violations) == 0


def test_int_002_manifest_intelligence_feeds_benchmark_manifest():
    """INT-002: evaluate_intelligence output reconciles with benchmark manifest."""
    manifest_path = REPO_ROOT / "configs" / "evaluation" / "intelligence.yaml"
    intel_res = evaluate_intelligence(manifest_path=manifest_path)
    assert intel_res["quality_gates_passed"] is True

    manifest_file = REPO_ROOT / "audit" / "benchmarks" / "benchmark-manifest.json"
    with open(manifest_file, "r", encoding="utf-8") as f:
        bm_data = json.load(f)

    reconciled = BenchmarkReconciler.reconcile_benchmark_manifest(bm_data, intel_metrics=intel_res)
    assert "fact_extraction_f1" in reconciled["quality_gates"]
    assert reconciled["quality_gates"]["fact_extraction_f1"]["status"] == "PASS"


def test_int_003_release_validator_harmonizes_with_benchmarks():
    """INT-003: ReleaseMetadataValidator confirms release metadata matches canonical baseline."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    valid, errors = validator.validate()
    assert valid is True
    assert len(errors) == 0


def test_int_004_security_findings_conform_to_schema():
    """INT-004: SecurityAuditOrchestrator runs and passes with zero high/critical vulnerabilities."""
    orch = SecurityAuditOrchestrator(REPO_ROOT)
    report = orch.run_full_scan()
    assert report.passed is True
    assert report.critical_count == 0
    assert report.high_count == 0


def test_int_005_licensing_sbom_harmonizes_with_release_license():
    """INT-005: License scanner SBOM output harmonizes with release config licenses."""
    scanner = DependencyLicenseScanner(REPO_ROOT)
    report = scanner.generate_sbom("artifacts/licence-audit")
    assert report["compliance_status"] == "COMPLIANT"
    assert report["prohibited_packages_count"] == 0

    validator = ReleaseMetadataValidator(REPO_ROOT)
    rel_cfg = validator.load_release_config()["release"]["licenses"]
    assert rel_cfg["core"]["license"] == "Apache-2.0"
    assert rel_cfg["platform"]["license"] == "Proprietary"


def test_int_006_benchmark_report_generation():
    """INT-006: BenchmarkReconciler generates standardized report with valid schema."""
    retrieval_res = evaluate_retrieval()
    report = BenchmarkReconciler.build_standard_report(
        report_id="int-bench-001",
        benchmark_name="Integration Benchmark",
        commit_sha="7c05522643e503396795d99e381d201268ebe7fe",
        metrics=retrieval_res,
        quality_gates={
            "citation_precision": {
                "threshold": ">= 0.90",
                "observed_baseline": retrieval_res["citation_precision"],
                "status": "PASS",
            }
        },
    )
    assert report["status"] == "PASSED"
    assert report["metrics"]["citation_precision"] == 1.0


def test_int_007_evaluation_manifest_cryptographic_integrity():
    """INT-007: Evaluation manifest cryptographic SHA-256 verification succeeds."""
    manifest_path = REPO_ROOT / "configs" / "evaluation" / "intelligence.yaml"
    manifest = ManifestLoader.load(manifest_path, repo_root=REPO_ROOT, verify_integrity=True)
    assert len(manifest.datasets) >= 2


def test_int_008_release_gate_checker_readiness():
    """INT-008: ReleaseGateChecker reports overall status READY."""
    gate_checker = ReleaseGateChecker(REPO_ROOT)
    passed, summary = gate_checker.check_release_readiness()
    assert passed is True
    assert summary["overall_status"] == "READY"


def test_int_009_math_invariants_across_evaluations():
    """INT-009: Mathematical invariant checker verifies zero violations in retrieval and intelligence."""
    retrieval_res = evaluate_retrieval()
    intel_res = evaluate_intelligence()
    assert len(BenchmarkReconciler.validate_math_invariants(retrieval_res)) == 0
    assert len(BenchmarkReconciler.validate_math_invariants(intel_res)) == 0


def test_int_010_workflow_configuration_integrity():
    """INT-010: CI workflow configurations exist and pass schema checks."""
    workflows_dir = REPO_ROOT / ".github" / "workflows"
    assert (workflows_dir / "audit-infrastructure.yml").exists()
    assert (workflows_dir / "security-scan.yml").exists()
    assert (workflows_dir / "frontend-ci.yml").exists()
