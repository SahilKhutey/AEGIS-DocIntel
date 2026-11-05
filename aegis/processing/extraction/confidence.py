"""
aegis.processing.extraction.confidence
======================================
Confidence scoring, distribution metrics, and calibration evaluation.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field


class CalibrationReport(BaseModel):
    mean_confidence: Optional[float] = None
    median_confidence: Optional[float] = None
    confidence_recorded_ratio: float = 0.0
    expected_calibration_error: Optional[float] = None
    bins: Dict[str, Dict[str, float]] = Field(default_factory=dict)


class ConfidenceEvaluator:
    """Evaluates confidence distributions and calibration against empirical accuracy."""

    @staticmethod
    def compute_distribution(scores: List[Optional[float]]) -> Dict[str, Any]:
        """Compute distribution statistics for a list of confidence scores."""
        valid_scores = [s for s in scores if s is not None and not math.isnan(s)]
        if not valid_scores:
            return {
                "recorded_count": 0,
                "missing_count": len(scores),
                "recorded_ratio": 0.0,
                "mean": None,
                "median": None,
                "min": None,
                "max": None,
            }

        valid_scores.sort()
        n = len(valid_scores)
        mean_val = sum(valid_scores) / n
        median_val = valid_scores[n // 2] if n % 2 != 0 else (valid_scores[n // 2 - 1] + valid_scores[n // 2]) / 2.0

        return {
            "recorded_count": n,
            "missing_count": len(scores) - n,
            "recorded_ratio": round(n / len(scores), 4) if scores else 0.0,
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "min": round(valid_scores[0], 4),
            "max": round(valid_scores[-1], 4),
        }

    @staticmethod
    def compute_ece(
        confidences: List[float],
        accuracies: List[float],
        n_bins: int = 10
    ) -> Tuple[float, Dict[str, Dict[str, float]]]:
        """Compute Expected Calibration Error (ECE).
        
        ECE = sum_b (|B_b| / N) * |acc(B_b) - conf(B_b)|
        """
        if not confidences or len(confidences) != len(accuracies):
            return 0.0, {}

        bin_boundaries = [i / n_bins for i in range(n_bins + 1)]
        bins_data: Dict[str, Dict[str, float]] = {}
        total_items = len(confidences)
        ece = 0.0

        for i in range(n_bins):
            low = bin_boundaries[i]
            high = bin_boundaries[i + 1]
            bin_name = f"{low:.1f}-{high:.1f}"

            bin_confs = []
            bin_accs = []

            for conf, acc in zip(confidences, accuracies):
                if conf is None or math.isnan(conf):
                    continue
                # Include upper boundary in last bin
                if (i == n_bins - 1 and low <= conf <= high) or (low <= conf < high):
                    bin_confs.append(conf)
                    bin_accs.append(acc)

            count = len(bin_confs)
            if count > 0:
                avg_conf = sum(bin_confs) / count
                avg_acc = sum(bin_accs) / count
                gap = abs(avg_acc - avg_conf)
                ece += (count / total_items) * gap

                bins_data[bin_name] = {
                    "count": float(count),
                    "avg_confidence": round(avg_conf, 4),
                    "avg_accuracy": round(avg_acc, 4),
                    "gap": round(gap, 4),
                }
            else:
                bins_data[bin_name] = {
                    "count": 0.0,
                    "avg_confidence": 0.0,
                    "avg_accuracy": 0.0,
                    "gap": 0.0,
                }

        return round(ece, 4), bins_data
