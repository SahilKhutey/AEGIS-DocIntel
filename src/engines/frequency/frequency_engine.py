"""
AEGIS-AMDI-OS — Frequency Engine
====================================
Computes term/entity/section frequencies and importance weights.

Formulations:
- I(x) = 1 / (1 + log(1 + f(x)))          (Inverse frequency weight)
- w(x) = α·IF(x) + β·type(e) + γ·rec(e)   (Composite weight)
- TF-IDF(t, D) = tf(t, D) · log(N / df(t))
- H(X) = -Σ p(x) log₂ p(x)               (Shannon entropy)
- ρ = I / A                              (Information density)

Theorems:
- 12.1: I_f strictly decreasing in f
- 12.2: I_f ∈ (0, 1]
- 13.1: H(X) ∈ [0, log₂|X|]
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Iterable, Optional, Any

import numpy as np

from src.engines.geometry.element import ElementType, GeometricElement

logger = logging.getLogger("amdi.frequency")


# ============================================================
# TOKENIZATION
# ============================================================

_TOKEN_RE = re.compile(r"\b\w+\b", re.UNICODE)
_SENTENCE_RE = re.compile(r"(?<=[.!?])\s+")

# Stopwords (English)
DEFAULT_STOPWORDS = frozenset({
    "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "as", "is", "was", "are", "were", "be",
    "been", "being", "have", "has", "had", "do", "does", "did", "will",
    "would", "could", "should", "may", "might", "must", "shall", "can",
    "this", "that", "these", "those", "i", "you", "he", "she", "it",
    "we", "they", "what", "which", "who", "whom", "whose", "where",
    "when", "why", "how", "all", "each", "every", "both", "few",
    "more", "most", "other", "some", "such", "no", "nor", "not",
    "only", "own", "same", "so", "than", "too", "very", "s", "t",
    "just", "don", "now", "re", "ve", "ll", "m", "o", "y", "d",
})


def tokenize(text: str, remove_stopwords: bool = False) -> list[str]:
    """
    Tokenize text into lowercase words.
    Optionally remove stopwords.
    """
    if not text:
        return []
    tokens = [t.lower() for t in _TOKEN_RE.findall(text)]
    if remove_stopwords:
        tokens = [t for t in tokens if t not in DEFAULT_STOPWORDS]
    return tokens


def split_sentences(text: str) -> list[str]:
    """Split text into sentences."""
    if not text:
        return []
    return [s.strip() for s in _SENTENCE_RE.split(text) if s.strip()]


# ============================================================
# TYPE WEIGHTS (baseline importance per element type)
# ============================================================

_TYPE_WEIGHTS = {
    ElementType.HEADING: 1.5,
    ElementType.TITLE: 1.6,
    ElementType.SUBTITLE: 1.3,
    ElementType.TABLE: 1.8,
    ElementType.EQUATION: 1.4,
    ElementType.FORMULA: 1.4,
    ElementType.FIGURE: 1.0,
    ElementType.TEXT: 1.0,
    ElementType.PARAGRAPH: 1.0,
    ElementType.CAPTION: 0.7,
    ElementType.LIST_ITEM: 0.9,
    ElementType.HEADER: 0.2,
    ElementType.FOOTER: 0.1,
    ElementType.QUOTE: 0.8,
    ElementType.CODE: 0.9,
    ElementType.REFERENCE: 0.6,
    ElementType.OTHER: 1.0,
}


@dataclass
class FrequencyStats:
    """Statistics about frequency analysis."""
    total_tokens: int = 0
    unique_tokens: int = 0
    n_elements: int = 0
    n_sections: int = 0
    n_entities: int = 0
    mean_entropy: float = 0.0
    mean_density: float = 0.0
    top_terms: list[tuple[str, int]] = field(default_factory=list)


@dataclass
class ImportanceMap:
    """Frequency-based importance profile."""
    idf:     dict[str, float]
    weights: dict[str, float]   # element_id → weight [0,1]

    def top_elements(self, n: int = 10) -> list[tuple[str, float]]:
        return sorted(self.weights.items(), key=lambda x: x[1], reverse=True)[:n]


class FrequencyEngine:
    """
    Phase 07: Frequency Engine.

    Computes:
    - Word/term frequency (TF, IDF, TF-IDF)
    - Section frequency
    - Entity frequency
    - Information density
    - Shannon entropy
    - Importance ranking
    """

    def __init__(self, remove_stopwords: bool = False):
        self.remove_stopwords = remove_stopwords
        self._tf: Counter = Counter()  # term frequency
        self._df: Counter = Counter()  # document frequency (elements)
        self._section_tf: dict[str, Counter] = defaultdict(Counter)
        self._section_count: dict[str, int] = defaultdict(int)
        self._entity_tf: Counter = Counter()
        self._element_count: int = 0
        self._is_fit: bool = False

        # Backwards compatibility state variables
        self._idf: dict[str, float] = {}
        self._n_docs: int = 0
        self._imp_map: Optional[ImportanceMap] = None

    # ============================================================
    # FITTING
    # ============================================================

    def fit(self, elements: list[GeometricElement]) -> "FrequencyEngine":
        """Compute frequency statistics from elements."""
        self._tf = Counter()
        self._df = Counter()
        self._section_tf = defaultdict(Counter)
        self._section_count = defaultdict(int)
        self._entity_tf = Counter()
        self._element_count = len(elements)
        self._n_docs = len(elements)
        
        for e in elements:
            # Token-level
            tokens = tokenize(e.content, self.remove_stopwords)
            self._tf.update(tokens)
            for t in set(tokens):
                self._df[t] += 1
            # Section-level
            section = e.section or "default"
            self._section_count[section] += 1
            self._section_tf[section].update(tokens)
            # Entity-level
            entities = self._extract_entities(e.content)
            self._entity_tf.update(entities)
            
        self._is_fit = True
        # Populate self._idf for backwards compatibility
        self._idf = {t: self.inverse_document_frequency(t) for t in self._df}
        logger.info("FrequencyEngine fitted: %d elements, %d unique terms", len(elements), len(self._idf))
        return self

    @staticmethod
    def _extract_entities(text: str) -> list[str]:
        """Extract entities (capitalized phrases as proxy)."""
        if not text:
            return []
        entities = re.findall(r"\b[A-Z][a-z]+(?:[ -][A-Z][a-z]+)*\b", text)
        return [e for e in entities if len(e) > 2]

    # ============================================================
    # 1. WORD FREQUENCY
    # ============================================================

    def term_frequency(self, term: str) -> int:
        """TF(t) = number of occurrences of t."""
        if not self._is_fit:
            return 0
        return self._tf.get(term.lower(), 0)

    def document_frequency(self, term: str) -> int:
        """DF(t) = number of elements containing t."""
        if not self._is_fit:
            return 0
        return self._df.get(term.lower(), 0)

    def inverse_document_frequency(self, term: str) -> float:
        """
        IDF(t) = log((1 + N) / (1 + DF(t))) + 1  (smoothed).

        Higher IDF = rarer term = more informative.
        """
        n = self._element_count
        if n == 0:
            return 0.0
        df = self._df.get(term.lower(), 0)
        return math.log((1 + n) / (1 + df)) + 1.0

    def tfidf(self, term: str, in_element: GeometricElement) -> float:
        """
        TF-IDF(t, e) = TF(t, e) · IDF(t).

        Higher = more informative for the specific element.
        """
        if not in_element.content:
            return 0.0
        tokens = tokenize(in_element.content, self.remove_stopwords)
        tf = sum(1 for t in tokens if t == term.lower())
        idf = self.inverse_document_frequency(term)
        return tf * idf

    def top_terms(self, n: int = 10, by: str = "tf") -> list[tuple[str, int | float]]:
        """Get top N terms by frequency or TF-IDF."""
        if not self._is_fit:
            return []
        if by == "tf":
            return self._tf.most_common(n)
        elif by == "idf":
            scored = [(t, self.inverse_document_frequency(t)) for t in self._df]
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:n]
        return []

    # ============================================================
    # 2. SECTION FREQUENCY
    # ============================================================

    def section_frequency(self, section: str) -> int:
        """Number of elements in a section."""
        return self._section_count.get(section, 0)

    def section_terms(self, section: str, n: int = 10) -> list[tuple[str, int]]:
        """Top terms in a specific section."""
        if section not in self._section_tf:
            return []
        return self._section_tf[section].most_common(n)

    def section_entropy(self, section: str) -> float:
        """Entropy of section's token distribution."""
        if section not in self._section_tf:
            return 0.0
        counter = self._section_tf[section]
        return entropy_from_counter(counter)

    def all_sections(self) -> list[str]:
        """Get all section names."""
        return list(self._section_count.keys())

    # ============================================================
    # 3. ENTITY FREQUENCY
    # ============================================================

    def entity_frequency(self, entity: str) -> int:
        """How often an entity appears."""
        return self._entity_tf.get(entity, 0)

    def top_entities(self, n: int = 10) -> list[tuple[str, int]]:
        """Most frequent entities."""
        return self._entity_tf.most_common(n)

    def rare_entities(self, n: int = 10) -> list[tuple[str, int]]:
        """Rarest entities (appear once)."""
        return [e for e in self._entity_tf.items() if e[1] == 1][:n]

    # ============================================================
    # 4. DENSITY ANALYSIS
    # ============================================================

    def information_density(
        self,
        element: GeometricElement,
    ) -> float:
        """
        ρ = I / A

        Where:
        - I: information content (entropy)
        - A: area (normalized bbox width × height)

        High density = small area + high information = important
        """
        if element.bbox is None or element.bbox.area <= 0:
            return 0.0
        entropy_val = self.element_entropy(element)
        return entropy_val / element.bbox.area

    def density_percentile(self, element: GeometricElement, all_elements: list[GeometricElement]) -> float:
        """What percentile is this element's density at?"""
        if not all_elements:
            return 0.5
        densities = [self.information_density(e) for e in all_elements]
        density = self.information_density(element)
        below = sum(1 for d in densities if d < density)
        return below / len(densities)

    def highest_density_elements(
        self,
        elements: list[GeometricElement],
        n: int = 5,
    ) -> list[tuple[GeometricElement, float]]:
        """Top N elements by information density."""
        densities = [(e, self.information_density(e)) for e in elements]
        densities.sort(key=lambda x: x[1], reverse=True)
        return densities[:n]

    # ============================================================
    # 5. ENTROPY ANALYSIS
    # ============================================================

    def element_entropy(self, element: GeometricElement) -> float:
        """
        H(e) = -Σ p(t|e) log₂ p(t|e)

        Shannon entropy of token distribution in element.
        """
        tokens = tokenize(element.content, self.remove_stopwords)
        return shannon_entropy(tokens)

    def document_entropy(self) -> float:
        """H(D) = -Σ p(t|D) log₂ p(t|D) over all tokens in document."""
        return entropy_from_counter(self._tf)

    def conditional_entropy(self, section: str) -> float:
        """H(section | rest of document)."""
        if not self._is_fit or section not in self._section_tf:
            return 0.0
        section_total = sum(self._section_tf[section].values())
        doc_total = sum(self._tf.values())
        if section_total == 0 or doc_total == 0:
            return 0.0
        
        section_entropy = self.section_entropy(section)
        cross = 0.0
        for token, p_doc in self._tf.items():
            if p_doc > 0:
                p_section = self._section_tf[section].get(token, 0) / section_total
                if p_section > 0:
                    cross -= (p_doc / doc_total) * math.log2(p_section)
        return section_entropy + cross

    def mean_element_entropy(self, elements: list[GeometricElement]) -> float:
        """Average entropy across elements."""
        if not elements:
            return 0.0
        entropies = [self.element_entropy(e) for e in elements]
        return float(np.mean(entropies))

    # ============================================================
    # 6. IMPORTANCE RANKING
    # ============================================================

    def type_baseline(self, etype: ElementType) -> float:
        """Heuristic baseline importance by element type."""
        return _TYPE_WEIGHTS.get(etype, 1.0)

    def inverse_frequency_weight(self, content: str) -> float:
        """
        I(x) = 1 / (1 + log(1 + f(x)))

        Theorem 12.1: Strictly decreasing in f.
        Theorem 12.2: Bounded in (0, 1].
        """
        if not self._is_fit or not content:
            return 0.0
        tokens = tokenize(content, self.remove_stopwords)
        if not tokens:
            return 0.0
        freqs = [self._tf.get(t, 0) for t in tokens]
        avg_f = sum(freqs) / len(freqs)
        return 1.0 / (1.0 + math.log(1.0 + avg_f))

    def composite_importance(
        self,
        element: GeometricElement,
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2,
    ) -> float:
        """
        w(e) = α · I_f(e) + β · type_baseline(e) + γ · area_importance(e)

        Composite importance score.
        """
        if not self._is_fit:
            self.fit([element])
        
        ifw = self.inverse_frequency_weight(element.content)
        type_w = self.type_baseline(element.type)
        
        if element.bbox:
            area = min(1.0, element.bbox.width * element.bbox.height * 2)
        else:
            area = 0.5
            
        composite = alpha * ifw + beta * min(1.0, type_w / 2.0) + gamma * area
        
        # Penalize if recurrent template boilerplate
        if element.recurrence_id and element.frequency > 1:
            composite *= 1.0 / math.log(2 + element.frequency)
        elif element.is_template:
            composite *= 0.5
            
        return composite

    def assign_weights(
        self,
        elements: list[GeometricElement],
        alpha: float = 0.5,
        beta: float = 0.3,
        gamma: float = 0.2,
    ) -> ImportanceMap:
        """
        Assign importance weights to all elements (in-place).

        w(e) = α · I_f(e) + β · type(e) + γ · area(e) / recurrence(e)
        Returns ImportanceMap for backwards compatibility.
        """
        self.fit(elements)
        
        raw_scores: dict[str, float] = {}
        for e in elements:
            score = self.composite_importance(e, alpha, beta, gamma)
            raw_scores[e.element_id] = score

        max_s = max(raw_scores.values(), default=1.0)
        min_s = min(raw_scores.values(), default=0.0)
        span = max_s - min_s + 1e-9
        
        weights: dict[str, float] = {}
        for e in elements:
            w = (raw_scores[e.element_id] - min_s) / span
            e.importance_weight = round(float(w), 4)
            weights[e.element_id] = e.importance_weight

        self._imp_map = ImportanceMap(idf=self._idf, weights=weights)
        return self._imp_map

    def rank_by_importance(
        self,
        elements: list[GeometricElement],
        n: int | None = None,
    ) -> list[GeometricElement]:
        """Sort elements by importance weight (descending)."""
        if not self._is_fit:
            self.fit(elements)
        ranked = sorted(elements, key=lambda e: e.importance_weight, reverse=True)
        return ranked[:n] if n else ranked

    def top_k_important(
        self,
        elements: list[GeometricElement],
        k: int = 10,
    ) -> list[GeometricElement]:
        """Get top K most important elements."""
        return self.rank_by_importance(elements, n=k)

    def percentile_rank(
        self,
        element: GeometricElement,
        all_elements: list[GeometricElement],
    ) -> float:
        """What percentile is this element's importance at?"""
        if not all_elements:
            return 0.5
        weights = [e.importance_weight for e in all_elements]
        target = element.importance_weight
        below = sum(1 for w in weights if w < target)
        return below / len(weights)

    # ============================================================
    # BACKWARDS COMPATIBILITY METHODS
    # ============================================================

    def frequency_score(self, element: GeometricElement) -> float:
        """F(q, e) = element importance weight."""
        return element.importance_weight

    def analyze(self, elements: list[GeometricElement]) -> None:
        self.assign_weights(elements)

    def score(self, query: str, elements: list[GeometricElement]) -> dict[str, float]:
        return {e.element_id: self.frequency_score(e) for e in elements}

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self, elements: list[GeometricElement] | None = None) -> FrequencyStats:
        """Get comprehensive frequency statistics."""
        if elements and not self._is_fit:
            self.fit(elements)
        total_tokens = sum(self._tf.values())
        
        # Calculate mean entropy and density
        mean_h = 0.0
        mean_d = 0.0
        if elements:
            mean_h = self.mean_element_entropy(elements)
            densities = [self.information_density(e) for e in elements]
            mean_d = float(np.mean(densities)) if densities else 0.0
            
        return FrequencyStats(
            total_tokens=total_tokens,
            unique_tokens=len(self._tf),
            n_elements=self._element_count,
            n_sections=len(self._section_count),
            n_entities=len(self._entity_tf),
            mean_entropy=mean_h,
            mean_density=mean_d,
            top_terms=self._tf.most_common(10),
        )


