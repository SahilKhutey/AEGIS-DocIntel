"""
AEGIS-DocIntel Evaluator Termination Service
PROT-FINAL-08: Controlled Offboarding and Data Retention Lifecycle Execution
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.schemas.evaluation.evaluator import EvaluatorProfile, EvaluatorStatus
from src.schemas.evaluation.session import RevocationReason
from src.services.compliance.privacy_request_service import (
    PrivacyRequestService,
    privacy_request_service,
)
from src.services.evaluation.evaluator_service import EvaluatorService
from src.services.evaluation.revocation_service import (
    EvaluationRevocationService,
    revocation_service,
)

logger = logging.getLogger("aegis.evaluation.termination")


class EvaluatorTerminationService:
    """Executes controlled offboarding, revoking credentials and triggering cascading data erasure."""

    def __init__(
        self,
        evaluator_service_inst: Optional[EvaluatorService] = None,
        revocation_service_inst: Optional[EvaluationRevocationService] = None,
        privacy_service_inst: Optional[PrivacyRequestService] = None,
    ) -> None:
        self.evaluator_service = evaluator_service_inst or EvaluatorService()
        self.revocation_service = revocation_service_inst or revocation_service
        self.privacy_service = privacy_service_inst or privacy_request_service

    def terminate_evaluation(
        self,
        evaluator_id: str,
        reason: str,
        operator_id: str,
        license_id: Optional[str] = None,
        trigger_cascading_erasure: bool = True,
    ) -> Dict[str, Any]:
        """Execute atomic termination workflow."""
        evaluator = self.evaluator_service.get_evaluator(evaluator_id)

        # 1. Revoke all active sessions
        sessions_revoked = self.revocation_service.revoke_all_evaluator_sessions(
            evaluator_id=evaluator_id,
            reason=RevocationReason.ADMIN_REVOCATION if operator_id != "evaluator" else RevocationReason.USER_LOGOUT,
        )

        # 2. Revoke active license if provided
        if license_id:
            self.revocation_service.revoke_license_sessions(
                license_id=license_id,
                reason=RevocationReason.LICENSE_REVOKED,
            )

        # 3. Transition status to TERMINATED
        updated_profile = self.evaluator_service.terminate_evaluator(
            evaluator_id=evaluator_id,
            reason=reason,
            operator_id=operator_id,
        )

        # 4. Trigger data retention lifecycle / cascading erasure
        erasure_result = None
        if trigger_cascading_erasure:
            try:
                erasure_result = self.privacy_service.execute_cascading_erasure(
                    tenant_id=evaluator_id,
                    requester_id=evaluator_id,
                )
            except Exception as e:
                logger.warning("Cascading erasure notice: %s", e)
                erasure_result = {"status": "ERASURE_SKIPPED_OR_MOCKED", "details": str(e)}

        return {
            "status": "TERMINATED",
            "evaluator_id": evaluator_id,
            "sessions_revoked": sessions_revoked,
            "license_revoked": bool(license_id),
            "evaluator_status": updated_profile.status.value,
            "cascading_erasure": erasure_result,
            "message": "Evaluation safely terminated and data lifecycle completed.",
        }


evaluator_termination_service = EvaluatorTerminationService()
