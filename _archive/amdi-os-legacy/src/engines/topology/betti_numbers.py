"""
Betti Numbers Calculator
========================

Mathematical Definition:
-----------------------
Betti numbers β₀, β₁, β₂ represent the number of independent topological
features of a simplicial complex in dimensions 0, 1, and 2 respectively.
"""

from __future__ import annotations

from dataclasses import dataclass

from .connected_components import ConnectedComponentsAnalyzer
from .loops import LoopsAnalyzer
from .clusters import TopologicalClusters
from .simplex import SimplicialComplex


@dataclass
class BettiNumbers:
    """
    Representation of homological Betti numbers.

    Attributes
    ----------
    betti_0 : int
        0-dimensional Betti number β₀ (connected components).
    betti_1 : int
        1-dimensional Betti number β₁ (cycles / loops).
    betti_2 : int
        2-dimensional Betti number β₂ (voids / cavities).
    """

    betti_0: int
    betti_1: int
    betti_2: int

    @classmethod
    def compute(cls, complex_: SimplicialComplex) -> BettiNumbers:
        """Compute Betti numbers for the given complex."""
        b0 = ConnectedComponentsAnalyzer().analyze(complex_).betti_0
        b1 = LoopsAnalyzer().analyze(complex_).betti_1
        b2 = TopologicalClusters()._compute_betti_2(complex_)
        return cls(betti_0=b0, betti_1=b1, betti_2=b2)
