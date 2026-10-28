"""
tests/test_mvp5_evaluation.py
=============================
Integration test verifying that the Document Intelligence evaluation benchmark
executes and satisfies all predefined quality gates.
"""

from evaluation.scripts.evaluate_intelligence import evaluate_intelligence


def test_document_intelligence_benchmark_quality_gates():
    results = evaluate_intelligence()

    assert results["extraction_precision"] >= 0.85
    assert results["extraction_recall"] >= 0.85
    assert results["extraction_f1"] >= 0.85
    assert results["grounding_fidelity"] >= 1.0  # 100% of facts must have grounded evidence
    assert results["normalization_accuracy"] >= 0.90
    assert results["comparison_accuracy"] >= 0.85
    assert results["conflict_detection_recall"] >= 0.85
