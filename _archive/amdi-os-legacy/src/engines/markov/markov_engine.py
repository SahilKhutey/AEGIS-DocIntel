'''
AEGIS-MIOS — Markov Engine
============================
Models section transitions as first-order Markov chains.
'''
from __future__ import annotations

import logging
from dataclasses import dataclass
import numpy as np

logger = logging.getLogger('amdi.engines.markov')


@dataclass
class MarkovSignature:
    '''Signature of a Markov transition chain.'''
    states: list[str]
    transition_matrix: np.ndarray
    stationary_distribution: np.ndarray


class MarkovEngine:
    '''
    Markov Engine.
    Builds transition matrix P_{ij} for state transitions and finds steady states.
    '''

    def __init__(self, smoothing: float = 0.05):
        self.smoothing = smoothing

    def build_transition_chain(self, sequences: list[list[str]], states: list[str] | None = None) -> MarkovSignature:
        '''Builds the transition probability matrix and stationary distribution from sequences.'''
        if not states:
            all_states = set()
            for seq in sequences:
                all_states.update(seq)
            states = sorted(list(all_states))
            
        n = len(states)
        state_idx = {s: idx for idx, s in enumerate(states)}
        
        # Initialize with Laplace smoothing
        counts = np.full((n, n), self.smoothing, dtype=np.float64)
        
        for seq in sequences:
            for i in range(len(seq) - 1):
                s0 = seq[i]
                s1 = seq[i + 1]
                if s0 in state_idx and s1 in state_idx:
                    counts[state_idx[s0], state_idx[s1]] += 1.0
                    
        # Row-normalize to transition probability matrix P_ij
        row_sums = counts.sum(axis=1, keepdims=True)
        P = counts / np.maximum(row_sums, 1e-9)
        
        # Find stationary distribution via power iteration (since transition is row-stochastic)
        pi = np.ones(n, dtype=np.float64) / n
        for _ in range(50):
            next_pi = np.dot(pi, P)
            if np.linalg.norm(next_pi - pi) < 1e-8:
                pi = next_pi
                break
            pi = next_pi
            
        # Normalize
        pi /= pi.sum()
        
        return MarkovSignature(
            states=states,
            transition_matrix=P,
            stationary_distribution=pi
        )

    def transition_probability(self, matrix: np.ndarray, states: list[str], current: str, next_state: str) -> float:
        '''Gets transition probability between two states.'''
        if current not in states or next_state not in states:
            return 0.0
        return float(matrix[states.index(current), states.index(next_state)])
