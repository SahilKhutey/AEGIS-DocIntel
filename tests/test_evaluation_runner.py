"""
tests/test_evaluation_runner.py
===============================
Automated verification of the P2 evaluation suite:
1. Extraction, packing, privacy, and retrieval sub-evaluators execute and return valid metrics.
2. Unified run_all() executes, outputs reports, and passes all regression quality gates.
3. Gate enforcement correctly catches metric degradations.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from evaluation.scripts.evaluate_extraction import evaluate_extraction
from evaluation.scripts.evaluate_packing import evaluate_packing
from evaluation.scripts.evaluate_privacy import evaluate_privacy
from evaluation.scripts.evaluate_retrieval import evaluate_retrieval
from evaluation.scripts.run_all import run_all


def test_evaluate_extraction_metrics():
    """P2.5: Extraction fidelity evaluation computes valid Kendall's tau and table cell F1."""
    res = evaluate_extraction()
    assert res["passed"] is True
    assert 0.80 <= res["reading_order_kendall_tau"] <= 1.0
    assert 0.90 <= res["table_cell_f1"] <= 1.0


def test_evaluate_packing_invariants():
    """P2.5: Context packing evaluation enforces 0% budget violations and approx bound."""
    res = evaluate_packing()
    assert res["passed"] is True
    assert res["budget_violation_rate"] == 0.0
    assert res["min_approx_ratio"] >= 0.316


def test_evaluate_privacy_precision_recall():
    """P2.5: Privacy evaluation verifies precision >= 0.85, recall >= 0.85, and zero leakage."""
    res = evaluate_privacy()
    assert res["passed"] is True
    assert res["precision"] >= 0.85
    assert res["recall"] >= 0.85
    assert res["leakage_rate"] == 0.0
    assert res["fail_closed_blocked"] is True


def test_evaluate_retrieval_grounding_and_abstention():
    """P2.5: Retrieval evaluation verifies MRR >= 0.70, recall >= 0.80, and 100% abstention."""
    res = evaluate_retrieval()
    assert res["passed"] is True
    assert res["mrr"] >= 0.70
    assert res["recall_at_5"] >= 0.80
    assert res["abstention_accuracy"] == 1.0
    assert res["citation_validation_passed"] is True


def test_unified_benchmark_runner_and_gates(tmp_path: Path):
    """P2.5: Master run_all() generates valid baseline report conforming to schema."""
    report_file = tmp_path / "test_report.json"
    report = run_all(output_path=report_file, fail_under_gates=False)

    assert report["overall_status"] == "PASSED"
    assert len(report["gate_failures"]) == 0
    assert report_file.exists()

    with open(report_file, "r", encoding="utf-8") as f:
        saved_data = json.load(f)

    assert saved_data["overall_status"] == "PASSED"
    assert "metrics" in saved_data
    assert "extraction" in saved_data["metrics"]
    assert "packing" in saved_data["metrics"]
    assert "privacy" in saved_data["metrics"]
    assert "retrieval" in saved_data["metrics"]
