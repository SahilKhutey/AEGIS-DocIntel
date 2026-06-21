"""
Information Energy
==================

Mathematical Definition:
-----------------------
Each document element v_i carries an information energy:

    I_E(i) = i_H(i) × i_R(i)

where:
    i_H(i) ∈ [0, 1]   is the entropy contribution (uniqueness / rarity)
    i_R(i) ∈ [0, 1]   is the relevance score (semantic importance)

High-energy elements:
    - Conclusions, warnings, critical values, page numbers, headers, footers
Low-energy elements:
    - Common phrases, filler words, repeated boilerplate

Total document energy:
    E_total = Σ_i I_E(i)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

import numpy as np

from .exceptions import InvalidDocumentError


@dataclass
class InformationEnergy:
    """
    Information energy of a single document element.

    Attributes
    ----------
    element_id : int
    entropy_component : float
    relevance_component : float
    total_energy : float
    """

    element_id: int
    entropy_component: float
    relevance_component: float
    total_energy: float

    @property
    def is_high_energy(self) -> bool:
        return self.total_energy >= 0.7

    @property
    def is_low_energy(self) -> bool:
        return self.total_energy <= 0.2


@dataclass
class EnergyField:
    """
    Energy distribution over all elements.

    Attributes
    ----------
    energies : Dict[int, float]
        Element ID → energy value.
    total_energy : float
    mean_energy : float
    max_energy_element : int
    """

    energies: Dict[int, float]
    total_energy: float
    mean_energy: float
    max_energy_element: int


class EnergyCalculator:
    """
    Computes information energy of document elements.
    """

    def __init__(
        self,
        entropy_weight: float = 0.5,
        relevance_weight: float = 0.5,
    ) -> None:
        if entropy_weight + relevance_weight <= 0:
            raise ValueError("weights must sum to a positive number.")
        s = entropy_weight + relevance_weight
        self.entropy_weight = entropy_weight / s
        self.relevance_weight = relevance_weight / s

    def compute(
        self,
        entropy_scores: np.ndarray,
        relevance_scores: np.ndarray,
    ) -> EnergyField:
        """
        Compute information energy.

        Parameters
        ----------
        entropy_scores : np.ndarray
            Per-element entropy / uniqueness scores in [0, 1].
        relevance_scores : np.ndarray
            Per-element relevance scores in [0, 1].
        """
        h = np.asarray(entropy_scores, dtype=np.float64)
        r = np.asarray(relevance_scores, dtype=np.float64)
        if h.shape != r.shape:
            raise InvalidDocumentError(
                f"Shape mismatch: entropy {h.shape} vs relevance {r.shape}"
            )
        if h.size == 0:
            raise InvalidDocumentError("Empty energy input.")

        energies = self.entropy_weight * h + self.relevance_weight * (h * r)
        # alternative formulation: combine multiplicatively for joint effect
        energies_multiplicative = h * r
        # weighted sum of both
        combined = 0.5 * energies + 0.5 * energies_multiplicative

        total = float(combined.sum())
        mean = float(combined.mean())
        max_idx = int(np.argmax(combined))

        return EnergyField(
            energies={i: float(combined[i]) for i in range(len(combined))},
            total_energy=total,
            mean_energy=mean,
            max_energy_element=max_idx,
        )

    def compute_from_frequencies(
        self,
        term_frequencies: Dict[str, int],
        relevance_scores: Optional[Dict[str, float]] = None,
    ) -> EnergyField:
        """
        Compute energies from term frequencies (TF-based entropy).
        """
        if not term_frequencies:
            raise InvalidDocumentError("term_frequencies is empty.")
        total_terms = sum(term_frequencies.values())
        if total_terms == 0:
            raise InvalidDocumentError("total term count is zero.")
        # entropy per term: -p log p, then normalized
        probs = np.array([c / total_terms for c in term_frequencies.values()])
        entropy_per_term = -probs * np.log2(probs + 1e-12)
        # normalize to [0, 1]
        max_ent = np.log2(len(probs)) if len(probs) > 1 else 1.0
        entropy_norm = entropy_per_term / max_ent if max_ent > 0 else entropy_per_term

        terms = list(term_frequencies.keys())
        if relevance_scores is None:
            relevance_norm = np.ones_like(entropy_norm)
        else:
            relevance_norm = np.array(
                [relevance_scores.get(t, 0.5) for t in terms]
            )

        energies = entropy_norm * relevance_norm
        total = float(energies.sum())
        mean = float(energies.mean())
        max_idx = int(np.argmax(energies))

        return EnergyField(
            energies={i: float(energies[i]) for i in range(len(terms))},
            total_energy=total,
            mean_energy=mean,
            max_energy_element=max_idx,
        )