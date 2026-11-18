"""
AEGIS-DocIntel Evaluator Support & Offboarding Router
PROT-FINAL-08: Support Inquiries and Self-Service Termination Requests
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant
from src.services.evaluation.evaluator_termination_service import evaluator_termination_service

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluator Support"])


class SupportRequest(BaseModel):
    subject: str = Field(..., min_length=5, max_length=120)
    message: str = Field(..., min_length=10, max_length=2000)
    category: str = Field(default="GENERAL")


class TerminationRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)
    confirm_data_deletion: bool = Field(..., description="Acknowledge cascading document and index deletion")


@router.post("/support-requests", summary="Submit Evaluator Support Request")
async def create_support_request(
    payload: SupportRequest,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """File a support request with the AEGIS operations desk."""
    req_id = f"sup-{uuid.uuid4().hex[:10]}"
    return {
        "support_ticket_id": req_id,
        "evaluator_id": tenant.tenant_id,
        "subject": payload.subject,
        "category": payload.category,
        "status": "QUEUED_FOR_TRIAGE",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "expected_response_hours": 24,
    }


@router.post("/termination-request", summary="Request Evaluation Termination & Erasure")
async def request_termination(
    payload: TerminationRequest,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Voluntarily terminate evaluation, revoke sessions, and trigger cascading data erasure."""
    if not payload.confirm_data_deletion:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You must acknowledge irreversible cascading document and index deletion.",
        )

    res = evaluator_termination_service.terminate_evaluation(
        evaluator_id=tenant.tenant_id,
        reason=payload.reason,
        operator_id="evaluator",
        trigger_cascading_erasure=True,
    )
    return res
