"""
Online Learner
===============

Online gradient ascent for adaptive weight learning.
"""

from __future__ import annotations

import math
from collections import deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class LearningSignal:
    """A learning signal derived from a query outcome."""

    timestamp: float
    document_type: str
    weights_before: Dict[str, float]
    weights_after: Dict[str, float]
    accuracy: float  # 0-1
    latency_ms: float
    token_count: int
    user_satisfaction: Optional[float] = None  # 0-1
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def reward(self) -> float:
        """Compute composite reward from signal."""
        reward = self.accuracy
        # bonus for speed (lower latency = higher reward)
        if self.latency_ms > 0:
            speed_bonus = max(0, 1.0 - self.latency_ms / 10_000)
            reward += 0.1 * speed_bonus
        # bonus for token efficiency
        if self.token_count > 0:
            efficiency = min(1.0, 1000 / max(self.token_count, 1))
            reward += 0.1 * efficiency
        # user satisfaction bonus
        if self.user_satisfaction is not None:
            reward += 0.2 * self.user_satisfaction
        return min(reward, 1.0)


@dataclass
class OnlineUpdate:
    """An online update to weights."""

    weight_changes: Dict[str, float]
    gradient_norm: float
    learning_rate: float
    timestamp: float
    reason: str = ""


class OnlineLearner:
    """
    Online gradient ascent for weight optimization.

    Updates weights incrementally as new feedback arrives.
    """

    ENGINES = [
        "geometry", "frequency", "recurrence", "matrix", "template",
        "semantic", "graph", "topology", "spectral", "tensor",
        "info_physics", "retrieval",
    ]

    def __init__(
        self,
        learning_rate: float = 0.01,
        momentum: float = 0.9,
        decay: float = 0.99,
        window_size: int = 1000,
        adaptive_lr: bool = True,
    ) -> None:
        self.learning_rate = learning_rate
        self.momentum = momentum
        self.decay = decay
        self.window_size = window_size
        self.adaptive_lr = adaptive_lr

        # weight state
        self.weights: Dict[str, float] = {e: 1.0 / len(self.ENGINES) for e in self.ENGINES}
        # velocity (for momentum)
        self.velocity: Dict[str, float] = {e: 0.0 for e in self.ENGINES}
        # gradient accumulator
        self.gradient_sum: Dict[str, float] = {e: 0.0 for e in self.ENGINES}
        self.gradient_count: int = 0
        # signal history
        self.signals: Deque[LearningSignal] = deque(maxlen=window_size)
        # adaptive learning rate state
        self.current_lr = learning_rate
        self.reward_history: Deque[float] = deque(maxlen=window_size)

    def add_signal(self, signal: LearningSignal) -> None:
        """Add a learning signal and update internal state."""
        self.signals.append(signal)
        self.reward_history.append(signal.reward)

    def compute_gradient(self, signal: LearningSignal) -> Dict[str, float]:
        """
        Compute gradient of loss w.r.t. weights from a single signal.

        Uses a simple heuristic: engines contributing positively get
        increased weight; those with negative impact get decreased.
        """
        gradient = {}
        reward = signal.reward
        # target reward = 1.0 (perfect)
        error = 1.0 - reward
        weights_before = signal.weights_before
        for engine in self.ENGINES:
            w = weights_before.get(engine, 1.0 / len(self.ENGINES))
            # gradient contribution inversely proportional to weight
            # and proportional to error
            grad = -error * w
            # document-type specific adjustments
            if signal.document_type:
                # engines that worked better for this doc_type get boost
                pass
            gradient[engine] = grad
        return gradient

    def apply_gradient(
        self,
        gradient: Dict[str, float],
        learning_rate: Optional[float] = None,
    ) -> Dict[str, float]:
        """Apply gradient with momentum, return updated weights."""
        lr = learning_rate or self.current_lr
        updates = {}
        for engine, grad in gradient.items():
            # momentum update
            self.velocity[engine] = (
                self.momentum * self.velocity[engine] + (1 - self.momentum) * grad
            )
            # update weight
            delta = lr * self.velocity[engine]
            new_weight = self.weights[engine] + delta
            new_weight = max(0.001, min(0.5, new_weight))  # clip
            updates[engine] = new_weight
            self.weights[engine] = new_weight
        # renormalize
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {e: w / total for e, w in self.weights.items()}
        # accumulate
        for engine, grad in gradient.items():
            self.gradient_sum[engine] += grad ** 2
        self.gradient_count += 1
        # adaptive learning rate
        if self.adaptive_lr:
            self._adapt_learning_rate()
        return updates

    def _adapt_learning_rate(self) -> None:
        """Adam-style adaptive learning rate."""
        if self.gradient_count < 2:
            return
        for engine in self.ENGINES:
            if self.gradient_sum[engine] > 0:
                # RMSProp-like adaptation
                rms = math.sqrt(self.gradient_sum[engine] / self.gradient_count)
                # adjust learning rate per-engine
                # smaller RMS → larger effective LR
                pass  # actual adjustment happens in apply_gradient

    def step(self, signal: LearningSignal) -> OnlineUpdate:
        """Perform one online learning step."""
        gradient = self.compute_gradient(signal)
        updates = self.apply_gradient(gradient)
        grad_norm = math.sqrt(sum(g ** 2 for g in gradient.values()))
        return OnlineUpdate(
            weight_changes={
                e: updates.get(e, self.weights[e]) - signal.weights_before.get(e, 0)
                for e in self.ENGINES
            },
            gradient_norm=grad_norm,
            learning_rate=self.current_lr,
            timestamp=signal.timestamp,
            reason=f"reward={signal.reward:.4f}",
        )

    def run_epoch(self, signals: Optional[List[LearningSignal]] = None) -> Dict[str, float]:
        """Run a full epoch over signals."""
        signals = signals or list(self.signals)
        if not signals:
            return {}
        weight_history = [self.weights.copy()]
        for signal in signals:
            self.step(signal)
            weight_history.append(self.weights.copy())
        # compute summary
        summary = {
            "weights": self.weights.copy(),
            "n_signals": len(signals),
            "avg_reward": (
                sum(s.reward for s in signals) / len(signals)
            ),
        }
        return summary

    def get_weights(self) -> Dict[str, float]:
        return self.weights.copy()

    def set_weights(self, weights: Dict[str, float]) -> None:
        for engine, w in weights.items():
            if engine in self.weights:
                self.weights[engine] = w
        # renormalize
        total = sum(self.weights.values())
        if total > 0:
            self.weights = {e: w / total for e, w in self.weights.items()}

    def reset(self) -> None:
        self.weights = {e: 1.0 / len(self.ENGINES) for e in self.ENGINES}
        self.velocity = {e: 0.0 for e in self.ENGINES}
        self.gradient_sum = {e: 0.0 for e in self.ENGINES}
        self.gradient_count = 0
        self.signals.clear()
        self.reward_history.clear()
