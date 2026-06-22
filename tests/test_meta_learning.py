import os
import sys
import time
from pathlib import Path
import numpy as np
import pytest

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.optimization.meta_learning import (
    MetaLearner,
    MetaLearningConfig,
    OnlineLearner,
    LearningSignal,
    RLOptimizer,
    RLConfig,
    State,
    Action,
    RewardSignal,
    FeedbackLoop,
    FeedbackType,
    BanditSelector,
    BanditConfig,
    BanditAlgorithm,
    Arm,
    ABTester,
    ABTestStatus,
)


def test_online_learner():
    learner = OnlineLearner(learning_rate=0.05, momentum=0.9, adaptive_lr=True)
    assert len(learner.weights) == len(OnlineLearner.ENGINES)
    
    # Verify initial weights are normalized
    assert abs(sum(learner.weights.values()) - 1.0) < 1e-6
    
    # Create a learning signal
    signal = LearningSignal(
        timestamp=time.time(),
        document_type="financial",
        weights_before=learner.get_weights(),
        weights_after=learner.get_weights(),
        accuracy=0.9,
        latency_ms=100.0,
        token_count=500,
        user_satisfaction=1.0,
    )
    
    # Check reward computation
    assert signal.reward > 0.9
    
    # Step the learner
    update = learner.step(signal)
    assert update.gradient_norm >= 0.0
    assert abs(sum(learner.get_weights().values()) - 1.0) < 1e-6
    
    # Run epoch
    learner.add_signal(signal)
    summary = learner.run_epoch()
    assert summary["n_signals"] == 1
    assert summary["avg_reward"] == signal.reward
    
    # Test reset
    learner.reset()
    assert len(learner.signals) == 0


def test_rl_optimizer():
    optimizer = RLOptimizer(RLConfig(batch_size=2))
    
    # Create State and select action
    weights = np.ones(optimizer.N_ENGINES) / optimizer.N_ENGINES
    state = State(weights=weights, document_type="legal")
    
    action = optimizer.select_action(state, training=True)
    assert action.engine_index in range(optimizer.N_ENGINES)
    assert -0.05 <= action.delta <= 0.05
    
    # Apply action
    next_state = optimizer.apply_action(state, action)
    assert abs(next_state.weights.sum() - 1.0) < 1e-6
    
    # Update Q-table
    reward = RewardSignal(value=0.8)
    td = optimizer.update(state, action, reward, next_state, done=True)
    assert abs(td) > 0.0
    
    # Test replay buffer
    assert len(optimizer.replay_buffer) == 1
    # Verify replay with insufficient batch size does not crash
    replay_td = optimizer.replay()
    assert replay_td == 0.0
    
    # Fill replay buffer to batch size and trigger replay
    optimizer.replay_buffer.append((state, action, reward, next_state, True))
    replay_td = optimizer.replay()
    assert replay_td >= 0.0
    
    # Test optimal weights retrieval
    opt_weights = optimizer.get_optimal_weights("legal")
    assert abs(sum(opt_weights.values()) - 1.0) < 1e-6


def test_feedback_loop():
    loop = FeedbackLoop()
    
    # Record explicit rating
    event1 = loop.record_explicit_rating(
        user_id="user1",
        query="test query",
        response="test response",
        rating=5,
        response_id="resp1",
        comment="excellent",
    )
    assert event1.rating == 1.0
    
    # Record thumbs down
    event2 = loop.record_thumbs(
        user_id="user2",
        query="test query",
        response="test response",
        up=False,
    )
    assert event2.rating == 0.0
    
    # Record implicit clicks
    event3 = loop.record_implicit(
        feedback_type=FeedbackType.IMPLICIT_CLICK,
        user_id="user3",
        query="test query",
        response="test response",
    )
    assert event3.rating == 0.6
    
    # Verify statistics
    stats = loop.get_stats()
    assert stats["total_events"] == 3
    assert stats["thumbs_down"] == 1
    assert stats["explicit_ratings"] == 1
    
    # Verify query feedback aggregation
    q_feedback = loop.get_query_feedback("test query")
    assert q_feedback["count"] == 3
    assert q_feedback["avg_rating"] == (1.0 + 0.0 + 0.6) / 3.0


