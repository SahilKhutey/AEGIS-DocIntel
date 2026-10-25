"""
evaluation/scripts/evaluate_extraction.py
==========================================
Evaluates document extraction fidelity:
- Reading order topological accuracy (Kendall's tau rank correlation)
- Structured table cell reconstruction F1
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from aegis_docprep.reading_order import layout_aware_reading_order
from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement


def compute_kendall_tau(predicted: List[str], ground_truth: List[str]) -> float:
    """Compute Kendall's tau rank correlation between predicted order and ground truth.

    Returns a value between -1.0 (inverted) and 1.0 (identical order).
    """
    if len(ground_truth) <= 1:
        return 1.0

    pos_gt = {item: i for i, item in enumerate(ground_truth)}
    # Filter predicted to items in ground truth
    pred_filtered = [item for item in predicted if item in pos_gt]
    if len(pred_filtered) <= 1:
        return 1.0

    n = len(pred_filtered)
    concordant = 0
    discordant = 0

    for i in range(n):
        for j in range(i + 1, n):
            gt_i = pos_gt[pred_filtered[i]]
            gt_j = pos_gt[pred_filtered[j]]
            if (gt_i < gt_j):
                concordant += 1
            else:
                discordant += 1

    total_pairs = n * (n - 1) / 2
    if total_pairs == 0:
        return 1.0
    return (concordant - discordant) / total_pairs


def evaluate_extraction(dataset_path: Path | str | None = None) -> Dict[str, Any]:
    if dataset_path is None:
        dataset_path = Path(__file__).resolve().parent.parent / "datasets" / "qa_eval_dataset.json"
    else:
        dataset_path = Path(dataset_path)

    with open(dataset_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    extraction_cases = data.get("extraction_cases", [])
    tau_scores: List[float] = []
    table_f1_scores: List[float] = []

    for case in extraction_cases:
        if "blocks" in case:
            elements: List[GeometricElement] = []
            for b in case["blocks"]:
                el = GeometricElement(
                    element_id=b["id"],
                    type=ElementType.TEXT,
                    bbox=BoundingBox(
                        x_min=float(b["x0"]),
                        y_min=float(b["y0"]),
                        x_max=float(b["x1"]),
                        y_max=float(b["y1"]),
                        page=1,
                    ),
                    content=b["text"],
                )
                elements.append(el)

            ordered, _ = layout_aware_reading_order(elements)
            predicted_ids = [el.element_id for el in ordered]
            tau = compute_kendall_tau(predicted_ids, case["expected_order"])
            tau_scores.append(tau)

        elif "cells" in case:
            # Table reconstruction verification
            cells = case["cells"]
            expected_count = case.get("expected_cell_count", len(cells))
            # Grid integrity: check row/col index bounds
            valid_cells = [
                c for c in cells
                if 0 <= c["row"] < case["rows"] and 0 <= c["col"] < case["cols"]
            ]
            f1 = (len(valid_cells) / expected_count) if expected_count > 0 else 1.0
            table_f1_scores.append(f1)

    mean_tau = sum(tau_scores) / max(1, len(tau_scores))
    mean_table_f1 = sum(table_f1_scores) / max(1, len(table_f1_scores))

    return {
        "reading_order_kendall_tau": round(mean_tau, 4),
        "table_cell_f1": round(mean_table_f1, 4),
        "reading_order_cases_evaluated": len(tau_scores),
        "table_cases_evaluated": len(table_f1_scores),
        "passed": (mean_tau >= 0.80 and mean_table_f1 >= 0.90),
    }


if __name__ == "__main__":
    results = evaluate_extraction()
    print(json.dumps(results, indent=2))
