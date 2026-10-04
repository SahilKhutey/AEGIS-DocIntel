"""
Tensor Engine — Main Orchestrator
==================================

End-to-end pipeline:

    Document Data
         ↓
    DocumentTensor Construction (5-mode)
         ↓
    ┌──────────────┬────────────────┬───────────────────┐
    │ Tucker       │ CP / PARAFAC   │ Tensor Train (TT) │
    │ Decomposition│ Decomposition  │ Decomposition     │
    └──────────────┴────────────────┴───────────────────┘
         ↓
    Reduction / Compression
         ↓
    TensorReport → Export Object

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from .decomposition import CPDecomposition, TuckerDecomposition
from .document_tensor import DocumentTensor, TensorMode
from .compression import TTDecomposition
from .tensor_ops import mode_n_product

logger = logging.getLogger("amdi.engines.tensor")


@dataclass
class TensorReport:
    """
    Summary report of document tensor properties and compression/decomposition metrics.
    """

    original_shape: Tuple[int, ...]
    original_size: int
    nnz: int
    density: float
    reconstruction_error: float
    explained_variance: float
    compression_ratio: float
    method: str
    core_shape: Optional[Tuple[int, ...]] = None
    factor_shapes: Optional[List[Tuple[int, ...]]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to standard dictionary format."""
        return {
            "original_shape": list(self.original_shape),
            "original_size": self.original_size,
            "nnz": self.nnz,
            "density": self.density,
            "reconstruction_error": self.reconstruction_error,
            "explained_variance": self.explained_variance,
            "compression_ratio": self.compression_ratio,
            "method": self.method,
            "core_shape": list(self.core_shape) if self.core_shape else None,
            "factor_shapes": [list(s) for s in self.factor_shapes] if self.factor_shapes else None,
            "metadata": self.metadata,
        }


