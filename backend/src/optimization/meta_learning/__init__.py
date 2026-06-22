"""
AMDI-OS Wave 5: Meta Learning Engine
=====================================

Adaptive weight learning and continuous improvement for AMDI-OS.

Components:
    - MetaLearner          : Main orchestrator
    - OnlineLearner        : Online gradient updates from query logs
    - RLOptimizer          : Reinforcement learning from user feedback
    - FeedbackLoop         : User feedback integration
    - BanditSelector        : Multi-armed bandit for strategy selection
    - ABTester             : A/B testing framework

Mathematical Foundation:
    Gradient ascent:
        w ← w + η · ∇L(w, feedback)

    Multi-armed bandit (UCB1):
        UCB(a) = Q(a) + c · √(log(t) / N(a))

    Contextual bandit:
        P(a | x) = softmax(θᵀ · x)

Author : AMDI-OS Development Team
Version: 1.1.0
"""

from .meta_learner import (
    MetaLearner,
    MetaLearningConfig,
    MetaLearningReport,
)
from .online_learner import (
    OnlineLearner,
    OnlineUpdate,
    LearningSignal,
)
from .rl_optimizer import (
    RLOptimizer,
    RLConfig,
    RewardSignal,
    State,
    Action,
)
from .feedback_loop import (
    FeedbackLoop,
    FeedbackEvent,
    FeedbackType,
    UserRating,
)
from .bandit_selector import (
    BanditSelector,
    BanditConfig,
    BanditAlgorithm,
    Arm,
)
from .ab_tester import (
    ABTester,
    ABTest,
    ABTestResult,
    ABTestVariant,
    ABTestStatus,
)

__all__ = [
    "MetaLearner",
    "MetaLearningConfig",
    "MetaLearningReport",
    "OnlineLearner",
    "OnlineUpdate",
    "LearningSignal",
    "RLOptimizer",
    "RLConfig",
    "RewardSignal",
    "State",
    "Action",
    "FeedbackLoop",
    "FeedbackEvent",
    "FeedbackType",
    "UserRating",
    "BanditSelector",
    "BanditConfig",
    "BanditAlgorithm",
    "Arm",
    "ABTester",
    "ABTest",
    "ABTestResult",
    "ABTestVariant",
    "ABTestStatus",
]

__version__ = "1.1.0"
