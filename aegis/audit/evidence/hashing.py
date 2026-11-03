"""
aegis/audit/evidence/hashing.py
===============================
SHA-256 cryptographic integrity utilities for artifacts and evidence manifests.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Union


def hash_bytes(data: bytes) -> str:
    """Calculate SHA-256 hex digest of bytes."""
    return hashlib.sha256(data).hexdigest()


def hash_file(path: Union[str, Path]) -> str:
    """Calculate SHA-256 hex digest of a physical file."""
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"Cannot hash non-existent file: {p}")
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    """Serialize object to deterministic, sorted, compact JSON bytes."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")


def hash_json(obj: Any) -> str:
    """Calculate SHA-256 of canonical serialized JSON object."""
    return hash_bytes(canonical_json_bytes(obj))
