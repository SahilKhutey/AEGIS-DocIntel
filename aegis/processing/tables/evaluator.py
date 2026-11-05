"""
aegis.processing.tables.evaluator
=================================
Quantitative evaluation of table extraction: cell accuracy, row/col structure,
exact numeric matching, and Tree-Edit-Distance-based Similarity (TEDS).
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aegis.processing.benchmarking.metrics import levenshtein_distance
from aegis.processing.models import TableCellModel, TableReconstruction
from aegis.processing.tables.structure import TableGridValidator


class TableEvaluationReport(BaseModel):
    table_id: str
    row_count_pred: int
    row_count_gt: int
    col_count_pred: int
    col_count_gt: int
    total_gt_cells: int
    total_pred_cells: int
    cell_exact_match_ratio: float = 0.0
    cell_numeric_accuracy: float = 0.0
    structure_accuracy: float = 0.0
    teds_score: float = 0.0
    grid_valid: bool = True
    grid_errors: List[str] = Field(default_factory=list)


def _clean_numeric(val: str) -> Optional[float]:
    """Extract numeric value if string represents a number."""
    clean = re.sub(r"[^\d.-]", "", val)
    try:
        return float(clean)
    except ValueError:
        return None


def _calculate_teds_score(html_pred: str, html_gt: str) -> float:
    """Calculate Tree-Edit-Distance-based Similarity (TEDS) between table HTML structures.
    
    TEDS = 1 - (TreeEditDistance / max(|Tree_pred|, |Tree_gt|))
    """
    # Tokenize HTML tags and text content
    tokens_pred = re.findall(r"<[^>]+>|[^<>\s]+", html_pred)
    tokens_gt = re.findall(r"<[^>]+>|[^<>\s]+", html_gt)

    if not tokens_pred and not tokens_gt:
        return 1.0
    if not tokens_pred or not tokens_gt:
        return 0.0

    dist, _, _, _ = levenshtein_distance(tokens_pred, tokens_gt)
    max_len = max(len(tokens_pred), len(tokens_gt))
    teds = max(0.0, 1.0 - (dist / max_len))
    return round(teds, 4)


class TableEvaluator:
    """Evaluates reconstructed tables against ground-truth references."""

    @classmethod
    def evaluate(
        cls,
        predicted: TableReconstruction,
        ground_truth: TableReconstruction
    ) -> TableEvaluationReport:
        """Compute structural, cell-level, and TEDS metrics."""
        is_valid, grid_errs = TableGridValidator.validate(predicted)

        pred_map = {(c.row_index, c.column_index): c.text for c in predicted.cells}
        gt_map = {(c.row_index, c.column_index): c.text for c in ground_truth.cells}

        total_gt = len(gt_map)
        exact_matches = 0
        numeric_matches = 0
        total_numeric_gt = 0
        correct_positions = 0

        for pos, gt_text in gt_map.items():
            if pos in pred_map:
                correct_positions += 1
                pred_text = pred_map[pos]

                # Exact cell match
                if pred_text.strip().lower() == gt_text.strip().lower():
                    exact_matches += 1

                # Numeric match
                gt_num = _clean_numeric(gt_text)
                if gt_num is not None:
                    total_numeric_gt += 1
                    pred_num = _clean_numeric(pred_text)
                    if pred_num is not None and abs(gt_num - pred_num) < 0.001:
                        numeric_matches += 1

        exact_ratio = exact_matches / total_gt if total_gt > 0 else 0.0
        struct_acc = correct_positions / total_gt if total_gt > 0 else 0.0
        num_acc = (numeric_matches / total_numeric_gt) if total_numeric_gt > 0 else 1.0

        html_pred = TableGridValidator.to_html(predicted)
        html_gt = TableGridValidator.to_html(ground_truth)
        teds = _calculate_teds_score(html_pred, html_gt)

        return TableEvaluationReport(
            table_id=predicted.table_id,
            row_count_pred=predicted.row_count,
            row_count_gt=ground_truth.row_count,
            col_count_pred=predicted.column_count,
            col_count_gt=ground_truth.column_count,
            total_gt_cells=total_gt,
            total_pred_cells=len(pred_map),
            cell_exact_match_ratio=round(exact_ratio, 4),
            cell_numeric_accuracy=round(num_acc, 4),
            structure_accuracy=round(struct_acc, 4),
            teds_score=teds,
            grid_valid=is_valid,
            grid_errors=grid_errs,
        )
