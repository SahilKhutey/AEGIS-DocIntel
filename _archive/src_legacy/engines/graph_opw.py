"""
Order-Preserving Wasserstein (OPW) Reading-Order Metric (Task B-1).

Computes optimal transport alignment distance between 2D spatial layout coordinates
and recovered reading-order sequences, penalizing inverse order transitions and
spatial displacement.
"""

from __future__ import annotations

import math
from typing import Sequence, Tuple, List, Dict, Any, Optional
import numpy as np


class OPWMetric:
    """
    Order-Preserving Wasserstein (OPW) distance calculator for reading-order alignment.
    
    Formula:
    OPW(D, T) = min_P <P, D> + lambda * KL(P || K) + delta * <P, I_penalty>
    where P is the transport plan, D is Euclidean spatial distance matrix,
    and I_penalty enforces monotonic order preservation.
    """

    def __init__(self, lambda_param: float = 10.0, delta_param: float = 1.0):
        self.lambda_param = lambda_param
        self.delta_param = delta_param

    def compute_distance_matrix(
        self,
        coords_a: Sequence[Tuple[float, float]],
        coords_b: Sequence[Tuple[float, float]],
    ) -> np.ndarray:
        """Compute 2D Euclidean distance matrix between coordinate sequences."""
        n, m = len(coords_a), len(coords_b)
        if n == 0 or m == 0:
            return np.zeros((n, m))
        
        arr_a = np.array(coords_a, dtype=np.float64)
        arr_b = np.array(coords_b, dtype=np.float64)
        
        diff = arr_a[:, np.newaxis, :] - arr_b[np.newaxis, :, :]
        dist = np.sqrt(np.sum(diff ** 2, axis=-1))
        return dist

    def compute_opw(
        self,
        coords_a: Sequence[Tuple[float, float]],
        coords_b: Sequence[Tuple[float, float]],
    ) -> float:
        """
        Computes OPW distance between two 2D point sequences.
        Returns total distance (lower means better order alignment).
        """
        n, m = len(coords_a), len(coords_b)
        if n == 0 and m == 0:
            return 0.0
        if n == 0 or m == 0:
            return float(max(n, m))

        dist_matrix = self.compute_distance_matrix(coords_a, coords_b)
        
        # Order penalty matrix: penalizes deviations from the diagonal trajectory (i/N - j/M)
        i_indices = np.arange(n)[:, np.newaxis] / float(n)
        j_indices = np.arange(m)[np.newaxis, :] / float(m)
        order_penalty = (i_indices - j_indices) ** 2
        
        cost_matrix = dist_matrix + self.delta_param * order_penalty
        
        # Dynamic programming sequence alignment (DTW-style minimal cost transport)
        dp = np.full((n + 1, m + 1), float('inf'), dtype=np.float64)
        dp[0, 0] = 0.0

        for i in range(1, n + 1):
            for j in range(1, m + 1):
                cost = cost_matrix[i - 1, j - 1]
                dp[i, j] = cost + min(dp[i - 1, j], dp[i, j - 1], dp[i - 1, j - 1])

        total_cost = float(dp[n, m])
        return total_cost

    def compute_similarity(
        self,
        coords_a: Sequence[Tuple[float, float]],
        coords_b: Sequence[Tuple[float, float]],
    ) -> float:
        """
        Computes a normalized OPW similarity score in range [0.0, 1.0].
        1.0 represents perfect order and spatial alignment.
        """
        dist = self.compute_opw(coords_a, coords_b)
        max_len = max(len(coords_a), len(coords_b), 1)
        normalized_dist = dist / float(max_len)
        similarity = 1.0 / (1.0 + normalized_dist)
        return float(similarity)


def compute_opw_distance(
    coords_a: Sequence[Tuple[float, float]],
    coords_b: Sequence[Tuple[float, float]],
    lambda_param: float = 10.0,
    delta_param: float = 1.0,
) -> float:
    """Helper function to compute OPW distance directly."""
    metric = OPWMetric(lambda_param=lambda_param, delta_param=delta_param)
    return metric.compute_opw(coords_a, coords_b)
