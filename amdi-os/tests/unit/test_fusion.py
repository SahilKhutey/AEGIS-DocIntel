"""
Unit tests for the new Fusion Engine.
"""

from __future__ import annotations

import numpy as np
import pytest

from src.engines.fusion import (
    FusionEngine,
    DynamicWeightLearner,
    Ranker,
    ConfidenceEstimator,
    ConfidenceScore,
    FusionScorer,
    WeightOptimizer,
    OptimizationMethod,
    ScoreCalculator,
    ScoreFormula,
    FusionManager,
    FusionLifecycle,
    FusionEngineError,
    InvalidSignalError,
    WeightDimensionError,
    OptimizationError,
)


def test_dynamic_weight_learner() -> None:
    learner = DynamicWeightLearner(learning_rate=0.1, max_weight=0.6, min_weight=0.01)
    
    # Softmax Update
    logits = np.ones(12) * 2.0
    weights = learner.softmax_update(logits)
    assert np.allclose(sum(weights.values()), 1.0)
    assert len(weights) == 12
    
    # Logits dimension validation
    with pytest.raises(WeightDimensionError):
        learner.softmax_update(np.ones(5))

    # Performance Update
    perf = {e: 0.9 for e in learner.DEFAULT_ENGINES}
    weights_p = learner.performance_update(perf)
    assert np.allclose(sum(weights_p.values()), 1.0)

    # Gradient Update
    grads = np.random.randn(12)
    weights_g = learner.gradient_update(grads)
    assert np.allclose(sum(weights_g.values()), 1.0)
    for w in weights_g.values():
        assert 0.005 <= w <= 0.65

    # Reset
    learner.reset()
    assert learner.state.iteration == 0
    assert len(learner.state.history) == 0


def test_ranker() -> None:
    # Set up mock engine scores for 3 items
    # item 0: high on all
    # item 1: medium
    # item 2: low
    scores = {
        "geometry": np.array([0.9, 0.5, 0.1]),
        "frequency": np.array([0.8, 0.4, 0.2]),
    }
    weights = {"geometry": 0.6, "frequency": 0.4}

    # Test validation
    with pytest.raises(InvalidSignalError):
        Ranker("weighted_sum").rank({}, weights)
    with pytest.raises(InvalidSignalError):
        Ranker("weighted_sum").rank({"geometry": np.array([1, 2]), "frequency": np.array([1, 2, 3])}, weights)

    # Weighted Sum Ranking
    ranker_ws = Ranker("weighted_sum")
    res_ws = ranker_ws.rank(scores, weights, item_ids=["itemA", "itemB", "itemC"])
    assert res_ws.num_items == 3
    assert res_ws.ranked_items[0].item_id == "itemA"
    assert res_ws.ranked_items[2].item_id == "itemC"
    assert res_ws.ranked_items[0].fused_score > res_ws.ranked_items[1].fused_score

    # RRF Ranking
    ranker_rrf = Ranker("rrf")
    res_rrf = ranker_rrf.rank(scores, weights, item_ids=["itemA", "itemB", "itemC"])
    assert len(res_rrf.ranked_items) == 3

    # Borda Ranking
    ranker_borda = Ranker("borda")
    res_b = ranker_borda.rank(scores, weights)
    assert len(res_b.ranked_items) == 3

    # Condorcet Ranking
    ranker_c = Ranker("condorcet")
    res_c = ranker_c.rank(scores, weights)
    assert len(res_c.ranked_items) == 3


def test_confidence_estimator() -> None:
    est = ConfidenceEstimator()
    
    scores = {
        "geometry": np.array([0.9, 0.5, 0.1]),
        "frequency": np.array([0.9, 0.4, 0.1]),
    }
    
    # Estimate confidence
    conf = est.estimate(scores, explained_variance=0.95, conservation_error=0.02, persistence_strength=0.8)
    assert len(conf) == 3
    for c in conf:
        assert 0.0 <= c.composite_confidence <= 1.0
        assert c.explained_variance == 0.95
        assert c.components["agreement"] >= 0.0
        
    agg = est.aggregate_confidence(conf)
    assert 0.0 <= agg <= 1.0


def test_fusion_scorer() -> None:
    scorer = FusionScorer(use_confidence=True, use_position_prior=True)
    
    scores = {
        "geometry": np.array([0.9, 0.5, 0.1]),
        "frequency": np.array([0.9, 0.4, 0.1]),
    }
    weights = {"geometry": 0.5, "frequency": 0.5}
    
    conf_scores = [
        ConfidenceScore("item0", 0.9, 0.9, 0.9, 0.9, 0.9, {}),
        ConfidenceScore("item1", 0.8, 0.8, 0.8, 0.8, 0.8, {}),
        ConfidenceScore("item2", 0.5, 0.5, 0.5, 0.5, 0.5, {}),
    ]
    
    res = scorer.score(
        scores,
        weights,
        confidence_scores=conf_scores,
        item_ids=["item0", "item1", "item2"],
        position_indices=np.array([0, 1, 2]),
    )
    
    assert len(res) == 3
    assert res[0].fused_score > res[2].fused_score
    assert res[0].position_prior == 1.0
    assert res[1].position_prior == 0.95


