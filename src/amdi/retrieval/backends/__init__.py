"""Pluggable index-store backends."""

from amdi.retrieval.backends.inmemory import InMemoryIndexStore
from amdi.retrieval.backends.filesystem import FilesystemIndexStore

__all__ = ["InMemoryIndexStore", "FilesystemIndexStore"]
