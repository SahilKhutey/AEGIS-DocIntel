"""
AEGIS-DocIntel Session Audit Repository (PROT-04 WP-04.07)
Maintains append-only audit trail for session events and security compromises.
"""

from __future__ import annotations

import threading
from typing import List, Optional

from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType


class SessionAuditRepository:
    """Thread-safe append-only audit repository."""

    def __init__(self):
        self._lock = threading.RLock()
        self._events: List[SessionAuditEvent] = []

    def record_event(self, event: SessionAuditEvent) -> SessionAuditEvent:
        with self._lock:
            self._events.append(event)
            return event

    def query_events(
        self,
        session_id: Optional[str] = None,
        evaluator_id: Optional[str] = None,
        event_type: Optional[SessionAuditEventType] = None,
        limit: int = 100,
    ) -> List[SessionAuditEvent]:
        with self._lock:
            results = self._events
            if session_id:
                results = [e for e in results if e.session_id == session_id]
            if evaluator_id:
                results = [e for e in results if e.evaluator_id == evaluator_id]
            if event_type:
                results = [e for e in results if e.event_type == event_type]
            return list(reversed(results))[:limit]

    def clear(self) -> None:
        with self._lock:
            self._events.clear()


session_audit_repository = SessionAuditRepository()
