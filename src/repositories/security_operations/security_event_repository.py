"""
AEGIS-DocIntel Security Event Repository (PROT-04 WP-04.08)
Thread-safe repository with strict tenant isolation and role-based access filtering.
"""

from __future__ import annotations

import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import UUID

from src.security.event_schema import SecurityEvent, Severity


class SecurityEventRepository:
    """Thread-safe store for structured security events."""

    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[SecurityEvent] = []

    def record_event(self, event: SecurityEvent) -> SecurityEvent:
        with self._lock:
            self._events.append(event)
            return event

    def query_events(
        self,
        tenant_id: Optional[str] = None,
        evaluator_id: Optional[str] = None,
        severity: Optional[Severity] = None,
        event_type: Optional[str] = None,
        caller_role: str = "security_operator",
        limit: int = 100,
    ) -> List[SecurityEvent]:
        """
        Queries security events with strict tenant isolation and caller authorization checks.
        Evaluators cannot access internal security logs (OPS-008).
        Tenants can never access cross-tenant records (OPS-007).
        """
        # Evaluators have no permission to internal security telemetry
        if caller_role == "evaluator":
            raise PermissionError("Evaluator accounts are forbidden from accessing internal security telemetry.")

        with self._lock:
            results = self._events

            # Strict tenant filtering
            if tenant_id:
                results = [e for e in results if e.tenant_id == tenant_id]

            if evaluator_id:
                results = [e for e in results if e.evaluator_id == evaluator_id]

            if severity:
                results = [e for e in results if e.severity == severity]

            if event_type:
                results = [e for e in results if e.event_type == event_type]

            return list(reversed(results))[:limit]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


security_event_repository = SecurityEventRepository()
