"""

Score Calculator

================



Computes per-item composite scores using configurable formulas.



Formulas:

- linear:   S = Σ w_i · score_i

- geometric: S = Π score_i^w_i

- harmonic:  S = (Σ w_i / score_i)^(-1)

- max:      S = max(score_i)

- min:      S = min(score_i)

"""



from __future__ import annotations



from dataclasses import dataclass

from enum import Enum

from typing import Dict, List, Optional



import numpy as np



from .exceptions import InvalidSignalError





class ScoreFormula(Enum):

    LINEAR = "linear"

    GEOMETRIC = "geometric"

    HARMONIC = "harmonic"

    MAX = "max"

    MIN = "min"





@dataclass

class ScoreCalculator:

    """

    Computes per-item scores using various fusion formulas.

    """



    formula: ScoreFormula = ScoreFormula.LINEAR



    def compute(

        self,

        engine_scores: Dict[str, np.ndarray],

        weights: Optional[Dict[str, float]] = None,

    ) -> np.ndarray:

        """

        Compute scores.



        Parameters

        ----------

        engine_scores : Dict[str, np.ndarray]

        weights : Optional[Dict[str, float]]

            Required for LINEAR, GEOMETRIC, HARMONIC.

        """

        if not engine_scores:

            raise InvalidSignalError("engine_scores is empty.")



        engines = list(engine_scores.keys())

        n = len(next(iter(engine_scores.values())))



        if self.formula in (ScoreFormula.LINEAR, ScoreFormula.GEOMETRIC, ScoreFormula.HARMONIC):

            if weights is None:

                weights = {e: 1.0 / len(engines) for e in engines}

            w_total = sum(weights.get(e, 0.0) for e in engines)

            if w_total <= 0:

                w_total = 1.0

            norm_w = {e: weights.get(e, 0.0) / w_total for e in engines}



        if self.formula == ScoreFormula.LINEAR:

            result = np.zeros(n, dtype=np.float64)

            for e in engines:

                result += norm_w[e] * np.asarray(engine_scores[e], dtype=np.float64)

            return result



        if self.formula == ScoreFormula.GEOMETRIC:

            log_sum = np.zeros(n, dtype=np.float64)

            for e in engines:

                s = np.asarray(engine_scores[e], dtype=np.float64)

                s = np.clip(s, 1e-9, None)

                log_sum += norm_w[e] * np.log(s)

            return np.exp(log_sum)



        if self.formula == ScoreFormula.HARMONIC:

            inv_sum = np.zeros(n, dtype=np.float64)

            for e in engines:

                s = np.asarray(engine_scores[e], dtype=np.float64)

                s = np.clip(s, 1e-9, None)

                inv_sum += norm_w[e] / s

            return 1.0 / np.maximum(inv_sum, 1e-9)



        if self.formula == ScoreFormula.MAX:

            return np.max(

                np.stack([np.asarray(engine_scores[e]) for e in engines], axis=0),

                axis=0,

            )



        if self.formula == ScoreFormula.MIN:

            return np.min(

                np.stack([np.asarray(engine_scores[e]) for e in engines], axis=0),

                axis=0,

            )



        raise InvalidSignalError(f"Unknown formula: {self.formula}")
