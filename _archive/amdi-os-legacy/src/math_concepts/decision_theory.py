'''
AEGIS-MIOS — Decision Theory & Game Theory
============================================
Mathematical models for decision-making:
- Expected Utility Theory (Linear, Logarithmic, Exponential)
- Bayesian Decision Theory (Expected Risk minimization)
- Nash Equilibrium for 2x2 normal form games (Pure and Mixed)
'''

from __future__ import annotations

import numpy as np


def expected_utility(
    outcomes: np.ndarray,
    probabilities: np.ndarray,
    utility_type: str = 'linear',
    risk_parameter: float = 1.0,
) -> float:
    '''
    Compute expected utility.
    utility_type: 'linear', 'log', or 'exponential'
    risk_parameter: parameter 'a' for exponential utility (u(x) = 1 - e^{-ax})
    '''
    probs = probabilities / np.sum(probabilities)

    if utility_type == 'linear':
        u = outcomes
    elif utility_type == 'log':
        # Shift outcomes to ensure positive values
        min_out = np.min(outcomes)
        shift = abs(min_out) + 1.0 if min_out <= 0 else 0.0
        u = np.log(outcomes + shift)
    elif utility_type == 'exponential':
        u = 1.0 - np.exp(-risk_parameter * outcomes)
    else:
        raise ValueError('Unknown utility type')

    return float(np.sum(probs * u))


def bayesian_decision(prior_probabilities: np.ndarray, loss_matrix: np.ndarray) -> int:
    '''
    Select the action that minimizes expected risk.
    prior_probabilities: vector P(theta) of shape (n_states,)
    loss_matrix: array L(action, state) of shape (n_actions, n_states)
    Returns: action index
    '''
    p = prior_probabilities / np.sum(prior_probabilities)
    expected_risks = loss_matrix @ p
    return int(np.argmin(expected_risks))


def nash_equilibrium_2x2(payoff_A: np.ndarray, payoff_B: np.ndarray) -> dict:
    '''
    Compute Pure Strategy and Mixed Strategy Nash Equilibria for 2x2 normal form games.
    payoff_A: 2x2 matrix for Player A (Row player)
    payoff_B: 2x2 matrix for Player B (Column player)
    '''
    # 1. Find Pure Strategy Nash Equilibria (PSNE)
    psne = []
    for r in range(2):
        for c in range(2):
            # Row player utility check: payoff_A[r, c] >= payoff_A[1-r, c]
            # Col player utility check: payoff_B[r, c] >= payoff_B[r, 1-c]
            if payoff_A[r, c] >= payoff_A[1-r, c] and payoff_B[r, c] >= payoff_B[r, 1-c]:
                psne.append((r, c))

    # 2. Find Mixed Strategy Nash Equilibria (MSNE)
    # Row player plays Row 0 with prob p, Row 1 with prob 1-p
    # Col player plays Col 0 with prob q, Col 1 with prob 1-q
    msne = None

    # Column player indifference: p * B[0, 0] + (1-p) * B[1, 0] = p * B[0, 1] + (1-p) * B[1, 1]
    denom_p = payoff_B[0, 0] - payoff_B[1, 0] - payoff_B[0, 1] + payoff_B[1, 1]
    if abs(denom_p) > 1e-12:
        p = (payoff_B[1, 1] - payoff_B[1, 0]) / denom_p
        # Row player indifference: q * A[0, 0] + (1-q) * A[0, 1] = q * A[1, 0] + (1-q) * A[1, 1]
        denom_q = payoff_A[0, 0] - payoff_A[1, 0] - payoff_A[0, 1] + payoff_A[1, 1]
        if abs(denom_q) > 1e-12:
            q = (payoff_A[1, 1] - payoff_A[0, 1]) / denom_q
            if 0.0 <= p <= 1.0 and 0.0 <= q <= 1.0:
                msne = {
                    'p': float(p),
                    'q': float(q),
                    'row_strategy': [float(p), float(1.0 - p)],
                    'col_strategy': [float(q), float(1.0 - q)],
                }

    return {
        'pure_equilibria': psne,
        'mixed_equilibrium': msne,
    }
