"""
Tensor Reduction
================

Reductions convert high-order tensors into lower-order summaries:

1. Marginalization (mode collapsing):
       T_reduced[m] = Σ_{iₙ} T[..., iₙ, ...]
    Sum (or mean) over a specific mode.

2. Contraction (mode pairing):
       T_reduced[i₁, i₂, i₃, i₄] = Σ_{i₅} T[i₁, i₂, i₃, i₄, i₅]
    Inner product along a mode — equivalent to multiplying two
    matrices if the mode is paired with another tensor.

3. Slice extraction:
       T_reduced = T[..., fixed_indices, ...]
    Keep only a slice of one mode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

import numpy as np

from .document_tensor import DocumentTensor
from .exceptions import DimensionMismatchError, InvalidTensorError
from .tensor_ops import mode_n_product, tensor_norm


@dataclass
class ReductionResult:
    """
    Result of a tensor reduction.

    Attributes
    ----------
    reduced_tensor : np.ndarray
        Reduced array.
    removed_modes : List[int]
        Modes that were collapsed.
    reduction_type : str
        'marginalize_sum', 'marginalize_mean', 'contract', 'slice'.
    metadata : Dict
    """

    reduced_tensor: np.ndarray
    removed_modes: List[int] = field(default_factory=list)
    reduction_type: str = "unknown"
    metadata: Dict = field(default_factory=dict)

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.reduced_tensor.shape

    @property
    def order(self) -> int:
        return self.reduced_tensor.ndim


def marginalize(
    tensor: np.ndarray,
    mode: int,
    method: str = "sum",
    keepdims: bool = False,
) -> np.ndarray:
    """
    Marginalize (collapse) a tensor along `mode`.

    Parameters
    ----------
    tensor : np.ndarray
    mode : int
        Mode to marginalize over.
    method : str
        'sum' or 'mean'.
    keepdims : bool
        If True, keep the collapsed dimension with size 1.
    """
    T = np.asarray(tensor)
    if method == "sum":
        out = T.sum(axis=mode)
    elif method == "mean":
        out = T.mean(axis=mode)
    else:
        raise ValueError(f"Unknown method: {method}")
    if keepdims:
        out = np.expand_dims(out, axis=mode)
    return out


def contract(
    T: np.ndarray,
    S: np.ndarray,
    mode_T: int,
    mode_S: int,
) -> np.ndarray:
    """
    Contract T and S along specified modes (generalized inner product).

    Reduces order by 2 (one mode from each tensor).

    Parameters
    ----------
    T, S : np.ndarray
    mode_T, mode_S : int
        Modes to contract.
    """
    T = np.asarray(T)
    S = np.asarray(S)
    if T.shape[mode_T] != S.shape[mode_S]:
        raise DimensionMismatchError(
            f"Cannot contract: T[{mode_T}]={T.shape[mode_T]} ≠ S[{mode_S}]={S.shape[mode_S]}."
        )
    return np.tensordot(T, S, axes=([mode_T], [mode_S]))


class TensorReducer:
    """
    Higher-level reduction orchestrator.
    """

    @staticmethod
    def marginalize_all(
        tensor: DocumentTensor,
        modes: List[int],
        method: str = "sum",
    ) -> DocumentTensor:
        """
        Marginalize over multiple modes sequentially.
        """
        data = tensor.data
        removed: List[int] = []
        for m in sorted(modes, reverse=True):
            data = marginalize(data, m, method=method)
            removed.append(m)
        return DocumentTensor(
            data=data,
            mode_labels={k: v for k, v in tensor.mode_labels.items() if k not in modes},
            mode_dims=data.shape,
            metadata={**tensor.metadata, "reduced_modes": removed, "method": method},
        )

    @staticmethod
    def to_matrix(
        tensor: DocumentTensor,
        row_mode: int,
        col_mode: int,
        method: str = "sum",
    ) -> np.ndarray:
        """
        Reduce a tensor to a 2D matrix by marginalizing over all other modes.
        """
        T = tensor.data
        N = T.ndim
        other_modes = [m for m in range(N) if m not in (row_mode, col_mode)]
        reduced = T
        for m in sorted(other_modes, reverse=True):
            reduced = marginalize(reduced, m, method=method)
        # `reduced` now has shape (row_dim, col_dim) if row_mode < col_mode
        # else (col_dim, row_dim)
        if row_mode > col_mode:
            reduced = np.transpose(reduced)
        return reduced

    @staticmethod
    def to_vector(
        tensor: DocumentTensor,
        method: str = "sum",
    ) -> np.ndarray:
        """Reduce a tensor to a 1D vector by marginalizing all modes into one."""
        reduced = tensor.data
        while reduced.ndim > 1:
            reduced = marginalize(reduced, 0, method=method)
        return reduced