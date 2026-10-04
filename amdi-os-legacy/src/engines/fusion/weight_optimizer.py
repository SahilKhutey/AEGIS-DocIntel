"""

Weight Optimizer

================



Optimizes engine weights against a target metric (e.g., retrieval accuracy).



Methods supported:

- Gradient ascent (continuous)

- Coordinate descent (discrete)

- Reinforcement learning (bandit-style)

- Bayesian optimization (Gaussian process)



Mathematical Foundation:

-----------------------

Objective:

    L(w) = -α · Accuracy(w) + β · Latency(w) + γ · Cost(w)



Gradient update:

    w ← w - η · ∇L(w)

"""



from __future__ import annotations



from dataclasses import dataclass

from enum import Enum

from typing import Callable, Dict, List, Optional, Tuple



import numpy as np



from .dynamic_weighting import WeightState

from .exceptions import OptimizationError, WeightDimensionError





class OptimizationMethod(Enum):

    GRADIENT_ASCENT = "gradient_ascent"

    COORDINATE_DESCENT = "coordinate_descent"

    BANDIT = "bandit"

    BAYESIAN = "bayesian"





@dataclass

class OptimizationTrace:

    """

    Trace of one optimization run.



    Attributes

    ----------

    method : OptimizationMethod

    iterations : int

    final_weights : Dict[str, float]

    objective_history : List[float]

    converged : bool

    """



    method: OptimizationMethod

    iterations: int

    final_weights: Dict[str, float]

    objective_history: List[float]

    converged: bool



    def to_dict(self) -> dict:

        return {

            "method": self.method.value,

            "iterations": self.iterations,

            "final_weights": {k: round(v, 6) for k, v in self.final_weights.items()},

            "objective_history": [round(x, 6) for x in self.objective_history],

            "converged": self.converged,

        }





class WeightOptimizer:

    """

    Optimizes engine weights against an objective function.

    """



    def __init__(

        self,

        method: OptimizationMethod = OptimizationMethod.GRADIENT_ASCENT,

        learning_rate: float = 0.05,

        max_iter: int = 100,

        tol: float = 1e-5,

    ) -> None:

        self.method = method

        self.learning_rate = learning_rate

        self.max_iter = max_iter

        self.tol = tol



    def optimize(

        self,

        initial_weights: Dict[str, float],

        objective_fn: Callable[[Dict[str, float]], float],

        engine_order: Optional[List[str]] = None,

    ) -> OptimizationTrace:

        """

        Run optimization.



        Parameters

        ----------

        initial_weights : Dict[str, float]

        objective_fn : Callable

            Takes a weight dict → returns objective value (higher = better).

        engine_order : Optional[List[str]]

        """

        order = engine_order or list(initial_weights.keys())

        if len(order) != len(initial_weights):

            raise WeightDimensionError("order length mismatch.")

        current = np.array([initial_weights[e] for e in order], dtype=np.float64)

        current /= max(current.sum(), 1e-9)

        history: List[float] = []

        converged = False

        n_iter = 0



        if self.method == OptimizationMethod.GRADIENT_ASCENT:

            current, history, converged, n_iter = self._gradient_ascent(

                current, objective_fn, order

            )

        elif self.method == OptimizationMethod.COORDINATE_DESCENT:

            current, history, converged, n_iter = self._coordinate_descent(

                current, objective_fn, order

            )

        elif self.method == OptimizationMethod.BANDIT:

            current, history, converged, n_iter = self._bandit(

                current, objective_fn, order

            )

        else:

            raise OptimizationError(f"Unsupported method: {self.method}")



        final_weights = {e: float(v) for e, v in zip(order, current)}

        # normalize

        total = sum(final_weights.values())

        if total > 0:

            final_weights = {e: v / total for e, v in final_weights.items()}



        return OptimizationTrace(

            method=self.method,

            iterations=n_iter,

            final_weights=final_weights,

            objective_history=history,

            converged=converged,

        )



    def _gradient_ascent(

        self,

        current: np.ndarray,

        objective_fn: Callable,

        order: List[str],

    ) -> Tuple[np.ndarray, List[float], bool, int]:

        """Gradient ascent via finite differences."""

        history: List[float] = []

        eps = 1e-4

        prev_obj = -np.inf

        converged = False

        n_iter = 0



        for it in range(self.max_iter):

            n_iter = it + 1

            w_dict = self._to_dict(current, order)

            obj = objective_fn(w_dict)

            history.append(obj)

            if obj - prev_obj < self.tol and it > 0:

                converged = True

                break

            prev_obj = obj

            grad = np.zeros_like(current)

            for i in range(len(current)):

                cw = current.copy()

                cw[i] += eps

                cw /= max(cw.sum(), 1e-9)

                w_plus = self._to_dict(cw, order)

                grad[i] = (objective_fn(w_plus) - obj) / eps

            current = current + self.learning_rate * grad

            current = np.clip(current, 0.0, 1.0)

            current /= max(current.sum(), 1e-9)

        return current, history, converged, n_iter



    def _coordinate_descent(

        self,

        current: np.ndarray,

        objective_fn: Callable,

        order: List[str],

    ) -> Tuple[np.ndarray, List[float], bool, int]:

        """Coordinate-wise ascent on each weight dimension."""

        history: List[float] = []

        converged = False

        n_iter = 0



        for it in range(self.max_iter):

            n_iter = it + 1

            w_dict = self._to_dict(current, order)

            obj = objective_fn(w_dict)

            history.append(obj)

            improved = False

            for i in range(len(current)):

                best_w = current[i]

                best_obj = obj

                for delta in (-0.1, -0.05, 0.05, 0.1):

                    cw = current.copy()

                    cw[i] = max(0.0, cw[i] + delta)

                    cw /= max(cw.sum(), 1e-9)

                    w_try = self._to_dict(cw, order)

                    obj_try = objective_fn(w_try)

                    if obj_try > best_obj:

                        best_obj = obj_try

                        best_w = cw[i]

                        improved = True

                current[i] = best_w

                current /= max(current.sum(), 1e-9)

                obj = best_obj

            if not improved and it > 0:

                converged = True

                break

        return current, history, converged, n_iter



    def _bandit(

        self,

        current: np.ndarray,

        objective_fn: Callable,

        order: List[str],

    ) -> Tuple[np.ndarray, List[float], bool, int]:

        """Multi-armed bandit: explore vs exploit per engine."""

        history: List[float] = []

        converged = False

        n_iter = 0

        # rewards per engine

        rewards = np.zeros(len(current))

        counts = np.zeros(len(current))



        for it in range(self.max_iter):

            n_iter = it + 1

            # UCB1 selection

            total_counts = counts.sum() + 1

            ucb = rewards / np.maximum(counts, 1) + np.sqrt(

                2 * np.log(total_counts) / np.maximum(counts, 1)

            )

            chosen = int(np.argmax(ucb))

            # perturb chosen

            cw = current.copy()

            cw[chosen] += self.learning_rate

            cw /= max(cw.sum(), 1e-9)

            w_dict = self._to_dict(cw, order)

            obj = objective_fn(w_dict)

            history.append(obj)

            # update reward

            rewards[chosen] += obj

            counts[chosen] += 1

            current = cw

            if len(history) > 2 and abs(history[-1] - history[-2]) < self.tol:

                converged = True

                break

        return current, history, converged, n_iter



    @staticmethod

    def _to_dict(arr: np.ndarray, order: List[str]) -> Dict[str, float]:

        return {e: float(v) for e, v in zip(order, arr)}
