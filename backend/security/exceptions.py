"""
Custom exceptions for the Security framework.
"""


class SecurityError(Exception):
    """Base exception for all security errors."""


class AuthenticationError(SecurityError):
    """Raised when authentication fails."""


class AuthorizationError(SecurityError):
    """Raised when access is denied (RBAC/ABAC)."""


class EncryptionError(SecurityError):
    """Raised when encryption/decryption fails."""


class SecretAccessError(SecurityError):
    """Raised when a secret cannot be accessed."""


class RateLimitExceededError(SecurityError):
    """Raised when rate limit is exceeded."""


class ThreatDetectedError(SecurityError):
    """Raised when a threat is detected."""
