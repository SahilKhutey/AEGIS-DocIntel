"""

Fusion Scoring

==============



Unified scoring that combines:

- Multi-engine weighted scores

- Confidence weighting

- Position priors

- Recency / freshness signals



Mathematical Foundation:

-----------------------

F(v) = Σ_i w_i · score_i(v) · C(v) · P(v) · R(v)



where:

    w_i      engine weight

    score_i  per-engine score

    C(v)     confidence weight

    P(v)     position prior

    R(v)     recency / freshness factor

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional



import numpy as np



from .confidence import ConfidenceScore

from .dynamic_weighting import WeightState

from .exceptions import InvalidSignalError





@dataclass

class FusionScore:

    """

    Final fusion score for an item.



    Attributes

    ----------

    item_id : Any

    fused_score : float

    weighted_sum : float

    confidence_weight : float

    position_prior : float

    recency_factor : float

    per_engine_contribution : Dict[str, float]

    """



    item_id: Any

    fused_score: float

    weighted_sum: float

    confidence_weight: float

    position_prior: float

    recency_factor: float

    per_engine_contribution: Dict[str, float] = field(default_factory=dict)



    def to_dict(self) -> dict:

        return {

            "item_id": self.item_id,

            "fused_score": round(self.fused_score, 6),

            "weighted_sum": round(self.weighted_sum, 6),

            "confidence_weight": round(self.confidence_weight, 6),

            "position_prior": round(self.position_prior, 6),

            "recency_factor": round(self.recency_factor, 6),

            "per_engine_contribution": {

                k: round(v, 6) for k, v in self.per_engine_contribution.items()

            },

        }





class FusionScorer:

    """

    Unified fusion scorer.

    """



    def __init__(

        self,

        use_confidence: bool = True,

        use_position_prior: bool = True,

        use_recency: bool = False,

        position_decay: float = 0.95,

    ) -> None:

        self.use_confidence = use_confidence

        self.use_position_prior = use_position_prior

        self.use_recency = use_recency

        self.position_decay = position_decay



    def score(

        self,

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        confidence_scores: Optional[List[ConfidenceScore]] = None,

        item_ids: Optional[List[Any]] = None,

        position_indices: Optional[np.ndarray] = None,

        recency_scores: Optional[np.ndarray] = None,

    ) -> List[FusionScore]:

        """

        Compute fusion scores.



        Parameters

        ----------

        engine_scores : Dict[str, np.ndarray]

        weights : Dict[str, float]

        confidence_scores : Optional[List[ConfidenceScore]]

        item_ids : Optional[List[Any]]

        position_indices : Optional[np.ndarray]

            Position per item (0-indexed). Used for position prior decay.

        recency_scores : Optional[np.ndarray]

            Per-item freshness in [0, 1].

        """

        if not engine_scores:

            raise InvalidSignalError("engine_scores is empty.")



        engines = list(engine_scores.keys())

        n = len(next(iter(engine_scores.values())))



        if item_ids is None:

            item_ids = list(range(n))



        # normalize weights

        w_total = sum(weights.get(e, 0.0) for e in engines)

        if w_total <= 0:

            w_total = 1.0

        norm_w = {e: weights.get(e, 0.0) / w_total for e in engines}



        # confidence map

        conf_map: Dict[Any, ConfidenceScore] = {}

        if confidence_scores is not None:

            for c in confidence_scores:

                conf_map[c.item_id] = c



        # position prior

        if position_indices is None:

            position_indices = np.arange(n)

        if self.use_position_prior:

            position_prior = self.position_decay ** position_indices

        else:

            position_prior = np.ones(n)



        # recency

        if recency_scores is None:

            recency_scores = np.ones(n)



        results: List[FusionScore] = []

        for i, item_id in enumerate(item_ids):

            weighted_sum = 0.0

            contributions: Dict[str, float] = {}

            for e in engines:

                s = float(engine_scores[e][i])

                contrib = norm_w[e] * s

                weighted_sum += contrib

                contributions[e] = contrib



            c_weight = 1.0

            if self.use_confidence and item_id in conf_map:

                c_weight = float(conf_map[item_id].composite_confidence)



            p_prior = float(position_prior[i])

            r_factor = float(recency_scores[i]) if self.use_recency else 1.0



            fused = weighted_sum * c_weight * p_prior * r_factor

            results.append(

                FusionScore(

                    item_id=item_id,

                    fused_score=float(fused),

                    weighted_sum=float(weighted_sum),

                    confidence_weight=c_weight,

                    position_prior=p_prior,

                    recency_factor=r_factor,

                    per_engine_contribution=contributions,

                )

            )



        return results



    def aggregate_score(

        self,

        fusion_scores: List[FusionScore],

    ) -> float:

        """Aggregate fusion scores into a single document-level score."""

        if not fusion_scores:

            return 0.0

        return float(np.mean([s.fused_score for s in fusion_scores]))
