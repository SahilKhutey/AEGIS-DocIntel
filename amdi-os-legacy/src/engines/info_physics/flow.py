"""
Information Flow / Kinetics
===========================

Mathematical Definition:
-----------------------
The rate of change of information through the document:

    I_K = dI/dt

Useful for:
- Tracking document evolution (versioned PDFs)
- Identifying rapidly-changing sections
- Quantifying update frequency

Discrete version:
    ΔI(i, t) = I(i, t+1) - I(i, t)

Flow vector:
    F(i, j) = I(j, t+1) - I(i, t)

Conservation form:
    Σ_i ΔI(i) = Σ_in - Σ_out
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .exceptions import InvalidDocumentError


@dataclass
class FlowVector:
    """
    Information flow from source to target.

    Attributes
    ----------
    source_id : int
    target_id : int
    flow_rate : float
    magnitude : float
    direction : Tuple[float, ...]
    """

    source_id: int
    target_id: int
    flow_rate: float
    magnitude: float
    direction: Tuple[float, ...]

    def is_inflow(self) -> bool:
        return self.flow_rate > 0

    def is_outflow(self) -> bool:
        return self.flow_rate < 0


@dataclass
class InformationFlow:
    """
    Aggregate flow information.

    Attributes
    ----------
    delta_I : np.ndarray
        Per-element change in information.
    flow_matrix : np.ndarray
        Pairwise flow rates.
    net_inflow : np.ndarray
        Net inflow per element.
    total_inflow : float
    total_outflow : float
    most_dynamic_element : int
    """

    delta_I: np.ndarray
    flow_matrix: np.ndarray
    net_inflow: np.ndarray
    total_inflow: float
    total_outflow: float
    most_dynamic_element: int


class FlowCalculator:
    """
    Computes information flow / kinetics.
    """

    def compute_delta(
        self,
        importance_t0: np.ndarray,
        importance_t1: np.ndarray,
    ) -> np.ndarray:
        """Compute ΔI between two time steps."""
        a = np.asarray(importance_t0, dtype=np.float64)
        b = np.asarray(importance_t1, dtype=np.float64)
        if a.shape != b.shape:
            raise InvalidDocumentError("Time-step shapes mismatch.")
        return b - a

    def compute_flow(
        self,
        importance_t0: np.ndarray,
        importance_t1: np.ndarray,
        adjacency: Optional[np.ndarray] = None,
    ) -> InformationFlow:
        """
        Compute information flow between two time steps.

        Parameters
        ----------
        importance_t0 : np.ndarray
            Importance at time t=0.
        importance_t1 : np.ndarray
            Importance at time t=1.
        adjacency : Optional[np.ndarray]
            (n, n) adjacency matrix. If None, only ΔI is computed.
        """
        delta = self.compute_delta(importance_t0, importance_t1)
        n = delta.shape[0]

        if adjacency is None:
            adj = np.eye(n)
        else:
            adj = np.asarray(adjacency, dtype=np.float64)
            if adj.shape != (n, n):
                raise InvalidDocumentError("Adjacency shape mismatch.")

        # flow_matrix[i, j] = delta[j] - delta[i] (signed flow direction)
        flow_matrix = np.outer(np.ones(n), delta) - np.outer(delta, np.ones(n))
        flow_matrix *= adj

        # net inflow per element
        net_inflow = flow_matrix.sum(axis=1)

        total_in = float(np.maximum(net_inflow, 0).sum())
        total_out = float(np.abs(np.minimum(net_inflow, 0).sum()))

        most_dynamic = int(np.argmax(np.abs(delta)))

        return InformationFlow(
            delta_I=delta,
            flow_matrix=flow_matrix,
            net_inflow=net_inflow,
            total_inflow=total_in,
            total_outflow=total_out,
            most_dynamic_element=most_dynamic,
        )

    def flow_vector(
        self,
        source_id: int,
        target_id: int,
        source_value: float,
        target_value: float,
        direction: Optional[Tuple[float, ...]] = None,
    ) -> FlowVector:
        """Build a single FlowVector."""
        if source_id == target_id:
            raise InvalidDocumentError("source and target must differ.")
        delta = target_value - source_value
        if direction is None:
            direction = (1.0, 0.0)
        magnitude = abs(delta)
        return FlowVector(
            source_id=source_id,
            target_id=target_id,
            flow_rate=delta,
            magnitude=magnitude,
            direction=direction,
        )