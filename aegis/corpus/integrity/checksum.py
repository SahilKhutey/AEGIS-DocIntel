"""
aegis.corpus.integrity.checksum
===============================
Cryptographic SHA-256 calculation utilities.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


def calculate_sha256(file_path: Path | str, chunk_size: int = 1024 * 1024) -> str:
    """Computes streaming SHA-256 digest of a file on disk."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def hash_bytes(data: bytes) -> str:
    """Computes SHA-256 digest of raw bytes."""
    return hashlib.sha256(data).hexdigest()
