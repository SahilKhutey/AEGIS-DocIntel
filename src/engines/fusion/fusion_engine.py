"""
Fusion Engine — Main Orchestrator
==================================

End-to-end fusion pipeline:

    12 Engine Signals
         ↓
    Dynamic Weighting
         ↓
    ┌──────────────┬──────────────┬──────────────┐
    │ Ranking      │ Confidence   │ Fusion Score │
    └──────────────┴──────────────┴──────────────┘
         ↓
    Optimization & Reporting
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .dynamic_weighting import DynamicWeightLearner, WeightState
from .ranking import Ranker, RankingResult, RankedItem
from .confidence import ConfidenceEstimator, ConfidenceScore
from .fusion_scoring import FusionScorer, FusionScore
from .score_calculator import ScoreCalculator, ScoreFormula
from .fusion_manager import FusionManager, FusionLifecycle
from .exceptions import FusionEngineError, InvalidSignalError


@dataclass
class FusionReport:
    """
    Complete signal fusion report.

    Attributes
    ----------
    ranking : RankingResult
        Final fused ranking.
    scores : List[FusionScore]
        Fused item scores.
    weights : Dict[str, float]
        Normalized engine weights.
    aggregate_confidence : float
        Overall document/context confidence.
    metadata : Dict[str, Any]
        Additional report metadata.
    """

    ranking: RankingResult
    scores: List[FusionScore]
    weights: Dict[str, float]
    aggregate_confidence: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ranking": self.ranking.to_dict(),
            "scores": [s.to_dict() for s in self.scores],
            "weights": self.weights,
            "aggregate_confidence": round(self.aggregate_confidence, 6),
            "metadata": self.metadata,
        }


class FusionEngine:
    """
    Main orchestrator for the AMDI-OS Fusion Engine.
    Combines representation signals from all 12 engines.
    """

    def __init__(
        self,
        initial_weights: Optional[Dict[str, float]] = None,
        ranking_method: str = "weighted_sum",
        score_formula: ScoreFormula = ScoreFormula.LINEAR,
        use_confidence: bool = True,
        use_position_prior: bool = True,
    ) -> None:
        self.manager = FusionManager(
            initial_weights=initial_weights,
            ranking_method=ranking_method,
            score_formula=score_formula,
            use_confidence=use_confidence,
            use_position_prior=use_position_prior,
        )

    def fuse(
        self,
        engine_signals: Dict[str, np.ndarray],
        item_ids: Optional[List[Any]] = None,
        explained_variance: Optional[float] = None,
        conservation_error: Optional[float] = None,
        persistence_strength: Optional[float] = None,
        top_k: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FusionReport:
        """
        Executes end-to-end signal fusion and ranking.

        Parameters
        ----------
        engine_signals : Dict[str, np.ndarray]
            Dictionary mapping engine name to array of scores.
        item_ids : Optional[List[Any]]
            Optional identifiers for the items being ranked.
        explained_variance : Optional[float]
            Optional explained variance from matrix/spectral/tensor engines.
        conservation_error : Optional[float]
            Optional conservation error from information physics engine.
        persistence_strength : Optional[float]
            Optional topological persistence strength.
        top_k : Optional[int]
            If provided, only return top-k results.
        metadata : Optional[Dict[str, Any]]
            Optional metadata.
        """
        # Ingest signals into the manager
        self.manager.ingest_signals(engine_signals)

        # Execute fusion
        ranking, fusion_scores = self.manager.fuse(
            item_ids=item_ids,
            explained_variance=explained_variance,
            conservation_error=conservation_error,
            persistence_strength=persistence_strength,
            top_k=top_k,
        )

        # Calculate aggregate confidence
        conf_scores = self.manager.confidence_est.estimate(
            engine_scores=engine_signals,
            explained_variance=explained_variance,
            conservation_error=conservation_error,
            persistence_strength=persistence_strength,
            item_ids=item_ids,
        )
        agg_conf = self.manager.confidence_est.aggregate_confidence(conf_scores)

        return FusionReport(
            ranking=ranking,
            scores=fusion_scores,
            weights=self.manager.weight_learner.state.normalized_weights(),
            aggregate_confidence=agg_conf,
            metadata=metadata or {},
        )
