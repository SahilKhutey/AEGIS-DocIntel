"""
AMDI-OS Topology Engine
=======================

Represents documents as topological manifolds and extracts structural invariants
(connected components, loops, clusters, persistence) for retrieval and analysis.

Mathematical Foundations:
- Simplicial Homology: H₀, H₁, H₂
- Persistent Homology: Vietoris-Rips filtration
- Betti Numbers: β₀ (components), β₁ (loops), β₂ (voids)
- Euler Characteristic: χ = Σ(-1)^i βᵢ

Author : AMDI-OS Development Team
Version: 1.0.0
License: Proprietary
"""

from .topology_engine import TopologyEngine, TopologicalSignature
from .manifold import DocumentManifold
from .connected_components import ConnectedComponentsAnalyzer, ConnectedComponentsResult
from .loops import LoopsAnalyzer, LoopsResult, Loop
from .clusters import TopologicalClusters, ClustersResult, Cluster
from .persistence import PersistenceAnalyzer, PersistenceResult, PersistenceDiagram, PersistencePoint
from .filtration import VietorisRipsFiltration
from .simplex import SimplicialComplex, Simplex
from .betti_numbers import BettiNumbers
from .euler_characteristic import EulerCharacteristic
from .distance_matrix import DistanceMatrix
from .topological_metrics import TopologicalMetrics
from .exceptions import (
    TopologyEngineError,
    InvalidManifoldError,
    InsufficientDataError,
    FiltrationError,
    PersistenceComputationError,
)

__all__ = [
    "TopologyEngine",
    "TopologicalSignature",
    "DocumentManifold",
    "ConnectedComponentsAnalyzer",
    "ConnectedComponentsResult",
    "LoopsAnalyzer",
    "LoopsResult",
    "Loop",
    "TopologicalClusters",
    "ClustersResult",
    "Cluster",
    "PersistenceAnalyzer",
    "PersistenceResult",
    "PersistenceDiagram",
    "PersistencePoint",
    "VietorisRipsFiltration",
    "SimplicialComplex",
    "Simplex",
    "BettiNumbers",
    "EulerCharacteristic",
    "DistanceMatrix",
    "TopologicalMetrics",
    "TopologyEngineError",
    "InvalidManifoldError",
    "InsufficientDataError",
    "FiltrationError",
    "PersistenceComputationError",
]

__version__ = "1.0.0"
