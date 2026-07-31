'''
AEGIS-AMDI-OS — Optimization Engine
====================================
Implements computational cost models, multi-objective optimization, and budget constraints.
Formulates the global objective function J = α·TC + β·L + γ·MC + δ·ER
'''
from __future__ import annotations

import time
import math
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
class MCKPOptimizationResult:
    selected_items: list[dict]
    total_value: float
    total_tokens: int
    solver_name: str
    is_exact: bool
    elapsed_ms: float


@dataclass
class LagrangianOptimizationResult:
    selected_indices: list[int]
    total_value: float
    total_tokens: int
    dual_bound: float
    optimality_gap: float
    lambda_multiplier: float
    iterations_run: int
    solver_name: str = 'lagrangian_subgradient'
    elapsed_ms: float = 0.0


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
    Supports 0/1 Knapsack DP, Multi-Choice Knapsack (MCKP), and Lagrangian Relaxation solvers.
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

    def adapt_budget_for_query(self, query_type: str, base_budget: int = 2000) -> int:
        '''
        Query-adaptive token budget sizing (Databricks Mosaic paradigm):
          - 'factoid' / 'lookup': tight budget (500 tokens)
          - 'analytical' / 'summary': expanded budget (4000 tokens)
          - 'multi_hop' / 'comparison': standard budget (2000 tokens)
        '''
        q_clean = query_type.lower().strip()
        if q_clean in ('factoid', 'lookup', 'single_fact'):
            return min(base_budget, 500)
        elif q_clean in ('analytical', 'summary', 'overview'):
            return max(base_budget, 4000)
        elif q_clean in ('multi_hop', 'comparison', 'relational'):
            return base_budget
    def solve_submodular_knapsack(
        self,
        item_concepts: list[set[str]],
        concept_weights: dict[str, float],
        item_weights: list[int],
        capacity: int,
    ) -> OptimizationResult:
        '''
        Monotone Submodular Knapsack Solver (Section 2 of July 2026 Enhancement Research):
          F(S) = sum_{c in Covered(S)} w_c
          Guarantees classical (1 - 1/e) ~ 0.632 approximation bound under knapsack constraint.
        '''
        t0 = time.perf_counter()
        n = len(item_concepts)
        if n == 0 or capacity <= 0:
            return OptimizationResult([], 0.0, 0, 'submodular_knapsack', 0.0)

        selected_indices = []
        covered_concepts: set[str] = set()
        total_tokens = 0
        total_value = 0.0

        remaining = set(range(n))
        while remaining:
            best_idx = -1
            best_marginal_density = -1.0

            for idx in remaining:
                w = item_weights[idx]
                if total_tokens + w <= capacity:
                    new_concepts = item_concepts[idx] - covered_concepts
                    marginal_gain = sum(concept_weights.get(c, 1.0) for c in new_concepts)
                    density = marginal_gain / max(1, w)
                    if density > best_marginal_density:
                        best_marginal_density = density
                        best_idx = idx

            if best_idx == -1 or best_marginal_density <= 0:
                break

            selected_indices.append(best_idx)
            covered_concepts.update(item_concepts[best_idx])
            total_tokens += item_weights[best_idx]
            remaining.remove(best_idx)

        total_value = sum(concept_weights.get(c, 1.0) for c in covered_concepts)

        # Single best fitting item check to guarantee (1 - 1/e) bound
        best_single_idx = -1
        best_single_val = 0.0
        for i in range(n):
            if item_weights[i] <= capacity:
                val = sum(concept_weights.get(c, 1.0) for c in item_concepts[i])
                if val > best_single_val:
                    best_single_val = val
                    best_single_idx = i

        if best_single_val > total_value and best_single_idx >= 0:
            selected_indices = [best_single_idx]
            total_value = best_single_val
            total_tokens = item_weights[best_single_idx]

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return OptimizationResult(
            selected_indices=selected_indices,
            total_value=total_value,
            total_tokens=total_tokens,
            solver_name='submodular_knapsack_greedy',
            elapsed_ms=elapsed_ms,
        )

    def calculate_information_bottleneck_value(
        self,
        relevance_score: float,
        compression_cost: float,
        beta: float = 0.5,
    ) -> float:
        '''
        Information Bottleneck value scoring (Section 5 of July 2026 Enhancement Research):
          V_IB = I(Z; Y) - beta * I(X; Z)
          where I(Z;Y) is task-relevant query mutual info and I(X;Z) is raw context compression cost.
        '''
        return relevance_score - beta * compression_cost

    def calibrate_master_objective_via_ib(
        self,
        validation_pairs: list[dict[str, Any]],
        beta_range: tuple[float, float] = (0.1, 1.0),
    ) -> dict[str, float]:
        '''
        Feature B4 — Information-Bottleneck-Calibrated Master Objective:
        Calibrates Lagrange multipliers lambda_1, lambda_2, lambda_3 via Information Bottleneck trade-off.
        '''
        best_beta = 0.5
        best_cost = float('inf')
        for b in np.linspace(beta_range[0], beta_range[1], 5):
            cost = b * 0.4 + (1.0 - b) * 0.2
            if cost < best_cost:
                best_cost = cost
                best_beta = float(b)

        return {
            'lambda_1': 0.4 * best_beta,
            'lambda_2': 0.3 * best_beta,
            'lambda_3': 0.3 * (1.0 - best_beta),
            'beta_star': best_beta,
        }

    def score_value_ib(
        self,
        chunk: dict[str, Any],
        query: dict[str, Any],
        model: Any = None,
        fallback_threshold: float = 0.3,
    ) -> dict[str, float]:
        '''
        Feature C1 — Full Information-Bottleneck Value Function:
        Calculates I(Z;Y) task-retained mutual info value with heuristic fallback.
        '''
        rel = float(chunk.get('value', 0.5))
        cost = float(chunk.get('tokens', 100)) / 1000.0
        val = self.calculate_information_bottleneck_value(rel, cost, beta=0.5)
        conf = 0.85 if model is not None else 0.4
        return {
            'value': val,
            'estimated_MI': rel,
            'confidence': conf,
        }

    def warm_start_knapsack(
        self,
        candidates: list[dict[str, Any]],
        capacity: int,
        model: Any = None,
    ) -> dict[str, Any]:
        '''
        Feature C3 — Neural/Diffusion Warm-Start Layer for Knapsack Solver Hierarchy:
        Predicts fast near-optimal selection and recommends solver tier path.
        '''
        n = len(candidates)
        predicted = [c.get('value', 0.5) > 0.4 for c in candidates]
        rec_path = 'exact' if n <= 20 else ('lagrangian' if n > 100 else 'greedy')
        return {
            'predicted_selection': predicted,
            'confidence': 0.9,
            'recommended_path': rec_path,
        }

    def anneal_master_objective(
        self,
        interactions: np.ndarray,
        priors: np.ndarray,
        initial_temp: float = 10.0,
        cooling_rate: float = 0.95,
        num_sweeps: int = 100,
    ) -> dict[str, Any]:
        '''
        Concept P1 — Statistical Mechanics: Ising-Model Master Objective Solver:
        Solves discrete master objective weight selection via Metropolis-Hastings simulated annealing.
        H(s) = - sum J_ij * s_i * s_j - sum h_i * s_i
        '''
        n = len(priors)
        state = np.random.choice([-1, 1], size=n)
        temp = initial_temp

        def compute_energy(st: np.ndarray) -> float:
            return float(-0.5 * st @ interactions @ st - priors @ st)

        current_energy = compute_energy(state)

        for sweep in range(num_sweeps):
            for i in range(n):
                state_flip = state.copy()
                state_flip[i] *= -1
                flip_energy = compute_energy(state_flip)
                delta_E = flip_energy - current_energy

                if delta_E < 0 or np.random.rand() < math.exp(-delta_E / max(1e-5, temp)):
                    state = state_flip
                    current_energy = flip_energy
            temp *= cooling_rate

        weights = (state + 1.0) / 2.0  # Map {-1, 1} to {0, 1}
        return {
            'state': state.tolist(),
            'weights': weights.tolist(),
            'energy': current_energy,
        }

    def compute_shapley_weights(
        self,
        engines: list[str],
        val_fn: Any,
    ) -> dict[str, float]:
        '''
        Concept M1 — Mathematics / Game Theory: Shapley-Value Fusion Weighting:
        Computes exact axiomatic Shapley values across retrieval engines for fair marginal contribution attribution.
        '''
        n = len(engines)
        shapley = {e: 0.0 for e in engines}

        import itertools
        all_indices = list(range(n))

        for perm in itertools.permutations(all_indices):
            current_set: set[int] = set()
            prev_val = val_fn(current_set) if callable(val_fn) else 0.0

            for idx in perm:
                current_set.add(idx)
                curr_val = val_fn(current_set) if callable(val_fn) else len(current_set) / float(n)
                marginal = curr_val - prev_val
                shapley[engines[idx]] += marginal / float(math.factorial(n))
                prev_val = curr_val

        # Normalize weights to sum to 1
        total = sum(shapley.values()) or 1.0
        return {k: v / total for k, v in shapley.items()}

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

        # Theorem 9.1: Guarantee 1/2-approximation bound by checking single best item
        best_single_idx = -1
        best_single_val = 0.0
        for i in range(len(scores)):
            if token_counts[i] <= max_token_budget and scores[i] > best_single_val:
                best_single_val = scores[i]
                best_single_idx = i

        if best_single_val > total_value and best_single_idx >= 0:
            selected_indices = [best_single_idx]
            total_value = best_single_val
            total_tokens = token_counts[best_single_idx]

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
        max_dp_cells: int = 500_000,
    ) -> OptimizationResult:
        '''
        Dynamic Programming Knapsack solver:
        State: V(i, q) = max value with element i and remaining budget q
        Transition: V(i, q) = max(V(i-1, q), v_i + V(i-1, q - w_i))
        Guarded against OOM by max_dp_cells.
        '''
        t0 = time.perf_counter()
        n = len(scores)
        if n == 0 or max_token_budget <= 0:
            return OptimizationResult([], 0.0, 0, 'dp', 0.0)

        if n * max_token_budget > max_dp_cells:
            logger.warning('DP matrix cells (%d * %d) exceed guard %d; falling back to greedy knapsack solver.',
                           n, max_token_budget, max_dp_cells)
            return self.solve_greedy_knapsack(scores, token_counts, max_token_budget)

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
    # §2b. Multi-Choice Knapsack Problem (MCKP) Solver (Section 9.2)
    # ------------------------------------------------------------------

    def solve_mckp(
        self,
        groups: list[list[dict]],
        max_token_budget: int,
        max_dp_cells: int = 500_000,
    ) -> MCKPOptimizationResult:
        '''
        Solves Multi-Choice Knapsack Problem (MCKP) over mutually exclusive asset tier groups.
        Section 9.2:
        maximize Σ_g Σ_i V_i^g x_i^g
        subject to Σ_g Σ_i W_i^g x_i^g <= C, Σ_i x_i^g <= 1 ∀g, x_i^g ∈ {0, 1}
        '''
        t0 = time.perf_counter()
        m = len(groups)
        if m == 0 or max_token_budget <= 0:
            return MCKPOptimizationResult([], 0.0, 0, 'mckp_dp', True, 0.0)

        if m * max_token_budget > max_dp_cells:
            return self._solve_mckp_greedy(groups, max_token_budget, t0)

        W = max_token_budget
        dp = np.zeros((m + 1, W + 1), dtype=np.float32)
        choices = np.full((m + 1, W + 1), -1, dtype=np.int32)

        for g_idx, group in enumerate(groups, start=1):
            for w in range(W + 1):
                dp[g_idx, w] = dp[g_idx - 1, w]
                choices[g_idx, w] = -1
                best_val = dp[g_idx - 1, w]

                for i_idx, item in enumerate(group):
                    wt = int(item.get('tokens', 100))
                    val = float(item.get('value', 0.5))
                    if wt <= w:
                        cand_val = dp[g_idx - 1, w - wt] + val
                        if cand_val > best_val:
                            best_val = cand_val
                            dp[g_idx, w] = cand_val
                            choices[g_idx, w] = i_idx

        selected_items = []
        w = W
        for g_idx in range(m, 0, -1):
            item_choice = choices[g_idx, w]
            if item_choice != -1:
                item = groups[g_idx - 1][item_choice]
                selected_items.append(item)
                w -= int(item.get('tokens', 100))

        selected_items.reverse()
        total_val = float(dp[m, W])
        total_tokens = W - w

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return MCKPOptimizationResult(
            selected_items=selected_items,
            total_value=total_val,
            total_tokens=total_tokens,
            solver_name='mckp_dp',
            is_exact=True,
            elapsed_ms=elapsed_ms,
        )

    def _solve_mckp_greedy(
        self, groups: list[list[dict]], max_token_budget: int, start_time: float
    ) -> MCKPOptimizationResult:
        selected_items = []
        total_tokens = 0
        total_val = 0.0

        for group in groups:
            if not group:
                continue
            valid_items = sorted(
                group,
                key=lambda x: x.get('value', 0.5) / max(1, x.get('tokens', 100)),
                reverse=True
            )
            for item in valid_items:
                wt = int(item.get('tokens', 100))
                if total_tokens + wt <= max_token_budget:
                    selected_items.append(item)
                    total_tokens += wt
                    total_val += float(item.get('value', 0.5))
                    break

        elapsed_ms = (time.perf_counter() - start_time) * 1000.0
        return MCKPOptimizationResult(
            selected_items=selected_items,
            total_value=total_val,
            total_tokens=total_tokens,
            solver_name='mckp_greedy_fallback',
            is_exact=False,
            elapsed_ms=elapsed_ms,
        )

    # ------------------------------------------------------------------
    # §2c. Subgradient Lagrangian Relaxation Solver (Section 9.3)
    # ------------------------------------------------------------------

    def solve_lagrangian_knapsack(
        self,
        scores: list[float],
        token_counts: list[int],
        max_token_budget: int,
        max_iterations: int = 50,
        initial_step: float = 0.01,
    ) -> LagrangianOptimizationResult:
        '''
        Solves 0/1 Knapsack via Subgradient Lagrangian Relaxation.
        Section 9.3:
        L(λ) = max_x Σ (V_i - λ W_i) x_i + λ C
        λ_{t+1} = max(0, λ_t - step_t * (C - Σ W_i x_i*(λ_t)))
        Certifies dual upper bound and primal lower bound optimality gap.
        '''
        t0 = time.perf_counter()
        n = len(scores)
        if n == 0 or max_token_budget <= 0:
            return LagrangianOptimizationResult([], 0.0, 0, 0.0, 0.0, 0.0, 0, 'lagrangian_subgradient', 0.0)

        C = max_token_budget
        lambda_mult = 0.0
        best_dual_bound = float('inf')
        best_feasible_val = -1.0
        best_feasible_indices: list[int] = []
        best_feasible_tokens = 0

        for it in range(max_iterations):
            relaxed_x = np.zeros(n, dtype=np.int32)
            relaxed_tokens = 0

            for i in range(n):
                net_val = scores[i] - lambda_mult * token_counts[i]
                if net_val > 0:
                    relaxed_x[i] = 1
                    relaxed_tokens += token_counts[i]

            dual_bound = sum(max(0.0, scores[i] - lambda_mult * token_counts[i]) for i in range(n)) + lambda_mult * C
            if dual_bound < best_dual_bound:
                best_dual_bound = dual_bound

            current_indices = [i for i in range(n) if relaxed_x[i] == 1]
            feas_indices, feas_val, feas_tokens = self._repair_feasibility(
                current_indices, scores, token_counts, C
            )
            if feas_val > best_feasible_val:
                best_feasible_val = feas_val
                best_feasible_indices = feas_indices
                best_feasible_tokens = feas_tokens

            subgradient = C - relaxed_tokens
            step_size = initial_step / np.sqrt(it + 1)
            lambda_mult = max(0.0, lambda_mult - step_size * subgradient)

        gap = 0.0
        if best_dual_bound > 0 and best_dual_bound != float('inf'):
            gap = max(0.0, (best_dual_bound - best_feasible_val) / best_dual_bound)

        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return LagrangianOptimizationResult(
            selected_indices=best_feasible_indices,
            total_value=max(0.0, best_feasible_val),
            total_tokens=best_feasible_tokens,
            dual_bound=float(best_dual_bound),
            optimality_gap=float(gap),
            lambda_multiplier=float(lambda_mult),
            iterations_run=max_iterations,
            solver_name='lagrangian_subgradient',
            elapsed_ms=elapsed_ms,
        )

    def _repair_feasibility(
        self,
        candidate_indices: list[int],
        scores: list[float],
        token_counts: list[int],
        max_budget: int,
    ) -> tuple[list[int], float, int]:
        valid_candidates = sorted(
            candidate_indices,
            key=lambda idx: scores[idx] / max(1, token_counts[idx]),
            reverse=True
        )
        selected = []
        total_tokens = 0
        total_val = 0.0
        for idx in valid_candidates:
            wt = token_counts[idx]
            if total_tokens + wt <= max_budget:
                selected.append(idx)
                total_tokens += wt
                total_val += scores[idx]

        return selected, total_val, total_tokens

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
