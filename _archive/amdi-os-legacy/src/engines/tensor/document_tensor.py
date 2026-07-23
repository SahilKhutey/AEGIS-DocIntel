"""
Document Tensor
===============

In AMDI-OS, a document is represented as a 5-mode tensor:

    T ∈ R^{|P| × |S| × |R| × |C| × |T|}

where:
    Mode 0 (Page):   pages in the document
    Mode 1 (Section): sections per page
    Mode 2 (Row):    rows per section (e.g., table rows)
    Mode 3 (Column): columns per row (e.g., table cells)
    Mode 4 (Token):  tokens per cell (semantic units)

Each entry T[p,s,r,c,t] encodes the importance / relevance / count of
token `t` in cell `(r,c)` of section `s` on page `p`.

This tensor is sparse (mostly zeros) and can be compressed via Tucker / CP / TT.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .exceptions import InvalidTensorError
from .tensor_ops import unfold


class TensorMode(Enum):
    """Standard tensor modes for documents."""

    PAGE = 0
    SECTION = 1
    ROW = 2
    COLUMN = 3
    TOKEN = 4


@dataclass
class DocumentTensor:
    """
    Multi-mode document tensor.

    Attributes
    ----------
    data : np.ndarray
        Dense tensor (may be sparse for large documents).
    mode_labels : Dict[int, List[str]]
        Per-mode labels (e.g., page-1, page-2, ...).
    mode_dims : Tuple[int, ...]
        Dimensions for each mode.
    sparse_repr : Optional[Any]
        Optional scipy.sparse representation.
    metadata : Dict
    """

    data: np.ndarray
    mode_labels: Dict[int, List[str]] = field(default_factory=dict)
    mode_dims: Tuple[int, ...] = ()
    sparse_repr: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        self.data = np.asarray(self.data, dtype=np.float64)
        if self.data.ndim < 2:
            raise InvalidTensorError(
                f"DocumentTensor requires order ≥ 2; got {self.data.ndim}."
            )
        if not self.mode_dims:
            self.mode_dims = tuple(self.data.shape)

    @property
    def order(self) -> int:
        """Tensor order (number of modes)."""
        return self.data.ndim

    @property
    def shape(self) -> Tuple[int, ...]:
        return self.data.shape

    @property
    def size(self) -> int:
        return int(self.data.size)

    @property
    def nnz(self) -> int:
        """Number of non-zero entries."""
        return int(np.count_nonzero(self.data))

    @property
    def density(self) -> float:
        """Fraction of non-zero entries."""
        if self.size == 0:
            return 0.0
        return self.nnz / self.size

    @property
    def num_modes(self) -> int:
        return self.order

    def mode_n_unfold(self, mode: int) -> np.ndarray:
        """Return the mode-n unfolding matrix."""
        return unfold(self.data, mode)

    def mode_n_fiber(self, mode: int, index: Tuple[int, ...]) -> np.ndarray:
        """
        Extract a mode-n fiber (fixing all other indices, varying mode-n).

        Parameters
        ----------
        mode : int
            Mode to vary.
        index : Tuple[int, ...]
            Fixed indices for other modes. Must have length order-1.
        """
        if len(index) != self.order - 1:
            raise InvalidTensorError(
                f"index length {len(index)} ≠ order-1 ({self.order - 1})."
            )
        full_idx = list(index)
        full_idx.insert(mode, slice(None))
        return self.data[tuple(full_idx)]

    def mode_n_slice(self, mode: int, idx: int) -> np.ndarray:
        """Return a sub-tensor by fixing mode-n at index idx."""
        slicer = [slice(None)] * self.order
        slicer[mode] = idx
        return self.data[tuple(slicer)]

    def to_dense(self) -> np.ndarray:
        return self.data.copy()

    def to_sparse(self) -> Any:
        """Convert to scipy.sparse (as a flattened sparse vector view)."""
        try:
            from scipy.sparse import csr_matrix
            flat = self.data.reshape(self.shape[0], -1)
            return csr_matrix(flat)
        except ImportError:
            raise InvalidTensorError("scipy is required for sparse conversion.")

    def normalize(self, ord: str = "frobenius") -> "DocumentTensor":
        """Return an L-norm-normalized copy."""
        n = float(np.linalg.norm(self.data)) if ord == "frobenius" else float(np.abs(self.data).sum())
        if n == 0:
            return self
        return DocumentTensor(
            data=self.data / n,
            mode_labels=self.mode_labels,
            mode_dims=self.mode_dims,
            metadata={**self.metadata, "normalized": ord},
        )

    def __repr__(self) -> str:
        return f"DocumentTensor(order={self.order}, shape={self.shape}, nnz={self.nnz})"


class TensorBuilder:
    """
    Builder for constructing DocumentTensor from structured data.
    """

    @staticmethod
    def from_token_counts(
        token_counts_by_location: Dict[Tuple[int, int, int, int, int], float],
        n_pages: int,
        n_sections: int,
        n_rows: int,
        n_cols: int,
        n_tokens: int,
    ) -> DocumentTensor:
        """
        Build a 5-mode tensor from sparse (p,s,r,c,t) → count mappings.

        Parameters
        ----------
        token_counts_by_location : Dict
            Sparse mapping (page, section, row, col, token) → count.
        n_pages, n_sections, n_rows, n_cols, n_tokens : int
            Mode dimensions.
        """
        T = np.zeros((n_pages, n_sections, n_rows, n_cols, n_tokens), dtype=np.float64)
        for (p, s, r, c, t), v in token_counts_by_location.items():
            if (
                0 <= p < n_pages
                and 0 <= s < n_sections
                and 0 <= r < n_rows
                and 0 <= c < n_cols
                and 0 <= t < n_tokens
            ):
                T[p, s, r, c, t] = v
        return DocumentTensor(
            data=T,
            mode_labels={
                TensorMode.PAGE.value: [f"page_{i}" for i in range(n_pages)],
                TensorMode.SECTION.value: [f"sec_{i}" for i in range(n_sections)],
                TensorMode.ROW.value: [f"row_{i}" for i in range(n_rows)],
                TensorMode.COLUMN.value: [f"col_{i}" for i in range(n_cols)],
                TensorMode.TOKEN.value: [f"tok_{i}" for i in range(n_tokens)],
            },
            mode_dims=(n_pages, n_sections, n_rows, n_cols, n_tokens),
        )

    @staticmethod
    def from_dense_array(data: np.ndarray) -> DocumentTensor:
        """Build from a dense numpy array."""
        return DocumentTensor(data=data)

    @staticmethod
    def from_random(
        shape: Tuple[int, ...],
        density: float = 0.1,
        seed: Optional[int] = 42,
    ) -> DocumentTensor:
        """
        Build a random tensor (for testing).
        """
        rng = np.random.RandomState(seed)
        total = int(np.prod(shape))
        nnz = max(1, int(total * density))
        flat = np.zeros(total)
        flat[:nnz] = rng.rand(nnz)
        rng.shuffle(flat)
        return DocumentTensor(data=flat.reshape(shape).astype(np.float64))

    @staticmethod
    def from_matrix(
        matrix: np.ndarray,
        row_mode: str = "row",
        col_mode: str = "column",
    ) -> DocumentTensor:
        """Lift a 2D matrix to a 2-mode tensor."""
        return DocumentTensor(data=np.asarray(matrix, dtype=np.float64))