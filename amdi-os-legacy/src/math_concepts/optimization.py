'''
AEGIS-MIOS — Mathematical Optimization
========================================
Optimization engine implementing:
- Pareto front extraction (Multi-objective optimization)
- Lagrangian constrained optimization (Solving KKT systems)
- Dynamic Programming (Knapsack problem solver)
'''

from __future__ import annotations

import numpy as np


def pareto_front(objectives: np.ndarray, maximize: bool = True) -> np.ndarray:
    '''
    Extract Pareto optimal front from a set of alternatives.
    objectives: array of shape (n_alternatives, n_objectives)
    maximize: True if maximizing all objectives, False if minimizing all objectives
    Returns boolean array indicating if each alternative is on the Pareto front.
    '''
    n = objectives.shape[0]
    is_pareto = np.ones(n, dtype=bool)
    for i in range(n):
        for j in range(n):
            if i == j:
                continue
            if maximize:
                # alternative j dominates alternative i if:
                # j is at least as good as i in all objectives AND strictly better in at least one
                if np.all(objectives[j] >= objectives[i]) and np.any(objectives[j] > objectives[i]):
                    is_pareto[i] = False
                    break
            else:
                if np.all(objectives[j] <= objectives[i]) and np.any(objectives[j] < objectives[i]):
                    is_pareto[i] = False
                    break
    return is_pareto


def solve_lagrangian_equality(
    Q: np.ndarray,
    c: np.ndarray,
    A: np.ndarray,
    b: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    '''
    Solve a constrained quadratic optimization problem:
    Minimize (1/2) x.T Q x + c.T x subject to A x = b.

    Formulates the KKT system:
    [ Q   A.T ] [ x ]   [ -c ]
    [ A    0  ] [ λ ] = [  b ]
    '''
    n_vars = Q.shape[0]
    n_constraints = A.shape[0]

    # Build KKT matrix
    kkt_matrix = np.zeros((n_vars + n_constraints, n_vars + n_constraints))
    kkt_matrix[:n_vars, :n_vars] = Q
    kkt_matrix[:n_vars, n_vars:] = A.T
    kkt_matrix[n_vars:, :n_vars] = A

    # Build RHS vector
    rhs = np.zeros(n_vars + n_constraints)
    rhs[:n_vars] = -c
    rhs[n_vars:] = b

    try:
        sol = np.linalg.solve(kkt_matrix, rhs)
        x = sol[:n_vars]
        lambda_val = sol[n_vars:]
        return x, lambda_val
    except np.linalg.LinAlgError:
        # Fallback using pseudo-inverse
        sol = np.linalg.pinv(kkt_matrix) @ rhs
        x = sol[:n_vars]
        lambda_val = sol[n_vars:]
        return x, lambda_val


def solve_dp_knapsack(
    values: list[float],
    weights: list[int],
    capacity: int,
) -> dict:
    '''
    Solve the classic 0-1 Knapsack problem using Dynamic Programming.
    Returns:
    - 'selected_indices': indices of items selected
    - 'total_value': optimal value
    - 'total_weight': weight of the optimal selection
    '''
    n = len(values)
    dp = np.zeros((n + 1, capacity + 1))

    for i in range(1, n + 1):
        w = weights[i - 1]
        v = values[i - 1]
        for c in range(capacity + 1):
            if w <= c:
                dp[i, c] = max(dp[i - 1, c], dp[i - 1, c - w] + v)
            else:
                dp[i, c] = dp[i - 1, c]

    # Traceback to find selected items
    selected_indices = []
    c = capacity
    for i in range(n, 0, -1):
        if dp[i, c] != dp[i - 1, c]:
            selected_indices.append(i - 1)
            c -= weights[i - 1]

    selected_indices.reverse()
    total_val = dp[n, capacity]
    total_wt = sum(weights[idx] for idx in selected_indices)

    return {
        'selected_indices': selected_indices,
        'total_value': float(total_val),
        'total_weight': int(total_wt),
    }
