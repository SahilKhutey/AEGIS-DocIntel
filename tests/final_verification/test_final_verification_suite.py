"""
tests/final_verification/test_final_verification_suite.py
==========================================================
Comprehensive automated verification suite for WP-FINAL:
Validates all 12 sub-work packages, directory integrity, checksums, and sign-off.
"""

import json
import csv
import hashlib
from pathlib import Path
import pytest

from aegis.audit.suites.final_verification import FinalVerificationSuite

ROOT_DIR = Path(__file__).resolve().parent.parent.parent
FINAL_DIR = ROOT_DIR / "release" / "final-verification"


def test_wp_final_01_repository_audit():
    d = FINAL_DIR / "01_repository_audit"
    assert (d / "REPOSITORY_STRUCTURE_AUDIT.md").is_file()
    assert (d / "MODULE_IMPLEMENTATION_INVENTORY.csv").is_file()
    assert (d / "DEPENDENCY_GRAPH.json").is_file()
    assert (d / "UNUSED_CODE_REPORT.md").is_file()
    assert (d / "ARCHITECTURE_CONSISTENCY_REPORT.md").is_file()
    assert (d / "MISSING_IMPLEMENTATION_REGISTER.csv").is_file()

    with open(d / "DEPENDENCY_GRAPH.json", "r", encoding="utf-8") as f:
        graph = json.load(f)
    assert len(graph.get("nodes", [])) >= 8
    assert len(graph.get("edges", [])) >= 8


def test_wp_final_02_requirements_traceability():
    d = FINAL_DIR / "02_requirements"
    assert (d / "MASTER_REQUIREMENTS_REGISTER.csv").is_file()
    assert (d / "REQUIREMENTS_TRACEABILITY_MATRIX.csv").is_file()
    assert (d / "REQUIREMENT_COVERAGE_REPORT.json").is_file()
    assert (d / "UNVERIFIED_REQUIREMENTS.md").is_file()

    with open(d / "REQUIREMENT_COVERAGE_REPORT.json", "r", encoding="utf-8") as f:
        rep = json.load(f)
    assert rep.get("coverage_percentage") == 100.0
    assert rep.get("unverified_requirements") == 0


def test_wp_final_03_functional_testing():
    d = FINAL_DIR / "03_functional"
    assert (d / "FUNCTIONAL_TEST_PLAN.md").is_file()
    assert (d / "FUNCTIONAL_TEST_CASES.jsonl").is_file()
    assert (d / "FUNCTIONAL_TEST_RESULTS.json").is_file()
    assert (d / "FUNCTIONAL_COVERAGE_REPORT.md").is_file()
    assert (d / "FUNCTIONAL_FAILURE_REGISTER.csv").is_file()

    with open(d / "FUNCTIONAL_TEST_RESULTS.json", "r", encoding="utf-8") as f:
        res = json.load(f)
    assert res.get("status") == "ALL_PASSED"
    assert res.get("pass_rate") == 100.0


def test_wp_final_04_unit_component_testing():
    d = FINAL_DIR / "04_unit_component"
    assert (d / "UNIT_TEST_PLAN.md").is_file()
    assert (d / "UNIT_TEST_RESULTS.json").is_file()
    assert (d / "COMPONENT_TEST_REPORT.md").is_file()
    assert (d / "CODE_COVERAGE_REPORT.json").is_file()
    assert (d / "MUTATION_TEST_REPORT.md").is_file()
    assert (d / "UNIT_FAILURE_REGISTER.csv").is_file()

    with open(d / "CODE_COVERAGE_REPORT.json", "r", encoding="utf-8") as f:
        cov = json.load(f)
    assert cov.get("statement_coverage_percentage", 0) > 90.0


def test_wp_final_05_integration_system_testing():
    d = FINAL_DIR / "05_integration_system"
    assert (d / "INTEGRATION_TEST_PLAN.md").is_file()
    assert (d / "API_CONTRACT_TEST_REPORT.json").is_file()
    assert (d / "SYSTEM_TEST_REPORT.json").is_file()
    assert (d / "END_TO_END_TEST_REPORT.json").is_file()
    assert (d / "WORKFLOW_VALIDATION_REPORT.md").is_file()

    with open(d / "API_CONTRACT_TEST_REPORT.json", "r", encoding="utf-8") as f:
        contract = json.load(f)
    assert contract.get("contract_mismatches") == 0


def test_wp_final_06_processing_validation():
    d = FINAL_DIR / "06_processing"
    assert (d / "PROCESSING_VALIDATION_PLAN.md").is_file()
    assert (d / "OCR_BENCHMARK_REPORT.json").is_file()
    assert (d / "LAYOUT_VALIDATION_REPORT.json").is_file()
    assert (d / "READING_ORDER_REPORT.json").is_file()
    assert (d / "TABLE_RECONSTRUCTION_REPORT.json").is_file()
    assert (d / "PROVENANCE_VALIDATION_REPORT.json").is_file()

    with open(d / "OCR_BENCHMARK_REPORT.json", "r", encoding="utf-8") as f:
        ocr = json.load(f)
    assert ocr.get("character_error_rate") < 0.02


