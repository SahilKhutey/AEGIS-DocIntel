"""
AEGIS-DocIntel Evaluation Session Audit Schema (PROT-04 WP-04.07)
Defines immutable audit event schemas for session and token lifecycle events.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SessionAuditEventType(str, Enum):
    SESSION_CREATED = "session.created"
    SESSION_VALIDATED = "session.validated"
    SESSION_REFRESHED = "session.refreshed"
    SESSION_REFRESH_REJECTED = "session.refresh_rejected"
    REFRESH_TOKEN_REUSE_DETECTED = "session.refresh_replay_detected"
    SESSION_LOGGED_OUT = "session.logged_out"
    SESSION_REVOKED = "session.revoked"
    ALL_SESSIONS_REVOKED = "session.all_revoked"
    DEVICE_SESSION_REVOKED = "session.device_revoked"
    LICENSE_SESSION_REVOKED = "session.license_revoked"
    SESSION_EXPIRED = "session.expired"
    WEBSOCKET_TICKET_ISSUED = "websocket.ticket_issued"
    WEBSOCKET_TICKET_CONSUMED = "websocket.ticket_consumed"
    WEBSOCKET_CONNECTION_REVOKED = "websocket.connection_revoked"


class SessionAuditEvent(BaseModel):
    """Immutable audit record emitted during session lifecycle actions."""
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique event identifier")
    event_type: SessionAuditEventType = Field(..., description="Categorized lifecycle event type")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="UTC timestamp of occurrence")
    session_id: Optional[str] = Field(default=None, description="Associated session identifier")
    evaluator_id: Optional[str] = Field(default=None, description="Actor evaluator identifier")
    license_id: Optional[str] = Field(default=None, description="Associated license identifier")
    device_id: Optional[str] = Field(default=None, description="Associated hardware device identifier")
    status: str = Field(default="SUCCESS", description="Outcome status (SUCCESS, DENIED, REPLAY_DETECTED, EXPIRED)")
    details: Dict[str, Any] = Field(default_factory=dict, description="Structured event telemetry")
