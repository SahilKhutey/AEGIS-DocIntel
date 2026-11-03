"""
aegis.processing.validation
===========================
Pre-processing validation gates, magic-byte checks, and resource limits.
"""

from aegis.processing.validation.file_validator import FileValidator, ValidationResult
from aegis.processing.validation.resource_limits import ResourceLimitsConfig

__all__ = [
    "FileValidator",
    "ValidationResult",
    "ResourceLimitsConfig",
]
