"""
Graph Signal Processing
=======================

A graph signal is a function f: V → R assigning a value to each vertex.
The Graph Fourier Transform (GFT) decomposes f into spectral components:

    F̂(λ_l) = <f, u_l> = Σ_i f(i) · u_l(i)

Inverse:
    f(i) = Σ_l F̂(λ_l) · u_l(i)

Applications in AMDI-OS:
- Importance scores as graph signals
- PageRank as a graph signal
- Topic distributions as signals
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np

from .eigen import EigenResult


@dataclass
class GraphSignal:
    """
    A signal defined on a graph's vertices.

    Attributes
    ----------
    values : np.ndarray
        f(v) for each vertex v.
    name : Optional[str]
        Signal identifier.
    """

    values: np.ndarray
    name: Optional[str] = None

    def __post_init__(self) -> None:
        self.values = np.asarray(self.values, dtype=np.float64)
        if self.values.ndim != 1:
            raise ValueError("Graph signal must be 1-dimensional.")

    @property
    def size(self) -> int:
        return len(self.values)

    @property
    def mean(self) -> float:
        return float(self.values.mean())

    @property
    def std(self) -> float:
        return float(self.values.std())

    @property
    def energy(self) -> float:
        """L2 norm squared."""
        return float(np.sum(self.values ** 2))

    @property
    def max(self) -> float:
        return float(self.values.max())

    @property
    def min(self) -> float:
        return float(self.values.min())

    def normalize(self) -> "GraphSignal":
        """L2-normalize the signal."""
        n = np.linalg.norm(self.values)
        if n == 0:
            return self
        return GraphSignal(values=self.values / n, name=self.name)

    def smooth(self, kernel: np.ndarray) -> "GraphSignal":
        """Convolve with a graph-domain kernel."""
        if len(kernel) != self.size:
            raise ValueError("Kernel size must match signal size.")
        return GraphSignal(values=self.values * kernel, name=self.name)

    @classmethod
    def from_dict(cls, mapping: Dict[int, float], n: Optional[int] = None) -> "GraphSignal":
        """Build from vertex → value mapping."""
        if n is None:
            n = max(mapping.keys()) + 1
        values = np.zeros(n)
        for k, v in mapping.items():
            if 0 <= k < n:
                values[k] = v
        return cls(values=values)
