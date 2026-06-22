'''
AEGIS-MIOS — Numerical Analysis
================================
Numerical computation algorithms:
- Polynomial Interpolation (Lagrange & Newton Divided Differences)
- Numerical Integration (Trapezoidal, Simpson's 1/3, 2-point Gaussian Quadrature)
- ODE Solvers (Euler method & Runge-Kutta 4th Order / RK4)
'''

from __future__ import annotations

from typing import Callable
import numpy as np


# ============================================================
# §1. POLYNOMIAL INTERPOLATION
# ============================================================

def lagrange_interpolation(x_points: np.ndarray, y_points: np.ndarray, x: float) -> float:
    '''
    Compute Lagrange polynomial interpolation at x.
    L(x) = Σ_i y_i * Π_{j≠i} (x - x_j) / (x_i - x_j)
    '''
    n = len(x_points)
    val = 0.0
    for i in range(n):
        term = y_points[i]
        for j in range(n):
            if i != j:
                term *= (x - x_points[j]) / (x_points[i] - x_points[j])
        val += term
    return float(val)


def newton_interpolation(x_points: np.ndarray, y_points: np.ndarray, x: float) -> float:
    '''
    Compute Newton divided difference polynomial interpolation at x.
    P(x) = f[x_0] + f[x_0, x_1](x - x_0) + ...
    '''
    n = len(x_points)
    coef = y_points.copy().astype(float)

    # Compute divided difference table
    for j in range(1, n):
        for i in range(n - 1, j - 1, -1):
            coef[i] = (coef[i] - coef[i - 1]) / (x_points[i] - x_points[i - j])

    # Evaluate polynomial
    val = coef[n - 1]
    for i in range(n - 2, -1, -1):
        val = coef[i] + (x - x_points[i]) * val
    return float(val)


# ============================================================
# §2. NUMERICAL INTEGRATION
# ============================================================

def trapezoidal_rule(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    '''
    Trapezoidal rule for integration:
    ∫ f(x) dx ≈ (h/2) * (f(a) + 2Σ f(x_i) + f(b))
    '''
    h = (b - a) / n
    s = 0.5 * (f(a) + f(b))
    for i in range(1, n):
        s += f(a + i * h)
    return float(s * h)


def simpsons_rule(f: Callable[[float], float], a: float, b: float, n: int) -> float:
    '''
    Simpson's 1/3 rule for integration (requires even n):
    ∫ f(x) dx ≈ (h/3) * (f(a) + 4Σ_{odd} f(x_i) + 2Σ_{even} f(x_i) + f(b))
    '''
    if n % 2 != 0:
        n += 1  # Make interval count even
    h = (b - a) / n
    s = f(a) + f(b)
    for i in range(1, n):
        factor = 4 if i % 2 != 0 else 2
        s += factor * f(a + i * h)
    return float(s * h / 3.0)


def gaussian_quadrature_2point(f: Callable[[float], float], a: float, b: float) -> float:
    '''
    2-point Gaussian Quadrature over [a, b]:
    ∫ f(x) dx ≈ (b-a)/2 * [ f(x_1) + f(x_2) ]
    where x_1, x_2 are mapped from roots ±1/√3.
    '''
    # Nodes in reference interval [-1, 1]
    t1 = -1.0 / np.sqrt(3.0)
    t2 = 1.0 / np.sqrt(3.0)

    # Map to [a, b]
    x1 = 0.5 * (b - a) * t1 + 0.5 * (b + a)
    x2 = 0.5 * (b - a) * t2 + 0.5 * (b + a)

    # Weights are 1.0 each for 2-point rule
    integral = 0.5 * (b - a) * (f(x1) + f(x2))
    return float(integral)


# ============================================================
# §3. ORDINARY DIFFERENTIAL EQUATIONS
# ============================================================

def euler_method(
    f: Callable[[float, float], float],
    y0: float,
    t_span: tuple[float, float],
    h: float,
) -> tuple[np.ndarray, np.ndarray]:
    '''
    Euler's method for solving ODE y' = f(t, y) with y(t0) = y0.
    Returns (t_values, y_values).
    '''
    t0, tf = t_span
    n_steps = int(np.ceil((tf - t0) / h))
    t_vals = np.linspace(t0, t0 + n_steps * h, n_steps + 1)
    y_vals = np.zeros(n_steps + 1)
    y_vals[0] = y0

    for i in range(n_steps):
        t = t_vals[i]
        y = y_vals[i]
        y_vals[i + 1] = y + h * f(t, y)

    return t_vals, y_vals


def rk4_method(
    f: Callable[[float, float], float],
    y0: float,
    t_span: tuple[float, float],
    h: float,
) -> tuple[np.ndarray, np.ndarray]:
    '''
    Runge-Kutta 4th Order method for solving ODE y' = f(t, y) with y(t0) = y0.
    Returns (t_values, y_values).
    '''
    t0, tf = t_span
    n_steps = int(np.ceil((tf - t0) / h))
    t_vals = np.linspace(t0, t0 + n_steps * h, n_steps + 1)
    y_vals = np.zeros(n_steps + 1)
    y_vals[0] = y0

    for i in range(n_steps):
        t = t_vals[i]
        y = y_vals[i]
        k1 = f(t, y)
        k2 = f(t + 0.5 * h, y + 0.5 * h * k1)
        k3 = f(t + 0.5 * h, y + 0.5 * h * k2)
        k4 = f(t + h, y + h * k3)
        y_vals[i + 1] = y + (h / 6.0) * (k1 + 2.0 * k2 + 2.0 * k3 + k4)

    return t_vals, y_vals
