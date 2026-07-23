"""
AEGIS-AMDI-OS — Base Loader Interface
=======================================
Abstract base for all document loaders.
"""
from __future__ import annotations

import abc
import logging
from pathlib import Path
from typing import Any, Union

from src.core.document_object import DocumentObject

logger = logging.getLogger(__name__)


PathLike = Union[str, Path, bytes]


class BaseLoader(abc.ABC):
    """
    Abstract base for all document loaders.
    
    Subclasses must implement:
    - load(source, filename) -> DocumentObject
    - validate(raw_bytes) -> bool
    """

    SUPPORTED_EXTENSIONS: set[str] = set()
    FORMAT_NAME: str = "unknown"

    def __init__(self, **options):
        self.options = options
        logger.debug(f"Initialized {self.FORMAT_NAME} loader with options: {options}")

    @abc.abstractmethod
    async def load(self, source: PathLike, filename: str = "") -> DocumentObject:
        """
        Load a document and return a DocumentObject.

        Args:
            source: File path, Path object, or raw bytes
            filename: Optional filename (required when source is bytes)

        Returns:
            DocumentObject with raw_bytes and metadata
        """
        raise NotImplementedError

    @abc.abstractmethod
    def validate(self, raw_bytes: bytes) -> bool:
        """Validate that bytes are a valid document of this format."""
        raise NotImplementedError

    def read_source(self, source: PathLike) -> tuple[bytes, str]:
        """
        Read source into bytes and extract filename.
        Returns: (raw_bytes, filename)
        """
        if isinstance(source, bytes):
            return source, ""
        if isinstance(source, (str, Path)):
            path = Path(source)
            return path.read_bytes(), path.name
        raise TypeError(f"Unsupported source type: {type(source)}")


class LoaderError(Exception):
    """Base exception for loader errors."""
    pass


class FormatError(LoaderError):
    """Invalid format / corrupt file."""
    pass


class SizeLimitError(LoaderError):
    """File exceeds size limit."""
    pass
