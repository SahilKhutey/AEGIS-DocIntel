"""
aegis/audit/config/fingerprint.py
=================================
Calculates reproducible SHA-256 configuration fingerprints.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict


SECRET_KEYS = {"password", "secret", "token", "key", "api_key", "credentials"}


def sanitize_dict(d: Any) -> Any:
    """Recursively strip any sensitive credential keys before computing fingerprint."""
    if isinstance(d, dict):
        clean = {}
        for k, v in d.items():
            if any(s in k.lower() for s in SECRET_KEYS):
                continue
            clean[k] = sanitize_dict(v)
        return clean
    elif isinstance(d, list):
        return [sanitize_dict(item) for item in d]
    return d


def compute_configuration_hash(config: Dict[str, Any]) -> str:
    """
    Computes a deterministic SHA-256 hash across sorted, sanitized JSON representation.
    """
    sanitized = sanitize_dict(config)
    canonical_json = json.dumps(sanitized, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical_json.encode("utf-8")).hexdigest()
