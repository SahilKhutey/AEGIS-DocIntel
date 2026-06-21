"""
Custom exceptions for the Validation framework.
"""


class ValidationError(Exception):
    """Base exception for all validation errors."""


class TestFailureError(ValidationError):
    """Raised when a test fails unexpectedly."""


class CoverageThresholdError(ValidationError):
    """Raised when test coverage is below threshold."""


class StressTestFailure(ValidationError):
    """Raised when a stress test detects performance degradation."""


class AblationError(ValidationError):
    """Raised when an ablation study fails."""


class RobustnessError(ValidationError):
    """Raised when robustness checks fail."""