class TensorEngine:
    """
    Main orchestrator for the Tensor Engine.
    Converts structured layout elements to a 5-mode tensor T_{psrcT}
    representing Pages, Sections, Rows, Columns, and Tokens.
    """

    def build_tensor(self, elements: List[Dict[str, Any]], max_rows: int = 10, max_cols: int = 10) -> DocumentTensor:
        """
        Converts raw layout blocks to a normalized 5-mode DocumentTensor.
        """
        # Determine vocabulary
        vocab = set()
        for el in elements:
            content = el.get("content", "") or ""
            words = content.split()
            for w in words:
                vocab.add(w)
        vocab_list = sorted(list(vocab))
        vocab_to_idx = {w: idx for idx, w in enumerate(vocab_list)}
        n_tokens = max(1, len(vocab_list))

        pages = sorted(list({el.get("page", 1) for el in elements}))
        sections = sorted(list({el.get("section", "default") or "default" for el in elements}))
        
        n_pages = max(1, len(pages))
        n_sections = max(1, len(sections))
        
        tensor_data = np.zeros((n_pages, n_sections, max_rows, max_cols, n_tokens), dtype=np.float64)
        slice_row_count: Dict[Tuple[int, int], int] = {}

        for el in elements:
            p = el.get("page", 1)
            s = el.get("section", "default") or "default"
            content = el.get("content", "") or ""
            
            p_idx = pages.index(p) if p in pages else 0
            s_idx = sections.index(s) if s in sections else 0
            
            curr_row = slice_row_count.get((p_idx, s_idx), 0)
            if curr_row >= max_rows:
                continue
                
            words = content.split()
            for col_idx in range(min(max_cols, len(words))):
                word = words[col_idx]
                t_idx = vocab_to_idx.get(word, 0)
                try:
                    val = float(word.replace("$", "").replace(",", ""))
                except ValueError:
                    val = float(len(word))
                tensor_data[p_idx, s_idx, curr_row, col_idx, t_idx] = val
                
            slice_row_count[(p_idx, s_idx)] = curr_row + 1

        mode_labels = {
            0: [f"page_{p}" for p in pages],
            1: [f"sec_{s}" for s in sections],
            2: [f"row_{r}" for r in range(max_rows)],
            3: [f"col_{c}" for c in range(max_cols)],
            4: [f"tok_{t}" for t in vocab_list],
        }

        return DocumentTensor(
            data=tensor_data,
            mode_labels=mode_labels,
            mode_dims=tensor_data.shape,
            metadata={"vocab": vocab_list, "pages": pages, "sections": sections},
        )

    def cp_decomposition(self, doc_tensor: DocumentTensor, rank: int = 3) -> List[np.ndarray]:
        """
        Runs CANDECOMP/PARAFAC (CP) decomposition via ALS.
        Falls back to SVD unfolding on failure.
        """
        try:
            cpd = CPDecomposition(rank=rank, max_iter=50, tol=1e-5)
            res = cpd.decompose(doc_tensor.data)
            return [F[:, :rank] for F in res.factors]
        except Exception as e:
            logger.warning(f"CP decomposition via ALS failed: {e}. Falling back to SVD unfolding.")
            T = doc_tensor.data
            factors = []
            for mode in range(T.ndim):
                unfolded = np.moveaxis(T, mode, 0).reshape(T.shape[mode], -1)
                try:
                    U, S, Vt = np.linalg.svd(unfolded, full_matrices=False)
                    if U.shape[1] < rank:
                        pad = np.zeros((U.shape[0], rank - U.shape[1]))
                        U_factor = np.hstack([U, pad])
                    else:
                        U_factor = U[:, :rank]
                    factors.append(U_factor)
                except Exception as svd_e:
                    logger.error(f"SVD unfolding fallback failed for mode {mode}: {svd_e}")
                    factors.append(np.zeros((T.shape[mode], rank)))
            return factors

    def tucker_decomposition(self, doc_tensor: DocumentTensor, ranks: List[int]) -> Tuple[np.ndarray, List[np.ndarray]]:
        """
        Tucker decomposition: T ≈ G x_1 U_1 x_2 U_2 x_3 U_3 x_4 U_4 ...
        Returns core tensor G and factor matrices U.
        """
        try:
            td = TuckerDecomposition(ranks=tuple(ranks), max_iter=30, tol=1e-5)
            res = td.decompose(doc_tensor.data)
            return res.core, res.factors
        except Exception as e:
            logger.warning(f"Tucker decomposition via HOOI failed: {e}. Falling back to SVD.")
            T = doc_tensor.data
            factors = []
            for mode in range(T.ndim):
                unfolded = np.moveaxis(T, mode, 0).reshape(T.shape[mode], -1)
                r = min(ranks[mode], unfolded.shape[0]) if mode < len(ranks) else min(10, unfolded.shape[0])
                try:
                    U, S, Vt = np.linalg.svd(unfolded, full_matrices=False)
                    factors.append(U[:, :r])
                except Exception as svd_e:
                    logger.error(f"SVD fallback failed for mode {mode}: {svd_e}")
                    factors.append(np.zeros((T.shape[mode], r)))
            
            # Compute core tensor by contracting along factor matrices
            core = T.copy()
            for mode in range(min(T.ndim, len(factors))):
                core = self.mode_n_product(core, factors[mode].T, mode)
            return core, factors

    @staticmethod
    def mode_n_product(tensor: np.ndarray, matrix: np.ndarray, mode: int) -> np.ndarray:
        """Computes the mode-n product of a tensor and a matrix."""
        return mode_n_product(tensor, matrix, mode)

    def analyze(
        self,
        tensor: DocumentTensor,
        method: str = "tucker",
        rank: int = 5,
        ranks: Optional[List[int]] = None,
        tol: float = 1e-6,
    ) -> TensorReport:
        """
        Perform complete tensor analysis and return a TensorReport.
        """
        original_size = tensor.size
        nnz = tensor.nnz
        density = tensor.density
        
        if method == "tucker":
            ranks_tuple = tuple(ranks) if ranks else tuple(min(s, rank) for s in tensor.shape)
            td = TuckerDecomposition(ranks=ranks_tuple, tol=tol)
            res = td.decompose(tensor.data)
            reconstruction_error = res.reconstruction_error
            explained_variance = res.explained_variance
            compression_ratio = res.compression_ratio
            core_shape = res.core.shape
            factor_shapes = [U.shape for U in res.factors]
            metadata = {
                "converged": res.converged,
                "iterations": res.n_iterations,
                "ranks": res.ranks,
            }
        elif method == "cp":
            cpd = CPDecomposition(rank=rank, tol=tol)
            res = cpd.decompose(tensor.data)
            reconstruction_error = res.reconstruction_error
            explained_variance = res.explained_variance
            compression_ratio = res.compression_ratio
            core_shape = (rank,)
            factor_shapes = [U.shape for U in res.factors]
            metadata = {
                "converged": res.converged,
                "iterations": res.n_iterations,
            }
        elif method == "tt":
            tt = TTDecomposition(max_rank=rank, tol=tol)
            res = tt.decompose(tensor.data)
            reconstruction_error = res.reconstruction_error
            explained_variance = max(0.0, 1.0 - res.reconstruction_error ** 2)
            compression_ratio = res.compression_ratio
            core_shape = None
            factor_shapes = [G.shape for G in res.cores]
            metadata = {
                "ranks": res.ranks,
                "compressed_size": res.compressed_size,
            }
        else:
            raise ValueError(f"Unknown analysis method: {method}")

        return TensorReport(
            original_shape=tensor.shape,
            original_size=original_size,
            nnz=nnz,
            density=density,
            reconstruction_error=reconstruction_error,
            explained_variance=explained_variance,
            compression_ratio=compression_ratio,
            method=method,
            core_shape=core_shape,
            factor_shapes=factor_shapes,
            metadata=metadata,
        )
