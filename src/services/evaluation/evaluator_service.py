"""
AEGIS-DocIntel Evaluator Service
PROT-FINAL-08: Evaluator Profile Management and State Enforcement
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.repositories.evaluation.evaluator_repository import (
    EvaluatorNotFoundError,
    EvaluatorRepository,
    InvalidStateTransitionError,
)
from src.schemas.evaluation.evaluator import (
    EvaluatorCreate,
    EvaluatorProfile,
    EvaluatorResponse,
    EvaluatorStatus,
)


class EvaluatorService:
    """Business service governing evaluator profiles and state transitions."""

    def __init__(self, repo: Optional[EvaluatorRepository] = None) -> None:
        self.repo = repo or EvaluatorRepository()

    def create_evaluator(self, payload: EvaluatorCreate, operator_id: str = "admin") -> EvaluatorProfile:
        existing = self.repo.get_by_email(payload.contact_email)
        if existing:
            raise ValueError(f"An evaluator with email '{payload.contact_email}' already exists.")

        now_iso = datetime.now(timezone.utc).isoformat()
        evaluator_id = f"eval-{uuid.uuid4().hex[:12]}"

        profile = EvaluatorProfile(
            evaluator_id=evaluator_id,
            organization=payload.organization,
            display_name=payload.display_name,
            contact_email=payload.contact_email,
            evaluation_purpose=payload.evaluation_purpose,
            agreement_version=payload.agreement_version,
            agreement_accepted_at=None,
            privacy_notice_version=payload.privacy_notice_version,
            privacy_notice_acknowledged_at=None,
            status=payload.initial_status,
            created_at=now_iso,
            updated_at=now_iso,
        )
        return self.repo.create(profile)

    def get_evaluator(self, evaluator_id: str) -> EvaluatorProfile:
        evaluator = self.repo.get_by_id(evaluator_id)
        if not evaluator:
            raise EvaluatorNotFoundError(f"Evaluator '{evaluator_id}' not found.")
        return evaluator

    def list_evaluators(self, status: Optional[EvaluatorStatus] = None) -> List[EvaluatorProfile]:
        return self.repo.list_all(status=status)

    def suspend_evaluator(self, evaluator_id: str, reason: str, operator_id: str) -> EvaluatorProfile:
        return self.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.SUSPENDED,
            reason=reason,
            operator_id=operator_id,
            allowed_from=[EvaluatorStatus.ACTIVE, EvaluatorStatus.ACTIVATION_PENDING, EvaluatorStatus.LICENSE_ISSUED],
        )

    def reinstate_evaluator(self, evaluator_id: str, reason: str, operator_id: str) -> EvaluatorProfile:
        return self.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.ACTIVE,
            reason=reason,
            operator_id=operator_id,
            allowed_from=[EvaluatorStatus.SUSPENDED],
        )

    def revoke_evaluator(self, evaluator_id: str, reason: str, operator_id: str) -> EvaluatorProfile:
        return self.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.REVOKED,
            reason=reason,
            operator_id=operator_id,
        )

    def terminate_evaluator(self, evaluator_id: str, reason: str, operator_id: str) -> EvaluatorProfile:
        return self.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.TERMINATED,
            reason=reason,
            operator_id=operator_id,
        )


evaluator_service = EvaluatorService()
