"""
Custom exceptions for AI Agent Connectors.
"""


class ConnectorError(Exception):
    """Base exception for all connector errors."""


class AuthenticationError(ConnectorError):
    """Raised when API authentication fails."""


class RateLimitError(ConnectorError):
    """Raised when API rate limit is exceeded."""


class TokenLimitError(ConnectorError):
    """Raised when the request exceeds the agent's token limit."""


class ConnectionTimeoutError(ConnectorError):
    """Raised when the connection times out."""


class InvalidResponseError(ConnectorError):
    """Raised when the agent returns an invalid response."""


class ModelNotFoundError(ConnectorError):
    """Raised when the specified model is not available."""