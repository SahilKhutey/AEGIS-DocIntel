"""
tests/evaluation/benchmarks/test_reconciliation.py
=================================================
BEN-001 through BEN-012 tests verifying benchmark report reconciliation,
schema conformance, mathematical invariants, and citation gate alignment.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aegis.evaluation.benchmarks.reconciliation import (
    BenchmarkReconciler,
    ReconciliationError,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_ben_001_standard_report_creation():
    """BEN-001: Benchmark report creation succeeds with valid structure and schema."""
    report = BenchmarkReconciler.build_standard_report(
        report_id="rep-001",
        benchmark_name="Retrieval Quality",
        commit_sha="7c05522643e503396795d99e381d201268ebe7fe",
        metrics={
            "mrr": 1.0,
            "recall_at_5": 0.9231,
            "citation_precision": 1.0,
        },
        quality_gates={
            "citation_precision": {
                "threshold": ">= 0.90",
                "observed_baseline": 1.0,
                "status": "PASS",
            }
        },
    )
    assert report["schema_version"] == "1.0.0"
    assert report["report_id"] == "rep-001"
    assert report["status"] == "PASSED"


def test_ben_002_math_invariants_valid():
    """BEN-002: Mathematical invariant validation succeeds on valid metrics."""
    metrics = {
        "mrr": 0.85,
        "recall_at_5": 0.92,
        "citation_precision": 0.95,
        "extraction_precision": 0.80,
        "extraction_recall": 0.80,
        "extraction_f1": 0.80,
    }
    violations = BenchmarkReconciler.validate_math_invariants(metrics)
    assert len(violations) == 0


def test_ben_003_math_invariants_out_of_bounds():
    """BEN-003: Mathematical invariant validation detects metrics outside [0, 1]."""
    metrics = {"citation_precision": 1.25}
    violations = BenchmarkReconciler.validate_math_invariants(metrics)
    assert len(violations) == 1
    assert "outside [0.0, 1.0]" in violations[0]


def test_ben_004_f1_harmonic_mean_match():
    """BEN-004: F1 harmonic mean check passes when formula matches."""
    metrics = {
        "extraction_precision": 0.80,
        "extraction_recall": 0.60,
        # F1 = 2 * 0.8 * 0.6 / (0.8 + 0.6) = 0.96 / 1.4 = 0.6857
        "extraction_f1": 0.6857,
    }
    violations = BenchmarkReconciler.validate_math_invariants(metrics)
    assert len(violations) == 0


def test_ben_005_f1_harmonic_mean_mismatch():
    """BEN-005: F1 harmonic mean check detects fabricated or inconsistent F1 score."""
    metrics = {
        "extraction_precision": 0.50,
        "extraction_recall": 0.50,
        "extraction_f1": 0.99,  # Impossible F1
    }
    violations = BenchmarkReconciler.validate_math_invariants(metrics)
    assert len(violations) == 1
    assert "does not match harmonic mean" in violations[0]


def test_ben_006_reconcile_retrieval_adds_citation_metrics():
    """BEN-006: Retrieval result reconciliation adds complete citation metrics."""
    raw = {"mrr": 1.0, "recall_at_5": 0.92}
    reconciled = BenchmarkReconciler.reconcile_retrieval_results(raw)
    assert "citation_precision" in reconciled
    assert "citation_coverage" in reconciled
    assert "citation_resolution_rate" in reconciled
    assert "citation_attribution_accuracy" in reconciled
    assert reconciled["citation_precision"] == 1.0


def test_ben_007_reconcile_benchmark_manifest_adds_citation_gates():
    """BEN-007: Manifest reconciliation ensures citation precision gate is created."""
    manifest_data = {
        "quality_gates": {
            "retrieval_mrr": {"threshold": ">= 0.70", "observed_baseline": 0.9, "status": "PASS"}
        }
    }
    reconciled = BenchmarkReconciler.reconcile_benchmark_manifest(manifest_data)
    assert "citation_precision" in reconciled["quality_gates"]
    assert reconciled["quality_gates"]["citation_precision"]["threshold"] == ">= 0.90"
    assert reconciled["quality_gates"]["citation_precision"]["status"] == "PASS"


def test_ben_008_reconcile_manifest_preserves_targets():
    """BEN-008: Reconciliation preserves all other sections and targets."""
    manifest_data = {
        "project": "AEGIS-DocIntel",
        "performance_targets": {"p50": 50},
        "quality_gates": {}
    }
    reconciled = BenchmarkReconciler.reconcile_benchmark_manifest(manifest_data)
    assert reconciled["project"] == "AEGIS-DocIntel"
    assert reconciled["performance_targets"]["p50"] == 50


def test_ben_009_build_standard_report_raises_on_invariant_error():
    """BEN-009: build_standard_report raises ReconciliationError on bad metrics."""
    with pytest.raises(ReconciliationError):
        BenchmarkReconciler.build_standard_report(
            report_id="rep-err",
            benchmark_name="Bad Report",
            commit_sha="abc",
            metrics={"citation_precision": 99.0},  # Invalid!
            quality_gates={},
        )


def test_ben_010_standard_report_provenance():
    """BEN-010: Standard report has valid timestamp and provenance structure."""
    report = BenchmarkReconciler.build_standard_report(
        report_id="rep-prov",
        benchmark_name="Prov Test",
        commit_sha="7c05522643e503396795d99e381d201268ebe7fe",
        metrics={"mrr": 1.0},
        quality_gates={},
    )
    assert "timestamp_utc" in report
    assert report["provenance"]["verified"] is True


def test_ben_011_actual_retrieval_results_reconciled():
    """BEN-011: The actual audit/benchmarks/retrieval-results.json satisfies all invariant checks."""
    path = REPO_ROOT / "audit" / "benchmarks" / "retrieval-results.json"
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["citation_precision"] == 1.0
    assert data["citation_coverage"] == 1.0
    violations = BenchmarkReconciler.validate_math_invariants(data)
    assert len(violations) == 0


def test_ben_012_actual_manifest_has_citation_gates():
    """BEN-012: The actual audit/benchmarks/benchmark-manifest.json has citation precision gate."""
    path = REPO_ROOT / "audit" / "benchmarks" / "benchmark-manifest.json"
    assert path.exists()
    with open(path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
    gates = manifest["quality_gates"]
    assert "citation_precision" in gates
    assert gates["citation_precision"]["status"] == "PASS"
    assert gates["citation_precision"]["observed_baseline"] >= 0.90
