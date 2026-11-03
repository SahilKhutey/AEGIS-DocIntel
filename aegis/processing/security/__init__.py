"""
aegis.processing.security
=========================
Document security containment, isolated sandbox execution, and sanitized error classification.
"""

from aegis.processing.security.error_classifier import ErrorClassifier
from aegis.processing.security.sandbox import ProcessingSandbox

__all__ = [
    "ErrorClassifier",
    "ProcessingSandbox",
]
