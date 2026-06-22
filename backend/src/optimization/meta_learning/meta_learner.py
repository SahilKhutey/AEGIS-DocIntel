"""
Meta Learner
==============

Main orchestrator for adaptive weight learning and continuous improvement.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import numpy as np

from .ab_tester import ABTest, ABTester, ABTestResult, ABTestStatus
from .bandit_selector import Arm, BanditAlgorithm, BanditConfig, BanditSelector
from .feedback_loop import FeedbackEvent, FeedbackLoop, FeedbackType
from .online_learner import LearningSignal, OnlineLearner, OnlineUpdate
from .rl_optimizer import Action, RLConfig, RLOptimizer, RewardSignal, State


@dataclass
class MetaLearningConfig:
    """Meta learning configuration."""

    # online learning
    online_learning_rate: float = 0.01
    online_momentum: float = 0.9
    # RL
    rl_epsilon: float = 0.1
    rl_gamma: float = 0.95
    # bandit
    bandit_algorithm: BanditAlgorithm = BanditAlgorithm.UCB1
    bandit_epsilon: float = 0.1
    # A/B testing
    ab_min_sample_size: int = 100
    # update cadence
    update_every_n_signals: int = 10


@dataclass
class MetaLearningReport:
    """Report of meta learning state."""

    current_weights: Dict[str, float]
    weight_history: List[Dict[str, float]]
    n_signals_processed: int
    avg_reward: float
    ab_test_winner: Optional[str]
    bandit_best_arm: Optional[str]
    recommendations: List[str] = field(default_factory=list)


class MetaLearner:
    """
    Main orchestrator for meta-learning in AMDI-OS.

    Combines:
        - Online learner (gradient ascent)
        - RL optimizer (Q-learning)
        - Bandit selector (strategy choice)
        - A/B tester (variant comparison)
        - Feedback loop (user signals)
    """

    ENGINES = [
        "geometry", "frequency", "recurrence", "matrix", "template",
        "semantic", "graph", "topology", "spectral", "tensor",
        "info_physics", "retrieval",
    ]

    def __init__(self, config: Optional[MetaLearningConfig] = None) -> None:
        self.config = config or MetaLearningConfig()
        # components
        self.online = OnlineLearner(
            learning_rate=self.config.online_learning_rate,
            momentum=self.config.online_momentum,
        )
        self.rl = RLOptimizer(
            RLConfig(
                epsilon=self.config.rl_epsilon,
                gamma=self.config.rl_gamma,
            )
        )
        self.feedback = FeedbackLoop()
        self.bandit = BanditSelector(
            BanditConfig(algorithm=self.config.bandit_algorithm, epsilon=self.config.bandit_epsilon)
        )
        self.ab_tester = ABTester()
        # default bandit arms
        self._setup_default_arms()
        # weight history
        self.weight_history: List[Dict[str, float]] = [
            self.online.get_weights()
        ]
        self.signals_processed: int = 0

    def _setup_default_arms(self) -> None:
        """Register default strategy variants as bandit arms."""
        self.bandit.add_arm(Arm(
            arm_id="balanced",
            strategy_name="balanced_weights",
            description="Default uniform weights",
        ))
        self.bandit.add_arm(Arm(
            arm_id="semantic_heavy",
            strategy_name="semantic_heavy",
            description="Boost semantic and retrieval engines",
            metadata={"semantic_boost": 1.5, "retrieval_boost": 1.5},
        ))
        self.bandit.add_arm(Arm(
            arm_id="topology_heavy",
            strategy_name="topology_heavy",
            description="Boost topology and spectral engines",
            metadata={"topology_boost": 1.5, "spectral_boost": 1.5},
        ))
        self.bandit.add_arm(Arm(
            arm_id="fast_path",
            strategy_name="fast_path",
            description="Lower latency, simpler engines only",
            metadata={"exclude_engines": ["tensor", "topology", "spectral"]},
        ))

    def get_current_weights(self) -> Dict[str, float]:
        return self.online.get_weights()

    def process_query_outcome(
        self,
        document_type: str,
        query: str,
        accuracy: float,
        latency_ms: float,
        token_count: int,
        user_satisfaction: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Process a query outcome and update all learning components.

        Returns dict with all updates applied.
        """
        weights_before = self.online.get_weights()
        # build learning signal
        signal = LearningSignal(
            timestamp=time.time(),
            document_type=document_type,
            weights_before=weights_before,
            weights_after=weights_before,  # placeholder
            accuracy=accuracy,
            latency_ms=latency_ms,
            token_count=token_count,
            user_satisfaction=user_satisfaction,
            metadata={"query": query[:200]},
        )
        # feed to online learner
        update = self.online.step(signal)
        weights_after = self.online.get_weights()
        signal.weights_after = weights_after
        # feed RL optimizer
        rl_state = State(
            weights=np.array([weights_after[e] for e in self.ENGINES]),
            document_type=document_type,
        )
        rl_action = self.rl.select_action(rl_state, training=True)
        rl_next_state = self.rl.apply_action(rl_state, rl_action)
        rl_reward = RewardSignal(value=signal.reward)
        self.rl.update(rl_state, rl_action, rl_reward, rl_next_state, done=True)
        # feed bandit selector with reward
        bandit_choice = self.bandit.select()
        self.bandit.update(bandit_choice, signal.reward)
        self.online.add_signal(signal)
        self.signals_processed += 1
        # record history
        self.weight_history.append(weights_after)
        if len(self.weight_history) > 1000:
            self.weight_history = self.weight_history[-1000:]
        return {
            "weights_before": weights_before,
            "weights_after": weights_after,
            "online_update": {
                "gradient_norm": update.gradient_norm,
                "learning_rate": update.learning_rate,
            },
            "bandit_choice": bandit_choice,
            "reward": signal.reward,
            "rl_action": {
                "engine": self.ENGINES[rl_action.engine_index],
                "delta": rl_action.delta,
            },
        }

    def record_user_feedback(
        self,
        user_id: str,
        query: str,
        response: str,
        feedback_type: FeedbackType,
        rating: Optional[float] = None,
        response_id: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> FeedbackEvent:
        """Record user feedback for learning."""
        if feedback_type == FeedbackType.EXPLICIT_RATING and rating is not None:
            # convert 0-1 rating to 1-5 stars
            stars = max(1, min(5, int(rating * 4) + 1))
            return self.feedback.record_explicit_rating(
                user_id=user_id,
                query=query,
                response=response,
                rating=stars,
                response_id=response_id,
            )
        elif feedback_type == FeedbackType.THUMBS_UP:
            return self.feedback.record_thumbs(
                user_id=user_id, query=query, response=response, up=True
            )
        elif feedback_type == FeedbackType.THUMBS_DOWN:
            return self.feedback.record_thumbs(
                user_id=user_id, query=query, response=response, up=False
            )
        else:
            return self.feedback.record_implicit(
                feedback_type=feedback_type,
                user_id=user_id,
                query=query,
                response=response,
                response_id=response_id,
                metadata=metadata,
            )

    def create_ab_test(
        self,
        test_name: str,
        variants: List[Dict[str, Any]],
        description: str = "",
    ) -> ABTest:
        """Create a new A/B test for weight variants."""
        return self.ab_tester.create_test(
            test_name=test_name,
            variants_config=variants,
            description=description,
        )

    def get_optimal_weights_for_document_type(self, document_type: str) -> Dict[str, float]:
        """Get optimal weights for a specific document type from the RL optimizer."""
        return self.rl.get_optimal_weights(document_type)

    def generate_report(self) -> MetaLearningReport:
        """Generate a performance and status report for the Meta Learning Engine."""
        current_weights = self.get_current_weights()
        
        # Calculate average reward
        avg_reward = 0.0
        if self.online.reward_history:
            avg_reward = sum(self.online.reward_history) / len(self.online.reward_history)
            
        # Analyze latest A/B test winner
        ab_winner = None
        tests = self.ab_tester.list_tests()
        if tests:
            latest_test = tests[-1]
            try:
                analysis = self.ab_tester.analyze(latest_test.test_id)
                if analysis.confidence >= 0.95:
                    ab_winner = analysis.winner
            except Exception:
                pass
                
        # Best bandit arm
        bandit_best = self.bandit.best_arm()
        
        # Generate recommendations
        recommendations = []
        if avg_reward < 0.6:
            recommendations.append("Average reward is below threshold (0.6). Weight strategy adjustments recommended.")
        if bandit_best:
            recommendations.append(f"Bandit strategy recommends arm: '{bandit_best}'.")
        if ab_winner:
            recommendations.append(f"A/B testing shows variant '{ab_winner}' is statistically superior. Recommend promoting to production.")
        else:
            recommendations.append("No statistically significant A/B test winner found yet. Continue running current tests.")
            
        return MetaLearningReport(
            current_weights=current_weights,
            weight_history=list(self.weight_history),
            n_signals_processed=self.signals_processed,
            avg_reward=avg_reward,
            ab_test_winner=ab_winner,
            bandit_best_arm=bandit_best,
            recommendations=recommendations,
        )
