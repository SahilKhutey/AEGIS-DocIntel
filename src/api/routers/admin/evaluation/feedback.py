"""
AEGIS-DocIntel Admin Evaluation Feedback Router
PROT-FINAL-08: Administrative Feedback Review & Defect Triage
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.api.auth import TenantContext, require_role
from src.schemas.evaluation.feedback import (
    EvaluationFeedback,
    FeedbackCategory,
    FeedbackSeverity,
    FeedbackStatus,
    FeedbackStatusUpdate,
)
from src.services.evaluation.evaluator_feedback_service import evaluator_feedback_service
from src.repositories.evaluation.feedback_repository import FeedbackNotFoundError

router = APIRouter(prefix="/v1/admin/evaluation/feedback", tags=["Admin Evaluation Feedback"])


@router.get("", response_model=List[EvaluationFeedback], summary="List All Evaluator Feedback")
async def list_feedback_items(
    category: Optional[FeedbackCategory] = Query(None),
    severity: Optional[FeedbackSeverity] = Query(None),
    status_filter: Optional[FeedbackStatus] = Query(None, alias="status"),
    admin: TenantContext = Depends(require_role("admin")),
):
    """Review feedback and defect tickets across all evaluators."""
    return evaluator_feedback_service.list_all_feedback(
        category=category,
        severity=severity,
        status=status_filter,
    )


@router.post("/{feedback_id}/status", response_model=EvaluationFeedback, summary="Update Feedback Triage Status")
async def update_status(
    feedback_id: str,
    payload: FeedbackStatusUpdate,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Update defect status, assign investigator, and log triage notes."""
    try:
        return evaluator_feedback_service.update_triage_status(
            feedback_id=feedback_id,
            new_status=payload.status,
            notes=payload.status_notes,
            assigned_to=payload.assigned_to,
        )
    except FeedbackNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Feedback record not found")
