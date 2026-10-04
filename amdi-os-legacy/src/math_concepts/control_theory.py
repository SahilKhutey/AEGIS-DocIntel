'''
AEGIS-MIOS — Control Theory
============================
Control system design algorithms:
- Proportional-Integral-Derivative (PID) Controller with anti-windup
- Discrete State-Space System Simulation
- System Stability Analysis (eigenvalues and Routh-Hurwitz criterion)
'''

from __future__ import annotations

import numpy as np


class PIDController:
    '''Proportional-Integral-Derivative (PID) controller with anti-windup.'''

    def __init__(
        self,
        kp: float,
        ki: float,
        kd: float,
        setpoint: float = 0.0,
        windup_limit: float | None = None,
    ):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.windup_limit = windup_limit

        self._integral = 0.0
        self._prev_error = 0.0

    def update(self, measurement: float, dt: float) -> float:
        '''Compute PID control output signal given current measurement and time step.'''
        if dt <= 0.0:
            dt = 1e-6

        error = self.setpoint - measurement

        # Proportional term
        p_term = self.kp * error

        # Integral term with anti-windup limit
        self._integral += error * dt
        if self.windup_limit is not None:
            self._integral = max(-self.windup_limit, min(self.windup_limit, self._integral))
        i_term = self.ki * self._integral

        # Derivative term
        d_term = self.kd * (error - self._prev_error) / dt

        self._prev_error = error

        return p_term + i_term + d_term

    def reset(self) -> None:
        '''Reset PID controller state.'''
        self._integral = 0.0
        self._prev_error = 0.0


class StateSpaceSystem:
    '''
    Discrete State-Space System representation:
    x_{k+1} = A * x_k + B * u_k
    y_k     = C * x_k + D * u_k
    '''

    def __init__(self, A: np.ndarray, B: np.ndarray, C: np.ndarray, D: np.ndarray | None = None):
        self.A = A
        self.B = B
        self.C = C
        self.D = D if D is not None else np.zeros((C.shape[0], B.shape[1]))

    def step(self, x_current: np.ndarray, u_current: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        '''Compute one step state transition and output.'''
        x_next = self.A @ x_current + self.B @ u_current
        y_current = self.C @ x_current + self.D @ u_current
        return x_next, y_current

    def simulate(self, u_sequence: np.ndarray, x0: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        '''Simulate system response over a sequence of inputs.'''
        n_steps = len(u_sequence)
        x_dim = self.A.shape[0]
        y_dim = self.C.shape[0]

        x_history = np.zeros((n_steps + 1, x_dim))
        y_history = np.zeros((n_steps, y_dim))

        x_history[0] = x0
        x_curr = x0.copy()

        for k in range(n_steps):
            x_next, y = self.step(x_curr, u_sequence[k])
            x_history[k + 1] = x_next
            y_history[k] = y
            x_curr = x_next

        return x_history, y_history


def analyze_stability(A: np.ndarray) -> dict:
    '''
    Analyze stability of the linear system defined by matrix A.
    Returns eigenvalues, spectral radius, and stability labels for continuous/discrete systems.
    '''
    eigvals = np.linalg.eigvals(A)
    spectral_radius = float(np.max(np.abs(eigvals)))

    # Continuous time: stable if all Re(lambda) < 0
    is_continuous_stable = bool(np.all(np.real(eigvals) < 0.0))

    # Discrete time: stable if all |lambda| < 1 (spectral radius < 1)
    is_discrete_stable = bool(spectral_radius < 1.0)

    return {
        'eigenvalues': eigvals,
        'spectral_radius': spectral_radius,
        'is_continuous_stable': is_continuous_stable,
        'is_discrete_stable': is_discrete_stable,
    }


def routh_hurwitz_criterion(coefficients: list[float]) -> tuple[bool, np.ndarray]:
    '''
    Assess stability of a polynomial using the Routh-Hurwitz stability criterion.
    coefficients: polynomial coefficients starting from highest degree s^n, s^{n-1}, ..., s^0.
    Returns: (is_stable, routh_table)
    '''
    n = len(coefficients) - 1
    if n <= 0:
        return True, np.zeros((0, 0))

    # Determine row count and column count of the Routh table
    col_count = int(np.ceil((n + 1) / 2.0))
    table = np.zeros((n + 1, col_count))

    # Fill first two rows
    row0 = coefficients[0::2]
    row1 = coefficients[1::2]

    table[0, :len(row0)] = row0
    table[1, :len(row1)] = row1

    # Populate Routh array
    for i in range(2, n + 1):
        for j in range(col_count - 1):
            denom = table[i - 1, 0]
            if denom == 0:
                # Replace with epsilon proxy
                denom = 1e-9
            num = table[i - 1, 0] * table[i - 2, j + 1] - table[i - 2, 0] * table[i - 1, j + 1]
            table[i, j] = num / denom

    # Stability is determined by signs of elements in the first column
    first_col = table[:, 0]
    is_stable = bool(np.all(first_col > 0.0) or np.all(first_col < 0.0))

    return is_stable, table
