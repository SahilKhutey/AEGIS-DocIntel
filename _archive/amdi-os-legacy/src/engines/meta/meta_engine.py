'''
AEGIS-MIOS — Meta Learning Engine
===================================
Optimizes routing weights dynamically based on historical feedback and success rate.
'''
from __future__ import annotations

import logging
import numpy as np

logger = logging.getLogger('amdi.engines.meta')


class MetaLearningEngine:
    '''
    Meta Learning Engine.
    Adjusts Adaptive Fusion Weights dynamically by analyzing past query success.
    '''

    def __init__(self, learning_rate: float = 0.05):
        self.learning_rate = learning_rate
        # Historical performance logs: category -> {weights_dict, success_rate}
        self.history: dict[str, list[dict]] = {}

    def log_attempt(self, category: str, weights: dict[str, float], success: bool, rating: float) -> None:
        '''Logs a retrieval attempt and its quality rating [0.0, 1.0].'''
        if category not in self.history:
            self.history[category] = []
        self.history[category].append({
            'weights': weights.copy(),
            'success': success,
            'rating': rating
        })

    def adapt_weights(self, category: str, current_weights: dict[str, float]) -> dict[str, float]:
        '''
        Optimizes weights for a query category based on historical gradient.
        If past attempts with higher weight on engine X resulted in higher success/rating,
        nudge weight on X up slightly and normalize.
        '''
        attempts = self.history.get(category, [])
        if len(attempts) < 3:
            return current_weights.copy()
            
        new_weights = current_weights.copy()
        
        # Calculate correlation of each weight dimension with rating
        for key in current_weights.keys():
            weights_val = [a['weights'].get(key, 0.0) for a in attempts]
            ratings = [a['rating'] for a in attempts]
            
            # Simple covariance
            cov = np.cov(weights_val, ratings)[0, 1] if len(attempts) > 1 else 0.0
            if not np.isnan(cov):
                # Nudge weight in direction of positive covariance
                new_weights[key] += self.learning_rate * cov
                new_weights[key] = max(0.01, new_weights[key])

        # Renormalize to sum = 1.0
        w_sum = sum(new_weights.values())
        if w_sum > 0.0:
            for k in new_weights.keys():
                new_weights[k] /= w_sum
                
        return new_weights
