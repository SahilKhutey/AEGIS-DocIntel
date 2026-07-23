"""
AEGIS-AMDI — Spectral Engine
==============================
Two complementary methods:

  1. FFT Layout Analysis — detects periodic element patterns per page
     L(f) = FFT(layout_signal)   →   P(f) = |L(f)|²
     High P(f₀) → template page

  2. Entropy-Based Importance — ranks elements by information content
     H(e) = -Σ p(x) log₂ p(x)
     High H(e) → unique, informative
     Low  H(e) → boilerplate, skip
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from AMDI.engines.geometry.element import Element, ElementType

log = logging.getLogger("amdi.spectral")

# ─────────────────────────────────────────────────────────────────
# Result models
# ─────────────────────────────────────────────────────────────────

@dataclass
class SpectralSignature:
    page:                int
    dominant_freqs:      list[float]
    power_spectrum:      np.ndarray
    layout_periodicity:  float          # [0, 1]   1 = strongly periodic
    is_repetitive:       bool


@dataclass
class EntropyProfile:
    element_id:   str
    entropy:      float
    tfidf_score:  float
    is_informative: bool
    priority:     int        # lower = more important


# ─────────────────────────────────────────────────────────────────
# Spectral Engine
# ─────────────────────────────────────────────────────────────────

class SpectralEngine:
    """
    Two spectral methods combined:
      - FFT on page layout → template page detection (complements RecurrenceEngine)
      - Shannon entropy + IDF weighting → element prioritization (complements FrequencyEngine)

    Neither requires external ML libraries.
    scipy.fft is optional — falls back to numpy.fft.
    """

    PERIODICITY_THRESHOLD = 0.55
    ENTROPY_LOW  = 1.0    # below → boilerplate
    SIGNAL_BINS  = 64     # FFT resolution

    def __init__(self):
        self._idf:         dict[str, float] = {}
        self._n_docs:      int = 0
        self._profiles:    dict[str, EntropyProfile] = {}

    # ──────────────────────────────────────────────────────────────
    # FFT Layout Analysis
    # ──────────────────────────────────────────────────────────────

    def analyze_page_layout(
        self,
        elements: list[Element],
        page: int,
    ) -> SpectralSignature:
        """
        Project element y-positions onto a 1-D density signal, then FFT.
        Strong periodicity → likely template page.
        """
        ys = [e.bbox.y0 for e in elements if e.bbox]
        if len(ys) < 4:
            return SpectralSignature(
                page=page, dominant_freqs=[],
                power_spectrum=np.zeros(self.SIGNAL_BINS),
                layout_periodicity=0.0, is_repetitive=False,
            )

        signal = np.zeros(self.SIGNAL_BINS)
        for y in ys:
            idx = min(int(y * self.SIGNAL_BINS), self.SIGNAL_BINS - 1)
            signal[idx] += 1.0

        try:
            from scipy.fft import fft, fftfreq
        except ImportError:
            from numpy.fft import fft, fftfreq

        spectrum = fft(signal)
        freqs    = fftfreq(self.SIGNAL_BINS)
        power    = np.abs(spectrum) ** 2
        power[0] = 0.0   # remove DC

        total = power.sum() + 1e-9
        top_k = 4
        top_ix = np.argsort(power)[-top_k:][::-1]
        dom_freqs = [float(abs(freqs[i])) for i in top_ix if power[i] > 0]
        periodicity = float(power[top_ix].sum() / total)

        return SpectralSignature(
            page=page,
            dominant_freqs=dom_freqs,
            power_spectrum=power,
            layout_periodicity=min(1.0, periodicity),
            is_repetitive=periodicity > self.PERIODICITY_THRESHOLD,
        )

    def find_repetitive_pages(self, elements: list[Element]) -> list[int]:
        from collections import defaultdict
        by_page: dict[int, list[Element]] = defaultdict(list)
        for e in elements:
            by_page[e.page].append(e)
        return [
            page for page in sorted(by_page)
            if self.analyze_page_layout(by_page[page], page).is_repetitive
        ]

    # ──────────────────────────────────────────────────────────────
    # Entropy-Based Prioritization
    # ──────────────────────────────────────────────────────────────

    def fit_idf(self, elements: list[Element]) -> None:
        """Build inverse-document-frequency from the element corpus."""
        df: Counter = Counter()
        n = len(elements)
        for e in elements:
            df.update(set(self._tok(e.content)))
        self._idf = {
            t: math.log((1 + n) / (1 + c)) + 1.0
            for t, c in df.items()
        }
        self._n_docs = n

    def element_entropy(self, element: Element) -> float:
        """
        H(e) = -Σ p(w|e) · log₂ p(w|e)
        Combined with IDF weight for global rareness.
        """
        tokens = self._tok(element.content)
        if not tokens:
            return 0.0
        tf    = Counter(tokens)
        total = len(tokens)
        # Local Shannon entropy
        probs = np.array([c / total for c in tf.values()], dtype=np.float64)
        local_h = float(-np.sum(probs * np.log2(probs + 1e-9)))
        # IDF-weighted score
        tfidf = sum(
            (c / total) * self._idf.get(t, 1.0)
            for t, c in tf.items()
        )
        return min(6.0, (local_h + tfidf) / 2.0)

    def profile_elements(self, elements: list[Element]) -> list[EntropyProfile]:
        """
        Assign entropy profiles and priority ranks to all elements.
        Writes `entropy` and `importance_weight` back to each element.
        """
        if not self._idf:
            self.fit_idf(elements)

        profiles: list[EntropyProfile] = []
        for e in elements:
            h    = self.element_entropy(e)
            toks = self._tok(e.content)
            total = max(1, len(toks))
            tf_counter = Counter(toks)
            tfidf = sum(
                (c / total) * self._idf.get(t, 1.0)
                for t, c in tf_counter.items()
            )
            informative = h > self.ENTROPY_LOW
            profiles.append(EntropyProfile(
                element_id=e.element_id,
                entropy=h, tfidf_score=tfidf,
                is_informative=informative,
                priority=0,
            ))
            e.entropy = h

        # Rank by entropy (highest = priority 0)
        ranked = sorted(profiles, key=lambda p: p.entropy, reverse=True)
        for rank, p in enumerate(ranked):
            p.priority = rank
        self._profiles = {p.element_id: p for p in profiles}
        return profiles

    def entropy_score(self, element: Element) -> float:
        """Normalized entropy score for use in fusion [0, 1]."""
        p = self._profiles.get(element.element_id)
        if p is None:
            return 0.5
        max_h = max((pp.entropy for pp in self._profiles.values()), default=1.0)
        return p.entropy / max_h if max_h > 0 else 0.5

    def split_by_entropy(
        self,
        elements: list[Element],
    ) -> tuple[list[Element], list[Element]]:
        """Split elements into informative vs. boilerplate."""
        ids = {p.element_id for p in self._profiles.values() if p.is_informative}
        return (
            [e for e in elements if e.element_id in ids],
            [e for e in elements if e.element_id not in ids],
        )

    @staticmethod
    def _tok(text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"\b\w+\b", text)]
