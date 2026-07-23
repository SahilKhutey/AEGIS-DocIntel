"""
Information Conservation Law
============================

Mathematical Definition:
-----------------------
Information is conserved through the document pipeline:

    I_in = I_out + I_compressed + I_discarded

where:
    I_in            input information (e.g., raw document content)
    I_out           output information (e.g., to AI agent)
    I_compressed    information retained in compressed form
    I_discarded     information loss (should be < 5%)

Conservation Error:
    E_c = |I_in - (I_out + I_compressed + I_discarded)|

Valid conservation: E_c < ε (typically ε = 0.05)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import numpy as np

from .exceptions import ConservationViolationError


@dataclass
class ConservationReport:
    """
    Conservation law verification result.

    Attributes
    ----------
    input_information : float
    output_information : float
    compressed_information : float
    discarded_information : float
    total_accounted : float
    conservation_error : float
    is_conserved : bool
    discarded_fraction : float
    """

    input_information: float
    output_information: float
    compressed_information: float
    discarded_information: float
    total_accounted: float
    conservation_error: float
    is_conserved: bool
    discarded_fraction: float

    def to_dict(self) -> dict:
        return {
            "input": round(self.input_information, 6),
            "output": round(self.output_information, 6),
            "compressed": round(self.compressed_information, 6),
            "discarded": round(self.discarded_information, 6),
            "total_accounted": round(self.total_accounted, 6),
            "conservation_error": round(self.conservation_error, 6),
            "is_conserved": self.is_conserved,
            "discarded_fraction": round(self.discarded_fraction, 6),
        }


class ConservationLaw:
    """
    Information conservation law.
    """

    def __init__(self, max_discarded_fraction: float = 0.05) -> None:
        if not (0 <= max_discarded_fraction < 1):
            raise ValueError("max_discarded_fraction must be in [0, 1).")
        self.max_discarded_fraction = max_discarded_fraction

    def check(
        self,
        input_info: float,
        output_info: float,
        compressed_info: float,
        discarded_info: float,
        strict: bool = False,
    ) -> ConservationReport:
        """
        Verify the conservation law.

        Parameters
        ----------
        input_info : float
        output_info : float
        compressed_info : float
        discarded_info : float
        strict : bool
            If True, raise on violation.
        """
        if input_info < 0:
            raise ValueError("input_info must be non-negative.")
        total = output_info + compressed_info + discarded_info
        error = abs(input_info - total)
        is_conserved = error < 1e-6

        discarded_fraction = (
            discarded_info / input_info if input_info > 0 else 0.0
        )
        within_threshold = discarded_fraction <= self.max_discarded_fraction

        report = ConservationReport(
            input_information=float(input_info),
            output_information=float(output_info),
            compressed_information=float(compressed_info),
            discarded_information=float(discarded_info),
            total_accounted=float(total),
            conservation_error=float(error),
            is_conserved=is_conserved and within_threshold,
            discarded_fraction=float(discarded_fraction),
        )

        if strict and not report.is_conserved:
            raise ConservationViolationError(
                f"Conservation violated: error={error:.6f}, "
                f"discarded_fraction={discarded_fraction:.4f}"
            )

        return report


class ConservationChecker:
    """
    Higher-level conservation checker using vectorized inputs.
    """

    def __init__(self, max_discarded_fraction: float = 0.05) -> None:
        self.law = ConservationLaw(max_discarded_fraction=max_discarded_fraction)

    def check_from_arrays(
        self,
        input_vector: np.ndarray,
        output_vector: np.ndarray,
        compressed_vector: np.ndarray,
        discarded_vector: np.ndarray,
    ) -> ConservationReport:
        """Check conservation using summed magnitudes of vectors."""
        return self.law.check(
            input_info=float(np.linalg.norm(input_vector)),
            output_info=float(np.linalg.norm(output_vector)),
            compressed_info=float(np.linalg.norm(compressed_vector)),
            discarded_info=float(np.linalg.norm(discarded_vector)),
        )