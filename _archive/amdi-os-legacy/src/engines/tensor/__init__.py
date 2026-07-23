"""
AMDI-OS Tensor Engine
======================

Represents documents as multi-mode tensors capturing relationships across:
- Page mode
- Section mode
- Row mode
- Column mode
- Token mode

Provides:
- Tucker decomposition (multi-mode PCA)
- CP / PARAFAC decomposition (sum of rank-1 tensors)
- Tensor Train (TT) compression
- Mode-n unfolding & matricization
- Multi-mode reduction & contraction

Mathematical Foundation:
- Tensor: T ∈ R^{I₁ × I₂ × ... × I_N}
- Tucker: T ≈ G ×₁ U₁ ×₂ U₂ ... ×ₙ Uₙ
- CP:      T ≈ Σᵣ λᵣ u₁ʳ ∘ u₂ʳ ∘ ... ∘ uₙʳ
- TT:      T(i₁,...,iₙ) = G₁(i₁) G₂(i₂) ... Gₙ(iₙ)

Author : AMDI-OS Development Team
Version: 1.0.0
License: Proprietary
"""

from .tensor_engine import TensorEngine, TensorReport
from .document_tensor import (
    DocumentTensor,
    TensorMode,
    TensorBuilder,
)
from .tensor_ops import (
    mode_n_product,
    unfold,
    fold,
    tensor_norm,
    outer_product,
    khatri_rao_product,
    hadamard_product,
)
from .decomposition import (
    TuckerDecomposition,
    TuckerResult,
    CPDecomposition,
    CPResult,
)
from .reduction import (
    TensorReducer,
    ReductionResult,
    marginalize,
    contract,
)
from .compression import (
    TensorCompressor,
    TTDecomposition,
    TTResult,
    rank_truncate,
)
from .metrics import (
    TensorMetrics,
    explained_variance_ratio,
    reconstruction_error,
)
from .exceptions import (
    TensorEngineError,
    InvalidTensorError,
    DecompositionError,
    CompressionError,
)

__all__ = [
    "TensorEngine",
    "TensorReport",
    "DocumentTensor",
    "TensorMode",
    "TensorBuilder",
    "mode_n_product",
    "unfold",
    "fold",
    "tensor_norm",
    "outer_product",
    "khatri_rao_product",
    "hadamard_product",
    "TuckerDecomposition",
    "TuckerResult",
    "CPDecomposition",
    "CPResult",
    "TensorReducer",
    "ReductionResult",
    "marginalize",
    "contract",
    "TensorCompressor",
    "TTDecomposition",
    "TTResult",
    "rank_truncate",
    "TensorMetrics",
    "explained_variance_ratio",
    "reconstruction_error",
    "TensorEngineError",
    "InvalidTensorError",
    "DecompositionError",
    "CompressionError",
]

__version__ = "1.0.0"