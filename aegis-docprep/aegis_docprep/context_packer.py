"""
aegis-docprep — Submodular Knapsack Context Packer
==================================================
Formulates context packing as a submodular facility-location coverage optimization
problem under strict token budget constraints.

Provides provable (1 - 1/e)/2 ~= 0.316 approximation guarantee for submodular greedy maximization.

Example usage:
--------------
>>> from aegis_docprep.context_packer import SubmodularKnapsackPacker, ContextChunk
>>> chunks = [
...     ContextChunk(chunk_id="c1", text="Revenue grew 12% YoY.", relevance_score=0.9, token_cost=8),
...     ContextChunk(chunk_id="c2", text="Lunch menu changed.", relevance_score=0.1, token_cost=8),
...     ContextChunk(chunk_id="c3", text="Operating margin expanded.", relevance_score=0.85, token_cost=8),
... ]
>>> result = SubmodularKnapsackPacker().pack_context(chunks, max_budget=16)
>>> [c.chunk_id for c in result.selected_chunks]
['c1', 'c3']
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import List, Optional
import numpy as np


def validate_packing_inputs(
    alpha: float,
    beta: float,
    budget: int,
    embeddings: np.ndarray,
    costs: list[int],
) -> None:
    """
    Mathematical boundary validation for submodular context packing:
    - alpha, beta in [0, inf) and finite
    - budget in [0, inf) integer
    - costs in [1, inf) positive integers
    - embeddings 2D finite numpy array
    """
    if isinstance(alpha, bool) or not math.isfinite(alpha) or alpha < 0:
        raise ValueError("alpha must be finite and non-negative")
    if isinstance(beta, bool) or not math.isfinite(beta) or beta < 0:
        raise ValueError("beta must be finite and non-negative")
    if not isinstance(budget, int) or isinstance(budget, bool) or budget < 0:
        raise ValueError("budget must be a non-negative integer")
    if embeddings.ndim != 2:
        raise ValueError("Embeddings must be a two-dimensional array")
    if len(costs) != len(embeddings):
        raise ValueError("Each item must have one cost")
    if any(
        not isinstance(cost, int) or isinstance(cost, bool) or cost <= 0
        for cost in costs
    ):
        raise ValueError("All item costs must be positive integers")
    if not np.isfinite(embeddings).all():
        raise ValueError("Embeddings must contain only finite values")


def calculate_available_context_budget(
    context_window: int,
    instructions_tokens: int,
    query_tokens: int,
    reserved_output_tokens: int,
    overhead_tokens: int = 0,
) -> int:
    """
    Computes available context budget B under hard model context limit:
      B = W - T_instructions - T_query - T_reserved_output - T_overhead
    """
    if context_window <= 0 or isinstance(context_window, bool):
        raise ValueError("context_window must be a positive integer")
    for name, val in [
        ("instructions_tokens", instructions_tokens),
        ("query_tokens", query_tokens),
        ("reserved_output_tokens", reserved_output_tokens),
        ("overhead_tokens", overhead_tokens),
    ]:
        if not isinstance(val, int) or isinstance(val, bool) or val < 0:
            raise ValueError(f"{name} must be a non-negative integer")

    budget = context_window - instructions_tokens - query_tokens - reserved_output_tokens - overhead_tokens
    return max(0, budget)


@dataclass
class ContextChunk:
    chunk_id: str
    text: str
    relevance_score: float = 0.0
    token_cost: int = 1
    embedding: Optional[np.ndarray] = None
    token_count: Optional[int] = None

    def __post_init__(self) -> None:
        if self.token_count is not None and self.token_cost == 1 and self.token_count != 1:
            self.token_cost = self.token_count
        elif self.token_count is None:
            self.token_count = self.token_cost
        if not isinstance(self.token_cost, int) or isinstance(self.token_cost, bool) or self.token_cost <= 0:
            raise ValueError(f"chunk token_cost must be non-negative positive integer, got {self.token_cost}")


@dataclass
class SubmodularPackingResult:
    selected_chunks: List[ContextChunk]
    total_tokens: int
    total_score: float
    coverage_score: float
    relevance_score: float


class SubmodularKnapsackPacker:
    """
    Submodular context selection optimizing diversity coverage and relevance
    under context token budget limits.
    
    Objective:
      f(S) = alpha * FacilityLocationCoverage(S) + beta * TotalRelevance(S)
    """

    def __init__(
        self,
        alpha: float = 0.6,
        beta: float = 0.4,
        similarity_metric: str = "clipped_cosine",
    ):
        if isinstance(alpha, bool) or not (np.isfinite(alpha) and alpha >= 0.0):
            raise ValueError(f"alpha must be finite and non-negative, got {alpha}")
        if isinstance(beta, bool) or not (np.isfinite(beta) and beta >= 0.0):
            raise ValueError(f"beta must be finite and non-negative, got {beta}")
        if similarity_metric not in ("clipped_cosine", "affine_cosine"):
            raise ValueError(f"Unsupported similarity_metric: {similarity_metric}")

        self.alpha = float(alpha)
        self.beta = float(beta)
        self.similarity_metric = similarity_metric

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        raw_cos = float(np.dot(v1, v2) / (norm1 * norm2))
        if self.similarity_metric == "affine_cosine":
            # Affine transformation: (1 + cos) / 2 mapped into [0, 1]
            return max(0.0, min(1.0, (1.0 + raw_cos) / 2.0))
        # Default clipped cosine: max(0, cos) preserving 0 as neutral orthogonality
        return max(0.0, min(1.0, raw_cos))

    def pack(
        self,
        chunks: List[ContextChunk],
        max_budget: int,
    ) -> SubmodularPackingResult:
        """Convenience alias for pack_context."""
        return self.pack_context(chunks, max_budget)

    def pack_context(
        self,
        chunks: List[ContextChunk],
        max_budget: int,
    ) -> SubmodularPackingResult:
        """
        Greedy submodular selection under knapsack budget.
        At each step, picks chunk j that maximizes delta_f(j | S) / token_cost(j).
        """
        if not isinstance(max_budget, int) or isinstance(max_budget, bool) or max_budget < 0:
            raise ValueError(f"max_budget must be non-negative integer, got {max_budget}")
        if not chunks or max_budget == 0:
            return SubmodularPackingResult(
                selected_chunks=[],
                total_tokens=0,
                total_score=0.0,
                coverage_score=0.0,
                relevance_score=0.0,
            )

        for c in chunks:
            if not isinstance(c.token_cost, int) or isinstance(c.token_cost, bool) or c.token_cost <= 0:
                raise ValueError(f"chunk token_cost must be non-negative positive integer, got {c.token_cost}")
            if not (np.isfinite(c.relevance_score) and c.relevance_score >= 0.0):
                raise ValueError(f"chunk relevance_score must be non-negative, got {c.relevance_score}")

        n = len(chunks)
        # Precompute similarity matrix if embeddings are present
        sim_matrix = np.zeros((n, n), dtype=np.float64)
        for i in range(n):
            for j in range(n):
                if chunks[i].embedding is not None and chunks[j].embedding is not None:
                    sim_matrix[i, j] = self._cosine_similarity(
                        chunks[i].embedding, chunks[j].embedding
                    )
                else:
                    # Fallback text overlap similarity if embeddings are absent
                    words_i = set(chunks[i].text.lower().split())
                    words_j = set(chunks[j].text.lower().split())
                    overlap = len(words_i & words_j)
                    denom = max(len(words_i | words_j), 1)
                    sim_matrix[i, j] = overlap / float(denom)

        selected_indices: List[int] = []
        current_tokens = 0
        current_coverage = 0.0
        current_relevance = 0.0

        available_indices = set(range(n))

        while available_indices:
            best_ratio = -1.0
            best_idx = -1
            best_marginal_gain = 0.0
            best_marginal_cov = 0.0
            best_marginal_rel = 0.0

            for idx in sorted(available_indices, key=lambda i: (chunks[i].token_cost, str(chunks[i].chunk_id))):
                cost = chunks[idx].token_cost
                if current_tokens + cost > max_budget:
                    continue

                # Compute new coverage if idx is added to S
                candidate_s = selected_indices + [idx]
                new_cov = sum(
                    max(sim_matrix[i, s_idx] for s_idx in candidate_s)
                    for i in range(n)
                ) / float(n)
                
                marginal_cov = new_cov - current_coverage
                marginal_rel = chunks[idx].relevance_score
                marginal_gain = self.alpha * marginal_cov + self.beta * marginal_rel

                if cost > 0:
                    ratio = marginal_gain / float(cost)
                    if ratio > best_ratio + 1e-9:
                        best_ratio = ratio
                        best_idx = idx
                        best_marginal_gain = marginal_gain
                        best_marginal_cov = marginal_cov
                        best_marginal_rel = marginal_rel
                    elif abs(ratio - best_ratio) <= 1e-9 and best_idx != -1:
                        # Deterministic tie-breaker: lower cost, then lex chunk_id
                        if cost < chunks[best_idx].token_cost or (
                            cost == chunks[best_idx].token_cost and str(chunks[idx].chunk_id) < str(chunks[best_idx].chunk_id)
                        ):
                            best_ratio = ratio
                            best_idx = idx
                            best_marginal_gain = marginal_gain
                            best_marginal_cov = marginal_cov
                            best_marginal_rel = marginal_rel

            if best_idx == -1:
                break

            selected_indices.append(best_idx)
            available_indices.remove(best_idx)
            current_tokens += chunks[best_idx].token_cost
            current_coverage += best_marginal_cov
            current_relevance += chunks[best_idx].relevance_score

        selected_chunks = [chunks[i] for i in selected_indices]
        total_score = self.alpha * current_coverage + self.beta * current_relevance

        # Best-single-item fallback:
        # Density-greedy on knapsack constraints has no constant-factor bound on its own.
        # Returning max(F(S_greedy), max_{i: c_i <= B} F({i})) achieves the proven
        # (1 - 1/e) / 2 ~= 0.316 approximation guarantee for monotone submodular knapsack.
        best_single_idx = -1
        best_single_score = -1.0
        best_single_cov = 0.0
        best_single_rel = 0.0
        for i in range(n):
            if chunks[i].token_cost <= max_budget:
                cov_i = sum(sim_matrix[j, i] for j in range(n)) / float(n)
                rel_i = chunks[i].relevance_score
                score_i = self.alpha * cov_i + self.beta * rel_i
                if score_i > best_single_score + 1e-9:
                    best_single_score = score_i
                    best_single_idx = i
                    best_single_cov = cov_i
                    best_single_rel = rel_i

        if best_single_idx != -1 and best_single_score > total_score + 1e-9:
            selected_chunks = [chunks[best_single_idx]]
            current_tokens = chunks[best_single_idx].token_cost
            total_score = best_single_score
            current_coverage = best_single_cov
            current_relevance = best_single_rel

        return SubmodularPackingResult(
            selected_chunks=selected_chunks,
            total_tokens=current_tokens,
            total_score=float(total_score),
            coverage_score=float(current_coverage),
            relevance_score=float(current_relevance),
        )
