"""
AMDI-OS SDK exceptions.
"""


class AmdiError(Exception):
    """Base exception for AMDI-OS SDK."""

    def __init__(self, message: str, status_code: int = None, response: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.response = response or {}

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(message={self.message!r}, status_code={self.status_code})"


class AmdiAuthError(AmdiError):
    """Authentication failed (401, 403)."""


class AmdiNotFoundError(AmdiError):
    """Resource not found (404)."""


class AmdiValidationError(AmdiError):
    """Invalid input (400, 422)."""


class AmdiRateLimitError(AmdiError):
    """Rate limit exceeded (429)."""

    def __init__(self, message: str, retry_after: int = None, **kwargs):
        super().__init__(message, **kwargs)
        self.retry_after = retry_after


class AmdiServerError(AmdiError):
    """Server error (5xx)."""


class AmdiTimeoutError(AmdiError):
    """Request timed out."""


class AmdiConnectionError(AmdiError):
    """Network connection failed."""
