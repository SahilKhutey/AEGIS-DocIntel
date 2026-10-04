"""

Fusion Manager — Lifecycle Orchestrator

=======================================



Manages the full fusion lifecycle:

1. Initialization (default weights)

2. Signal ingestion (per-engine scores)

3. Fusion (ranking + scoring + confidence)

4. Optimization (feedback-driven weight updates)

5. Export (for AI agents)



State machine:

    INIT → INGEST → FUSE → OPTIMIZE → EXPORT

"""



from __future__ import annotations



from dataclasses import dataclass, field

from enum import Enum

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .confidence import ConfidenceEstimator

from .dynamic_weighting import DynamicWeightLearner, WeightState

from .fusion_scoring import FusionScorer

from .ranking import Ranker, RankingResult

from .score_calculator import ScoreCalculator, ScoreFormula

from .weight_optimizer import OptimizationMethod, WeightOptimizer, OptimizationTrace





class FusionLifecycle(Enum):

    INIT = "init"

    INGEST = "ingest"

    FUSE = "fuse"

    OPTIMIZE = "optimize"

    EXPORT = "export"





@dataclass

class FusionState:

    """

    Current fusion manager state.



    Attributes

    ----------

    lifecycle : FusionLifecycle

    weights : WeightState

    last_ranking : Optional[RankingResult]

    last_optimization : Optional[OptimizationTrace]

    num_signals_ingested : int

    num_fusions_performed : int

    """



    lifecycle: FusionLifecycle

    weights: WeightState

    last_ranking: Optional[RankingResult] = None

    last_optimization: Optional[OptimizationTrace] = None

    num_signals_ingested: int = 0

    num_fusions_performed: int = 0





class FusionManager:

    """

    Manages the full fusion lifecycle.

    """



    def __init__(

        self,

        initial_weights: Optional[Dict[str, float]] = None,

        ranking_method: str = "weighted_sum",

        score_formula: ScoreFormula = ScoreFormula.LINEAR,

        use_confidence: bool = True,

        use_position_prior: bool = True,

    ) -> None:

        self.weight_learner = DynamicWeightLearner(initial_weights=initial_weights)

        self.ranker = Ranker(method=ranking_method)

        self.score_calc = ScoreCalculator(formula=score_formula)

        self.scorer = FusionScorer(

            use_confidence=use_confidence,

            use_position_prior=use_position_prior,

        )

        self.confidence_est = ConfidenceEstimator()

        self.optimizer = WeightOptimizer()

        self.state = FusionState(

            lifecycle=FusionLifecycle.INIT,

            weights=self.weight_learner.state,

        )



    def ingest_signals(

        self,

        engine_scores: Dict[str, np.ndarray],

    ) -> None:

        """Stage 1: register engine signals for fusion."""

        if not engine_scores:

            raise ValueError("engine_scores is empty.")

        # align dimensions

        n = len(next(iter(engine_scores.values())))

        for e, s in engine_scores.items():

            if s.shape != (n,):

                raise ValueError(

                    f"Engine '{e}' shape {s.shape} ≠ expected ({n},)."

                )

        self._signals = engine_scores

        self._n = n

        self.state.lifecycle = FusionLifecycle.INGEST

        self.state.num_signals_ingested += 1



    def fuse(

        self,

        item_ids: Optional[List[Any]] = None,

        explained_variance: Optional[float] = None,

        conservation_error: Optional[float] = None,

        persistence_strength: Optional[float] = None,

        top_k: Optional[int] = None,

    ) -> Tuple[RankingResult, List]:

        """

        Stage 2: perform fusion.



        Returns (ranking_result, fusion_scores).

        """

        if not hasattr(self, "_signals"):

            raise RuntimeError("Call ingest_signals() before fuse().")

        signals = self._signals

        weights = self.weight_learner.state.weights



        # compute base score

        base_scores = self.score_calc.compute(signals, weights=weights)



        # confidence

        conf_scores = self.confidence_est.estimate(

            engine_scores=signals,

            explained_variance=explained_variance,

            conservation_error=conservation_error,

            persistence_strength=persistence_strength,

            item_ids=item_ids,

        )



        # ranking

        ranking = self.ranker.rank(

            engine_scores=signals,

            weights=weights,

            item_ids=item_ids,

            top_k=top_k,

        )



        # fusion scoring

        fusion_scores = self.scorer.score(

            engine_scores=signals,

            weights=weights,

            confidence_scores=conf_scores,

            item_ids=item_ids,

        )



        self.state.lifecycle = FusionLifecycle.FUSE

        self.state.last_ranking = ranking

        self.state.num_fusions_performed += 1



        return ranking, fusion_scores



    def optimize(

        self,

        objective_fn,

        method: OptimizationMethod = OptimizationMethod.GRADIENT_ASCENT,

    ) -> OptimizationTrace:

        """

        Stage 3: optimize weights based on feedback.

        """

        order = list(self.weight_learner.state.weights.keys())

        current_weights = self.weight_learner.state.weights

        self.optimizer.method = method

        trace = self.optimizer.optimize(

            initial_weights=current_weights,

            objective_fn=objective_fn,

            engine_order=order,

        )

        # commit optimized weights

        self.weight_learner.state.weights = trace.final_weights

        self.weight_learner.state.iteration += 1

        self.state.lifecycle = FusionLifecycle.OPTIMIZE

        self.state.last_optimization = trace

        return trace



    def export(self) -> Dict[str, Any]:

        """

        Stage 4: export current fusion state for AI agents.

        """

        self.state.lifecycle = FusionLifecycle.EXPORT

        return {

            "weights": self.weight_learner.state.normalized_weights(),

            "lifecycle": self.state.lifecycle.value,

            "num_signals_ingested": self.state.num_signals_ingested,

            "num_fusions_performed": self.state.num_fusions_performed,

            "last_ranking_method": (

                self.state.last_ranking.method

                if self.state.last_ranking is not None

                else None

            ),

        }



    def reset(self) -> None:

        """Reset manager to initial state."""

        self.weight_learner.reset()

        self.state = FusionState(

            lifecycle=FusionLifecycle.INIT,

            weights=self.weight_learner.state,

        )

        if hasattr(self, "_signals"):

            del self._signals
