"""
AEGIS-AMDI-OS — Entropy Engine
================================
Implements Formula §13: Shannon entropy for elements.
Used for information-density-based prioritization.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass
from typing import Iterable, List, Set, Tuple, Dict, Any

import numpy as np
from scipy.stats import entropy as scipy_entropy

from src.engines.coordinate.coordinate_engine import CoordinateEngine, NormalizedCoordinate

logger = logging.getLogger("amdi.math.entropy")

_TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text)]


@dataclass
class EntropyProfile:
    """
    Entropy metrics for an element or document region.
    """
    element_id: str
    shannon_entropy: float    # H(X) = -Σ p log p
    max_entropy: float        # log₂ |X|
    normalized_entropy: float # H / H_max ∈ [0, 1]
    information_density: float # H / area
    token_count: int
    unique_token_count: int
    priority: int = 0        # 0 = highest
    is_informative: bool = True


class EntropyEngine:
    """
    Shannon entropy computation for document elements.

    H(X) = -Σ p(x) log₂ p(x)

    Theorem 13.1: H(X) ∈ [0, log₂|X|]
    """

    DEFAULT_INFORMATIVENESS_THRESHOLD = 1.5  # bits

    def __init__(self, threshold: float | None = None):
        self.threshold = threshold or self.DEFAULT_INFORMATIVENESS_THRESHOLD
        # Global term frequencies
        self._global_tf: Counter = Counter()
        self._n_docs = 0

    def fit_collection(self, all_texts: Iterable[str]) -> EntropyEngine:
        """Build collection-level term frequencies."""
        self._n_docs += 1
        for t in all_texts:
            self._global_tf.update(_tokenize(t))
        return self

    # ------------------------------------------------------------------ #
    # Formula §13: Shannon entropy                                         #
    # ------------------------------------------------------------------ #

    def shannon_entropy(self, text: str) -> float:
        """
        H(X) = -Σ p(x) log₂ p(x)
        where p(x) = count(x) / total_tokens
        """
        tokens = _tokenize(text)
        if not tokens:
            return 0.0
        tf = Counter(tokens)
        probs = np.array([c / len(tokens) for c in tf.values()], dtype=np.float64)
        return float(scipy_entropy(probs, base=2))

    def max_entropy(self, text: str) -> float:
        """H_max = log₂|X| where |X| = number of unique tokens."""
        tokens = _tokenize(text)
        if not tokens:
            return 0.0
        return math.log2(len(set(tokens)))

    def normalized_entropy(self, text: str) -> float:
        """
        H_norm = H / H_max ∈ [0, 1]
        0 = repetitive, 1 = maximally diverse
        """
        h = self.shannon_entropy(text)
        h_max = self.max_entropy(text)
        return h / h_max if h_max > 0 else 0.0

    # ------------------------------------------------------------------ #
    # Formula §14: Information density                                    #
    # ------------------------------------------------------------------ #

    def information_density(self, text: str, area: float) -> float:
        """
        D = N / A  (information per unit area)
        """
        if area <= 0:
            return 0.0
        return self.shannon_entropy(text) / area

    # ------------------------------------------------------------------ #
    # Batch profiling                                                      #
    # ------------------------------------------------------------------ #

    def profile(self, coords: List[NormalizedCoordinate]) -> List[EntropyProfile]:
        """Compute entropy profiles for all elements."""
        profiles: List[EntropyProfile] = []
        for c in coords:
            text = c.content
            h = self.shannon_entropy(text)
            h_max = self.max_entropy(text)
            h_norm = h / h_max if h_max > 0 else 0.0
            area = c.area_ratio()
            density = h / area if area > 0 else 0.0
            tokens = _tokenize(text)
            profiles.append(EntropyProfile(
                element_id=c.element_id,
                shannon_entropy=h,
                max_entropy=h_max,
                normalized_entropy=h_norm,
                information_density=density,
                token_count=len(tokens),
                unique_token_count=len(set(tokens)),
                is_informative=h > self.threshold,
            ))
        # Assign priority ranks
        profiles.sort(key=lambda p: p.information_density, reverse=True)
        for i, p in enumerate(profiles):
            p.priority = i
        return profiles

    def filter_informative(
        self,
        coords: List[NormalizedCoordinate],
        profiles: List[EntropyProfile] | None = None,
    ) -> Tuple[List[NormalizedCoordinate], List[NormalizedCoordinate]]:
        """Split into informative and non-informative."""
        if profiles is None:
            profiles = self.profile(coords)
        informative_ids = {p.element_id for p in profiles if p.is_informative}
        informative = [c for c in coords if c.element_id in informative_ids]
        non_informative = [c for c in coords if c.element_id not in informative_ids]
        return informative, non_informative

    # ------------------------------------------------------------------ #
    # Document-level statistics                                            #
    # ------------------------------------------------------------------ #

    def document_statistics(self, coords: List[NormalizedCoordinate]) -> Dict[str, Any]:
        """Aggregate document-level entropy statistics."""
        entropies = [self.shannon_entropy(c.content) for c in coords if c.content]
        if not entropies:
            return {"mean_entropy": 0.0, "max_entropy": 0.0, "min_entropy": 0.0}
        return {
            "mean_entropy": float(np.mean(entropies)),
            "max_entropy": float(np.max(entropies)),
            "min_entropy": float(np.min(entropies)),
            "std_entropy": float(np.std(entropies)),
            "median_entropy": float(np.median(entropies)),
            "n_elements": len(coords),
            "n_informative": sum(1 for h in entropies if h > self.threshold),
        }
