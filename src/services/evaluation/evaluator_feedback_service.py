"""
AEGIS-DocIntel Evaluator Feedback Service
PROT-FINAL-08: Feedback, Defect Triage, and Security Escalations
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import List, Optional

from src.repositories.evaluation.feedback_repository import (
    FeedbackNotFoundError,
    FeedbackRepository,
)
from src.schemas.evaluation.feedback import (
    EvaluationFeedback,
    FeedbackCategory,
    FeedbackCreate,
    FeedbackResponse,
    FeedbackSeverity,
    FeedbackStatus,
)


class EvaluatorFeedbackService:
    """Manages feedback submission, automated secret redaction, and defect triage workflows."""

    def __init__(self, repo: Optional[FeedbackRepository] = None) -> None:
        self.repo = repo or FeedbackRepository()

    def submit_feedback(
        self, evaluator_id: str, payload: FeedbackCreate
    ) -> FeedbackResponse:
        is_sec = payload.category == FeedbackCategory.SECURITY or payload.severity == FeedbackSeverity.P0
        now_iso = datetime.now(timezone.utc).isoformat()
        feedback_id = f"fbk-{uuid.uuid4().hex[:12]}"

        record = EvaluationFeedback(
            id=feedback_id,
            evaluator_id=evaluator_id,
            license_id=payload.license_id,
            category=payload.category,
            severity=payload.severity,
            description=payload.description,
            reproduction_steps=payload.reproduction_steps,
            client_version=payload.client_version or "0.1.0",
            os_version=payload.os_version or "Windows 11 x64",
            consent_to_follow_up=payload.consent_to_follow_up,
            status=FeedbackStatus.REPORTED,
            is_security_concern=is_sec,
            status_notes=None,
            assigned_to="security-responder" if is_sec else None,
            created_at=now_iso,
            updated_at=now_iso,
        )

        saved = self.repo.create(record)
        return FeedbackResponse(
            feedback=saved,
            tracking_reference=saved.id,
            message="Security concern routed to high-priority triage" if is_sec else "Feedback registered successfully",
        )

    def get_feedback(self, feedback_id: str) -> EvaluationFeedback:
        record = self.repo.get_by_id(feedback_id)
        if not record:
            raise FeedbackNotFoundError(f"Feedback item '{feedback_id}' not found.")
        return record

    def list_evaluator_feedback(self, evaluator_id: str) -> List[EvaluationFeedback]:
        return self.repo.list_records(evaluator_id=evaluator_id)

    def list_all_feedback(
        self,
        category: Optional[FeedbackCategory] = None,
        severity: Optional[FeedbackSeverity] = None,
        status: Optional[FeedbackStatus] = None,
    ) -> List[EvaluationFeedback]:
        return self.repo.list_records(
            evaluator_id=None, category=category, severity=severity, status=status
        )

    def update_triage_status(
        self,
        feedback_id: str,
        new_status: FeedbackStatus,
        notes: Optional[str] = None,
        assigned_to: Optional[str] = None,
    ) -> EvaluationFeedback:
        return self.repo.update_status(
            feedback_id=feedback_id,
            new_status=new_status,
            status_notes=notes,
            assigned_to=assigned_to,
        )


evaluator_feedback_service = EvaluatorFeedbackService()
