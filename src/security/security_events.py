"""
AEGIS-DocIntel Security Event Dispatcher (PROT-FINAL-02 / REM-06)
Centralized dispatching and logging for security events, integrating
automatic redaction, audit ledger hash-chaining, and threshold alerting.
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from uuid import UUID

from src.security.event_schema import SecurityEvent, Severity
from src.services.security_operations.security_event_service import (
    SecurityEventService,
    security_event_service,
)

__all__ = [
    "SecurityEvent",
    "Severity",
    "SecurityEventService",
    "security_event_service",
]
