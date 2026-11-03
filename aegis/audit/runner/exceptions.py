"""
aegis/audit/runner/exceptions.py
================================
Core exception hierarchy for the AEGIS audit infrastructure.
"""

from __future__ import annotations


class AuditError(Exception):
    """Base class for all audit infrastructure exceptions."""
    pass


class ConfigurationError(AuditError):
    """Raised when audit configuration is invalid or missing."""
    pass


class SuiteNotFoundError(AuditError):
    """Raised when a requested audit suite is not registered."""
    pass


class DuplicateSuiteError(AuditError):
    """Raised when attempting to register a suite with an existing ID."""
    pass


class SuiteValidationError(AuditError):
    """Raised when a suite's prerequisites are not satisfied."""
    pass


class SuiteExecutionError(AuditError):
    """Raised when an unhandled exception occurs during suite execution."""
    pass


class TimeoutException(AuditError):
    """Raised when a suite or run exceeds its configured timeout ceiling."""
    pass


class EvidenceValidationError(AuditError):
    """Raised when generated evidence violates schema contracts or integrity rules."""
    pass


class ProvenanceError(AuditError):
    """Raised when provenance, git state, or traceability cannot be captured or validated."""
    pass


class SecurityViolationError(AuditError):
    """Raised when sensitive credentials, tokens, or forbidden paths are detected."""
    pass
