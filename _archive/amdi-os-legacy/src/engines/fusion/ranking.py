"""

Multi-Signal Ranking

====================



Combines per-engine scores into a unified ranking using:

- Weighted sum

- Reciprocal rank fusion (RRF)

- Borda count

- Condorcet fusion



Mathematical Foundation:

-----------------------

Weighted sum:

    R(v) = Σ_i w_i · score_i(v)



Reciprocal Rank Fusion (RRF):

    RRF(v) = Σ_i w_i / (k + rank_i(v))



Borda count:

    B(v) = Σ_i w_i · (N - rank_i(v))



Condorcet:

    pairwise wins weighted by engine importance

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .dynamic_weighting import WeightState

from .exceptions import InvalidSignalError





@dataclass

class RankedItem:

    """

    A single item in the ranking.



    Attributes

    ----------

    item_id : Any

        Document element identifier.

    fused_score : float

        Final fused score.

    engine_scores : Dict[str, float]

        Per-engine scores.

    rank : int

        Position in ranking (1-indexed).

    """



    item_id: Any

    fused_score: float

    engine_scores: Dict[str, float] = field(default_factory=dict)

    rank: int = 0



    def to_dict(self) -> dict:

        return {

            "item_id": self.item_id,

            "fused_score": round(self.fused_score, 6),

            "engine_scores": {k: round(v, 6) for k, v in self.engine_scores.items()},

            "rank": self.rank,

        }





@dataclass

class RankingResult:

    """

    Final ranking output.



    Attributes

    ----------

    ranked_items : List[RankedItem]

    method : str

    num_items : int

    top_k : int

    """



    ranked_items: List[RankedItem]

    method: str

    num_items: int

    top_k: int



    def top(self, k: int = 10) -> List[RankedItem]:

        return self.ranked_items[:k]



    def by_id(self, item_id: Any) -> Optional[RankedItem]:

        for item in self.ranked_items:

            if item.item_id == item_id:

                return item

        return None



    def to_dict(self) -> dict:

        return {

            "method": self.method,

            "num_items": self.num_items,

            "top_k": self.top_k,

            "items": [item.to_dict() for item in self.ranked_items],

        }





class Ranker:

    """

    Multi-signal ranker.



    Supports: weighted_sum, rrf, borda, condorcet

    """



    def __init__(self, method: str = "weighted_sum", rrf_k: int = 60) -> None:

        if method not in {"weighted_sum", "rrf", "borda", "condorcet"}:

            raise ValueError(f"Unknown ranking method: {method}")

        self.method = method

        self.rrf_k = rrf_k



    def rank(

        self,

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        item_ids: Optional[List[Any]] = None,

        top_k: Optional[int] = None,

    ) -> RankingResult:

        """

        Compute fused ranking.



        Parameters

        ----------

        engine_scores : Dict[str, np.ndarray]

            Engine name → score vector of length n.

        weights : Dict[str, float]

            Engine name → weight (will be normalized).

        item_ids : Optional[List[Any]]

            Optional identifiers (default: 0..n-1).

        top_k : Optional[int]

            If given, return only top-k.

        """

        if not engine_scores:

            raise InvalidSignalError("engine_scores is empty.")



        engines = list(engine_scores.keys())

        n = len(next(iter(engine_scores.values())))

        for e, s in engine_scores.items():

            if s.shape != (n,):

                raise InvalidSignalError(

                    f"Engine '{e}' has shape {s.shape}, expected ({n},)."

                )



        if item_ids is None:

            item_ids = list(range(n))



        # normalize weights

        w_total = sum(weights.get(e, 0.0) for e in engines)

        if w_total <= 0:

            w_total = 1.0

        norm_w = {e: weights.get(e, 0.0) / w_total for e in engines}



        if self.method == "weighted_sum":

            fused = self._weighted_sum(engine_scores, norm_w, engines, n)

        elif self.method == "rrf":

            fused = self._rrf(engine_scores, norm_w, engines, n)

        elif self.method == "borda":

            fused = self._borda(engine_scores, norm_w, engines, n)

        elif self.method == "condorcet":

            fused = self._condorcet(engine_scores, norm_w, engines, n)

        else:

            fused = np.zeros(n)



        # sort descending

        order = np.argsort(-fused)

        ranked_items: List[RankedItem] = []

        for rank, idx in enumerate(order, start=1):

            ranked_items.append(

                RankedItem(

                    item_id=item_ids[idx],

                    fused_score=float(fused[idx]),

                    engine_scores={

                        e: float(engine_scores[e][idx]) for e in engines

                    },

                    rank=rank,

                )

            )



        if top_k is not None:

            ranked_items = ranked_items[:top_k]



        return RankingResult(

            ranked_items=ranked_items,

            method=self.method,

            num_items=n,

            top_k=top_k or len(ranked_items),

        )



    @staticmethod

    def _weighted_sum(

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        engines: List[str],

        n: int,

    ) -> np.ndarray:

        fused = np.zeros(n, dtype=np.float64)

        for e in engines:

            fused += weights[e] * np.asarray(engine_scores[e], dtype=np.float64)

        return fused



    def _rrf(

        self,

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        engines: List[str],

        n: int,

    ) -> np.ndarray:

        fused = np.zeros(n, dtype=np.float64)

        for e in engines:

            s = np.asarray(engine_scores[e], dtype=np.float64)

            order = np.argsort(-s)

            ranks = np.empty(n, dtype=np.float64)

            for rank, idx in enumerate(order, start=1):

                ranks[idx] = rank

            fused += weights[e] / (self.rrf_k + ranks)

        return fused



    @staticmethod

    def _borda(

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        engines: List[str],

        n: int,

    ) -> np.ndarray:

        fused = np.zeros(n, dtype=np.float64)

        for e in engines:

            s = np.asarray(engine_scores[e], dtype=np.float64)

            order = np.argsort(-s)

            borda = np.empty(n, dtype=np.float64)

            for rank, idx in enumerate(order):

                borda[idx] = n - rank

            fused += weights[e] * borda

        return fused



    @staticmethod

    def _condorcet(

        engine_scores: Dict[str, np.ndarray],

        weights: Dict[str, float],

        engines: List[str],

        n: int,

    ) -> np.ndarray:

        fused = np.zeros(n, dtype=np.float64)

        for e in engines:

            s = np.asarray(engine_scores[e], dtype=np.float64)

            for i in range(n):

                wins = (s[i] > s).sum()

                fused[i] += weights[e] * wins

        return fused
