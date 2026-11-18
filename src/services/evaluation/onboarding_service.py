"""
AEGIS-DocIntel Onboarding Service
PROT-FINAL-08: Complete Evaluator Onboarding Journey Coordinator
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.schemas.evaluation.evaluator import EvaluatorProfile, EvaluatorStatus
from src.schemas.evaluation.invitation import InviteCreate, InviteResponse
from src.services.evaluation.evaluator_service import EvaluatorService
from src.services.evaluation.invitation_service import InvitationService
from src.services.evaluation.license_service import EvaluationLicenseService


class OnboardingService:
    """Orchestrates the sequential steps of an evaluator's onboarding lifecycle."""

    def __init__(
        self,
        evaluator_service_inst: Optional[EvaluatorService] = None,
        invitation_service_inst: Optional[InvitationService] = None,
        license_service_inst: Optional[EvaluationLicenseService] = None,
    ) -> None:
        self.evaluator_service = evaluator_service_inst or EvaluatorService()
        self.invitation_service = invitation_service_inst or InvitationService()
        self.license_service = license_service_inst or EvaluationLicenseService()

    def start_onboarding(self, evaluator_id: str, operator_id: str, ttl_hours: int = 72) -> InviteResponse:
        """Step 1: Administrator issues an invitation token."""
        return self.invitation_service.issue_invitation(
            InviteCreate(
                evaluator_id=evaluator_id,
                ttl_hours=ttl_hours,
                operator_id=operator_id,
            )
        )

    def complete_registration(
        self,
        token: str,
        accept_agreement: bool,
        acknowledge_privacy: bool,
    ) -> EvaluatorProfile:
        """Step 2: Evaluator accepts terms and transitions to REGISTERED."""
        return self.invitation_service.accept_invitation(
            raw_token=token,
            accept_agreement=accept_agreement,
            acknowledge_privacy_notice=acknowledge_privacy,
        )

    def issue_evaluation_license(
        self,
        evaluator_id: str,
        duration_days: int = 14,
        device_limit: int = 1,
        features: Optional[List[str]] = None,
        quotas: Optional[Dict[str, int]] = None,
        operator_id: str = "admin",
    ) -> Dict[str, Any]:
        """Step 3: Issue an Ed25519 evaluation license and transition to LICENSE_ISSUED."""
        evaluator = self.evaluator_service.get_evaluator(evaluator_id)
        if evaluator.status not in [EvaluatorStatus.REGISTERED, EvaluatorStatus.LICENSE_ISSUED]:
            raise ValueError(
                f"Cannot issue license for evaluator in status '{evaluator.status.value}'. Must be REGISTERED."
            )

        license_data = self.license_service.issue_license(
            evaluator_id=evaluator_id,
            tenant_id=evaluator_id,
            duration_days=duration_days,
            device_limit=device_limit,
            features=features or ["query", "intelligence", "documents", "export"],
            quotas=quotas or {"documents": 50, "queries": 200, "storage_mb": 500},
        )

        self.evaluator_service.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.LICENSE_ISSUED,
            reason="Evaluation license issued by operator",
            operator_id=operator_id,
            allowed_from=[EvaluatorStatus.REGISTERED, EvaluatorStatus.LICENSE_ISSUED],
        )

        return license_data

    def confirm_device_activated(self, evaluator_id: str, device_id: str) -> EvaluatorProfile:
        """Step 4: Device activation confirmed; transition to ACTIVE."""
        evaluator = self.evaluator_service.get_evaluator(evaluator_id)
        if evaluator.status in [EvaluatorStatus.SUSPENDED, EvaluatorStatus.REVOKED, EvaluatorStatus.TERMINATED]:
            raise ValueError(f"Cannot activate device: evaluator is {evaluator.status.value}")

        return self.evaluator_service.repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.ACTIVE,
            reason=f"Device {device_id} successfully bound and activated",
            operator_id="system",
            allowed_from=[EvaluatorStatus.LICENSE_ISSUED, EvaluatorStatus.ACTIVATION_PENDING, EvaluatorStatus.ACTIVE],
        )


onboarding_service = OnboardingService()
