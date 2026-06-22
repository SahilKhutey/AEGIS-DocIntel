"""
Custom exceptions for the Verification Engine.
"""


class VerificationEngineError(Exception):
    """Base exception for all Verification Engine errors."""


class CitationMissingError(VerificationEngineError):
    """Raised when a citation is missing or invalid."""


class FactMismatchError(VerificationEngineError):
    """Raised when a factual claim does not match the source."""


class ConfidenceThresholdError(VerificationEngineError):
    """Raised when confidence is below the required threshold."""


class HallucinationDetectedError(VerificationEngineError):
    """Raised when hallucination is detected with high confidence."""
