"""
AEGIS-DocIntel Secret Redaction Engine (PROT-FINAL-02 / REM-06)
Wraps and exposes automated credential sanitization, private key masking,
and bearer token scrubbing for operational logs and audit events.
"""

from __future__ import annotations

from typing import Any, Dict, Union

from src.security.event_redaction import (
    sanitize_event_details,
    redact_text,
    contains_sensitive_data,
    SENSITIVE_KEY_PATTERNS,
)

__all__ = [
    "sanitize_event_details",
    "redact_text",
    "contains_sensitive_data",
    "SENSITIVE_KEY_PATTERNS",
]
