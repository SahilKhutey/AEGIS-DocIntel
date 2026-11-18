"""
AEGIS-DocIntel Invitation Repository
PROT-FINAL-08: Invitation Token Management and Verification
"""

from __future__ import annotations

import hashlib
import threading
from datetime import datetime, timezone
from typing import Dict, List, Optional

from src.schemas.evaluation.invitation import EvaluationInvite, InvitationStatus


class InvitationNotFoundError(Exception):
    pass


class InvitationExpiredError(Exception):
    pass


class InvitationAlreadyAcceptedError(Exception):
    pass


class InvitationRepository:
    """Thread-safe in-memory store for evaluation invitations."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._invitations: Dict[str, EvaluationInvite] = {}
        self._token_hash_index: Dict[str, str] = {}  # token_hash -> invite_id

    def create(self, invite: EvaluationInvite) -> EvaluationInvite:
        with self._lock:
            self._invitations[invite.id] = invite
            self._token_hash_index[invite.token_hash] = invite.id
            return invite

    def get_by_id(self, invite_id: str) -> Optional[EvaluationInvite]:
        with self._lock:
            return self._invitations.get(invite_id)

    def get_by_token(self, raw_token: str) -> Optional[EvaluationInvite]:
        with self._lock:
            token_hash = hashlib.sha256(raw_token.encode("utf-8")).hexdigest()
            invite_id = self._token_hash_index.get(token_hash)
            if not invite_id:
                return None
            return self._invitations.get(invite_id)

    def list_by_evaluator(self, evaluator_id: str) -> List[EvaluationInvite]:
        with self._lock:
            return [
                inv for inv in self._invitations.values()
                if inv.evaluator_id == evaluator_id
            ]

    def accept(self, raw_token: str) -> EvaluationInvite:
        with self._lock:
            invite = self.get_by_token(raw_token)
            if not invite:
                raise InvitationNotFoundError("Invalid invitation token")

            if invite.status == InvitationStatus.ACCEPTED:
                raise InvitationAlreadyAcceptedError("Invitation has already been accepted")

            if invite.status != InvitationStatus.PENDING:
                raise InvitationExpiredError(f"Invitation is not pending (status: {invite.status.value})")

            # Check expiration
            expires_at = datetime.fromisoformat(invite.expires_at)
            now = datetime.now(timezone.utc)
            if now > expires_at:
                updated_expired = invite.model_copy(update={"status": InvitationStatus.EXPIRED})
                self._invitations[invite.id] = updated_expired
                raise InvitationExpiredError("Invitation token has expired")

            now_iso = now.isoformat()
            accepted = invite.model_copy(
                update={"status": InvitationStatus.ACCEPTED, "accepted_at": now_iso}
            )
            self._invitations[invite.id] = accepted
            return accepted

    def revoke(self, invite_id: str) -> EvaluationInvite:
        with self._lock:
            invite = self.get_by_id(invite_id)
            if not invite:
                raise InvitationNotFoundError(f"Invitation '{invite_id}' not found")
            revoked = invite.model_copy(update={"status": InvitationStatus.REVOKED})
            self._invitations[invite.id] = revoked
            return revoked
