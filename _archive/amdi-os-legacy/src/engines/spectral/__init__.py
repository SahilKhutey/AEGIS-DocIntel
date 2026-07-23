"""
AMDI-OS Spectral Engine
========================

Performs spectral analysis of document graphs:
- Eigenvalues / Eigenvectors of graph Laplacian
- Spectral Clustering (Ng-Jordan-Weiss)
- Pattern Detection (periodicity, repetition)
- Graph Signal Processing & Fourier Transform
- Heat Kernel diffusion for importance ranking

Mathematical Foundation:
- Graph Laplacian: L = D - A
- Normalized Laplacian: L_norm = D^(-1/2) L D^(-1/2)
- Spectral decomposition: L = U Λ U^T
- Graph Fourier Transform: F(x) = U^T x
- Heat kernel: H_t = exp(-tL)

Author : AMDI-OS Development Team
Version: 1.0.0
License: Proprietary
"""

from .spectral_engine import SpectralEngine, SpectralReport
from .adjacency import AdjacencyMatrix, AdjacencyType
from .laplacian import LaplacianBuilder, LaplacianType, LaplacianMatrix
from .eigen import EigenSolver, EigenResult
from .spectral_clustering import SpectralClusterer, SpectralClusterResult, Cluster
from .pattern_detector import PatternDetector, PatternResult, Pattern
from .graph_signals import GraphSignal
from .heat_kernel import HeatKernel, HeatDiffusionResult
from .fourier import GraphFourierTransform, FourierResult
from .exceptions import (
    SpectralEngineError,
    InvalidGraphError,
    EigenDecompositionError,
    ConvergenceError,
    InsufficientDataError,
)

__all__ = [
    "SpectralEngine",
    "SpectralReport",
    "AdjacencyMatrix",
    "AdjacencyType",
    "LaplacianBuilder",
    "LaplacianType",
    "LaplacianMatrix",
    "EigenSolver",
    "EigenResult",
    "SpectralClusterer",
    "SpectralClusterResult",
    "Cluster",
    "PatternDetector",
    "PatternResult",
    "Pattern",
    "GraphSignal",
    "HeatKernel",
    "HeatDiffusionResult",
    "GraphFourierTransform",
    "FourierResult",
    "SpectralEngineError",
    "InvalidGraphError",
    "EigenDecompositionError",
    "ConvergenceError",
    "InsufficientDataError",
]

__version__ = "1.0.0"
