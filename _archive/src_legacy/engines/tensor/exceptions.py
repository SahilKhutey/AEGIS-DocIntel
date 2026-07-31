"""
Custom exceptions for the Tensor Engine.
"""


class TensorEngineError(Exception):
    """Base exception for all Tensor Engine errors."""


class InvalidTensorError(TensorEngineError):
    """Raised when a tensor has invalid shape or invalid data."""


class DecompositionError(TensorEngineError):
    """Raised when tensor decomposition fails to converge."""


class CompressionError(TensorEngineError):
    """Raised when tensor compression fails."""


class DimensionMismatchError(TensorEngineError):
    """Raised when tensor dimensions are incompatible for an operation."""