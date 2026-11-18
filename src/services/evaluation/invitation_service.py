"""
AEGIS-DocIntel Invitation Service
PROT-FINAL-08: High-Entropy Invitation Issuance and Acceptance
"""

from __future__ import annotations

import hashlib
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from src.repositories.evaluation.evaluator_repository import EvaluatorRepository
from src.repositories.evaluation.invitation_repository import (
    InvitationExpiredError,
    InvitationNotFoundError,
    InvitationRepository,
)
from src.schemas.evaluation.evaluator import EvaluatorProfile, EvaluatorStatus
from src.schemas.evaluation.invitation import (
    EvaluationInvite,
    InvitationStatus,
    InviteCreate,
    InviteResponse,
)


class InvitationService:
    """Issues, verifies, and accepts time-limited evaluation invitations."""

    def __init__(
        self,
        invite_repo: Optional[InvitationRepository] = None,
        evaluator_repo: Optional[EvaluatorRepository] = None,
    ) -> None:
        self.invite_repo = invite_repo or InvitationRepository()
        self.evaluator_repo = evaluator_repo or EvaluatorRepository()

    def issue_invitation(self, payload: InviteCreate) -> InviteResponse:
        evaluator = self.evaluator_repo.get_by_id(payload.evaluator_id)
        if not evaluator:
            raise ValueError(f"Cannot invite nonexistent evaluator '{payload.evaluator_id}'")

        if evaluator.status in [EvaluatorStatus.TERMINATED, EvaluatorStatus.REVOKED]:
            raise ValueError(f"Cannot issue invitation for evaluator in terminal state '{evaluator.status.value}'")

        raw_token = f"aegis-inv-{secrets.token_urlsafe(32)}"
        token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(hours=payload.ttl_hours)).isoformat()
        invite_id = f"inv-{uuid.uuid4().hex[:12]}"

        invite = EvaluationInvite(
            id=invite_id,
            evaluator_id=payload.evaluator_id,
            token_hash=token_hash,
            status=InvitationStatus.PENDING,
            expires_at=expires_at,
            accepted_at=None,
            created_by=payload.operator_id,
            created_at=now.isoformat(),
        )

        created_invite = self.invite_repo.create(invite)
        invitation_url = f"https://evaluate.aegis.corp/onboarding?token={raw_token}"

        return InviteResponse(
            invitation=created_invite,
            raw_token=raw_token,
            invitation_url=invitation_url,
            message="Evaluation invitation generated successfully",
        )

    def accept_invitation(
        self,
        raw_token: str,
        accept_agreement: bool,
        acknowledge_privacy_notice: bool,
        agreement_version: str = "1.0.0",
        privacy_notice_version: str = "1.0.0",
    ) -> EvaluatorProfile:
        if not accept_agreement:
            raise ValueError("You must explicitly accept the Evaluation Agreement to proceed.")
        if not acknowledge_privacy_notice:
            raise ValueError("You must explicitly acknowledge the Privacy Notice to proceed.")

        accepted_invite = self.invite_repo.accept(raw_token)
        evaluator_id = accepted_invite.evaluator_id

        # Update agreements
        self.evaluator_repo.record_agreements(
            evaluator_id=evaluator_id,
            agreement_version=agreement_version,
            privacy_notice_version=privacy_notice_version,
        )

        # Transition status to REGISTERED
        updated_profile = self.evaluator_repo.transition_status(
            evaluator_id=evaluator_id,
            target_status=EvaluatorStatus.REGISTERED,
            reason="Invitation accepted and agreements signed",
            operator_id="evaluator",
            allowed_from=[EvaluatorStatus.INVITED],
        )

        return updated_profile


invitation_service = InvitationService()
