"""

AMDI-OS Fusion Engine

=====================



Multi-engine signal fusion: combines outputs from all 12 AMDI-OS engines

(geometry, frequency, recurrence, matrix, template, semantic, graph,

topology, spectral, tensor, information physics, retrieval) into a

single ranked, confidence-scored context for AI agents.



Mathematical Foundation:

    R = α·S + β·G + γ·R + δ·F + ε·M + ζ·T + η·X + θ·P + ι·Φ

    (semantic + geometry + recurrence + frequency + matrix + tensor + graph + topology + physics)



Dynamic weighting:

    w_i(t+1) = w_i(t) + η · ∇_w L(w)



Confidence estimation:

    C = 1 - H_norm · (1 - EV) · CE



Fusion scoring:

    F(v) = Σ_i w_i(v) · score_i(v)



Author : AMDI-OS Development Team

Version: 1.0.0

"""



from .fusion_engine import FusionEngine, FusionReport

from .dynamic_weighting import DynamicWeightLearner, WeightState

from .ranking import Ranker, RankingResult, RankedItem

from .confidence import ConfidenceEstimator, ConfidenceScore

from .fusion_scoring import FusionScorer, FusionScore

from .weight_optimizer import WeightOptimizer, OptimizationMethod

from .score_calculator import ScoreCalculator, ScoreFormula

from .fusion_manager import FusionManager, FusionLifecycle

from .exceptions import (

    FusionEngineError,

    InvalidSignalError,

    WeightDimensionError,

    OptimizationError,

)



__all__ = [

    "FusionEngine",

    "FusionReport",

    "DynamicWeightLearner",

    "WeightState",

    "Ranker",

    "RankingResult",

    "RankedItem",

    "ConfidenceEstimator",

    "ConfidenceScore",

    "FusionScorer",

    "FusionScore",

    "WeightOptimizer",

    "OptimizationMethod",

    "ScoreCalculator",

    "ScoreFormula",

    "FusionManager",

    "FusionLifecycle",

    "FusionEngineError",

    "InvalidSignalError",

    "WeightDimensionError",

    "OptimizationError",

]



__version__ = "1.0.0"
