"""
Topological Metrics Invariants Summary
======================================

Aggregates multiple topological invariants (Betti numbers, Euler characteristic,
and persistent homology metrics) into a unified document signature.
"""

from __future__ import annotations

from dataclasses import dataclass

from .betti_numbers import BettiNumbers
from .persistence import PersistenceDiagram


@dataclass
class TopologicalMetrics:
    """
    Unified summary of topological invariants for a document.

    Attributes
    ----------
    betti_0 : int
        β₀ (connected components).
    betti_1 : int
        β₁ (loops).
    betti_2 : int
        β₂ (voids).
    euler_characteristic : int
        χ = β₀ - β₁ + β₂
    total_persistence : float
        Sum of finite persistence point lifetimes.
    max_persistence : float
        Maximum lifespan of any finite feature.
    num_persistence_features : int
        Total number of features in the persistence diagram.
    """

    betti_0: int
    betti_1: int
    betti_2: int
    euler_characteristic: int
    total_persistence: float
    max_persistence: float
    num_persistence_features: int

    @classmethod
    def compute(
        cls,
        betti: BettiNumbers,
        diagram: PersistenceDiagram,
    ) -> TopologicalMetrics:
        """Compute aggregated metrics from Betti numbers and persistence diagram."""
        euler = betti.betti_0 - betti.betti_1 + betti.betti_2
        return cls(
            betti_0=betti.betti_0,
            betti_1=betti.betti_1,
            betti_2=betti.betti_2,
            euler_characteristic=euler,
            total_persistence=diagram.total_persistence,
            max_persistence=diagram.max_persistence,
            num_persistence_features=diagram.num_features,
        )
