"""
AEGIS-DocIntel — Storage & Document Lifecycle Exceptions
========================================================
Typed exceptions for persistence, recovery, and cascading deletion failures.
"""
from __future__ import annotations


class DocumentStorageError(RuntimeError):
    """Base exception for persistent document storage operation failures."""
    pass


class DocumentPersistenceError(DocumentStorageError):
    """Raised when document metadata or raw bytes fail to persist reliably."""
    pass


class DocumentNotFoundError(DocumentStorageError):
    """Document does not exist or is not accessible to the tenant."""
    pass


class DocumentRecoveryError(DocumentStorageError):
    """Stored document state or raw bytes could not be recovered or verified."""
    pass


class DocumentCleanupPending(DocumentStorageError):
    """Deletion was requested and tombstoned, but downstream store cleanup is pending or failed."""
    pass
