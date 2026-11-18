"""
AEGIS-DocIntel Invitation Schemas
PROT-FINAL-08: Evaluator Onboarding & Invitation Protocol
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class InvitationStatus(str, Enum):
    PENDING = "PENDING"
    ACCEPTED = "ACCEPTED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"


class InviteCreate(BaseModel):
    evaluator_id: str
    ttl_hours: int = Field(default=72, ge=1, le=720)
    operator_id: str


class InviteAccept(BaseModel):
    token: str = Field(..., min_length=16)
    accept_agreement: bool = Field(..., description="Must explicitly accept Evaluation Agreement")
    acknowledge_privacy_notice: bool = Field(..., description="Must explicitly acknowledge Privacy Notice")


class EvaluationInvite(BaseModel):
    id: str
    evaluator_id: str
    token_hash: str
    status: InvitationStatus
    expires_at: str
    accepted_at: Optional[str] = None
    created_by: str
    created_at: str


class InviteResponse(BaseModel):
    invitation: EvaluationInvite
    raw_token: Optional[str] = None  # Returned only on initial creation
    invitation_url: Optional[str] = None
    message: str = "Invitation processed successfully"
