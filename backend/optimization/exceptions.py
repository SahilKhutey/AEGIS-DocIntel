"""
Custom exceptions for the Optimization framework.
"""


class OptimizationError(Exception):
    """Base exception for all optimization errors."""


class OptimizationTargetError(OptimizationError):
    """Raised when an optimization target cannot be met."""


class TokenBudgetExceededError(OptimizationError):
    """Raised when tokens exceed the configured budget."""


class MemoryAllocationError(OptimizationError):
    """Raised when memory allocation fails."""