def test_wp_final_07_intelligence_validation():
    d = FINAL_DIR / "07_intelligence"
    assert (d / "INTELLIGENCE_VALIDATION_PLAN.md").is_file()
    assert (d / "GOLDEN_QUESTION_DATASET.jsonl").is_file()
    assert (d / "RETRIEVAL_BENCHMARK_REPORT.json").is_file()
    assert (d / "QUESTION_ANSWERING_REPORT.json").is_file()
    assert (d / "CITATION_CORRECTNESS_REPORT.json").is_file()
    assert (d / "ABSTENTION_REPORT.json").is_file()

    with open(d / "CITATION_CORRECTNESS_REPORT.json", "r", encoding="utf-8") as f:
        cit = json.load(f)
    assert cit.get("unsupported_claims") == 0


def test_wp_final_08_security_privacy_validation():
    d = FINAL_DIR / "08_security_privacy"
    assert (d / "SECURITY_VALIDATION_PLAN.md").is_file()
    assert (d / "AUTHENTICATION_AUTHORIZATION_REPORT.json").is_file()
    assert (d / "TENANT_ISOLATION_REPORT.json").is_file()
    assert (d / "PRIVACY_VALIDATION_REPORT.json").is_file()
    assert (d / "DOCUMENT_DELETION_REPORT.json").is_file()

    with open(d / "TENANT_ISOLATION_REPORT.json", "r", encoding="utf-8") as f:
        ten = json.load(f)
    assert ten.get("cross_tenant_leakage_detected") is False


def test_wp_final_09_reliability_recovery_testing():
    d = FINAL_DIR / "09_reliability_recovery"
    assert (d / "RELIABILITY_TEST_PLAN.md").is_file()
    assert (d / "WORKER_FAULT_INJECTION_REPORT.json").is_file()
    assert (d / "QUEUE_RELIABILITY_REPORT.json").is_file()
    assert (d / "DATABASE_RECOVERY_REPORT.json").is_file()
    assert (d / "BACKUP_RESTORATION_REPORT.json").is_file()

    with open(d / "BACKUP_RESTORATION_REPORT.json", "r", encoding="utf-8") as f:
        bak = json.load(f)
    assert bak.get("restoration_success_rate") == 1.0


def test_wp_final_10_performance_benchmarking():
    d = FINAL_DIR / "10_benchmarks"
    assert (d / "BENCHMARK_METHODOLOGY.md").is_file()
    assert (d / "BENCHMARK_ENVIRONMENT.json").is_file()
    assert (d / "API_PERFORMANCE_REPORT.json").is_file()
    assert (d / "BENCHMARK_COMPARISON_REPORT.md").is_file()

    with open(d / "API_PERFORMANCE_REPORT.json", "r", encoding="utf-8") as f:
        perf = json.load(f)
    assert perf.get("latency_p95_ms") < 100.0


def test_wp_final_11_documentation_completeness():
    d = FINAL_DIR / "11_documentation"
    assert (d / "DOCUMENTATION_COMPLETENESS_AUDIT.csv").is_file()

    with open(d / "DOCUMENTATION_COMPLETENESS_AUDIT.csv", "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = list(reader)
    assert len(rows) >= 40
    # Verify every documented file actually exists on disk
    for r in rows:
        path = ROOT_DIR / r[0]
        assert path.is_file(), f"Documented file does not exist: {r[0]}"


def test_wp_final_12_final_certification_manifest_and_signoff():
    d = FINAL_DIR / "12_final_assessment"
    assert (d / "MASTER_FINDINGS_REGISTER.csv").is_file()
    assert (d / "FINAL_VERIFICATION_REPORT.json").is_file()
    assert (d / "FINAL_SYSTEM_VALIDATION_REPORT.md").is_file()
    assert (d / "FINAL_EVIDENCE_MANIFEST.json").is_file()
    assert (d / "CHECKSUMS.sha256").is_file()
    assert (d / "WP_FINAL_SIGNOFF.md").is_file()

    with open(d / "FINAL_VERIFICATION_REPORT.json", "r", encoding="utf-8") as f:
        rep = json.load(f)
    assert rep.get("verdict") == "CERTIFIED_READY_FOR_RELEASE"
    assert rep.get("completion_ratio") == 1.0


def test_wp_final_checksum_integrity():
    d = FINAL_DIR / "12_final_assessment"
    checksums_file = d / "CHECKSUMS.sha256"
    assert checksums_file.is_file()
    with open(checksums_file, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip()]
    assert len(lines) >= 70

    for line in lines:
        parts = line.split(maxsplit=1)
        expected_hash = parts[0]
        rel_path = parts[1]
        target_file = FINAL_DIR / rel_path
        assert target_file.is_file(), f"Checksum target file missing: {rel_path}"
        with open(target_file, "rb") as tf:
            actual_hash = hashlib.sha256(tf.read()).hexdigest()
        assert actual_hash == expected_hash, f"Hash mismatch for {rel_path}"


def test_final_verification_suite_execution():
    suite = FinalVerificationSuite()
    assert suite.suite_id == "final_verification"
    suite.validate()
    result = suite.execute()
    assert result["status"] == "PASSED"
    assert result["statistics"]["total"] == 12
    assert result["statistics"]["passed"] == 12
    assert result["statistics"]["failed"] == 0
    assert len(result["findings"]) == 0
