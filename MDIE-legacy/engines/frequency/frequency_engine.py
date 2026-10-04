"""
AEGIS-MDIE — Frequency Engine
==============================
w(x) = 1 / log(1 + f(x))
TF-IDF-style structural importance weighting.
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from typing import Iterable

from MDIE.engines.geometry.element import ElementType, GeometricElement

log = logging.getLogger("mdie.frequency")

_TOK = re.compile(r"\w+", re.UNICODE)


def _tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOK.findall(text)]


# ─────────────────────────────────────────────────────────────────
# Type Baseline Weights  (heuristic importance by element type)
# ─────────────────────────────────────────────────────────────────

TYPE_BASELINE: dict[ElementType, float] = {
    ElementType.HEADING:   1.60,
    ElementType.TABLE:     1.80,
    ElementType.EQUATION:  1.50,
    ElementType.FORMULA:   1.50,
    ElementType.FIGURE:    1.10,
    ElementType.PARAGRAPH: 1.00,
    ElementType.LIST_ITEM: 0.90,
    ElementType.TEXT:      1.00,
    ElementType.CAPTION:   0.70,
    ElementType.CODE:      0.80,
    ElementType.HEADER:    0.15,   # page header → almost always boilerplate
    ElementType.FOOTER:    0.10,   # page footer → usually ignored
}


class FrequencyEngine:
    """
    Assigns importance weights to elements using:

        w(e) = α · IF(e) + β · TFIDF(e) + γ · type_baseline(e)

    Where:
        IF(e)    = 1 / log(1 + mean_token_freq(e))      [inverse frequency]
        TFIDF(e) = tf(e) × log(N / df(e))               [classic TF-IDF]
        type_baseline = heuristic weight by ElementType

    High f(x) → boilerplate (header/footer/page number)  → low weight
    Low f(x)  → unique content (conclusion/revenue figure) → high weight
    """

    def __init__(self):
        # Document-level counters
        self.term_tf:  Counter = Counter()   # term → total occurrences in doc
        self.term_df:  Counter = Counter()   # term → number of elements containing it
        self.n_elements: int = 0
        self._fitted = False

    # ──────────────────────────────────────────────────────────────
    # Fitting
    # ──────────────────────────────────────────────────────────────

    def fit(self, elements: Iterable[GeometricElement]) -> "FrequencyEngine":
        self.term_tf.clear()
        self.term_df.clear()
        self.n_elements = 0

        for e in elements:
            self.n_elements += 1
            tokens = _tokenize(e.content)
            self.term_tf.update(tokens)
            self.term_df.update(set(tokens))  # doc frequency: count once per element

        self._fitted = True
        log.info(
            "FrequencyEngine fitted: %d elements, %d unique terms",
            self.n_elements, len(self.term_df),
        )
        return self

    # ──────────────────────────────────────────────────────────────
    # Individual metrics
    # ──────────────────────────────────────────────────────────────

    def inverse_frequency(self, content: str) -> float:
        """w(x) = 1 / log(1 + f(x)) — inverse structural frequency."""
        tokens = _tokenize(content)
        if not tokens:
            return 0.0
        avg_tf = sum(self.term_tf.get(t, 0) for t in tokens) / len(tokens)
        return 1.0 / math.log(2.0 + avg_tf)

    def tfidf(self, content: str) -> float:
        """Summed TF-IDF score over tokens, normalized by token count."""
        tokens = _tokenize(content)
        if not tokens or self.n_elements == 0:
            return 0.0
        score = 0.0
        for t in tokens:
            tf = self.term_tf.get(t, 0)
            df = self.term_df.get(t, 0)
            if df == 0:
                continue
            idf = math.log((1 + self.n_elements) / (1 + df)) + 1.0
            score += tf * idf
        return score / len(tokens)

    def type_baseline(self, t: ElementType) -> float:
        return TYPE_BASELINE.get(t, 1.0)

    def composite_weight(
        self,
        e: GeometricElement,
        alpha: float = 0.45,
        beta:  float = 0.35,
        gamma: float = 0.20,
    ) -> float:
        """
        w(e) = α · IF_norm + β · TFIDF_norm + γ · type_norm

        All sub-scores normalized to [0, 1] before blending.
        """
        if not self._fitted:
            return 1.0

        if_score   = min(1.0, self.inverse_frequency(e.content))
        tfidf_score = min(1.0, self.tfidf(e.content) / 20.0)   # empirical max ≈ 20
        type_score  = min(1.0, self.type_baseline(e.type) / 2.0)

        return alpha * if_score + beta * tfidf_score + gamma * type_score

    # ──────────────────────────────────────────────────────────────
    # Batch assignment
    # ──────────────────────────────────────────────────────────────

    def assign_weights(self, elements: list[GeometricElement]) -> None:
        """
        Fit and assign importance_weight to every element in-place.
        Applies recurrence penalty: high-frequency groups get further suppressed.
        """
        self.fit(elements)

        # Count recurrence group sizes
        group_sizes: Counter = Counter(
            e.recurrence_id for e in elements if e.recurrence_id
        )

        for e in elements:
            w = self.composite_weight(e)

            # Recurrence penalty: R_n = R_0 → only the first occurrence matters
            if e.recurrence_id and group_sizes[e.recurrence_id] > 1:
                rec_freq = group_sizes[e.recurrence_id]
                penalty  = 1.0 / math.log(2.0 + rec_freq)
                w *= penalty

            # Page header/footer always suppressed regardless of content
            if e.type in (ElementType.HEADER, ElementType.FOOTER):
                w = min(w, 0.15)

            e.importance_weight = round(max(0.01, min(1.0, w)), 4)

        log.info(
            "Weights assigned to %d elements | avg=%.3f | max=%.3f | min=%.3f",
            len(elements),
            sum(e.importance_weight for e in elements) / max(1, len(elements)),
            max((e.importance_weight for e in elements), default=0),
            min((e.importance_weight for e in elements), default=0),
        )

    # ──────────────────────────────────────────────────────────────
    # Ranking & filtering
    # ──────────────────────────────────────────────────────────────

    def top_k(
        self,
        elements: list[GeometricElement],
        k: int = 10,
    ) -> list[GeometricElement]:
        """Return top-k highest importance elements."""
        return sorted(elements, key=lambda e: e.importance_weight, reverse=True)[:k]

    def filter_boilerplate(
        self,
        elements: list[GeometricElement],
        threshold: float = 0.15,
    ) -> list[GeometricElement]:
        """Remove elements with importance_weight < threshold."""
        return [e for e in elements if e.importance_weight >= threshold]

    # ──────────────────────────────────────────────────────────────
    # Query-time importance  F(q, e)
    # ──────────────────────────────────────────────────────────────

    def query_frequency_score(
        self,
        query: str,
        element: GeometricElement,
    ) -> float:
        """
        F(q, e) = element.importance_weight × query_term_overlap
        Used in hybrid retrieval formula: R = αS + βG + γF + δM
        """
        query_tokens = set(_tokenize(query))
        elem_tokens  = set(_tokenize(element.content))
        if not query_tokens or not elem_tokens:
            return element.importance_weight * 0.5
        overlap = len(query_tokens & elem_tokens) / len(query_tokens)
        return element.importance_weight * (0.5 + 0.5 * overlap)

    # ──────────────────────────────────────────────────────────────
    # Statistics
    # ──────────────────────────────────────────────────────────────

    def statistics(self) -> dict:
        return {
            "total_elements":  self.n_elements,
            "unique_terms":    len(self.term_df),
            "top_5_terms":     self.term_tf.most_common(5),
            "bottom_5_terms":  self.term_tf.most_common()[:-6:-1],
        }
