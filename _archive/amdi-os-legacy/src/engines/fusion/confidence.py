"""

Confidence Estimation

====================



Mathematical Foundation:

-----------------------

Confidence combines:

1. Inter-engine agreement (lower variance → higher confidence)

2. Reconstruction quality (decomposition EV → confidence)

3. Conservation error (lower error → higher confidence)

4. Persistence strength (higher → higher confidence)



Composite confidence:

    C = (1 - H_norm · σ_norm) · EV · (1 - CE)



where:

    H_norm    normalized score entropy

    σ_norm    normalized inter-engine std

    EV        explained variance from decomposition

    CE        conservation error

"""



from __future__ import annotations



from dataclasses import dataclass

from typing import Dict, List, Optional



import numpy as np



from .exceptions import ConfidenceEstimationError





@dataclass

class ConfidenceScore:

    """

    Confidence score for a single item.



    Attributes

    ----------

    item_id : Any

    composite_confidence : float

    inter_engine_agreement : float

    explained_variance : float

    conservation_score : float

    persistence_strength : float

    components : Dict[str, float]

    """



    item_id: Any

    composite_confidence: float

    inter_engine_agreement: float

    explained_variance: float

    conservation_score: float

    persistence_strength: float

    components: Dict[str, float]



    def to_dict(self) -> dict:

        return {

            "item_id": self.item_id,

            "composite_confidence": round(self.composite_confidence, 6),

            "inter_engine_agreement": round(self.inter_engine_agreement, 6),

            "explained_variance": round(self.explained_variance, 6),

            "conservation_score": round(self.conservation_score, 6),

            "persistence_strength": round(self.persistence_strength, 6),

            "components": {k: round(v, 6) for k, v in self.components.items()},

        }





class ConfidenceEstimator:

    """

    Estimates confidence of fusion results.

    """



    def __init__(

        self,

        agreement_weight: float = 0.4,

        ev_weight: float = 0.3,

        conservation_weight: float = 0.2,

        persistence_weight: float = 0.1,

    ) -> None:

        s = agreement_weight + ev_weight + conservation_weight + persistence_weight

        if s <= 0:

            raise ValueError("weights must sum to a positive number.")

        self.agreement_weight = agreement_weight / s

        self.ev_weight = ev_weight / s

        self.conservation_weight = conservation_weight / s

        self.persistence_weight = persistence_weight / s



    def estimate(

        self,

        engine_scores: Dict[str, np.ndarray],

        explained_variance: Optional[float] = None,

        conservation_error: Optional[float] = None,

        persistence_strength: Optional[float] = None,

        item_ids: Optional[List] = None,

    ) -> List[ConfidenceScore]:

        """

        Estimate confidence per item.



        Parameters

        ----------

        engine_scores : Dict[str, np.ndarray]

            Engine name → score vector.

        explained_variance : Optional[float]

            From tensor / spectral decomposition.

        conservation_error : Optional[float]

            From information-physics conservation check.

        persistence_strength : Optional[float]

            From topological persistence analysis.

        item_ids : Optional[List]

        """

        if not engine_scores:

            raise ConfidenceEstimationError("engine_scores is empty.")



        engines = list(engine_scores.keys())

        n = len(next(iter(engine_scores.values())))

        scores_matrix = np.stack(

            [np.asarray(engine_scores[e], dtype=np.float64) for e in engines],

            axis=0,

        )  # shape: (num_engines, n)



        # normalize scores per engine to [0, 1]

        mins = scores_matrix.min(axis=1, keepdims=True)

        maxs = scores_matrix.max(axis=1, keepdims=True)

        ranges = np.where((maxs - mins) > 0, maxs - mins, 1.0)

        norm_scores = (scores_matrix - mins) / ranges



        # inter-engine agreement: 1 - normalized std

        mean = norm_scores.mean(axis=0)

        std = norm_scores.std(axis=0)

        # normalize std to [0, 1] across items

        std_norm = std / max(std.max(), 1e-9) if std.max() > 0 else std

        agreement = 1.0 - std_norm



        # default values

        ev = explained_variance if explained_variance is not None else 1.0

        ce = conservation_error if conservation_error is not None else 0.0

        ps = persistence_strength if persistence_strength is not None else 0.5



        # conservation score: 1 - normalized error

        cs = max(0.0, 1.0 - ce)



        if item_ids is None:

            item_ids = list(range(n))



        results: List[ConfidenceScore] = []

        for i, item_id in enumerate(item_ids):

            comp = {

                "agreement": float(agreement[i]),

                "explained_variance": float(ev),

                "conservation": float(cs),

                "persistence": float(ps),

            }

            composite = (

                self.agreement_weight * agreement[i]

                + self.ev_weight * ev

                + self.conservation_weight * cs

                + self.persistence_weight * ps

            )

            composite = float(np.clip(composite, 0.0, 1.0))

            results.append(

                ConfidenceScore(

                    item_id=item_id,

                    composite_confidence=composite,

                    inter_engine_agreement=float(agreement[i]),

                    explained_variance=float(ev),

                    conservation_score=float(cs),

                    persistence_strength=float(ps),

                    components=comp,

                )

            )



        return results



    def aggregate_confidence(

        self,

        confidence_scores: List[ConfidenceScore],

    ) -> float:

        """Aggregate per-item confidences into one document-level score."""

        if not confidence_scores:

            return 0.0

        return float(

            np.mean([c.composite_confidence for c in confidence_scores])

        )
