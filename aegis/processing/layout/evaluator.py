"""
aegis.processing.layout.evaluator
=================================
Layout analysis evaluation engine calculating IoU, class-aware precision, recall, F1, and mAP.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from aegis.processing.layout.regions import compute_iou
from aegis.processing.models import LayoutRegion, RegionType


class ClassMetric(BaseModel):
    category: str
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    precision: float = 0.0
    recall: float = 0.0
    f1_score: float = 0.0
    average_iou: float = 0.0


class LayoutEvaluationReport(BaseModel):
    iou_threshold: float = 0.50
    total_ground_truth_regions: int = 0
    total_predicted_regions: int = 0
    overall_precision: float = 0.0
    overall_recall: float = 0.0
    overall_f1: float = 0.0
    mean_average_precision: float = 0.0
    class_metrics: Dict[str, ClassMetric] = Field(default_factory=dict)
    matched_pairs: List[Dict[str, Any]] = Field(default_factory=list)
    unmatched_predictions: List[str] = Field(default_factory=list)
    unmatched_ground_truths: List[str] = Field(default_factory=list)


class LayoutEvaluator:
    """Evaluates predicted layout bounding boxes and categories against ground truth."""

    def __init__(self, iou_threshold: float = 0.50):
        self.iou_threshold = iou_threshold

    def evaluate(
        self,
        predictions: List[LayoutRegion],
        ground_truths: List[LayoutRegion]
    ) -> LayoutEvaluationReport:
        """Perform class-aware one-to-one matching and compute performance metrics."""
        report = LayoutEvaluationReport(
            iou_threshold=self.iou_threshold,
            total_ground_truth_regions=len(ground_truths),
            total_predicted_regions=len(predictions),
        )

        all_categories = sorted(list({r.region_type.value for r in ground_truths} | {r.region_type.value for r in predictions}))

        total_tp = 0
        total_fp = 0
        total_fn = 0
        ap_sum = 0.0

        for cat in all_categories:
            preds_cat = [p for p in predictions if p.region_type.value == cat]
            gts_cat = [g for g in ground_truths if g.region_type.value == cat]

            # Candidate pairs with IoU >= threshold
            candidate_pairs = []
            for p_idx, p in enumerate(preds_cat):
                for g_idx, g in enumerate(gts_cat):
                    iou = compute_iou(p.bbox, g.bbox)
                    if iou >= self.iou_threshold:
                        candidate_pairs.append((iou, p_idx, g_idx, p, g))

            # Greedy one-to-one matching by highest IoU
            candidate_pairs.sort(key=lambda x: x[0], reverse=True)
            matched_p = set()
            matched_g = set()
            cat_ious = []

            for iou, p_idx, g_idx, p, g in candidate_pairs:
                if p_idx not in matched_p and g_idx not in matched_g:
                    matched_p.add(p_idx)
                    matched_g.add(g_idx)
                    cat_ious.append(iou)
                    report.matched_pairs.append({
                        "category": cat,
                        "pred_id": p.region_id,
                        "gt_id": g.region_id,
                        "iou": round(iou, 4),
                    })

            tp = len(matched_p)
            fp = len(preds_cat) - tp
            fn = len(gts_cat) - tp

            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = (2 * prec * rec) / (prec + rec) if (prec + rec) > 0 else 0.0
            avg_iou = sum(cat_ious) / len(cat_ious) if cat_ious else 0.0

            total_tp += tp
            total_fp += fp
            total_fn += fn
            ap_sum += prec  # standard proxy for AP at fixed IoU threshold

            report.class_metrics[cat] = ClassMetric(
                category=cat,
                true_positives=tp,
                false_positives=fp,
                false_negatives=fn,
                precision=round(prec, 4),
                recall=round(rec, 4),
                f1_score=round(f1, 4),
                average_iou=round(avg_iou, 4),
            )

            # Record unmatched
            for p_idx, p in enumerate(preds_cat):
                if p_idx not in matched_p:
                    report.unmatched_predictions.append(p.region_id)
            for g_idx, g in enumerate(gts_cat):
                if g_idx not in matched_g:
                    report.unmatched_ground_truths.append(g.region_id)

        overall_prec = total_tp / (total_tp + total_fp) if (total_tp + total_fp) > 0 else 0.0
        overall_rec = total_tp / (total_tp + total_fn) if (total_tp + total_fn) > 0 else 0.0
        overall_f1 = (2 * overall_prec * overall_rec) / (overall_prec + overall_rec) if (overall_prec + overall_rec) > 0 else 0.0
        m_ap = ap_sum / len(all_categories) if all_categories else 0.0

        report.overall_precision = round(overall_prec, 4)
        report.overall_recall = round(overall_rec, 4)
        report.overall_f1 = round(overall_f1, 4)
        report.mean_average_precision = round(m_ap, 4)

        return report
