"""
AEGIS-DocIntel Evaluator Feedback & Defect Reporting Schemas
PROT-FINAL-08: Support, Feedback & Defect Workflows
"""

from __future__ import annotations

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FeedbackCategory(str, Enum):
    ACTIVATION = "ACTIVATION"
    INSTALLATION = "INSTALLATION"
    AUTHENTICATION = "AUTHENTICATION"
    FUNCTIONAL = "FUNCTIONAL"
    PERFORMANCE = "PERFORMANCE"
    UX = "UX"
    SECURITY = "SECURITY"
    PRIVACY = "PRIVACY"


class FeedbackSeverity(str, Enum):
    P0 = "P0"  # Security breach / privacy issue / total system block
    P1 = "P1"  # Critical installation / activation / parsing failure
    P2 = "P2"  # Non-blocking defect / performance degradation
    P3 = "P3"  # Minor UX suggestion / cosmetic inquiry


class FeedbackStatus(str, Enum):
    REPORTED = "REPORTED"
    TRIAGE = "TRIAGE"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"
    CONFIRMED = "CONFIRMED"
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    FIX_AVAILABLE = "FIX_AVAILABLE"
    VERIFICATION = "VERIFICATION"
    REOPENED = "REOPENED"
    CLOSED = "CLOSED"


class FeedbackCreate(BaseModel):
    category: FeedbackCategory
    severity: FeedbackSeverity = Field(default=FeedbackSeverity.P2)
    description: str = Field(..., min_length=10, max_length=2000)
    reproduction_steps: Optional[str] = Field(default=None, max_length=2000)
    client_version: Optional[str] = Field(default="0.1.0", max_length=32)
    os_version: Optional[str] = Field(default="Windows 11 x64", max_length=64)
    consent_to_follow_up: bool = Field(default=True)
    license_id: Optional[str] = None


class EvaluationFeedback(BaseModel):
    id: str
    evaluator_id: str
    license_id: Optional[str] = None
    category: FeedbackCategory
    severity: FeedbackSeverity
    description: str
    reproduction_steps: Optional[str] = None
    client_version: str
    os_version: str
    consent_to_follow_up: bool
    status: FeedbackStatus
    is_security_concern: bool
    status_notes: Optional[str] = None
    assigned_to: Optional[str] = None
    created_at: str
    updated_at: str


class FeedbackResponse(BaseModel):
    feedback: EvaluationFeedback
    tracking_reference: str
    message: str = "Feedback registered successfully"


class FeedbackStatusUpdate(BaseModel):
    status: FeedbackStatus
    status_notes: Optional[str] = Field(default=None, max_length=500)
    assigned_to: Optional[str] = Field(default=None, max_length=120)
    operator_id: str
