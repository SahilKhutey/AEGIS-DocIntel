"""
Graph Fourier Transform
=======================

Given eigen-decomposition L = U Λ U^T:

    Forward:  F̂ = U^T · f
    Inverse:  f   = U · F̂

Energy spectrum:
    E(λ) = |F̂(λ)|²

In AMDI-OS:
- Decompose document importance signals into spectral bands
- Identify which frequencies (clusters/components) carry most energy
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

import numpy as np

from .eigen import EigenResult
from .exceptions import InvalidGraphError
from .graph_signals import GraphSignal


@dataclass
class FourierResult:
    """
    Result of graph Fourier transform.

    Attributes
    ----------
    coefficients : np.ndarray
        F̂(λ_l) for each eigenvalue.
    energy_spectrum : np.ndarray
        |F̂(λ_l)|².
    dominant_frequencies : List[int]
        Indices of dominant frequency components.
    energy_concentration : float
        Fraction of energy in top-3 frequencies.
    """

    coefficients: np.ndarray
    energy_spectrum: np.ndarray
    dominant_frequencies: List[int]
    energy_concentration: float


class GraphFourierTransform:
    """
    Performs forward/inverse Graph Fourier Transform.
    """

    @staticmethod
    def forward(signal: GraphSignal, eigen_result: EigenResult) -> FourierResult:
        """
        Compute forward GFT: F̂ = U^T f
        """
        if signal.size != eigen_result.eigenvectors.shape[0]:
            raise InvalidGraphError(
                f"Signal size {signal.size} ≠ graph size {eigen_result.eigenvectors.shape[0]}."
            )
        U = eigen_result.eigenvectors
        coeffs = U.T @ signal.values
        energy = coeffs ** 2
        total_energy = energy.sum()
        # dominant = top 3 (excluding zero-freq if needed)
        sorted_idx = np.argsort(energy)[::-1]
        dominant = sorted_idx[:3].tolist()
        concentration = float(energy[dominant].sum() / total_energy) if total_energy > 0 else 0.0

        return FourierResult(
            coefficients=coeffs,
            energy_spectrum=energy,
            dominant_frequencies=dominant,
            energy_concentration=concentration,
        )

    @staticmethod
    def inverse(fourier: FourierResult, eigen_result: EigenResult) -> GraphSignal:
        """
        Inverse GFT: f = U F̂
        """
        U = eigen_result.eigenvectors
        reconstructed = U @ fourier.coefficients
        return GraphSignal(values=reconstructed)

    @staticmethod
    def filter_lowpass(
        signal: GraphSignal,
        eigen_result: EigenResult,
        cutoff: int,
    ) -> GraphSignal:
        """Keep only the lowest `cutoff` frequency components."""
        fourier = GraphFourierTransform.forward(signal, eigen_result)
        filtered_coeffs = np.zeros_like(fourier.coefficients)
        filtered_coeffs[:cutoff] = fourier.coefficients[:cutoff]
        return GraphFourierTransform.inverse(
            FourierResult(
                coefficients=filtered_coeffs,
                energy_spectrum=filtered_coeffs ** 2,
                dominant_frequencies=[],
                energy_concentration=0.0,
            ),
            eigen_result,
        )

    @staticmethod
    def filter_highpass(
        signal: GraphSignal,
        eigen_result: EigenResult,
        cutoff: int,
    ) -> GraphSignal:
        """Keep only frequencies above `cutoff`."""
        fourier = GraphFourierTransform.forward(signal, eigen_result)
        filtered_coeffs = np.zeros_like(fourier.coefficients)
        filtered_coeffs[cutoff:] = fourier.coefficients[cutoff:]
        return GraphFourierTransform.inverse(
            FourierResult(
                coefficients=filtered_coeffs,
                energy_spectrum=filtered_coeffs ** 2,
                dominant_frequencies=[],
                energy_concentration=0.0,
            ),
            eigen_result,
        )
