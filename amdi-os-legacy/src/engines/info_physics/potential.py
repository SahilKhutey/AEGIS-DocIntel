"""
Information Potential
=====================

Mathematical Definition:
-----------------------
Information potential energy measures "stored" importance due to position
and connectivity:

    PE(i) = Importance_i × Position_i

where:
    Importance_i ∈ [0, 1]  semantic / structural importance
    Position_i ∈ [0, 1]   location score (e.g., 1.0 at top of page, 0.0 at bottom)

Total potential of a document:
    PE_total = Σ_i PE(i)

High PE → immediate retrieval priority
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .exceptions import InvalidDocumentError


@dataclass
class InformationPotential:
    """
    Potential energy of a single element.

    Attributes
    ----------
    element_id : int
    importance : float
    position_score : float
    potential_energy : float
    """

    element_id: int
    importance: float
    position_score: float
    potential_energy: float


@dataclass
class PotentialField:
    """
    Potential energy distribution.

    Attributes
    ----------
    potentials : np.ndarray
    total_potential : float
    mean_potential : float
    high_potential_elements : List[int]
    """

    potentials: np.ndarray
    total_potential: float
    mean_potential: float
    high_potential_elements: List[int]

    @property
    def max_potential(self) -> float:
        return float(self.potentials.max())

    @property
    def max_element(self) -> int:
        return int(np.argmax(self.potentials))


class PotentialCalculator:
    """
    Computes information potential energy.
    """

    def __init__(self, threshold: float = 0.7) -> None:
        self.threshold = threshold

    def compute(
        self,
        importance: np.ndarray,
        position_scores: Optional[np.ndarray] = None,
        coordinates: Optional[np.ndarray] = None,
    ) -> PotentialField:
        """
        Compute potential energy.

        Parameters
        ----------
        importance : np.ndarray
            (n,) per-element importance.
        position_scores : Optional[np.ndarray]
            (n,) explicit position scores in [0, 1]. If None, computed from coordinates.
        coordinates : Optional[np.ndarray]
            (n, d) coordinates used to compute position scores if not provided.
        """
        imp = np.asarray(importance, dtype=np.float64)
        n = imp.shape[0]
        if n == 0:
            raise InvalidDocumentError("Empty importance array.")

        if position_scores is None:
            if coordinates is None:
                position_scores = np.ones(n, dtype=np.float64)
            else:
                coords = np.asarray(coordinates, dtype=np.float64)
                if coords.ndim != 2 or coords.shape[0] != n:
                    raise InvalidDocumentError("Invalid coordinates.")
                # use y-coordinate (or first dim) to derive position score
                # top = high score
                first_axis = coords[:, 0]
                if first_axis.max() > first_axis.min():
                    pos = (first_axis - first_axis.min()) / (
                        first_axis.max() - first_axis.min()
                    )
                    position_scores = 1.0 - pos  # invert: top has high score
                else:
                    position_scores = np.ones(n) * 0.5
        else:
            position_scores = np.asarray(position_scores, dtype=np.float64)
            if position_scores.shape[0] != n:
                raise InvalidDocumentError("position_scores length mismatch.")

        potentials = imp * position_scores
        high_pe = [int(i) for i in range(n) if potentials[i] >= self.threshold]

        return PotentialField(
            potentials=potentials,
            total_potential=float(potentials.sum()),
            mean_potential=float(potentials.mean()),
            high_potential_elements=high_pe,
        )

    def compute_from_layout(
        self,
        importance: np.ndarray,
        y_coordinates: np.ndarray,
    ) -> PotentialField:
        """Compute PE from explicit y-coordinates."""
        n = importance.shape[0]
        if y_coordinates.shape[0] != n:
            raise InvalidDocumentError("y_coordinates length mismatch.")
        y_min, y_max = y_coordinates.min(), y_coordinates.max()
        if y_max > y_min:
            pos = 1.0 - (y_coordinates - y_min) / (y_max - y_min)
        else:
            pos = np.ones(n) * 0.5
        return self.compute(importance, position_scores=pos)