"""
Information Thermodynamics
==========================

Mathematical Definition:
-----------------------
Shannon entropy of a discrete distribution:

    H(X) = -Σ_x p(x) log₂ p(x)

Document entropy:
    H(D) = -Σ_i p_i log₂ p_i

Temperature (effective "heat"):
    T_eff = H(D) / log₂(N)

Free energy:
    F = U - T_eff · S

where:
    U   internal energy (e.g., total importance)
    S   entropy
    T_eff effective temperature

Used to determine:
- Document disorder
- Optimal compression threshold
- Equilibrium states
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .exceptions import InvalidDocumentError


@dataclass
class ThermodynamicState:
    """
    A complete thermodynamic state of a document.

    Attributes
    ----------
    entropy : float
        Shannon entropy in bits.
    max_entropy : float
        Maximum possible entropy = log₂(N).
    normalized_entropy : float
        H / H_max in [0, 1].
    effective_temperature : float
        T_eff = H / log₂(N).
    internal_energy : float
        U (e.g., total importance).
    free_energy : float
        F = U - T_eff · S.
    heat_capacity : float
        C = dU/dT.
    """

    entropy: float
    max_entropy: float
    normalized_entropy: float
    effective_temperature: float
    internal_energy: float
    free_energy: float
    heat_capacity: float

    def to_dict(self) -> dict:
        return {
            "entropy": round(self.entropy, 6),
            "max_entropy": round(self.max_entropy, 6),
            "normalized_entropy": round(self.normalized_entropy, 6),
            "effective_temperature": round(self.effective_temperature, 6),
            "internal_energy": round(self.internal_energy, 6),
            "free_energy": round(self.free_energy, 6),
            "heat_capacity": round(self.heat_capacity, 6),
        }


class EntropyCalculator:
    """
    Computes Shannon entropy and related quantities.
    """

    @staticmethod
    def shannon(probabilities: np.ndarray, base: float = 2.0) -> float:
        """Shannon entropy: H(X) = -Σ p log_b p."""
        p = np.asarray(probabilities, dtype=np.float64)
        p = p[p > 0]
        if p.size == 0:
            return 0.0
        # normalize
        s = p.sum()
        if s <= 0:
            return 0.0
        p = p / s
        return float(-np.sum(p * np.log(p) / np.log(base)))

    @staticmethod
    def max_entropy(n: int, base: float = 2.0) -> float:
        """Maximum entropy = log_b(n) for uniform distribution."""
        if n <= 1:
            return 0.0
        return float(np.log(n) / np.log(base))

    @staticmethod
    def normalized(probabilities: np.ndarray) -> float:
        """H_norm = H / log(n)."""
        p = np.asarray(probabilities, dtype=np.float64)
        p = p[p > 0]
        if p.size == 0:
            return 0.0
        s = p.sum()
        if s <= 0:
            return 0.0
        p = p / s
        H = float(-np.sum(p * np.log(p)))
        H_max = float(np.log(p.size))
        if H_max < 1e-12:
            return 0.0
        return H / H_max


class Thermodynamics:
    """
    Compute thermodynamic state of a document.
    """

    def __init__(self, base: float = 2.0) -> None:
        self.base = base

    def compute_state(
        self,
        importance: np.ndarray,
        entropy: Optional[np.ndarray] = None,
    ) -> ThermodynamicState:
        """
        Compute thermodynamic state.

        Parameters
        ----------
        importance : np.ndarray
            Per-element importance (used as internal energy proxy).
        entropy : Optional[np.ndarray]
            Per-element entropy. If None, derived from importance distribution.
        """
        imp = np.asarray(importance, dtype=np.float64)
        if imp.size == 0:
            raise InvalidDocumentError("Empty importance array.")
        n = imp.shape[0]

        # probability distribution
        if entropy is None:
            p = imp / max(imp.sum(), 1e-12)
        else:
            ent = np.asarray(entropy, dtype=np.float64)
            if ent.shape != imp.shape:
                raise InvalidDocumentError("entropy shape mismatch.")
            p = ent / max(ent.sum(), 1e-12)

        H = EntropyCalculator.shannon(p, base=self.base)
        H_max = EntropyCalculator.max_entropy(n, base=self.base)
        H_norm = H / H_max if H_max > 0 else 0.0

        U = float(imp.sum())
        T_eff = H_norm  # use normalized entropy as effective temperature
        S = float(np.log(n + 1))
        F = U - T_eff * S
        # heat capacity (rough): dU/dT ≈ U / T
        C = U / max(T_eff, 1e-6)

        return ThermodynamicState(
            entropy=H,
            max_entropy=H_max,
            normalized_entropy=H_norm,
            effective_temperature=T_eff,
            internal_energy=U,
            free_energy=F,
            heat_capacity=C,
        )