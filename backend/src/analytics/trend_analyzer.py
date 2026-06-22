"""
AMDI-OS Advanced Analytics: Trend Analyzer
===========================================

Performs timeseries trend calculations, moving averages (SMA, EMA), 
linear regression metrics (slope, intercept, R-squared), and future forecasts.
"""

from typing import List, Dict, Tuple, Optional, Any
import numpy as np


class TrendAnalyzer:
    """
    Analyzes sequences of timeseries observations to extract trends and forecasts.
    """
    @staticmethod
    def simple_moving_average(data: List[float], window: int) -> List[float]:
        """
        Computes the Simple Moving Average (SMA) of a sequence.
        """
        if window <= 0:
            raise ValueError("Window size must be greater than 0.")
        if not data:
            return []
            
        sma = []
        for i in range(len(data)):
            start_idx = max(0, i - window + 1)
            subset = data[start_idx:i + 1]
            sma.append(sum(subset) / len(subset))
        return sma

    @staticmethod
    def exponential_moving_average(data: List[float], window: int) -> List[float]:
        """
        Computes the Exponential Moving Average (EMA) of a sequence.
        """
        if window <= 0:
            raise ValueError("Window size must be greater than 0.")
        if not data:
            return []
            
        alpha = 2.0 / (window + 1)
        ema = []
        for i, val in enumerate(data):
            if i == 0:
                ema.append(val)
            else:
                ema.append(alpha * val + (1.0 - alpha) * ema[-1])
        return ema

    @staticmethod
    def fit_linear_trend(timestamps: List[float], values: List[float]) -> Dict[str, float]:
        """
        Fits a simple linear regression (y = mx + c) on the given timeseries.
        Returns metrics including: slope (m), intercept (c), r_squared, and direction.
        """
        if len(timestamps) != len(values):
            raise ValueError("Timestamps and values must be of the same length.")
        if len(timestamps) < 2:
            return {
                "slope": 0.0,
                "intercept": values[0] if values else 0.0,
                "r_squared": 0.0,
                "direction": 0.0  # 0: flat, 1: positive, -1: negative
            }

        x = np.array(timestamps)
        y = np.array(values)

        # Shift X to prevent numerical instability with unix timestamps
        x_min = x.min()
        x_shifted = x - x_min

        # Compute regression using numpy
        A = np.vstack([x_shifted, np.ones(len(x_shifted))]).T
        m, c = np.linalg.lstsq(A, y, rcond=None)[0]

        # Calculate R-squared
        y_pred = m * x_shifted + c
        y_mean = np.mean(y)
        ss_res = np.sum((y - y_pred) ** 2)
        ss_tot = np.sum((y - y_mean) ** 2)
        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0.0 else 0.0

        # Adjust intercept to match unshifted timestamps
        # y = m * (t - x_min) + c => y = m * t + (c - m * x_min)
        adjusted_intercept = c - m * x_min

        direction = 1.0 if m > 1e-5 else (-1.0 if m < -1e-5 else 0.0)

        return {
            "slope": float(m),
            "intercept": float(adjusted_intercept),
            "r_squared": float(r_squared),
            "direction": direction
        }

    @staticmethod
    def forecast(timestamps: List[float], values: List[float], future_timestamps: List[float]) -> List[float]:
        """
        Forecasts future values based on a linear regression fit.
        """
        fit = TrendAnalyzer.fit_linear_trend(timestamps, values)
        m = fit["slope"]
        c = fit["intercept"]
        return [float(m * t + c) for t in future_timestamps]
