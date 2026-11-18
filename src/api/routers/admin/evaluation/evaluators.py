"""
AEGIS-DocIntel Admin Evaluators Router
PROT-FINAL-08: Administrative Evaluator Lifecycle Operations
"""

from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, require_role
from src.schemas.evaluation.evaluator import (
    EvaluatorCreate,
    EvaluatorProfile,
    EvaluatorStatus,
)
from src.schemas.evaluation.invitation import InviteCreate, InviteResponse
from src.services.evaluation.evaluator_service import evaluator_service
from src.services.evaluation.invitation_service import invitation_service
from src.services.evaluation.evaluator_termination_service import evaluator_termination_service
from src.repositories.evaluation.evaluator_repository import (
    EvaluatorNotFoundError,
    InvalidStateTransitionError,
)

router = APIRouter(prefix="/v1/admin/evaluators", tags=["Admin Evaluators"])


class SuspendRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


class TerminateRequest(BaseModel):
    reason: str = Field(..., min_length=5, max_length=255)


@router.post("", response_model=EvaluatorProfile, status_code=status.HTTP_201_CREATED, summary="Create Evaluator Profile")
async def create_evaluator(
    payload: EvaluatorCreate,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Create an authorized evaluator record prior to invitation issuance."""
    try:
        return evaluator_service.create_evaluator(payload, operator_id=admin.user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))


@router.get("", response_model=List[EvaluatorProfile], summary="List Evaluators")
async def list_evaluators(
    status_filter: Optional[EvaluatorStatus] = Query(None, alias="status"),
    admin: TenantContext = Depends(require_role("admin")),
):
    """List all registered evaluators filtered by status."""
    return evaluator_service.list_evaluators(status=status_filter)


@router.get("/{evaluator_id}", response_model=EvaluatorProfile, summary="Get Evaluator Profile")
async def get_evaluator(
    evaluator_id: str,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Retrieve full profile for a specific evaluator."""
    try:
        return evaluator_service.get_evaluator(evaluator_id)
    except EvaluatorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluator not found")


@router.post("/{evaluator_id}/invite", response_model=InviteResponse, summary="Issue Evaluator Invitation")
async def issue_invite(
    evaluator_id: str,
    ttl_hours: int = Query(72, ge=1, le=720),
    admin: TenantContext = Depends(require_role("admin")),
):
    """Issue a high-entropy, time-limited onboarding invitation token."""
    try:
        return invitation_service.issue_invitation(
            InviteCreate(evaluator_id=evaluator_id, ttl_hours=ttl_hours, operator_id=admin.user_id)
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{evaluator_id}/suspend", response_model=EvaluatorProfile, summary="Suspend Evaluator")
async def suspend_evaluator(
    evaluator_id: str,
    payload: SuspendRequest,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Suspend evaluator access with documented reason."""
    try:
        return evaluator_service.suspend_evaluator(evaluator_id, reason=payload.reason, operator_id=admin.user_id)
    except (EvaluatorNotFoundError, InvalidStateTransitionError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/{evaluator_id}/terminate", summary="Terminate Evaluator")
async def terminate_evaluator(
    evaluator_id: str,
    payload: TerminateRequest,
    admin: TenantContext = Depends(require_role("admin")),
):
    """Terminate evaluator, revoke credentials, and trigger data retention lifecycle."""
    try:
        res = evaluator_termination_service.terminate_evaluation(
            evaluator_id=evaluator_id,
            reason=payload.reason,
            operator_id=admin.user_id,
            trigger_cascading_erasure=True,
        )
        return res
    except EvaluatorNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Evaluator not found")
