"""
Statistical Significance Tests
==============================

Performs statistical testing to determine if AMDI-OS performance
is significantly different from baselines.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional

import numpy as np


@dataclass
class SignificanceResult:
    """Statistical significance test result."""

    test_name: str
    statistic: float
    p_value: float
    significant: bool
    confidence_interval: Optional[tuple[float, float]] = None

    def to_dict(self) -> dict:
        return {
            "test_name": self.test_name,
            "statistic": round(self.statistic, 6),
            "p_value": round(self.p_value, 6),
            "significant": self.significant,
            "confidence_interval": (
                [round(self.confidence_interval[0], 6), round(self.confidence_interval[1], 6)]
                if self.confidence_interval else None
            ),
        }


class StatisticalTests:
    """Perform significance tests comparing two sets of performance scores."""

    @staticmethod
    def paired_ttest(a: List[float], b: List[float]) -> SignificanceResult:
        from scipy import stats
        res = stats.ttest_rel(a, b)
        # compute confidence interval of difference (a - b)
        diff = np.array(a) - np.array(b)
        mean_diff = float(np.mean(diff)) if len(diff) > 0 else 0.0
        sem = float(stats.sem(diff)) if len(diff) > 1 else 0.0
        ci = stats.t.interval(0.95, len(diff) - 1, loc=mean_diff, scale=sem) if len(diff) > 1 else (mean_diff, mean_diff)
        return SignificanceResult(
            test_name="paired_t_test",
            statistic=float(res.statistic) if not np.isnan(res.statistic) else 0.0,
            p_value=float(res.pvalue) if not np.isnan(res.pvalue) else 1.0,
            significant=bool(res.pvalue < 0.05) if not np.isnan(res.pvalue) else False,
            confidence_interval=(float(ci[0]), float(ci[1]))
        )

    @staticmethod
    def wilcoxon_signed_rank(a: List[float], b: List[float]) -> SignificanceResult:
        from scipy import stats
        diff = np.array(a) - np.array(b)
        if np.all(diff == 0):
            return SignificanceResult(
                test_name="wilcoxon_signed_rank",
                statistic=0.0,
                p_value=1.0,
                significant=False,
            )
        try:
            res = stats.wilcoxon(a, b)
            return SignificanceResult(
                test_name="wilcoxon_signed_rank",
                statistic=float(res.statistic),
                p_value=float(res.pvalue),
                significant=bool(res.pvalue < 0.05),
            )
        except Exception:
            return SignificanceResult(
                test_name="wilcoxon_signed_rank",
                statistic=0.0,
                p_value=1.0,
                significant=False,
            )
