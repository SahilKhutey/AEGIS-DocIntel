'''
AEGIS-MIOS — Statistics
========================
Statistical analysis algorithms:
- Hypothesis Testing (One-sample t-test, Two-sample t-test, Z-test)
- Ordinary Least Squares (OLS) Linear Regression with standard errors
- Bootstrap Resampling for confidence interval estimation
'''

from __future__ import annotations

from typing import Callable
import numpy as np
from scipy.stats import t as student_t, norm as normal_dist


def t_test_one_sample(x: np.ndarray, pop_mean: float) -> tuple[float, float]:
    '''
    Compute a one-sample t-test.
    Returns: (t_statistic, two_tailed_p_value)
    '''
    n = len(x)
    if n <= 1:
        return 0.0, 1.0
    sample_mean = np.mean(x)
    sample_var = np.var(x, ddof=1)
    se = np.sqrt(sample_var / n)

    if se == 0.0:
        return 0.0, 1.0 if sample_mean == pop_mean else 0.0

    t_stat = (sample_mean - pop_mean) / se
    p_val = 2.0 * (1.0 - student_t.cdf(abs(t_stat), df=n - 1))
    return float(t_stat), float(p_val)


def t_test_two_sample(x1: np.ndarray, x2: np.ndarray) -> tuple[float, float]:
    '''
    Compute an independent two-sample t-test (assuming equal variances / Student's t).
    Returns: (t_statistic, two_tailed_p_value)
    '''
    n1, n2 = len(x1), len(x2)
    if n1 <= 1 or n2 <= 1:
        return 0.0, 1.0

    mean1, mean2 = np.mean(x1), np.mean(x2)
    var1, var2 = np.var(x1, ddof=1), np.var(x2, ddof=1)

    # Pooled variance
    df = n1 + n2 - 2
    pooled_var = ((n1 - 1) * var1 + (n2 - 1) * var2) / df
    se = np.sqrt(pooled_var * (1.0 / n1 + 1.0 / n2))

    if se == 0.0:
        return 0.0, 1.0 if mean1 == mean2 else 0.0

    t_stat = (mean1 - mean2) / se
    p_val = 2.0 * (1.0 - student_t.cdf(abs(t_stat), df=df))
    return float(t_stat), float(p_val)


def z_test(x: np.ndarray, pop_mean: float, pop_std: float) -> tuple[float, float]:
    '''
    Compute a z-test given known population standard deviation.
    Returns: (z_statistic, two_tailed_p_value)
    '''
    n = len(x)
    if n == 0 or pop_std <= 0:
        return 0.0, 1.0

    sample_mean = np.mean(x)
    se = pop_std / np.sqrt(n)

    z_stat = (sample_mean - pop_mean) / se
    p_val = 2.0 * (1.0 - normal_dist.cdf(abs(z_stat)))
    return float(z_stat), float(p_val)


def linear_regression(x: np.ndarray, y: np.ndarray) -> dict:
    '''
    Fit an Ordinary Least Squares (OLS) simple linear regression model: y = beta_0 + beta_1 * x
    Returns:
    - 'slope': beta_1
    - 'intercept': beta_0
    - 'r_squared': R² coefficient of determination
    - 'slope_se': standard error of slope
    - 'intercept_se': standard error of intercept
    '''
    n = len(x)
    assert n == len(y), 'x and y must have same length'

    x_mean = np.mean(x)
    y_mean = np.mean(y)

    # Calculate coefficients
    num = np.sum((x - x_mean) * (y - y_mean))
    denom = np.sum((x - x_mean) ** 2)

    if denom == 0.0:
        return {
            'slope': 0.0, 'intercept': float(y_mean), 'r_squared': 0.0,
            'slope_se': 0.0, 'intercept_se': 0.0,
        }

    slope = num / denom
    intercept = y_mean - slope * x_mean

    # Predictions and residuals
    y_pred = intercept + slope * x
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)
    ss_tot = np.sum((y - y_mean) ** 2)

    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

    # Residual variance and standard errors
    df = n - 2
    if df > 0:
        s_sq = ss_res / df
        slope_se = np.sqrt(s_sq / denom)
        intercept_se = np.sqrt(s_sq * (1.0 / n + (x_mean ** 2) / denom))
    else:
        slope_se = 0.0
        intercept_se = 0.0

    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_squared),
        'slope_se': float(slope_se),
        'intercept_se': float(intercept_se),
    }


def bootstrap_ci(
    data: np.ndarray,
    statistic_fn: Callable[[np.ndarray], float],
    alpha: float = 0.05,
    n_resamples: int = 1000,
) -> tuple[float, float, np.ndarray]:
    '''
    Estimate confidence intervals using non-parametric bootstrap resampling.
    Returns (lower_ci, upper_ci, resampled_statistics).
    '''
    n = len(data)
    stats = np.zeros(n_resamples)

    for i in range(n_resamples):
        resample = np.random.choice(data, size=n, replace=True)
        stats[i] = statistic_fn(resample)

    # Compute percentiles
    lower_pct = 100.0 * (alpha / 2.0)
    upper_pct = 100.0 * (1.0 - alpha / 2.0)

    lower_ci = np.percentile(stats, lower_pct)
    upper_ci = np.percentile(stats, upper_pct)

    return float(lower_ci), float(upper_ci), stats
