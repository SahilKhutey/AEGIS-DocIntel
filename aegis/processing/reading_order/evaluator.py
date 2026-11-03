"""
aegis.processing.reading_order.evaluator
=======================================
Quantitative metrics for reading order: Kendall's tau, pairwise ordering accuracy,
normalized sequence similarity, and interleaving detection.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aegis.processing.benchmarking.metrics import levenshtein_distance


class ReadingOrderEvaluationReport(BaseModel):
    document_id: str
    page_number: int
    total_regions: int
    pairwise_accuracy: float = 1.0
    kendall_tau: float = 1.0
    sequence_similarity: float = 1.0
    concordant_pairs: int = 0
    discordant_pairs: int = 0
    total_pairs: int = 0
    column_interleaving_detected: bool = False
    discrepancies: List[Dict[str, Any]] = Field(default_factory=list)


class ReadingOrderEvaluator:
    """Evaluates predicted reading order sequences against ground truth references."""

    @staticmethod
    def evaluate(
        predicted: List[str],
        ground_truth: List[str],
        document_id: str = "DOC",
        page_number: int = 1
    ) -> ReadingOrderEvaluationReport:
        """Calculate Kendall's tau, pairwise accuracy, and sequence similarity."""
        if len(ground_truth) <= 1:
            return ReadingOrderEvaluationReport(
                document_id=document_id,
                page_number=page_number,
                total_regions=len(ground_truth),
                pairwise_accuracy=1.0,
                kendall_tau=1.0,
                sequence_similarity=1.0,
            )

        pos_gt = {item: i for i, item in enumerate(ground_truth)}
        pred_filtered = [item for item in predicted if item in pos_gt]

        n = len(pred_filtered)
        if n <= 1:
            return ReadingOrderEvaluationReport(
                document_id=document_id,
                page_number=page_number,
                total_regions=len(ground_truth),
                pairwise_accuracy=1.0,
                kendall_tau=1.0,
                sequence_similarity=1.0,
            )

        concordant = 0
        discordant = 0
        discrepancies = []

        for i in range(n):
            for j in range(i + 1, n):
                item_i = pred_filtered[i]
                item_j = pred_filtered[j]
                gt_i = pos_gt[item_i]
                gt_j = pos_gt[item_j]

                if gt_i < gt_j:
                    concordant += 1
                else:
                    discordant += 1
                    discrepancies.append({
                        "item_before": item_i,
                        "item_after": item_j,
                        "predicted_order": (i, j),
                        "ground_truth_order": (gt_i, gt_j),
                    })

        total_pairs = n * (n - 1) // 2
        pairwise_acc = concordant / total_pairs if total_pairs > 0 else 1.0
        tau = (concordant - discordant) / total_pairs if total_pairs > 0 else 1.0

        # Normalized sequence similarity using Levenshtein distance
        dist, _, _, _ = levenshtein_distance(pred_filtered, ground_truth)
        max_len = max(len(pred_filtered), len(ground_truth))
        seq_sim = 1.0 - (dist / max_len) if max_len > 0 else 1.0

        return ReadingOrderEvaluationReport(
            document_id=document_id,
            page_number=page_number,
            total_regions=len(ground_truth),
            pairwise_accuracy=round(pairwise_acc, 4),
            kendall_tau=round(tau, 4),
            sequence_similarity=round(seq_sim, 4),
            concordant_pairs=concordant,
            discordant_pairs=discordant,
            total_pairs=total_pairs,
            column_interleaving_detected=(discordant > 0),
            discrepancies=discrepancies[:10],
        )
