"""
Custom exceptions for the Topology Engine.
"""


class TopologyEngineError(Exception):
    """Base exception for all Topology Engine errors."""


class InvalidManifoldError(TopologyEngineError):
    """Raised when the input manifold is malformed or empty."""


class InsufficientDataError(TopologyEngineError):
    """Raised when there is not enough data to compute topological features."""


class FiltrationError(TopologyEngineError):
    """Raised when filtration construction fails."""


class PersistenceComputationError(TopologyEngineError):
    """Raised when persistent homology computation fails."""
