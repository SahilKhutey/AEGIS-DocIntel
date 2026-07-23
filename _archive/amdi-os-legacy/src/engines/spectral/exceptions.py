"""
Custom exceptions for the Spectral Engine.
"""


class SpectralEngineError(Exception):
    """Base exception for all Spectral Engine errors."""


class InvalidGraphError(SpectralEngineError):
    """Raised when the input graph is malformed or empty."""


class EigenDecompositionError(SpectralEngineError):
    """Raised when eigenvalue decomposition fails."""


class ConvergenceError(SpectralEngineError):
    """Raised when an iterative algorithm fails to converge."""


class InsufficientDataError(SpectralEngineError):
    """Raised when there is not enough data for analysis."""
