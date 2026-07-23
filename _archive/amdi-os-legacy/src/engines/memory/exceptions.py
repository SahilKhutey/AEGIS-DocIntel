"""
Custom exceptions for the Hierarchical Memory Engine.
"""


class MemoryEngineError(Exception):
    """Base exception for all Memory Engine errors."""


class LevelNotFoundError(MemoryEngineError):
    """Raised when a referenced memory level does not exist."""


class CapacityExceededError(MemoryEngineError):
    """Raised when a memory level exceeds its capacity and cannot accept more items."""


class EvictionError(MemoryEngineError):
    """Raised when eviction fails to free sufficient space."""


class PromotionError(MemoryEngineError):
    """Raised when level promotion fails."""


class RetrievalError(MemoryEngineError):
    """Raised when a retrieval query is malformed or fails."""


class SerializationError(MemoryEngineError):
    """Raised when memory serialization/deserialization fails."""