def test_bandit_selector():
    config = BanditConfig(algorithm=BanditAlgorithm.UCB1)
    selector = BanditSelector(config)
    
    # Register arms
    selector.add_arm(Arm("arm_a", "strategy_a", "Description A"))
    selector.add_arm(Arm("arm_b", "strategy_b", "Description B"))
    
    # Select under UCB1 (should select unexplored arms first)
    choice1 = selector.select()
    assert choice1 in ["arm_a", "arm_b"]
    
    selector.update(choice1, 0.9)
    choice2 = selector.select()
    # The other arm should be selected next as it has 0 pulls
    assert choice2 != choice1
    
    selector.update(choice2, 0.2)
    
    # Statistics
    stats = selector.get_arm_stats()
    assert stats["arm_a"]["pulls"] == 1
    assert stats["arm_b"]["pulls"] == 1
    
    # Verify best arm
    best = selector.best_arm()
    assert best == choice1  # The one with reward 0.9
    
    # Test Thompson Sampling
    selector.config.algorithm = BanditAlgorithm.THOMPSON_SAMPLING
    choice_ts = selector.select()
    assert choice_ts in ["arm_a", "arm_b"]


def test_ab_tester():
    tester = ABTester()
    
    variants = [
        {"variant_id": "control", "name": "Control Variant", "config": {"w": 0.5}, "weight": 0.5},
        {"variant_id": "treatment", "name": "Treatment Variant", "config": {"w": 0.6}, "weight": 0.5},
    ]
    
    test = tester.create_test("Test 1", variants, min_sample_size=10)
    assert test.status == ABTestStatus.DRAFT
    
    tester.start_test(test.test_id)
    assert test.status == ABTestStatus.RUNNING
    
    # Assign variants
    vid1 = tester.assign_variant(test.test_id, "user_xyz")
    vid2 = tester.assign_variant(test.test_id, "user_abc")
    assert vid1 in ["control", "treatment"]
    assert vid2 in ["control", "treatment"]
    
    # Record metrics
    for _ in range(10):
        tester.record_impression(test.test_id, "control")
        tester.record_metric(test.test_id, "control", 0.7, converted=True)
        
        tester.record_impression(test.test_id, "treatment")
        tester.record_metric(test.test_id, "treatment", 0.9, converted=True)
        
    # Analyze results
    result = tester.analyze(test.test_id)
    assert result.winner == "treatment"
    assert result.confidence > 0.5
    assert result.lift > 0.0
    
    # Complete test
    final_result = tester.complete_test(test.test_id)
    assert final_result.status == ABTestStatus.COMPLETED


def test_meta_learner_orchestration():
    config = MetaLearningConfig(
        online_learning_rate=0.02,
        rl_epsilon=0.1,
        bandit_algorithm=BanditAlgorithm.UCB1,
    )
    meta = MetaLearner(config)
    
    # Process several query outcomes
    for i in range(5):
        res = meta.process_query_outcome(
            document_type="financial",
            query=f"Query {i}",
            accuracy=0.8 + 0.04 * i,
            latency_ms=150.0 - 10 * i,
            token_count=600 - 20 * i,
            user_satisfaction=0.9,
        )
        assert "weights_before" in res
        assert "weights_after" in res
        assert "bandit_choice" in res
        assert "reward" in res
        
    # Record some feedback
    meta.record_user_feedback(
        user_id="user1",
        query="Query 1",
        response="Response 1",
        feedback_type=FeedbackType.EXPLICIT_RATING,
        rating=0.8,
    )
    
    meta.record_user_feedback(
        user_id="user2",
        query="Query 2",
        response="Response 2",
        feedback_type=FeedbackType.THUMBS_UP,
    )
    
    # Get optimal weights by doc type
    opt_weights = meta.get_optimal_weights_for_document_type("financial")
    assert abs(sum(opt_weights.values()) - 1.0) < 1e-6
    
    # Generate report
    report = meta.generate_report()
    assert report.n_signals_processed == 5
    assert report.avg_reward > 0.0
    assert len(report.recommendations) > 0
