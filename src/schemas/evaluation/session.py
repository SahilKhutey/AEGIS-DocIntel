"""
AEGIS-DocIntel Evaluation Session Schema (PROT-04 WP-04.07)
Defines authoritative session lifecycle states, models, and revocation reasons.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class SessionStatus(str, Enum):
    ACTIVE = "active"
    REVOKED = "revoked"
    EXPIRED = "expired"
    SUSPENDED = "suspended"


class RevocationReason(str, Enum):
    USER_LOGOUT = "user_logout"
    ALL_SESSIONS_LOGOUT = "all_sessions_logout"
    DEVICE_DEACTIVATED = "device_deactivated"
    LICENSE_REVOKED = "license_revoked"
    LICENSE_EXPIRED = "license_expired"
    LICENSE_SUSPENDED = "license_suspended"
    EVALUATOR_SUSPENDED = "evaluator_suspended"
    REFRESH_REPLAY_DETECTED = "refresh_replay_detected"
    ADMIN_REVOCATION = "admin_revocation"
    IDLE_TIMEOUT = "idle_timeout"
    ABSOLUTE_TIMEOUT = "absolute_timeout"
    SECURITY_COMPROMISE = "security_compromise"


class EvaluationSession(BaseModel):
    """
    Authoritative server-side evaluation session model.
    Enforces strict binding to evaluator, tenant, license, and registered device.
    """
    session_id: str = Field(..., description="Unique session identifier (UUIDv4)")
    evaluator_id: str = Field(..., description="Evaluator subject identifier")
    tenant_id: str = Field(..., description="Isolated evaluation tenant identifier")
    license_id: str = Field(..., description="Bound evaluation license ID")
    device_id: str = Field(..., description="Bound registered hardware device ID")
    status: SessionStatus = Field(default=SessionStatus.ACTIVE, description="Current lifecycle state")
    token_family_id: str = Field(..., description="Lineage identifier for rotating refresh tokens")
    access_token_hash: str = Field(..., description="SHA-256 digest of active access token")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Session creation UTC timestamp")
    last_seen_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Last active request timestamp")
    idle_expires_at: datetime = Field(..., description="Sliding idle timeout timestamp (e.g. 30 min)")
    absolute_expires_at: datetime = Field(..., description="Fixed maximum session lifetime timestamp (e.g. 7 days)")
    revoked_at: Optional[datetime] = Field(default=None, description="Timestamp of revocation if inactive")
    revocation_reason: Optional[RevocationReason] = Field(default=None, description="Reason code for revocation")
    ip_address: Optional[str] = Field(default=None, description="Client IP address recorded at login/refresh")
    user_agent: Optional[str] = Field(default=None, description="Client user agent string")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary session metadata")

    def is_active(self, now: Optional[datetime] = None) -> bool:
        """Determines whether the session is currently valid and usable."""
        check_time = now or datetime.now(timezone.utc)
        if self.status != SessionStatus.ACTIVE:
            return False
        if check_time > self.idle_expires_at:
            return False
        if check_time > self.absolute_expires_at:
            return False
        return True
