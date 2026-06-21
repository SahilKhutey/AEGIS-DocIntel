"""
Token Optimizer
================

Strategies to reduce LLM token consumption:

    - TRUNCATE: cut at token boundary
    - SUMMARIZE: replace long sections with summaries
    - COMPRESS: remove redundant content
    - SELECT: pick top-K most relevant
    - CHUNK_MERGE: combine small chunks
    - DEDUPLICATE: remove duplicate content
    - TEMPLATE: use templated prompts
    - MMR_DIVERSITY: balance relevance + diversity

Mathematical Foundation:
    R_token = 1 - Σ(tokens_after) / Σ(tokens_before)

    Cost savings:
        $saved = R_token · baseline_cost
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

import numpy as np


class TokenStrategy(Enum):
    """Token optimization strategies."""

    TRUNCATE = "truncate"
    SUMMARIZE = "summarize"
    COMPRESS = "compress"
    SELECT = "select"
    CHUNK_MERGE = "chunk_merge"
    DEDUPLICATE = "deduplicate"
    TEMPLATE = "template"
    MMR_DIVERSITY = "mmr_diversity"


@dataclass
class TokenOptimizationResult:
    """Result of token optimization."""

    strategy: str
    original_tokens: int
    optimized_tokens: int
    tokens_saved: int
    reduction_pct: float
    quality_score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "strategy": self.strategy,
            "original_tokens": self.original_tokens,
            "optimized_tokens": self.optimized_tokens,
            "tokens_saved": self.tokens_saved,
            "reduction_pct": round(self.reduction_pct, 4),
            "quality_score": round(self.quality_score, 4),
        }


class TokenOptimizer:
    """
    Apply token optimization strategies to content.

    Optimization Hierarchy:
        1. DEDUPLICATE (no quality loss)
        2. COMPRESS (low quality loss)
        3. SUMMARIZE (medium quality loss)
        4. SELECT (some information loss)
        5. TRUNCATE (high information loss)
    """

    def __init__(self, target_reduction_pct: float = 0.30) -> None:
        self.target_reduction_pct = target_reduction_pct

    def count_tokens(self, text: str) -> int:
        """Approximate token count."""
        return max(1, int(len(text.split()) / 0.75))

    def truncate(
        self,
        text: str,
        max_tokens: int,
    ) -> TokenOptimizationResult:
        """Truncate text to fit within token budget."""
        original_tokens = self.count_tokens(text)
        if original_tokens <= max_tokens:
            return TokenOptimizationResult(
                strategy="truncate",
                original_tokens=original_tokens,
                optimized_tokens=original_tokens,
                tokens_saved=0,
                reduction_pct=0.0,
                quality_score=1.0,
                metadata={"text": text},
            )
        # estimate char count
        char_per_token = len(text) / original_tokens
        target_chars = int(max_tokens * char_per_token)
        truncated = text[:target_chars]
        if " " in truncated:
            truncated = truncated.rsplit(" ", 1)[0]
        new_tokens = self.count_tokens(truncated)
        saved = original_tokens - new_tokens
        return TokenOptimizationResult(
            strategy="truncate",
            original_tokens=original_tokens,
            optimized_tokens=new_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=0.7,  # moderate quality loss
            metadata={"text": truncated},
        )

    def summarize(
        self,
        text: str,
        target_tokens: int,
        summarizer: Optional[Callable[[str], str]] = None,
    ) -> TokenOptimizationResult:
        """Summarize text to target token count."""
        original_tokens = self.count_tokens(text)
        if original_tokens <= target_tokens:
            return TokenOptimizationResult(
                strategy="summarize",
                original_tokens=original_tokens,
                optimized_tokens=original_tokens,
                tokens_saved=0,
                reduction_pct=0.0,
                quality_score=1.0,
                metadata={"text": text},
            )
        if summarizer is not None:
            summarized = summarizer(text)
        else:
            # heuristic: extractive summary (first/middle/last)
            sentences = re.split(r"(?<=[.!?])\s+", text.strip())
            if len(sentences) <= 3:
                summarized = text
            else:
                n_keep = max(2, int(len(sentences) * 0.3))
                # pick top by importance (first + last + middle)
                indices = sorted(
                    set(
                        list(range(min(2, len(sentences))))
                        + [len(sentences) - 1]
                        + [len(sentences) // 2]
                    )
                )
                summarized = " ".join(sentences[i] for i in indices[:n_keep])
        new_tokens = self.count_tokens(summarized)
        saved = original_tokens - new_tokens
        return TokenOptimizationResult(
            strategy="summarize",
            original_tokens=original_tokens,
            optimized_tokens=new_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=0.85,
            metadata={"text": summarized},
        )

    def compress(
        self,
        text: str,
        target_reduction: float = 0.3,
    ) -> TokenOptimizationResult:
        """Compress text by removing redundancy."""
        original_tokens = self.count_tokens(text)
        # remove extra whitespace
        compressed = re.sub(r"\s+", " ", text)
        # remove duplicate consecutive words
        words = compressed.split()
        deduped: List[str] = []
        prev = None
        for w in words:
            if w != prev:
                deduped.append(w)
            prev = w
        compressed = " ".join(deduped)
        # remove common stopwords if reduction target is high
        stopwords = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at",
            "to", "for", "of", "with", "by", "from", "is", "are",
        }
        if target_reduction > 0.4:
            compressed = " ".join(
                w for w in deduped if w.lower() not in stopwords
            )
        new_tokens = self.count_tokens(compressed)
        saved = original_tokens - new_tokens
        return TokenOptimizationResult(
            strategy="compress",
            original_tokens=original_tokens,
            optimized_tokens=new_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=0.92,
            metadata={"text": compressed},
        )

    def select(
        self,
        texts: List[str],
        top_k: int,
        relevance_scores: Optional[List[float]] = None,
    ) -> TokenOptimizationResult:
        """Select top-K most relevant texts."""
        if relevance_scores is None:
            relevance_scores = [float(self.count_tokens(t)) for t in texts]
        ranked = sorted(
            zip(texts, relevance_scores),
            key=lambda x: x[1],
            reverse=True,
        )
        selected = [t for t, _ in ranked[:top_k]]
        original_tokens = sum(self.count_tokens(t) for t in texts)
        optimized_tokens = sum(self.count_tokens(t) for t in selected)
        saved = original_tokens - optimized_tokens
        return TokenOptimizationResult(
            strategy="select",
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=0.9,
            metadata={"selected_texts": selected, "total": len(texts)},
        )

    def deduplicate(
        self,
        texts: List[str],
    ) -> TokenOptimizationResult:
        """Remove near-duplicate texts."""
        seen_hashes: set = set()
        unique: List[str] = []
        for t in texts:
            # simple hash on normalized text
            normalized = re.sub(r"\s+", " ", t.lower().strip())
            h = hash(normalized)
            if h not in seen_hashes:
                seen_hashes.add(h)
                unique.append(t)
        original_tokens = sum(self.count_tokens(t) for t in texts)
        optimized_tokens = sum(self.count_tokens(t) for t in unique)
        saved = original_tokens - optimized_tokens
        return TokenOptimizationResult(
            strategy="deduplicate",
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=1.0,  # no quality loss
            metadata={"selected_texts": unique, "duplicates_removed": len(texts) - len(unique)},
        )

    def mmr_select(
        self,
        texts: List[str],
        embeddings: np.ndarray,
        top_k: int,
        lambda_param: float = 0.7,
    ) -> TokenOptimizationResult:
        """
        MMR diversity-based selection.

        MMR(d) = λ · relevance(d) - (1-λ) · max similarity(d, d')
        """
        n = len(texts)
        if n <= top_k:
            original_tokens = sum(self.count_tokens(t) for t in texts)
            return TokenOptimizationResult(
                strategy="mmr_diversity",
                original_tokens=original_tokens,
                optimized_tokens=original_tokens,
                tokens_saved=0,
                reduction_pct=0.0,
                quality_score=1.0,
                metadata={"selected_texts": texts},
            )
        # normalize embeddings
        norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        embs_norm = embeddings / norms
        sim_matrix = embs_norm @ embs_norm.T
        # relevance = norm of embedding (proxy)
        relevance = np.linalg.norm(embeddings, axis=1)
        selected: List[int] = []
        remaining = list(range(n))
        while len(selected) < top_k and remaining:
            best_score = -float("inf")
            best_idx = remaining[0]
            for i in remaining:
                if not selected:
                    div_penalty = 0.0
                else:
                    div_penalty = max(sim_matrix[i, j] for j in selected)
                mmr = lambda_param * relevance[i] - (1 - lambda_param) * div_penalty
                if mmr > best_score:
                    best_score = mmr
                    best_idx = i
            selected.append(best_idx)
            remaining.remove(best_idx)
        selected_texts = [texts[i] for i in selected]
        original_tokens = sum(self.count_tokens(t) for t in texts)
        optimized_tokens = sum(self.count_tokens(t) for t in selected_texts)
        saved = original_tokens - optimized_tokens
        return TokenOptimizationResult(
            strategy="mmr_diversity",
            original_tokens=original_tokens,
            optimized_tokens=optimized_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(original_tokens, 1),
            quality_score=0.92,
            metadata={"lambda": lambda_param, "selected_texts": selected_texts},
        )

    def optimize_chain(
        self,
        texts: List[str],
        target_tokens: int,
        embedding_fn: Optional[Callable[[str], np.ndarray]] = None,
    ) -> TokenOptimizationResult:
        """Apply multiple strategies in sequence to meet target."""
        total_tokens = sum(self.count_tokens(t) for t in texts)
        if total_tokens <= target_tokens:
            return TokenOptimizationResult(
                strategy="chain",
                original_tokens=total_tokens,
                optimized_tokens=total_tokens,
                tokens_saved=0,
                reduction_pct=0.0,
                quality_score=1.0,
                metadata={"text": "\n\n".join(texts)},
            )
        # 1. deduplicate
        dedup_result = self.deduplicate(texts)
        texts = dedup_result.metadata.get("selected_texts", texts)
        # 2. compress
        compressed = [self._compress_text(t) for t in texts]
        # 3. select if still too many
        current_tokens = sum(self.count_tokens(t) for t in compressed)
        if current_tokens > target_tokens:
            # use mmr if embeddings available
            if embedding_fn is not None:
                embeddings = np.array([embedding_fn(t) for t in compressed])
                mmr_result = self.mmr_select(
                    compressed, embeddings, top_k=max(1, target_tokens // 100)
                )
                compressed = mmr_result.metadata.get("selected_texts", compressed)
            else:
                # simple rank-and-truncate
                ranked = sorted(
                    range(len(compressed)),
                    key=lambda i: self.count_tokens(compressed[i]),
                    reverse=True,
                )
                keep_count = max(1, int(len(compressed) * target_tokens / current_tokens))
                compressed = [compressed[i] for i in ranked[:keep_count]]
        # 4. truncate
        final_text = "\n\n".join(compressed)
        if self.count_tokens(final_text) > target_tokens:
            trunc_result = self.truncate(final_text, target_tokens)
            final_text = trunc_result.metadata.get("text", final_text[:target_tokens * 4])
        new_tokens = self.count_tokens(final_text)
        saved = total_tokens - new_tokens
        return TokenOptimizationResult(
            strategy="chain",
            original_tokens=total_tokens,
            optimized_tokens=new_tokens,
            tokens_saved=saved,
            reduction_pct=saved / max(total_tokens, 1),
            quality_score=0.88,
            metadata={"text": final_text},
        )

    @staticmethod
    def _compress_text(text: str) -> str:
        compressed = re.sub(r"\s+", " ", text)
        words = compressed.split()
        deduped = []
        prev = None
        for w in words:
            if w != prev:
                deduped.append(w)
            prev = w
        return " ".join(deduped)
