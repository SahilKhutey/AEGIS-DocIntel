"""
AEGIS-DocIntel Evaluator Schemas
PROT-FINAL-08: Evaluator Onboarding & Lifecycle Management
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class EvaluatorStatus(str, Enum):
    INVITED = "INVITED"
    REGISTERED = "REGISTERED"
    LICENSE_ISSUED = "LICENSE_ISSUED"
    ACTIVATION_PENDING = "ACTIVATION_PENDING"
    ACTIVE = "ACTIVE"
    SUSPENDED = "SUSPENDED"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    TERMINATED = "TERMINATED"


class EvaluatorCreate(BaseModel):
    organization: str = Field(..., min_length=2, max_length=120)
    display_name: str = Field(..., min_length=2, max_length=120)
    contact_email: EmailStr
    evaluation_purpose: str = Field(..., min_length=5, max_length=500)
    agreement_version: str = Field(default="1.0.0")
    privacy_notice_version: str = Field(default="1.0.0")
    initial_status: EvaluatorStatus = Field(default=EvaluatorStatus.INVITED)


class EvaluatorProfile(BaseModel):
    evaluator_id: str
    organization: str
    display_name: str
    contact_email: str
    evaluation_purpose: str
    agreement_version: str
    agreement_accepted_at: Optional[str] = None
    privacy_notice_version: str
    privacy_notice_acknowledged_at: Optional[str] = None
    status: EvaluatorStatus
    created_at: str
    updated_at: str


class EvaluatorResponse(BaseModel):
    evaluator: EvaluatorProfile
    active_license_id: Optional[str] = None
    registered_devices_count: int = 0
    message: str = "Evaluator record retrieved successfully"


class EvaluatorStateTransition(BaseModel):
    target_status: EvaluatorStatus
    reason: str = Field(..., min_length=3, max_length=255)
    operator_id: str
