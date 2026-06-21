'''
AEGIS-MIOS — Decision Theory Engine
=====================================
Evaluates retrieval candidates using Multi-Criteria Decision Analysis (MCDA).
'''
from __future__ import annotations

import logging
import numpy as np

logger = logging.getLogger('amdi.engines.decision')


class DecisionEngine:
    '''
    Decision Theory Engine.
    Combines diverse scoring vectors using Multi-Criteria Decision Analysis (MCDA) and AHP weights.
    '''

    def __init__(self, criterion_names: list[str] | None = None):
        self.criterion_names = criterion_names or ['s', 'g', 'r', 'f', 'm', 't', 'x']

    def pairwise_comparison_matrix(self, preferences: dict[tuple[str, str], float]) -> np.ndarray:
        '''
        Builds a pairwise comparison matrix for AHP based on criterion preferences.
        preferences: {(c1, c2): relative_importance_c1_vs_c2}
        '''
        n = len(self.criterion_names)
        matrix = np.ones((n, n), dtype=np.float64)
        
        for i, c_i in enumerate(self.criterion_names):
            for j, c_j in enumerate(self.criterion_names):
                if i == j:
                    continue
                if (c_i, c_j) in preferences:
                    matrix[i, j] = preferences[(c_i, c_j)]
                    matrix[j, i] = 1.0 / preferences[(c_i, c_j)]
                elif (c_j, c_i) in preferences:
                    matrix[j, i] = preferences[(c_j, c_i)]
                    matrix[i, j] = 1.0 / preferences[(c_j, c_i)]
        return matrix

    def ahp_weights(self, comparison_matrix: np.ndarray) -> np.ndarray:
        '''
        Extracts priority weights from the pairwise comparison matrix.
        Returns normalized principal eigenvector.
        '''
        # Geometric mean approximation method for speed and robustness
        row_geom_mean = np.exp(np.log(comparison_matrix).mean(axis=1))
        weights = row_geom_mean / row_geom_mean.sum()
        return weights

    def compute_decision_score(self, scores: dict[str, float], weights: dict[str, float]) -> float:
        '''
        Computes weighted sum model: D = sum w_i * X_i
        '''
        total = 0.0
        weight_sum = 0.0
        for name, score in scores.items():
            w = weights.get(name, 0.0)
            total += w * score
            weight_sum += w
            
        if weight_sum == 0.0:
            return 0.0
        return total / weight_sum

    def compute_consistency_ratio(self, matrix: np.ndarray, weights: np.ndarray) -> float:
        '''Computes consistency ratio (CR) to verify pairwise ranking validity.'''
        n = matrix.shape[0]
        if n <= 2:
            return 0.0
        # Principal eigenvalue approximation lambda_max
        ax = np.dot(matrix, weights)
        lambda_max = np.mean(ax / weights)
        
        ci = (lambda_max - n) / (n - 1)
        # Random Index table up to size 10
        ri_table = [0.0, 0.0, 0.58, 0.90, 1.12, 1.24, 1.32, 1.41, 1.45, 1.49]
        ri = ri_table[n - 1] if n <= 10 else 1.49
        
        if ri == 0.0:
            return 0.0
        return float(ci / ri)
