"""
Audit Log
=========

Tamper-evident event log for security-relevant actions.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import uuid
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Deque, Dict, List, Optional

from .exceptions import SecurityError


class AuditEventType(Enum):
    """Types of audit events."""

    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PASSWORD_CHANGE = "password_change"
    API_KEY_CREATED = "api_key_created"
    API_KEY_REVOKED = "api_key_revoked"
    TOKEN_ISSUED = "token_issued"
    TOKEN_REVOKED = "token_revoked"
    ACCESS_GRANTED = "access_granted"
    ACCESS_DENIED = "access_denied"
    DATA_READ = "data_read"
    DATA_WRITE = "data_write"
    DATA_DELETE = "data_delete"
    SECRET_ACCESSED = "secret_accessed"
    ENCRYPTION_OPERATION = "encryption_operation"
    CONFIG_CHANGE = "config_change"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


class AuditSeverity(Enum):
    """Severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class AuditEvent:
    """A single audit event."""

    event_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    timestamp: float
    actor_id: str
    actor_type: str  # user / service / system
    resource_type: str
    resource_id: str
    action: str
    outcome: str  # success / failure / denied
    source_ip: Optional[str] = None
    user_agent: Optional[str] = None
    details: Dict[str, Any] = field(default_factory=dict)
    prev_hash: Optional[str] = None
    hash: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "actor_type": self.actor_type,
            "resource_type": self.resource_type,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "source_ip": self.source_ip,
            "user_agent": self.user_agent,
            "details": self.details,
            "prev_hash": self.prev_hash,
            "hash": self.hash,
        }

    def compute_hash(self) -> str:
        """Compute a hash of this event for chain integrity."""
        payload = {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp,
            "actor_id": self.actor_id,
            "resource_id": self.resource_id,
            "action": self.action,
            "outcome": self.outcome,
            "prev_hash": self.prev_hash or "",
        }
        payload_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        return hashlib.sha256(payload_str.encode("utf-8")).hexdigest()


class AuditLogger:
    """
    Tamper-evident audit logger.

    Each event contains a hash of the previous event, forming
    a hash chain that detects tampering.
    """

    def __init__(self, max_in_memory: int = 10_000) -> None:
        self.events: Deque[AuditEvent] = deque(maxlen=max_in_memory)
        self._last_hash: Optional[str] = None
        self._by_type: Dict[AuditEventType, List[AuditEvent]] = {}
        self._by_actor: Dict[str, List[AuditEvent]] = {}

    def log(
        self,
        event_type: AuditEventType,
        actor_id: str,
        resource_type: str,
        resource_id: str,
        action: str,
        outcome: str = "success",
        actor_type: str = "user",
        severity: AuditSeverity = AuditSeverity.INFO,
        source_ip: Optional[str] = None,
        user_agent: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ) -> AuditEvent:
        """Log an audit event."""
        event = AuditEvent(
            event_id=str(uuid.uuid4()),
            event_type=event_type,
            severity=severity,
            timestamp=time.time(),
            actor_id=actor_id,
            actor_type=actor_type,
            resource_type=resource_type,
            resource_id=resource_id,
            action=action,
            outcome=outcome,
            source_ip=source_ip,
            user_agent=user_agent,
            details=details or {},
            prev_hash=self._last_hash,
        )
        event.hash = event.compute_hash()
        self._last_hash = event.hash
        self.events.append(event)
        # indexes
        self._by_type.setdefault(event_type, []).append(event)
        self._by_actor.setdefault(actor_id, []).append(event)
        return event

    def verify_chain(self) -> bool:
        """Verify the integrity of the hash chain."""
        prev_hash = None
        for event in self.events:
            if event.prev_hash != prev_hash:
                return False
            if event.compute_hash() != event.hash:
                return False
            prev_hash = event.hash
        return True

    def query(
        self,
        event_type: Optional[AuditEventType] = None,
        actor_id: Optional[str] = None,
        resource_id: Optional[str] = None,
        severity: Optional[AuditSeverity] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        limit: int = 100,
    ) -> List[AuditEvent]:
        """Query events."""
        results = list(self.events)
        if event_type is not None:
            results = [e for e in results if e.event_type == event_type]
        if actor_id is not None:
            results = [e for e in results if e.actor_id == actor_id]
        if resource_id is not None:
            results = [e for e in results if e.resource_id == resource_id]
        if severity is not None:
            results = [e for e in results if e.severity == severity]
        if start_time is not None:
            results = [e for e in results if e.timestamp >= start_time]
        if end_time is not None:
            results = [e for e in results if e.timestamp <= end_time]
        return results[-limit:]

    def get_stats(self) -> Dict[str, Any]:
        """Get audit log statistics."""
        total = len(self.events)
        by_type = {et.value: len(evs) for et, evs in self._by_type.items()}
        by_severity: Dict[str, int] = {}
        for event in self.events:
            by_severity[event.severity.value] = by_severity.get(event.severity.value, 0) + 1
        return {
            "total_events": total,
            "by_type": by_type,
            "by_severity": by_severity,
            "chain_valid": self.verify_chain(),
        }

    def export_to_jsonl(self) -> str:
        """Export all events as JSON Lines."""
        lines = [json.dumps(e.to_dict(), default=str) for e in self.events]
        return "\n".join(lines)
