"""

Dynamic Weighting

=================



Mathematical Foundation:

-----------------------

Engine weights are dynamically adjusted based on:

1. Historical performance (per-engine accuracy)

2. Document type (different weights for invoices vs research papers)

3. Query type (semantic-heavy vs structural-heavy queries)

4. Real-time feedback signals



Adaptive update rule:

    w_i(t+1) = w_i(t) + η · ∇_w L(w, feedback)



Constraints:

    Σ w_i = 1       (weights sum to 1)

    w_i ≥ 0         (non-negative)

    w_i ≤ w_max     (max weight per engine)



Soft constraint via softmax:

    w_i = exp(z_i / T) / Σ exp(z_j / T)

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Dict, List, Optional, Tuple



import numpy as np



from .exceptions import WeightDimensionError





@dataclass

class WeightState:

    """

    State of dynamic weights across engines.



    Attributes

    ----------

    weights : Dict[str, float]

        Engine name → weight in [0, 1].

    temperature : float

        Softmax temperature.

    iteration : int

        Update iteration counter.

    history : List[Dict[str, float]]

        History of weight updates.

    performance : Dict[str, float]

        Per-engine performance scores (e.g., accuracy).

    """



    weights: Dict[str, float]

    temperature: float = 1.0

    iteration: int = 0

    history: List[Dict[str, float]] = field(default_factory=list)

    performance: Dict[str, float] = field(default_factory=dict)



    def normalized_weights(self) -> Dict[str, float]:

        """Return weights re-normalized to sum to 1."""

        total = sum(self.weights.values())

        if total <= 0:

            n = len(self.weights)

            return {k: 1.0 / max(n, 1) for k in self.weights}

        return {k: v / total for k, v in self.weights.items()}



    def to_array(self, engine_order: List[str]) -> np.ndarray:

        """Convert to numpy array in given engine order."""

        return np.array([self.weights.get(e, 0.0) for e in engine_order])



    def from_array(self, engine_order: List[str], arr: np.ndarray) -> None:

        """Update from numpy array."""

        if len(arr) != len(engine_order):

            raise WeightDimensionError(

                f"Array length {len(arr)} ≠ engine count {len(engine_order)}."

            )

        for e, v in zip(engine_order, arr):

            self.weights[e] = float(v)





class DynamicWeightLearner:

    """

    Learns dynamic engine weights based on feedback.



    Supports:

    - Softmax-based soft weighting

    - Hard upper-bound per engine

    - Performance-based updates

    - Document-type / query-type conditioning

    """



    DEFAULT_ENGINES = [

        "geometry",

        "frequency",

        "recurrence",

        "matrix",

        "template",

        "semantic",

        "graph",

        "topology",

        "spectral",

        "tensor",

        "info_physics",

        "retrieval",

    ]



    def __init__(

        self,

        initial_weights: Optional[Dict[str, float]] = None,

        temperature: float = 1.0,

        learning_rate: float = 0.05,

        max_weight: float = 0.5,

        min_weight: float = 0.0,

    ) -> None:

        self.learning_rate = learning_rate

        self.max_weight = max_weight

        self.min_weight = min_weight



        if initial_weights is None:

            n = len(self.DEFAULT_ENGINES)

            initial_weights = {e: 1.0 / n for e in self.DEFAULT_ENGINES}



        self.state = WeightState(

            weights=initial_weights,

            temperature=temperature,

        )



    def softmax_update(

        self,

        logits: np.ndarray,

        engine_order: Optional[List[str]] = None,

    ) -> Dict[str, float]:

        """

        Update weights via softmax of logits.



        Parameters

        ----------

        logits : np.ndarray

            Raw log-weight values (length = num engines).

        engine_order : Optional[List[str]]

            Engine names. If None, use defaults.

        """

        order = engine_order or self.DEFAULT_ENGINES

        if len(logits) != len(order):

            raise WeightDimensionError(

                f"logits length {len(logits)} ≠ engine count {len(order)}."

            )

        # softmax with temperature

        scaled = logits / max(self.state.temperature, 1e-6)

        scaled = scaled - scaled.max()  # numerical stability

        exp_s = np.exp(scaled)

        probs = exp_s / exp_s.sum()

        new_weights = {e: float(p) for e, p in zip(order, probs)}

        self._apply_constraints(new_weights)

        self._commit(new_weights)

        return self.state.normalized_weights()



    def performance_update(

        self,

        performance: Dict[str, float],

        engine_order: Optional[List[str]] = None,

    ) -> Dict[str, float]:

        """

        Update weights based on per-engine performance (e.g., accuracy in [0, 1]).



        Higher performance → higher weight.

        """

        order = engine_order or self.DEFAULT_ENGINES

        perf = np.array([performance.get(e, 0.5) for e in order])

        # softmax weighting

        logits = np.log(perf + 1e-6)

        return self.softmax_update(logits, engine_order=order)



    def gradient_update(

        self,

        gradients: np.ndarray,

        engine_order: Optional[List[str]] = None,

    ) -> Dict[str, float]:

        """

        Update weights via gradient ascent on objective.



        w_i ← w_i + η · ∂L/∂w_i

        """

        order = engine_order or self.DEFAULT_ENGINES

        if len(gradients) != len(order):

            raise WeightDimensionError("gradient length mismatch.")

        current = self.state.to_array(order)

        new = current + self.learning_rate * gradients

        new = np.clip(new, self.min_weight, self.max_weight)

        new_weights = {e: float(v) for e, v in zip(order, new)}

        self._apply_constraints(new_weights)

        self._commit(new_weights)

        return self.state.normalized_weights()



    def reset(self, engine_order: Optional[List[str]] = None) -> None:

        """Reset weights to uniform."""

        order = engine_order or self.DEFAULT_ENGINES

        n = len(order)

        self.state.weights = {e: 1.0 / n for e in order}

        self.state.iteration = 0

        self.state.history = []



    def _apply_constraints(self, weights: Dict[str, float]) -> None:

        """Clip weights to [min_weight, max_weight] and renormalize."""

        for k in weights:

            weights[k] = float(np.clip(weights[k], self.min_weight, self.max_weight))

        total = sum(weights.values())

        if total > 0:

            for k in weights:

                weights[k] /= total

        else:

            n = len(weights)

            for k in weights:

                weights[k] = 1.0 / max(n, 1)



    def _commit(self, weights: Dict[str, float]) -> None:

        """Commit weights and update history."""

        self.state.weights = weights

        self.state.iteration += 1

        self.state.history.append(dict(weights))