def test_weight_optimizer() -> None:
    initial_weights = {"e1": 0.5, "e2": 0.5}
    
    # Objective function: maximize weight for e1
    def objective_fn(w: dict[str, float]) -> float:
        return w.get("e1", 0.0) - w.get("e2", 0.0)

    # Gradient Ascent Optimization
    opt_ga = WeightOptimizer(method=OptimizationMethod.GRADIENT_ASCENT, max_iter=10)
    trace_ga = opt_ga.optimize(initial_weights, objective_fn)
    assert trace_ga.converged or trace_ga.iterations > 0
    assert trace_ga.final_weights["e1"] > 0.5

    # Coordinate Descent Optimization
    opt_cd = WeightOptimizer(method=OptimizationMethod.COORDINATE_DESCENT, max_iter=10)
    trace_cd = opt_cd.optimize(initial_weights, objective_fn)
    assert trace_cd.iterations > 0
    assert trace_cd.final_weights["e1"] > 0.5

    # Bandit Optimization
    opt_b = WeightOptimizer(method=OptimizationMethod.BANDIT, max_iter=10)
    trace_b = opt_b.optimize(initial_weights, objective_fn)
    assert trace_b.iterations > 0


def test_score_calculator() -> None:
    scores = {
        "e1": np.array([0.9, 0.5]),
        "e2": np.array([0.8, 0.2]),
    }
    weights = {"e1": 0.7, "e2": 0.3}

    # Linear
    assert np.allclose(
        ScoreCalculator(ScoreFormula.LINEAR).compute(scores, weights),
        np.array([0.7*0.9 + 0.3*0.8, 0.7*0.5 + 0.3*0.2])
    )
    
    # Geometric
    geom = ScoreCalculator(ScoreFormula.GEOMETRIC).compute(scores, weights)
    assert geom[0] > geom[1]
    
    # Harmonic
    harm = ScoreCalculator(ScoreFormula.HARMONIC).compute(scores, weights)
    assert harm[0] > harm[1]

    # Max
    max_scores = ScoreCalculator(ScoreFormula.MAX).compute(scores)
    assert np.allclose(max_scores, np.array([0.9, 0.5]))

    # Min
    min_scores = ScoreCalculator(ScoreFormula.MIN).compute(scores)
    assert np.allclose(min_scores, np.array([0.8, 0.2]))


def test_fusion_manager_lifecycle() -> None:
    mgr = FusionManager(ranking_method="rrf")
    assert mgr.state.lifecycle == FusionLifecycle.INIT

    # 12 signals setup
    signals = {e: np.random.rand(5) for e in mgr.weight_learner.DEFAULT_ENGINES}
    
    # Ingest
    mgr.ingest_signals(signals)
    assert mgr.state.lifecycle == FusionLifecycle.INGEST
    
    # Fuse
    ranking, scores = mgr.fuse(
        explained_variance=0.9,
        conservation_error=0.01,
        persistence_strength=0.7
    )
    assert mgr.state.lifecycle == FusionLifecycle.FUSE
    assert ranking.num_items == 5
    assert len(scores) == 5

    # Optimize
    def dummy_objective(w: dict[str, float]) -> float:
        return float(np.mean(list(w.values())))
        
    trace = mgr.optimize(dummy_objective)
    assert mgr.state.lifecycle == FusionLifecycle.OPTIMIZE
    assert trace.iterations > 0

    # Export
    exp = mgr.export()
    assert mgr.state.lifecycle == FusionLifecycle.EXPORT
    assert exp["lifecycle"] == "export"
    assert "weights" in exp


def test_fusion_engine_orchestration() -> None:
    engine = FusionEngine()
    
    signals = {e: np.random.rand(5) for e in engine.manager.weight_learner.DEFAULT_ENGINES}
    
    report = engine.fuse(
        signals,
        item_ids=["doc0", "doc1", "doc2", "doc3", "doc4"],
        explained_variance=0.85,
        conservation_error=0.04,
        persistence_strength=0.6,
        top_k=3,
        metadata={"session_id": "test_123"},
    )
    
    assert report.ranking.top_k == 3
    assert len(report.scores) == 5 # scores lists all, ranking is sliced
    assert len(report.weights) == 12
    assert report.aggregate_confidence > 0
    assert report.metadata["session_id"] == "test_123"
    
    d = report.to_dict()
    assert "ranking" in d
    assert "scores" in d
    assert "weights" in d
    assert "aggregate_confidence" in d
    assert "metadata" in d
