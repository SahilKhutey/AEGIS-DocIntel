"""
RL Optimizer
==============

Reinforcement learning for weight optimization.
Uses Q-learning with function approximation.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict, deque
from dataclasses import dataclass, field
from typing import Any, Deque, Dict, List, Optional, Tuple

import numpy as np


@dataclass
class State:
    """RL state: current weight distribution + context."""

    weights: np.ndarray  # weight vector
    document_type: str
    context_features: np.ndarray = field(default_factory=lambda: np.zeros(8))

    def to_key(self) -> tuple:
        # discretize weights for tabular Q-learning
        discrete = tuple(int(w * 10) for w in self.weights)
        return (self.document_type, discrete)

    def __hash__(self):
        return hash(self.to_key())

    def __eq__(self, other):
        return self.to_key() == other.to_key()


@dataclass
class Action:
    """RL action: weight adjustment."""

    engine_index: int
    delta: float  # weight change [-0.1, +0.1]


@dataclass
class RewardSignal:
    """Reward from environment."""

    value: float  # -1 to +1
    components: Dict[str, float] = field(default_factory=dict)
    timestamp: float = 0.0


@dataclass
class RLConfig:
    """RL optimizer configuration."""

    learning_rate: float = 0.1
    discount_factor: float = 0.95
    epsilon: float = 0.1
    epsilon_decay: float = 0.995
    epsilon_min: float = 0.01
    buffer_size: int = 10000
    batch_size: int = 32
    target_update_freq: int = 100
    gamma: float = 0.99


class RLOptimizer:
    """
    Reinforcement learning optimizer for engine weights.

    Uses Q-learning with epsilon-greedy exploration and experience replay.
    """

    ENGINES = [
        "geometry", "frequency", "recurrence", "matrix", "template",
        "semantic", "graph", "topology", "spectral", "tensor",
        "info_physics", "retrieval",
    ]
    N_ENGINES = len(ENGINES)
    ACTION_SPACE = 11  # -5, -4, -3, -2, -1, 0, +1, +2, +3, +4, +5 (×0.01)
    DELTA_MULTIPLIER = 0.01

    def __init__(self, config: Optional[RLConfig] = None) -> None:
        self.config = config or RLConfig()
        # Q-table: state_key → action_index → Q value
        # Note: Fixed lambda to initialize array size to ACTION_SPACE * N_ENGINES
        self.q_table: Dict[tuple, np.ndarray] = defaultdict(
            lambda: np.zeros(self.ACTION_SPACE * self.N_ENGINES)
        )
        # experience replay buffer
        self.replay_buffer: Deque = deque(maxlen=self.config.buffer_size)
        # stats
        self.episode_rewards: List[float] = []
        self.epsilon = self.config.epsilon

    def select_action(self, state: State, training: bool = True) -> Action:
        """Select action using epsilon-greedy policy."""
        if training and random.random() < self.epsilon:
            # explore
            engine_idx = random.randint(0, self.N_ENGINES - 1)
            delta_idx = random.randint(0, self.ACTION_SPACE - 1)
        else:
            # exploit
            state_key = state.to_key()
            q_values = self.q_table[state_key]
            action_idx = int(np.argmax(q_values))
            engine_idx = action_idx // self.ACTION_SPACE
            engine_idx = min(engine_idx, self.N_ENGINES - 1)
            delta_idx = action_idx % self.ACTION_SPACE
        delta = (delta_idx - 5) * self.DELTA_MULTIPLIER
        return Action(engine_index=engine_idx, delta=delta)

    def apply_action(self, state: State, action: Action) -> State:
        """Apply action to state, return new state."""
        new_weights = state.weights.copy()
        new_weights[action.engine_index] += action.delta
        # clip and renormalize
        new_weights = np.clip(new_weights, 0.001, 0.5)
        new_weights = new_weights / new_weights.sum()
        return State(
            weights=new_weights,
            document_type=state.document_type,
            context_features=state.context_features,
        )

    def get_action_index(self, action: Action) -> int:
        """Convert action to integer index."""
        delta_idx = int(action.delta / self.DELTA_MULTIPLIER) + 5
        delta_idx = max(0, min(self.ACTION_SPACE - 1, delta_idx))
        return action.engine_index * self.ACTION_SPACE + delta_idx

    def update(
        self,
        state: State,
        action: Action,
        reward: RewardSignal,
        next_state: State,
        done: bool = False,
    ) -> float:
        """Q-learning update."""
        state_key = state.to_key()
        next_state_key = next_state.to_key()
        action_idx = self.get_action_index(action)
        # current Q
        current_q = self.q_table[state_key][action_idx]
        # target Q
        if done:
            target_q = reward.value
        else:
            target_q = reward.value + self.config.gamma * np.max(
                self.q_table[next_state_key]
            )
        # update
        td_error = target_q - current_q
        self.q_table[state_key][action_idx] += self.config.learning_rate * td_error
        # store in replay buffer
        self.replay_buffer.append(
            (state, action, reward, next_state, done)
        )
        # decay epsilon
        self.epsilon = max(
            self.config.epsilon_min,
            self.epsilon * self.config.epsilon_decay,
        )
        return td_error

    def replay(self) -> float:
        """Experience replay: sample batch and update Q-values."""
        if len(self.replay_buffer) < self.config.batch_size:
            return 0.0
        batch = random.sample(
            list(self.replay_buffer),
            min(self.config.batch_size, len(self.replay_buffer)),
        )
        total_td = 0.0
        for state, action, reward, next_state, done in batch:
            td = self.update(state, action, reward, next_state, done)
            total_td += abs(td)
        return total_td / len(batch)

    def get_optimal_weights(self, document_type: str) -> Dict[str, float]:
        """Get the best weights for a document type."""
        state = State(
            weights=np.ones(self.N_ENGINES) / self.N_ENGINES,
            document_type=document_type,
        )
        state_key = state.to_key()
        if state_key in self.q_table and np.any(self.q_table[state_key]):
            # derive weights from Q-values
            q = self.q_table[state_key]
            best_action_idx = int(np.argmax(q))
            best_engine_idx = best_action_idx // self.ACTION_SPACE
            # boost that engine
            weights = np.ones(self.N_ENGINES) / self.N_ENGINES
            weights[best_engine_idx] *= 1.5
            weights = weights / weights.sum()
        else:
            weights = np.ones(self.N_ENGINES) / self.N_ENGINES
        return {
            self.ENGINES[i]: float(weights[i])
            for i in range(self.N_ENGINES)
        }

    def train_episode(
        self,
        signals: List[Tuple[State, RewardSignal]],
    ) -> Dict[str, float]:
        """Train on a batch of state-reward pairs."""
        rewards = []
        for state, reward in signals:
            # get current best action
            action = self.select_action(state, training=True)
            next_state = self.apply_action(state, action)
            td = self.update(state, action, reward, next_state, done=True)
            rewards.append(reward.value)
        # replay
        replay_td = self.replay()
        self.episode_rewards.append(float(np.mean(rewards)))
        return {
            "mean_reward": float(np.mean(rewards)),
            "replay_td_error": replay_td,
            "epsilon": self.epsilon,
        }
