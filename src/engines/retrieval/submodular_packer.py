"""
Submodular Knapsack Context Packer (Task C-1).

Formulates context packing as a submodular facility-location coverage optimization
problem under strict token budget constraints.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple
import numpy as np


@dataclass
class ContextChunk:
    chunk_id: str
    text: str
    relevance_score: float
    token_cost: int
    embedding: Optional[np.ndarray] = None


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
    
    f(S) = alpha * FacilityLocationCoverage(S) + beta * TotalRelevance(S)
    """

    def __init__(self, alpha: float = 0.6, beta: float = 0.4):
        if not (np.isfinite(alpha) and alpha >= 0.0):
            raise ValueError(f"alpha must be finite and non-negative, got {alpha}")
        if not (np.isfinite(beta) and beta >= 0.0):
            raise ValueError(f"beta must be finite and non-negative, got {beta}")
        self.alpha = float(alpha)
        self.beta = float(beta)

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        raw_cos = float(np.dot(v1, v2) / (norm1 * norm2))
        return max(0.0, raw_cos)

    def pack_context(
        self,
        chunks: List[ContextChunk],
        max_budget: int,
    ) -> SubmodularPackingResult:
        """
        Greedy submodular selection under knapsack budget.
        At each step, picks chunk j that maximizes delta_f(j | S) / token_cost(j).
        """
        if max_budget < 0:
            raise ValueError(f"max_budget must be non-negative, got {max_budget}")
        if not chunks or max_budget == 0:
            return SubmodularPackingResult(
                selected_chunks=[],
                total_tokens=0,
                total_score=0.0,
                coverage_score=0.0,
                relevance_score=0.0,
            )

        for c in chunks:
            if c.token_cost < 0:
                raise ValueError(f"chunk token_cost must be non-negative, got {c.token_cost}")
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

            for idx in available_indices:
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
                    if ratio > best_ratio:
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
                if score_i > best_single_score:
                    best_single_score = score_i
                    best_single_idx = i
                    best_single_cov = cov_i
                    best_single_rel = rel_i

        if best_single_idx != -1 and best_single_score > total_score:
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
