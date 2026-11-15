"""
AEGIS-DocIntel Private Engine Isolation & Internal Authorization Guard
Complies with PROT-04 WP-04.09 specifications:
- Enforces strict boundary between Evaluation Gateway and Private Processing Engine.
- Validates internal server-generated authorization tokens carrying HMAC-SHA256 signatures.
- Rejects unauthenticated direct requests, forged tenant contexts, expired service credentials,
  and unmetered requests lacking valid quota reservations (INT-ENGINE-001 through INT-ENGINE-010).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import secrets
import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional, Set, Tuple

from pydantic import BaseModel, Field, ConfigDict

from services.evaluation_gateway.revocation import registry as revocation_registry

logger = logging.getLogger("aegis.security.private_engine")

# Internal shared secret for gateway-to-engine service authentication
# In production, injected via secure environment variable; never distributed to clients
INTERNAL_SERVICE_SECRET = "aegis_engine_internal_sec_2026_09"


class EngineAuthContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    request_id: str
    principal_id: str
    tenant_id: str
    license_id: str
    session_id: str
    device_id: str
    operation: str
    entitlement_revision: int = 1
    quota_reservation_id: Optional[str] = None
    issued_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    expires_at: datetime
    role: str = "evaluator"


class PrivateEngineGuard:
    def __init__(self, secret: str = INTERNAL_SERVICE_SECRET):
        self._secret = secret.encode("utf-8")
        self._consumed_reservations: Set[str] = set()
        self._consumed_requests: Set[str] = set()

    def create_authorized_token(
        self,
        principal_id: str,
        tenant_id: str,
        license_id: str,
        session_id: str,
        device_id: str,
        operation: str,
        quota_reservation_id: Optional[str] = None,
        ttl_seconds: int = 60,
        role: str = "evaluator",
    ) -> str:
        """
        Gateway-side utility to issue a short-lived internal service token authorizing
        the private engine to execute a specific operation.
        """
        now = datetime.now(timezone.utc)
        req_id = f"eng-req-{secrets.token_hex(8)}"
        payload = {
            "request_id": req_id,
            "principal_id": principal_id,
            "tenant_id": tenant_id,
            "license_id": license_id,
            "session_id": session_id,
            "device_id": device_id,
            "operation": operation,
            "entitlement_revision": 1,
            "quota_reservation_id": quota_reservation_id,
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=ttl_seconds)).isoformat(),
            "role": role,
        }
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        sig = hmac.new(self._secret, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        signed_token = {
            "payload": payload,
            "signature": sig,
        }
        return json.dumps(signed_token)

    def verify_engine_request(
        self,
        raw_token: str,
        expected_operation: str,
        expected_tenant_id: Optional[str] = None,
        requires_quota: bool = True,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Engine-side guard enforcing isolation invariants:
        - Authenticated service-to-service transport (INT-ENGINE-001, INT-ENGINE-002)
        - Tenant context matching (INT-ENGINE-003)
        - Expiration checks (INT-ENGINE-004)
        - One-time quota reservation reuse prevention (INT-ENGINE-005)
        - Mandatory quota reservation check (INT-ENGINE-006)
        - License revocation check (INT-ENGINE-007)
        - Evaluator administrative operation denial (INT-ENGINE-008)
        """
        if not raw_token:
            return False, "MISSING_SERVICE_CREDENTIAL", None

        try:
            doc = json.loads(raw_token)
            payload = doc["payload"]
            signature = doc["signature"]
        except Exception:
            return False, "INVALID_TOKEN_FORMAT", None

        # 1. Verify HMAC Signature
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected_sig = hmac.new(self._secret, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected_sig):
            return False, "TAMPERED_SERVICE_SIGNATURE", None

        # 2. Check Expiration (INT-ENGINE-004)
        now = datetime.now(timezone.utc)
        exp = datetime.fromisoformat(payload["expires_at"])
        if now > exp:
            return False, "EXPIRED_SERVICE_CREDENTIAL", None

        # 3. Check Tenant Isolation (INT-ENGINE-003)
        if expected_tenant_id and payload.get("tenant_id") != expected_tenant_id:
            return False, "CROSS_TENANT_CONTEXT_MISMATCH", None

        # 4. Check Operation Match
        if payload.get("operation") != expected_operation:
            return False, "OPERATION_MISMATCH", None

        # 5. Check Evaluator Privileged Action Denial (INT-ENGINE-008)
        if payload.get("operation", "").startswith("admin.") or payload.get("operation", "").startswith("engine.configure"):
            if payload.get("role") != "engine_admin":
                return False, "ADMIN_OPERATION_DENIED_TO_EVALUATOR", None

        # 6. Check License Revocation (INT-ENGINE-007)
        lic_id = payload.get("license_id")
        if lic_id and revocation_registry.is_revoked(lic_id):
            return False, "LICENSE_REVOKED", None

        # 7. Check Quota Reservation Requirement (INT-ENGINE-006)
        reservation_id = payload.get("quota_reservation_id")
        if requires_quota and not reservation_id:
            return False, "MISSING_QUOTA_RESERVATION", None

        # 8. Check Replay of One-Time Quota Reservation (INT-ENGINE-005)
        if reservation_id:
            if reservation_id in self._consumed_reservations:
                return False, "RESERVATION_ALREADY_CONSUMED", None
            self._consumed_reservations.add(reservation_id)

        req_id = payload.get("request_id")
        if req_id in self._consumed_requests:
            return False, "REQUEST_REPLAY_DETECTED", None
        self._consumed_requests.add(req_id)

        return True, None, payload

    def reset(self) -> None:
        self._consumed_reservations.clear()
        self._consumed_requests.clear()


private_engine_guard = PrivateEngineGuard()
