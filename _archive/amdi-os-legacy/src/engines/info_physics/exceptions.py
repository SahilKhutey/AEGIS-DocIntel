"""
Custom exceptions for the Information Physics Engine.
"""


class PhysicsEngineError(Exception):
    """Base exception for all Information Physics Engine errors."""


class InvalidDocumentError(PhysicsEngineError):
    """Raised when the input document representation is invalid."""


class ConservationViolationError(PhysicsEngineError):
    """Raised when an information conservation law is violated."""


class FieldComputationError(PhysicsEngineError):
    """Raised when field computation fails (e.g., divergence, NaN)."""