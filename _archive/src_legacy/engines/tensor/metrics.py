"""
Tensor Metrics
==============

Provides:
- Frobenius / L1 / L2 / L∞ norms
- Explained variance ratio
- Reconstruction error
- Compression efficiency
- Tensor sparsity / density
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List

import numpy as np

from .exceptions import InvalidTensorError
from .tensor_ops import tensor_norm


@dataclass
class TensorMetrics:
    """
    Aggregated tensor metrics.

    Attributes
    ----------
    order : int
    shape : tuple
    size : int
    nnz : int
    density : float
    frobenius_norm : float
    l1_norm : float
    l2_norm : float
    linfinity_norm : float
    mean : float
    std : float
    max_value : float
    min_value : float
    sparsity_index : float
    """

    order: int
    shape: tuple
    size: int
    nnz: int
    density: float
    frobenius_norm: float
    l1_norm: float
    l2_norm: float
    linfinity_norm: float
    mean: float
    std: float
    max_value: float
    min_value: float
    sparsity_index: float

    def to_dict(self) -> dict:
        return {
            "order": self.order,
            "shape": list(self.shape),
            "size": self.size,
            "nnz": self.nnz,
            "density": round(self.density, 6),
            "frobenius_norm": round(self.frobenius_norm, 6),
            "l1_norm": round(self.l1_norm, 6),
            "l2_norm": round(self.l2_norm, 6),
            "linfinity_norm": round(self.linfinity_norm, 6),
            "mean": round(self.mean, 6),
            "std": round(self.std, 6),
            "max_value": round(self.max_value, 6),
            "min_value": round(self.min_value, 6),
            "sparsity_index": round(self.sparsity_index, 6),
        }


def explained_variance_ratio(
    original: np.ndarray,
    reconstructed: np.ndarray,
) -> float:
    """
    Compute explained variance ratio:

        EVR = 1 - ||T - T̂||²_F / ||T - mean(T)||²_F
    """
    T = np.asarray(original)
    R = np.asarray(reconstructed)
    if T.shape != R.shape:
        raise InvalidTensorError(
            f"Shape mismatch: {T.shape} vs {R.shape}"
        )
    residual = np.linalg.norm(T - R) ** 2
    total = np.linalg.norm(T - T.mean()) ** 2
    if total < 1e-12:
        return 1.0 if residual < 1e-12 else 0.0
    return float(max(0.0, 1.0 - residual / total))


def reconstruction_error(
    original: np.ndarray,
    reconstructed: np.ndarray,
    norm: str = "frobenius",
) -> float:
    """
    Relative reconstruction error: ||T - T̂|| / ||T||.
    """
    T = np.asarray(original)
    R = np.asarray(reconstructed)
    if T.shape != R.shape:
        raise InvalidTensorError(
            f"Shape mismatch: {T.shape} vs {R.shape}"
        )
    n_T = tensor_norm(T, norm)
    if n_T < 1e-12:
        return 0.0
    return float(tensor_norm(T - R, norm) / n_T)


def compute_metrics(tensor: np.ndarray) -> TensorMetrics:
    """Compute all aggregated metrics for a tensor."""
    T = np.asarray(tensor)
    size = int(T.size)
    nnz = int(np.count_nonzero(T))
    density = nnz / size if size > 0 else 0.0
    return TensorMetrics(
        order=T.ndim,
        shape=T.shape,
        size=size,
        nnz=nnz,
        density=density,
        frobenius_norm=tensor_norm(T, "frobenius"),
        l1_norm=tensor_norm(T, "l1"),
        l2_norm=tensor_norm(T, "l2"),
        linfinity_norm=tensor_norm(T, "linf"),
        mean=float(T.mean()) if size > 0 else 0.0,
        std=float(T.std()) if size > 0 else 0.0,
        max_value=float(T.max()) if size > 0 else 0.0,
        min_value=float(T.min()) if size > 0 else 0.0,
        sparsity_index=1.0 - density,
    )