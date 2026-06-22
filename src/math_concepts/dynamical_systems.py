'''
AEGIS-MIOS — Dynamical Systems
================================
Chaos and nonlinear dynamics formulations:
- Lyapunov Exponent Estimation (Logistic map)
- 2D Phase Portrait Vector Field Generation
- Bifurcation Diagram Data Sweep
'''

from __future__ import annotations

from typing import Callable
import numpy as np


def lyapunov_exponent_logistic(
    r: float,
    x0: float = 0.5,
    n_steps: int = 1000,
    discard_steps: int = 100,
) -> float:
    '''
    Compute the Lyapunov exponent of the logistic map x_{n+1} = r * x_n * (1 - x_n).
    Derivative f'(x) = r * (1 - 2*x)
    λ = (1/N) Σ log|f'(x_i)|
    '''
    x = x0
    # Discard transient steps
    for _ in range(discard_steps):
        x = r * x * (1.0 - x)

    # Accumulate log derivatives
    log_sum = 0.0
    for _ in range(n_steps):
        x = r * x * (1.0 - x)
        deriv = abs(r * (1.0 - 2.0 * x))
        if deriv > 0.0:
            log_sum += np.log(deriv)
        else:
            log_sum += np.log(1e-15)

    return float(log_sum / n_steps)


def phase_portrait_2d(
    f: Callable[[np.ndarray, float], np.ndarray],
    x_range: tuple[float, float],
    y_range: tuple[float, float],
    grid_size: int = 20,
) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    '''
    Generate a 2D phase portrait grid of velocity vectors.
    f: function mapping state vector [x, y] to derivatives [dx/dt, dy/dt].
    Returns meshgrid arrays X, Y and derivatives U, V.
    '''
    x_vals = np.linspace(x_range[0], x_range[1], grid_size)
    y_vals = np.linspace(y_range[0], y_range[1], grid_size)
    X, Y = np.meshgrid(x_vals, y_vals)

    U = np.zeros_like(X)
    V = np.zeros_like(Y)

    for i in range(grid_size):
        for j in range(grid_size):
            state = np.array([X[i, j], Y[i, j]])
            derivs = f(state, 0.0)  # Assume autonomous system (t=0)
            U[i, j] = derivs[0]
            V[i, j] = derivs[1]

    return X, Y, U, V


def bifurcation_diagram_logistic(
    r_range: np.ndarray,
    x0: float = 0.5,
    n_steps: int = 500,
    last_steps: int = 100,
) -> list[tuple[float, float]]:
    '''
    Generate bifurcation diagram trajectory sweep data for the logistic map.
    Returns a list of tuples (r, x) containing the final 'last_steps' iterations.
    '''
    points = []
    for r in r_range:
        x = x0
        # Discard transient steps
        for _ in range(n_steps - last_steps):
            x = r * x * (1.0 - x)
        # Store steady-state points
        for _ in range(last_steps):
            x = r * x * (1.0 - x)
            points.append((float(r), float(x)))
    return points
