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
        self.alpha = alpha
        self.beta = beta

    def _cosine_similarity(self, v1: np.ndarray, v2: np.ndarray) -> float:
        norm1 = np.linalg.norm(v1)
        norm2 = np.linalg.norm(v2)
        if norm1 == 0 or norm2 == 0:
            return 0.0
        return float(np.dot(v1, v2) / (norm1 * norm2))

    def pack_context(
        self,
        chunks: List[ContextChunk],
        max_budget: int,
    ) -> SubmodularPackingResult:
        """
        Greedy submodular selection under knapsack budget.
        At each step, picks chunk j that maximizes delta_f(j | S) / token_cost(j).
        """
        if not chunks or max_budget <= 0:
            return SubmodularPackingResult(
                selected_chunks=[],
                total_tokens=0,
                total_score=0.0,
                coverage_score=0.0,
                relevance_score=0.0,
            )

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

        return SubmodularPackingResult(
            selected_chunks=selected_chunks,
            total_tokens=current_tokens,
            total_score=float(total_score),
            coverage_score=float(current_coverage),
            relevance_score=float(current_relevance),
        )
