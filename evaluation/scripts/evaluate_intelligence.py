"""
evaluation/scripts/evaluate_intelligence.py
===========================================
Benchmark evaluation suite for Document Intelligence, Fact Extraction,
Deterministic Normalization, and Cross-Document Conflict Reasoning.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from src.engines.intelligence.comparison import DocumentComparator
from src.engines.intelligence.conflict_detection import ConflictDetector
from src.engines.intelligence.fact_extractor import FactExtractor, verify_quote_in_source


def evaluate_intelligence(data_dir: Path | str | None = None) -> Dict[str, Any]:
    base_dir = (
        Path(data_dir)
        if data_dir
        else Path(__file__).resolve().parent.parent / "datasets" / "document_intelligence"
    )

    extractor = FactExtractor()
    comparator = DocumentComparator()
    conflict_detector = ConflictDetector()

    # 1. Extraction Evaluation
    extract_file = base_dir / "extraction_cases.jsonl"
    total_expected = 0
    total_extracted = 0
    correctly_extracted = 0
    grounded_evidence_count = 0
    normalized_correct_count = 0

    if extract_file.exists():
        with extract_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                case = json.loads(line)
                res = extractor.extract_document_facts(
                    tenant_id=case["tenant_id"],
                    document_id=case["document_id"],
                    passages=case["passages"],
                    schema_name=case["schema_name"],
                )

                extracted_by_attr = {fact.attribute: fact for fact in res.facts}
                total_extracted += len(res.facts)

                # Check evidence grounding for all extracted facts
                for fact in res.facts:
                    for ev in fact.evidence:
                        # Find passage source text
                        passage_text = ""
                        for p in case["passages"]:
                            if p["chunk_id"] == ev.chunk_id:
                                passage_text = p["text"]
                                break
                        valid, _, _ = verify_quote_in_source(
                            quote=ev.quoted_text,
                            source_text=passage_text,
                            start_offset=ev.start_offset,
                            end_offset=ev.end_offset,
                        )
                        if valid:
                            grounded_evidence_count += 1

                for exp in case.get("expected_facts", []):
                    total_expected += 1
                    attr = exp["attribute"]
                    if attr in extracted_by_attr:
                        fact = extracted_by_attr[attr]
                        # Check value equivalence
                        val = fact.value
                        exp_val = exp["expected_value"]

                        val_matches = False
                        if isinstance(val, (int, float)) and isinstance(exp_val, (int, float)):
                            val_matches = math.isclose(float(val), float(exp_val), rel_tol=1e-4)
                        elif str(val).strip().lower() == str(exp_val).strip().lower():
                            val_matches = True

                        if val_matches:
                            correctly_extracted += 1
                            normalized_correct_count += 1

    precision = (
        correctly_extracted / total_extracted if total_extracted > 0 else 1.0
    )
    recall = (
        correctly_extracted / total_expected if total_expected > 0 else 1.0
    )
    f1 = (
        (2 * precision * recall) / (precision + recall)
        if (precision + recall) > 0
        else 0.0
    )
    grounding_fidelity = (
        grounded_evidence_count / total_extracted if total_extracted > 0 else 1.0
    )
    norm_acc = (
        normalized_correct_count / total_expected if total_expected > 0 else 1.0
    )

    # 2. Comparison & Conflict Detection Evaluation
    compare_file = base_dir / "comparison_cases.jsonl"
    total_expected_comparisons = 0
    correct_comparisons = 0
    total_expected_conflicts = 0
    detected_conflicts = 0

    if compare_file.exists():
        with compare_file.open("r", encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                case = json.loads(line)
                t_id = case["tenant_id"]
                schema = case["schema_name"]

                left_res = extractor.extract_document_facts(
                    tenant_id=t_id,
                    document_id=case["left_doc_id"],
                    passages=case["left_passages"],
                    schema_name=schema,
                )
                right_res = extractor.extract_document_facts(
                    tenant_id=t_id,
                    document_id=case["right_doc_id"],
                    passages=case["right_passages"],
                    schema_name=schema,
                )

                comp_res = comparator.compare_facts(
                    tenant_id=t_id,
                    left_doc_id=case["left_doc_id"],
                    left_facts=left_res.facts,
                    right_doc_id=case["right_doc_id"],
                    right_facts=right_res.facts,
                )

                comp_by_attr = {c.attribute: c.status for c in comp_res.comparisons}
                for exp_comp in case.get("expected_comparisons", []):
                    total_expected_comparisons += 1
                    attr = exp_comp["attribute"]
                    if comp_by_attr.get(attr) == exp_comp["expected_status"]:
                        correct_comparisons += 1

                all_facts = list(left_res.facts) + list(right_res.facts)
                conflicts = conflict_detector.detect_conflicts(tenant_id=t_id, facts=all_facts)
                conflicts_by_attr = {c.attribute: c.conflict_type for c in conflicts}

                for exp_conf in case.get("expected_conflicts", []):
                    total_expected_conflicts += 1
                    attr = exp_conf["attribute"]
                    if conflicts_by_attr.get(attr) == exp_conf["conflict_type"]:
                        detected_conflicts += 1

    comp_accuracy = (
        correct_comparisons / total_expected_comparisons
        if total_expected_comparisons > 0
        else 1.0
    )
    conflict_recall = (
        detected_conflicts / total_expected_conflicts
        if total_expected_conflicts > 0
        else 1.0
    )

    return {
        "extraction_precision": round(precision, 4),
        "extraction_recall": round(recall, 4),
        "extraction_f1": round(f1, 4),
        "grounding_fidelity": round(grounding_fidelity, 4),
        "normalization_accuracy": round(norm_acc, 4),
        "comparison_accuracy": round(comp_accuracy, 4),
        "conflict_detection_recall": round(conflict_recall, 4),
    }


if __name__ == "__main__":
    results = evaluate_intelligence()
    print("=" * 60)
    print("Document Intelligence Benchmark Results")
    print("=" * 60)
    for k, v in results.items():
        print(f"  {k}: {v}")
    print("=" * 60)
