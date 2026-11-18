"""
AEGIS-DocIntel Evaluator Feedback Router
PROT-FINAL-08: Feedback Submission and Tracking
"""

from __future__ import annotations

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status

from src.api.auth import TenantContext, get_current_tenant
from src.schemas.evaluation.feedback import (
    EvaluationFeedback,
    FeedbackCreate,
    FeedbackResponse,
)
from src.services.evaluation.evaluator_feedback_service import evaluator_feedback_service

router = APIRouter(prefix="/v1/evaluation", tags=["Evaluator Feedback"])


@router.post("/feedback", response_model=FeedbackResponse, summary="Submit Evaluation Feedback")
async def submit_feedback(
    payload: FeedbackCreate,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Submit structured feedback, bug report, or security notice with automatic redaction."""
    return evaluator_feedback_service.submit_feedback(
        evaluator_id=tenant.tenant_id,
        payload=payload,
    )


@router.get("/feedback", response_model=List[EvaluationFeedback], summary="List Evaluator Feedback")
async def list_feedback(tenant: TenantContext = Depends(get_current_tenant)):
    """List feedback items submitted by the authenticated evaluator."""
    return evaluator_feedback_service.list_evaluator_feedback(evaluator_id=tenant.tenant_id)
