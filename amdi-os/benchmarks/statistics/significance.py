'''
Statistical significance tests and calibration calculations.
'''
from __future__ import annotations

import math
from typing import Sequence

import numpy as np

try:
    from scipy import stats
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


def paired_t_test(baseline: Sequence[float], amdi: Sequence[float]) -> tuple[float, float]:
    '''
    Paired t-test: tests if mean difference is significant.
    Returns (t_statistic, p_value).
    '''
    if len(baseline) < 2 or len(amdi) < 2:
        return 0.0, 1.0
    if len(baseline) != len(amdi):
        raise ValueError('Paired test requires equal-length samples')
    
    if HAS_SCIPY:
        try:
            diff = np.array(amdi) - np.array(baseline)
            if np.std(diff) == 0:
                return 0.0, 1.0
            t, p = stats.ttest_rel(amdi, baseline)
            return float(t), float(p)
        except Exception:
            pass

    # Fallback / manual calculation
    n = len(baseline)
    diffs = [amdi[i] - baseline[i] for i in range(n)]
    mean_diff = sum(diffs) / n
    var_diff = sum((d - mean_diff) ** 2 for d in diffs) / (n - 1) if n > 1 else 0.0
    std_err = math.sqrt(var_diff / n) if n > 0 and var_diff > 0 else 0.0
    if std_err == 0:
        return 0.0, 1.0
    t_stat = mean_diff / std_err
    # Simple two-tailed p-value approximation
    p_val = 2.0 * (1.0 - 0.5 * (1.0 + math.erf(abs(t_stat) / math.sqrt(2.0))))
    return t_stat, p_val


def wilcoxon_signed_rank(baseline: Sequence[float], amdi: Sequence[float]) -> tuple[float, float]:
    '''Non-parametric paired test.'''
    if len(baseline) < 2 or len(amdi) < 2:
        return 0.0, 1.0
    
    if HAS_SCIPY:
        try:
            diff = np.array(amdi) - np.array(baseline)
            diff = diff[diff != 0]
            if len(diff) < 2:
                return 0.0, 1.0
            w, p = stats.wilcoxon(diff)
            return float(w), float(p)
        except Exception:
            pass
            
    return 0.0, 1.0


def cohens_d(baseline: Sequence[float], amdi: Sequence[float]) -> float:
    '''Cohen's d effect size.'''
    if len(baseline) < 2 or len(amdi) < 2:
        return 0.0
    b = np.array(baseline)
    a = np.array(amdi)
    n1, n2 = len(b), len(a)
    var1, var2 = b.var(ddof=1), a.var(ddof=1)
    pooled_std = math.sqrt(((n1 - 1) * var1 + (n2 - 1) * var2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
    return float((a.mean() - b.mean()) / pooled_std)


def confidence_interval(values: Sequence[float], confidence: float = 0.95) -> tuple[float, float]:
    '''Compute CI for the mean.'''
    if not values:
        return 0.0, 0.0
    arr = np.array(values)
    mean = arr.mean()
    n = len(arr)
    std_dev = arr.std(ddof=1) if n > 1 else 0.0
    se = std_dev / math.sqrt(n) if n > 0 and std_dev > 0 else 0.0
    
    if HAS_SCIPY and n > 1:
        try:
            h = se * stats.t.ppf((1 + confidence) / 2, n - 1)
            return float(mean - h), float(mean + h)
        except Exception:
            pass
            
    # Z-critical fallback for 95% confidence (1.96)
    h = se * 1.96
    return float(mean - h), float(mean + h)


def calibration_error(confidences: Sequence[float], accuracies: Sequence[float], n_bins: int = 10) -> float:
    '''Expected Calibration Error (ECE).'''
    if not confidences or len(confidences) != len(accuracies):
        return 0.0
    bins = np.linspace(0, 1, n_bins + 1)
    ece = 0.0
    n = len(confidences)
    for i in range(n_bins):
        lo, hi = bins[i], bins[i + 1]
        in_bin = [(c, a) for c, a in zip(confidences, accuracies) if lo <= c < hi or (i == n_bins - 1 and c == 1.0)]
        if in_bin:
            avg_conf = sum(c for c, _ in in_bin) / len(in_bin)
            avg_acc = sum(a for _, a in in_bin) / len(in_bin)
            ece += (len(in_bin) / n) * abs(avg_conf - avg_acc)
    return ece
