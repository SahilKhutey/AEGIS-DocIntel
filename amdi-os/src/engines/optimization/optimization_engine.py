'''
AEGIS-AMDI-OS — Optimization Engine
====================================
Implements computational cost models, multi-objective optimization, and budget constraints.
Formulates the global objective function J = α·TC + β·L + γ·MC + δ·ER
'''
from __future__ import annotations

import time
import logging
from dataclasses import dataclass
from typing import List, Dict, Tuple, Any

import numpy as np

logger = logging.getLogger('amdi.engines.optimization')


@dataclass
class OptimizationResult:
    selected_indices: List[int]
    total_value: float
    total_tokens: int
    solver_name: str
    elapsed_ms: float


@dataclass
class OptimizationWeights:
    '''Weights for context budget optimization.'''
    token_weight: float       # α
    memory_weight: float      # β
    latency_weight: float     # γ


class OptimizationEngine:
    '''
    Optimization Engine.
    Minimizes J = α*T + β*M + γ*L subject to system constraints.
    '''

    def __init__(
        self,
        alpha: float = 0.4,   # Token Cost coefficient
        beta: float = 0.3,    # Latency coefficient
        gamma: float = 0.2,   # Memory Cost coefficient
        delta: float = 0.1,   # Error Rate coefficient
        default_weights: OptimizationWeights | None = None,
    ) -> None:
        self.alpha = alpha
        self.beta = beta
        self.gamma = gamma
        self.delta = delta
        self.weights = default_weights or OptimizationWeights(0.5, 0.25, 0.25)

    # ------------------------------------------------------------------
    # §1. Global Cost Function J
    # ------------------------------------------------------------------

    def calculate_cost(
        self,
        token_cost: float,
        latency_ms: float,
        memory_mb: float,
        error_rate: float,
    ) -> float:
        '''J = α·TC + β·L + γ·MC + δ·ER'''
        return (
            self.alpha * token_cost +
            self.beta * (latency_ms / 1000.0) +
            self.gamma * (memory_mb / 1024.0) +
            self.delta * error_rate
        )

    def objective_function(self, tokens: float, memory: float, latency: float) -> float:
        '''
        Objective J = α*T + β*M + γ*L
        All inputs should be normalized to range [0, 1].
        '''
        return (
            self.weights.token_weight * tokens +
            self.weights.memory_weight * memory +
            self.weights.latency_weight * latency
        )

    # ------------------------------------------------------------------
    # §2. Context & Resource Optimization (MCDA / Knapsack)
    # ------------------------------------------------------------------

    def optimize_context(
        self, candidates: list[dict], max_tokens: int, max_latency_s: float, max_memory_mb: float
    ) -> list[dict]:
        '''
        Greedy constraint optimization.
        Sorts candidates by value/cost ratio and adds them until budget constraints are hit.
        '''
        sorted_candidates = sorted(
            candidates,
            key=lambda c: c.get('value', 0.5) / max(1, c.get('tokens', 100)),
            reverse=True
        )

        selected = []
        total_tokens = 0
        total_latency = 0.0
        total_memory = 0.0

        for c in sorted_candidates:
            c_tokens = c.get('tokens', 100)
            c_latency = c.get('latency', 0.05)
            c_memory = c.get('memory', 1.0)
            
            # Check constraints
            if total_tokens + c_tokens > max_tokens:
                continue
            if total_latency + c_latency > max_latency_s:
                continue
            if total_memory + c_memory > max_memory_mb:
                continue
                
            selected.append(c)
            total_tokens += c_tokens
            total_latency += c_latency
            total_memory += c_memory

        return selected

    def solve_greedy_knapsack(
        self,
        scores: List[float],
        token_counts: List[int],
        max_token_budget: int,
    ) -> OptimizationResult:
        '''
        Greedy selection based on value/weight ratio (relevance score / token count).
        Theorem §3: 1/2-approximation for 0/1 knapsack.
        '''
        t0 = time.perf_counter()
        n = len(scores)
        if n == 0 or max_token_budget <= 0:
            return OptimizationResult([], 0.0, 0, 'greedy', 0.0)

        ratios = []
        for i in range(n):
            tc = max(1, token_counts[i])
            ratios.append((scores[i] / tc, i))

        ratios.sort(key=lambda x: x[0], reverse=True)

        selected_indices = []
        total_tokens = 0
        total_value = 0.0

        for ratio, idx in ratios:
            tokens = token_counts[idx]
            if total_tokens + tokens <= max_token_budget:
                selected_indices.append(idx)
                total_tokens += tokens
                total_value += scores[idx]

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return OptimizationResult(
            selected_indices=selected_indices,
            total_value=total_value,
            total_tokens=total_tokens,
            solver_name='greedy_knapsack',
            elapsed_ms=elapsed_ms,
        )

    def solve_dp_knapsack(
        self,
        scores: List[float],
        token_counts: List[int],
        max_token_budget: int,
    ) -> OptimizationResult:
        '''
        Dynamic Programming Knapsack solver:
        State: V(i, q) = max value with element i and remaining budget q
        Transition: V(i, q) = max(V(i-1, q), v_i + V(i-1, q - w_i))
        '''
        t0 = time.perf_counter()
        n = len(scores)
        if n == 0 or max_token_budget <= 0:
            return OptimizationResult([], 0.0, 0, 'dp', 0.0)

        W = max_token_budget
        dp = np.zeros((n + 1, W + 1), dtype=np.float32)

        for i in range(1, n + 1):
            val = scores[i - 1]
            wt = token_counts[i - 1]
            for w in range(W + 1):
                if wt <= w:
                    dp[i, w] = max(dp[i - 1, w], dp[i - 1, w - wt] + val)
                else:
                    dp[i, w] = dp[i - 1, w]

        selected_indices = []
        w = W
        for i in range(n, 0, -1):
            if dp[i, w] != dp[i - 1, w]:
                selected_indices.append(i - 1)
                w -= token_counts[i - 1]

        selected_indices.reverse()
        total_value = float(dp[n, W])
        total_tokens = W - w

        elapsed_ms = (time.perf_counter() - t0) * 1000
        return OptimizationResult(
            selected_indices=selected_indices,
            total_value=total_value,
            total_tokens=total_tokens,
            solver_name='dp_knapsack',
            elapsed_ms=elapsed_ms,
        )

    # ------------------------------------------------------------------
    # §3. Pareto front calculations
    # ------------------------------------------------------------------

    def pareto_front(self, candidates: list[dict]) -> list[dict]:
        '''
        Finds the Pareto-efficient subset of candidates.
        Optimizes for maximizing accuracy value while minimizing token costs.
        '''
        pareto = []
        for i, c_i in enumerate(candidates):
            dominated = False
            val_i = c_i.get('value', 0.0)
            cost_i = c_i.get('tokens', 0.0)
            
            for j, c_j in enumerate(candidates):
                if i == j:
                    continue
                val_j = c_j.get('value', 0.0)
                cost_j = c_j.get('tokens', 0.0)
                
                # c_j dominates c_i if it has higher value and lower cost
                if val_j >= val_i and cost_j <= cost_i:
                    if val_j > val_i or cost_j < cost_i:
                        dominated = True
                        break
            if not dominated:
                pareto.append(c_i)
        return pareto

    # ------------------------------------------------------------------
    # §4. Linear Programming Weight Mixing Relaxation
    # ------------------------------------------------------------------

    @staticmethod
    def optimize_weights_mixing(
        scores_matrix: np.ndarray,
        target_relevance: np.ndarray,
        lr: float = 0.01,
        iterations: int = 200,
    ) -> np.ndarray:
        '''
        Finds optimal layer weights W satisfying Σ W_i = 1 using gradient descent.
        scores_matrix: shape (N, 9) representing 9 layers' relevance scores per element.
        target_relevance: shape (N,) representing target score distributions.
        '''
        N, num_layers = scores_matrix.shape
        w = np.ones(num_layers, dtype=np.float32) / num_layers

        for _ in range(iterations):
            pred = np.dot(scores_matrix, w)
            error = pred - target_relevance
            
            grad = 2.0 * np.dot(scores_matrix.T, error) / N
            w -= lr * grad
            
            w = np.maximum(0.0, w)
            s = np.sum(w)
            if s > 0.0:
                w = w / s
            else:
                w = np.ones(num_layers, dtype=np.float32) / num_layers

        return w
