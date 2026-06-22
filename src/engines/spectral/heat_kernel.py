"""
Heat Kernel Diffusion
=====================

The heat equation on a graph:

    ∂f/∂t = -L f

Solution:
    f(t) = exp(-t L) · f(0)

The heat kernel H_t = exp(-t L) = U · exp(-t Λ) · U^T

Properties:
- H_t(i,i) = Σ_l u_l(i)² exp(-t λ_l)  →  diagonal = heat content at vertex i
- As t → 0:  H_t → I  (identity)
- As t → ∞:  H_t → ½½^T  (projects onto trivial eigenvector)
- H_t spreads "heat" from sources across the graph

In AMDI-OS, used for:
- Multi-scale importance ranking
- Information diffusion simulation
- Relevance propagation
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

import numpy as np

from .eigen import EigenResult, EigenSolver
from .graph_signals import GraphSignal
from .laplacian import LaplacianBuilder, LaplacianType
from .adjacency import AdjacencyMatrix


@dataclass
class HeatDiffusionResult:
    """
    Result of heat diffusion.

    Attributes
    ----------
    diffused_signals : Dict[float, np.ndarray]
        t → f(t) (diffused signal at each time).
    diagonal : np.ndarray
        H_t(i,i) — heat content at each vertex.
    total_heat : np.ndarray
        Row sums of H_t.
    heat_sources : List[int]
        Vertices identified as heat sources.
    """

    diffused_signals: Dict[float, np.ndarray] = field(default_factory=dict)
    diagonal: np.ndarray = field(default_factory=lambda: np.array([]))
    total_heat: np.ndarray = field(default_factory=lambda: np.array([]))
    heat_sources: List[int] = field(default_factory=list)


class HeatKernel:
    """
    Heat diffusion on a graph.
    """

    def __init__(
        self,
        laplacian_type: LaplacianType = LaplacianType.SYMMETRIC_NORMALIZED,
    ) -> None:
        self.laplacian_type = laplacian_type

    def diffuse(
        self,
        adjacency: AdjacencyMatrix,
        initial_signal: np.ndarray,
        times: List[float],
        eigen_result: EigenResult | None = None,
    ) -> HeatDiffusionResult:
        """
        Run heat diffusion from initial signal at given time points.

        Parameters
        ----------
        adjacency : AdjacencyMatrix
        initial_signal : np.ndarray
            f(0) — initial signal.
        times : List[float]
            Diffusion times to evaluate.
        eigen_result : Optional[EigenResult]
        """
        n = adjacency.size
        initial_signal = np.asarray(initial_signal, dtype=np.float64)
        if initial_signal.shape[0] != n:
            raise ValueError(
                f"Signal size {initial_signal.shape[0]} ≠ graph size {n}."
            )

        # Build Laplacian and eigen-decompose
        if eigen_result is None:
            laplacian = LaplacianBuilder.build(adjacency, self.laplacian_type)
            eigen_result = EigenSolver().solve(laplacian, k=n)

        U = eigen_result.eigenvectors
        eigvals = eigen_result.eigenvalues

        # F̂ = U^T f(0)
        coeffs = U.T @ initial_signal

        diffused: Dict[float, np.ndarray] = {}
        diag_at_max: np.ndarray | None = None
        for t in times:
            # f(t) = U · exp(-t Λ) · F̂
            decay = np.exp(-t * eigvals)
            f_t = U @ (decay * coeffs)
            diffused[t] = f_t
            # diagonal of H_t = U · exp(-t Λ) · U^T
            if diag_at_max is None or t == max(times):
                diag_at_max = (U ** 2) @ np.exp(-t * eigvals)

        # heat sources = vertices with highest initial signal
        heat_sources = np.argsort(initial_signal)[::-1][: max(1, n // 10)].tolist()
        heat_sources = [int(x) for x in heat_sources]

        max_t = max(times) if times else 1.0
        return HeatDiffusionResult(
            diffused_signals=diffused,
            diagonal=diag_at_max if diag_at_max is not None else np.array([]),
            total_heat=(U ** 2 @ np.exp(-max_t * eigvals)) if times else np.zeros(n),
            heat_sources=heat_sources,
        )

    def importance_ranking(
        self,
        adjacency: AdjacencyMatrix,
        seed_vertices: List[int],
        t: float = 1.0,
    ) -> Dict[int, float]:
        """
        Compute importance ranking via heat diffusion from seed vertices.
        """
        n = adjacency.size
        initial = np.zeros(n)
        for v in seed_vertices:
            if 0 <= v < n:
                initial[v] = 1.0
        result = self.diffuse(adjacency, initial, times=[t])
        if t in result.diffused_signals:
            return {int(i): float(result.diffused_signals[t][i]) for i in range(n)}
        return {}
