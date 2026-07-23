"""
Euler Characteristic Calculator
==============================

Mathematical Definition:
-----------------------
The Euler characteristic χ is a topological invariant representing the structural
alternating sum of Betti numbers or simplicial complex counts:
χ = β₀ - β₁ + β₂ = V - E + F
"""

from __future__ import annotations

from dataclasses import dataclass

from .betti_numbers import BettiNumbers
from .simplex import SimplicialComplex


@dataclass
class EulerCharacteristic:
    """
    Topological Euler characteristic (χ).

    Attributes
    ----------
    value : int
        The computed integer value of χ.
    """

    value: int

    @classmethod
    def from_complex(cls, complex_: SimplicialComplex) -> EulerCharacteristic:
        """Compute χ from the alternating sum of simplices: χ = Σ (-1)^i n_i."""
        val = 0
        for dim, simps in complex_.simplices.items():
            sign = 1 if dim % 2 == 0 else -1
            val += sign * len(simps)
        return cls(value=val)

    @classmethod
    def from_betti(cls, betti: BettiNumbers) -> EulerCharacteristic:
        """Compute χ from Betti numbers: χ = β₀ - β₁ + β₂."""
        val = betti.betti_0 - betti.betti_1 + betti.betti_2
        return cls(value=val)
