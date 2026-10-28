"""
evaluation/scripts/run_all.py
=============================
Unified CLI benchmark and regression gate runner for AEGIS-DocIntel.
Executes extraction, packing, privacy, and retrieval evaluations,
verifies quality gates, and outputs structured JSON reports.
"""
from __future__ import annotations

import argparse
import datetime
import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from evaluation.scripts.evaluate_extraction import evaluate_extraction
from evaluation.scripts.evaluate_packing import evaluate_packing
from evaluation.scripts.evaluate_privacy import evaluate_privacy
from evaluation.scripts.evaluate_retrieval import evaluate_retrieval
from evaluation.scripts.evaluate_intelligence import evaluate_intelligence


def run_all(output_path: Path | str | None = None, fail_under_gates: bool = False) -> Dict[str, Any]:
    eval_dir = Path(__file__).resolve().parent.parent
    manifest_path = eval_dir / "datasets" / "manifest.json"

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    gates = manifest.get("quality_gates", {})

    print("=" * 60)
    print("AEGIS-DocIntel P2 Quality & Evaluation Suite")
    print("=" * 60)

    # 1. Extraction evaluation
    print("[1/4] Running Document Extraction Fidelity Evaluation...")
    extraction_res = evaluate_extraction()
    print(f"      Reading Order Tau: {extraction_res['reading_order_kendall_tau']} | Table Cell F1: {extraction_res['table_cell_f1']}")

    # 2. Packing evaluation
    print("[2/4] Running Context Packing Invariants Evaluation...")
    packing_res = evaluate_packing()
    print(f"      Budget Violations: {packing_res['budget_violation_rate']} | Min Approx Ratio: {packing_res['min_approx_ratio']}")

    # 3. Privacy evaluation
    print("[3/4] Running Privacy & PII Redaction Evaluation...")
    privacy_res = evaluate_privacy()
    print(f"      Precision: {privacy_res['precision']} | Recall: {privacy_res['recall']} | Leakage: {privacy_res['leakage_rate']}")

    # 4. Retrieval evaluation
    print("[4/5] Running Retrieval & Grounding Evaluation...")
    retrieval_res = evaluate_retrieval()
    print(f"      MRR: {retrieval_res['mrr']} | Recall@5: {retrieval_res['recall_at_5']} | Abstention: {retrieval_res['abstention_accuracy']}")

    # 5. Document Intelligence evaluation
    print("[5/5] Running Document Intelligence Evaluation...")
    intel_res = evaluate_intelligence()
    print(f"      Extraction F1: {intel_res['extraction_f1']} | Grounding Fidelity: {intel_res['grounding_fidelity']} | Conflict Recall: {intel_res['conflict_detection_recall']}")

    # Gate Verification
    passed_all = True
    gate_failures = []

    # Extraction gates
    if extraction_res["reading_order_kendall_tau"] < gates.get("extraction", {}).get("min_reading_order_kendall_tau", 0.80):
        passed_all = False
        gate_failures.append("extraction.reading_order_kendall_tau below gate")
    if extraction_res["table_cell_f1"] < gates.get("extraction", {}).get("min_table_cell_f1", 0.90):
        passed_all = False
        gate_failures.append("extraction.table_cell_f1 below gate")

    # Packing gates
    if packing_res["budget_violation_rate"] > gates.get("packing", {}).get("max_budget_violation_rate", 0.0):
        passed_all = False
        gate_failures.append("packing.budget_violation_rate exceeds gate")
    if packing_res["min_approx_ratio"] < gates.get("packing", {}).get("min_approx_ratio", 0.316):
        passed_all = False
        gate_failures.append("packing.min_approx_ratio below gate")

    # Privacy gates
    if privacy_res["precision"] < gates.get("privacy", {}).get("min_precision", 0.85):
        passed_all = False
        gate_failures.append("privacy.precision below gate")
    if privacy_res["recall"] < gates.get("privacy", {}).get("min_recall", 0.85):
        passed_all = False
        gate_failures.append("privacy.recall below gate")
    if privacy_res["leakage_rate"] > gates.get("privacy", {}).get("max_leakage_rate", 0.0):
        passed_all = False
        gate_failures.append("privacy.leakage_rate exceeds gate")

    # Retrieval gates
    if retrieval_res["mrr"] < gates.get("retrieval", {}).get("min_mrr", 0.70):
        passed_all = False
        gate_failures.append("retrieval.mrr below gate")
    if retrieval_res["recall_at_5"] < gates.get("retrieval", {}).get("min_recall_at_5", 0.80):
        passed_all = False
        gate_failures.append("retrieval.recall_at_5 below gate")
    if retrieval_res["abstention_accuracy"] < gates.get("retrieval", {}).get("min_abstention_accuracy", 1.0):
        passed_all = False
        gate_failures.append("retrieval.abstention_accuracy below gate")

    # Document intelligence gates
    if intel_res["extraction_f1"] < 0.85:
        passed_all = False
        gate_failures.append("intelligence.extraction_f1 below gate")
    if intel_res["grounding_fidelity"] < 1.0:
        passed_all = False
        gate_failures.append("intelligence.grounding_fidelity below gate")

    report: Dict[str, Any] = {
        "benchmark_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "overall_status": "PASSED" if passed_all else "FAILED",
        "gate_failures": gate_failures,
        "metrics": {
            "extraction": extraction_res,
            "packing": packing_res,
            "privacy": privacy_res,
            "retrieval": retrieval_res,
            "document_intelligence": intel_res,
        },
        "gates_applied": gates,
    }

    if output_path:
        out_file = Path(output_path)
        out_file.parent.mkdir(parents=True, exist_ok=True)
        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"\nReport written to: {out_file}")

    print("-" * 60)
    print(f"OVERALL EVALUATION RESULT: {report['overall_status']}")
    if gate_failures:
        print(f"Gate Failures: {gate_failures}")
    print("-" * 60)

    if fail_under_gates and not passed_all:
        sys.exit(1)

    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run AEGIS-DocIntel evaluation benchmarks.")
    parser.add_argument("--output", type=str, default="evaluation/reports/baseline_report.json", help="Path to output report JSON")
    parser.add_argument("--fail-under-gates", action="store_true", help="Exit with non-zero status if any gate fails")
    args = parser.parse_args()

    run_all(output_path=args.output, fail_under_gates=args.fail_under_gates)
