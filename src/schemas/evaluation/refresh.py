"""
AEGIS-DocIntel Evaluation Refresh Token Schema (PROT-04 WP-04.07)
Defines refresh token lifecycle, rotation lineage, and hash storage specifications.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class RefreshTokenStatus(str, Enum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    REVOKED = "revoked"
    EXPIRED = "expired"


class EvaluationRefreshToken(BaseModel):
    """
    Authoritative server-side refresh token entity.
    CRITICAL: Raw refresh tokens are never persisted. Only SHA-256 hashes are stored.
    """
    token_id: str = Field(..., description="Unique record identifier (UUIDv4)")
    session_id: str = Field(..., description="Parent session identifier")
    family_id: str = Field(..., description="Token family identifier for replay detection")
    token_hash: str = Field(..., description="SHA-256 digest of high-entropy refresh token secret")
    status: RefreshTokenStatus = Field(default=RefreshTokenStatus.ACTIVE, description="Token status")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc), description="Issuance timestamp")
    expires_at: datetime = Field(..., description="Refresh token expiration timestamp (e.g. 7 days)")
    consumed_at: Optional[datetime] = Field(default=None, description="Timestamp when rotated/consumed")
    replaced_by_id: Optional[str] = Field(default=None, description="token_id of the replacement token")
    revoked_at: Optional[datetime] = Field(default=None, description="Timestamp if revoked before or after consumption")
    revocation_reason: Optional[str] = Field(default=None, description="Revocation justification")

    def is_usable(self, now: Optional[datetime] = None) -> bool:
        """Checks if this token is currently eligible for rotation."""
        check_time = now or datetime.now(timezone.utc)
        if self.status != RefreshTokenStatus.ACTIVE:
            return False
        if check_time > self.expires_at:
            return False
        return True
