"""
AEGIS-DocIntel Evaluation Revocation Service (PROT-FINAL-02 / REM-05)
Centralized revocation dispatcher for sessions, devices, licenses, and token families.
"""

from __future__ import annotations

from typing import Optional

from src.schemas.evaluation.session import RevocationReason
from src.services.evaluation.session_revocation_service import (
    session_revocation_service,
    SessionRevocationService,
)
from services.evaluation_gateway.revocation import registry as revocation_registry


class EvaluationRevocationService:
    def __init__(self, inner: Optional[SessionRevocationService] = None):
        self._inner = inner or session_revocation_service

    def revoke_session(self, session_id: str, reason: RevocationReason = RevocationReason.USER_LOGOUT) -> bool:
        return self._inner.revoke_session(session_id, reason)

    def revoke_all_evaluator_sessions(
        self, evaluator_id: str, reason: RevocationReason = RevocationReason.ALL_SESSIONS_LOGOUT
    ) -> int:
        return self._inner.revoke_all_evaluator_sessions(evaluator_id, reason)

    def revoke_license_sessions(
        self, license_id: str, reason: RevocationReason = RevocationReason.LICENSE_REVOKED
    ) -> int:
        revocation_registry.revoke(license_id, reason=reason.value)
        return self._inner.revoke_license_sessions(license_id, reason)

    def revoke_device_sessions(
        self, device_id: str, reason: RevocationReason = RevocationReason.DEVICE_DEACTIVATED
    ) -> int:
        return self._inner.revoke_device_sessions(device_id, reason)


revocation_service = EvaluationRevocationService()
