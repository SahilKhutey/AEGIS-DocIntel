"""
Custom exceptions for the Export Engine.
"""


class ExportEngineError(Exception):
    """Base exception for all Export Engine errors."""


class InvalidContextError(ExportEngineError):
    """Raised when context data is malformed or incomplete."""


class FormatError(ExportEngineError):
    """Raised when export formatting fails."""


class VerificationError(ExportEngineError):
    """Raised when pre-export verification fails."""


class TokenBudgetExceededError(ExportEngineError):
    """Raised when the export exceeds the agent's token budget."""