# ============================================================
# STANDALONE FUNCTIONS
# ============================================================

def shannon_entropy(tokens: list[str], base: float = 2) -> float:
    """
    H(X) = -Σ p(x) log_b p(x)

    Shannon entropy of a token list.
    """
    if not tokens:
        return 0.0
    counter = Counter(tokens)
    total = len(tokens)
    probs = np.array([c / total for c in counter.values()], dtype=np.float64)
    probs = probs[probs > 0]
    if len(probs) == 0:
        return 0.0
    entropy_val = -np.sum(probs * np.log(probs) / np.log(base))
    return float(entropy_val)


def entropy_from_counter(counter: Counter, base: float = 2) -> float:
    """Compute entropy from a Counter."""
    total = sum(counter.values())
    if total == 0:
        return 0.0
    probs = np.array([c / total for c in counter.values() if c > 0], dtype=np.float64)
    return float(-np.sum(probs * np.log(probs) / np.log(base)))


def information_density(entropy: float, area: float) -> float:
    """ρ = H / A. Higher = more info per unit area."""
    if area <= 0:
        return 0.0
    return entropy / area


def jensen_shannon_divergence(p: list[float], q: list[float]) -> float:
    """JSD(P || Q) = symmetric version of KL divergence."""
    p_arr = np.array(p, dtype=np.float64)
    q_arr = np.array(q, dtype=np.float64)
    p_arr = p_arr / (p_arr.sum() + 1e-9)
    q_arr = q_arr / (q_arr.sum() + 1e-9)
    m = (p_arr + q_arr) / 2
    return float(0.5 * _kl(p_arr, m) + 0.5 * _kl(q_arr, m))


def _kl(p: np.ndarray, q: np.ndarray) -> float:
    p_safe = p + 1e-10
    q_safe = q + 1e-10
    return float(np.sum(p * np.log2(p_safe / q_safe)))


def tfidf_score(tf: int, df: int, n_docs: int) -> float:
    """Standard TF-IDF: tf · log(N / df)."""
    if df == 0 or n_docs == 0:
        return 0.0
    return tf * math.log(n_docs / df)
