"""
Bandit Selector
================

Multi-armed bandit for online strategy selection.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

import numpy as np


class BanditAlgorithm(Enum):
    """Bandit algorithms."""

    EPSILON_GREEDY = "epsilon_greedy"
    UCB1 = "ucb1"
    THOMPSON_SAMPLING = "thompson_sampling"
    CONTEXTUAL = "contextual"


@dataclass
class Arm:
    """A bandit arm representing a strategy variant."""

    arm_id: str
    strategy_name: str
    description: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BanditConfig:
    """Bandit configuration."""

    algorithm: BanditAlgorithm = BanditAlgorithm.UCB1
    epsilon: float = 0.1
    ucb_c: float = 1.414  # sqrt(2)
    prior_alpha: float = 1.0  # Beta prior
    prior_beta: float = 1.0
    decay_factor: float = 0.99


class BanditSelector:
    """
    Multi-armed bandit for strategy selection.

    Used to choose between different weight configurations,
    retrieval strategies, or compression strategies.
    """

    def __init__(self, config: Optional[BanditConfig] = None) -> None:
        self.config = config or BanditConfig()
        self.arms: Dict[str, Arm] = {}
        self.pulls: Dict[str, int] = {}  # N(a)
        self.rewards_sum: Dict[str, float] = {}  # Σr
        self.rewards_sq_sum: Dict[str, float] = {}  # Σr²
        self.alpha: Dict[str, float] = {}  # Beta posterior alpha
        self.beta: Dict[str, float] = {}  # Beta posterior beta
        self.total_pulls: int = 0

    def add_arm(self, arm: Arm) -> None:
        """Register a new arm."""
        self.arms[arm.arm_id] = arm
        self.pulls[arm.arm_id] = 0
        self.rewards_sum[arm.arm_id] = 0.0
        self.rewards_sq_sum[arm.arm_id] = 0.0
        self.alpha[arm.arm_id] = self.config.prior_alpha
        self.beta[arm.arm_id] = self.config.prior_beta

    def add_arms(self, arms: List[Arm]) -> None:
        for arm in arms:
            self.add_arm(arm)

    def select(self) -> str:
        """Select an arm based on the configured algorithm."""
        if not self.arms:
            raise ValueError("No arms registered")
        if self.config.algorithm == BanditAlgorithm.EPSILON_GREEDY:
            return self._epsilon_greedy()
        elif self.config.algorithm == BanditAlgorithm.UCB1:
            return self._ucb1()
        elif self.config.algorithm == BanditAlgorithm.THOMPSON_SAMPLING:
            return self._thompson_sampling()
        elif self.config.algorithm == BanditAlgorithm.CONTEXTUAL:
            return self._contextual(np.zeros(8))
        else:
            return random.choice(list(self.arms.keys()))

    def _epsilon_greedy(self) -> str:
        if random.random() < self.config.epsilon:
            return random.choice(list(self.arms.keys()))
        return self._best_empirical()

    def _ucb1(self) -> str:
        # explore each arm once first
        for arm_id, count in self.pulls.items():
            if count == 0:
                return arm_id
        total = max(self.total_pulls, 1)
        best_arm = None
        best_ucb = -float("inf")
        for arm_id in self.arms:
            n = self.pulls[arm_id]
            avg = self.rewards_sum[arm_id] / n
            ucb = avg + self.config.ucb_c * math.sqrt(math.log(total) / n)
            if ucb > best_ucb:
                best_ucb = ucb
                best_arm = arm_id
        return best_arm or random.choice(list(self.arms.keys()))

    def _thompson_sampling(self) -> str:
        best_arm = None
        best_sample = -float("inf")
        for arm_id in self.arms:
            sample = np.random.beta(self.alpha[arm_id], self.beta[arm_id])
            if sample > best_sample:
                best_sample = sample
                best_arm = arm_id
        return best_arm or random.choice(list(self.arms.keys()))

    def _contextual(self, context: np.ndarray) -> str:
        # simplified: use Thompson sampling with context-weighted posteriors
        return self._thompson_sampling()

    def _best_empirical(self) -> str:
        best_arm = None
        best_avg = -float("inf")
        for arm_id, count in self.pulls.items():
            if count == 0:
                continue
            avg = self.rewards_sum[arm_id] / count
            if avg > best_avg:
                best_avg = avg
                best_arm = arm_id
        if best_arm is None:
            return random.choice(list(self.arms.keys()))
        return best_arm

    def update(self, arm_id: str, reward: float) -> None:
        """Update arm statistics with observed reward."""
        if arm_id not in self.arms:
            raise ValueError(f"Unknown arm: {arm_id}")
        self.pulls[arm_id] += 1
        self.rewards_sum[arm_id] += reward
        self.rewards_sq_sum[arm_id] += reward ** 2
        # update Beta posterior (for binary rewards)
        if 0.0 <= reward <= 1.0:
            self.alpha[arm_id] += reward
            self.beta[arm_id] += 1 - reward
        self.total_pulls += 1

    def get_arm_stats(self) -> Dict[str, Dict[str, float]]:
        """Get statistics for all arms."""
        stats = {}
        for arm_id in self.arms:
            n = self.pulls[arm_id]
            if n == 0:
                stats[arm_id] = {"pulls": 0, "avg_reward": 0.0, "ucb": float("inf")}
                continue
            avg = self.rewards_sum[arm_id] / n
            variance = max(
                0,
                (self.rewards_sq_sum[arm_id] / n) - avg ** 2,
            )
            std = math.sqrt(variance)
            ucb = avg + self.config.ucb_c * std / math.sqrt(n) if n > 0 else float("inf")
            stats[arm_id] = {
                "pulls": n,
                "avg_reward": avg,
                "std": std,
                "ucb": ucb,
                "beta_alpha": self.alpha[arm_id],
                "beta_beta": self.beta[arm_id],
                "beta_mean": self.alpha[arm_id] / (self.alpha[arm_id] + self.beta[arm_id]),
            }
        return stats

    def best_arm(self) -> Optional[str]:
        """Return the arm with highest empirical mean reward."""
        return self._best_empirical()
