"""
AEGIS-DocIntel Gateway Service Authentication
PROT-FINAL-05: Workstream DEP-02 & DEP-03

Manages cryptographic service-to-service authentication between the
Public Evaluation Gateway and Private Processing Engine using HMAC-SHA256,
short-lived tokens, environment tagging, and replay detection.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional, Set, Tuple

from src.gateway.request_context import TrustedInternalContext

logger = logging.getLogger("aegis.gateway.service_auth")

DEFAULT_INTERNAL_SECRET = os.getenv("AEGIS_INTERNAL_SERVICE_SECRET", "aegis_engine_internal_sec_2026_09")
DEFAULT_STAGING_SECRET = os.getenv("AEGIS_STAGING_SERVICE_SECRET", "aegis_staging_internal_sec_2026_staging")


class GatewayServiceAuth:
    """
    Handles issuance and validation of gateway-to-engine service authorization tokens.
    """

    def __init__(
        self,
        production_secret: str = DEFAULT_INTERNAL_SECRET,
        staging_secret: str = DEFAULT_STAGING_SECRET,
        current_env: str = "production",
    ):
        self._prod_secret = production_secret.encode("utf-8")
        self._staging_secret = staging_secret.encode("utf-8")
        self._current_env = current_env
        self._consumed_request_ids: Set[str] = set()
        self._consumed_reservations: Set[str] = set()

    def set_environment(self, env: str) -> None:
        """Sets the active runtime environment (e.g., 'production', 'staging')."""
        self._current_env = env

    def issue_token(self, context: TrustedInternalContext) -> str:
        """
        Signs the given TrustedInternalContext with the environment secret.
        Returns a JSON string containing the payload and HMAC-SHA256 signature.
        """
        secret = self._prod_secret if context.environment == "production" else self._staging_secret
        canonical_dict = context.to_canonical_dict()
        canonical_str = json.dumps(canonical_dict, sort_keys=True, separators=(",", ":"))
        signature = hmac.new(secret, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()

        envelope = {
            "payload": canonical_dict,
            "signature": signature,
            "key_id": f"gw-{context.environment}-v1",
        }
        return json.dumps(envelope)

    def verify_token(
        self,
        raw_token: str,
        expected_operation: Optional[str] = None,
        expected_tenant_id: Optional[str] = None,
        enforce_environment: bool = True,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Verifies a service token received by the private engine:
        - Validates JSON format and schema
        - Verifies HMAC signature against environment secret
        - Rejects staging credentials presented to production (DEP-TEST-007)
        - Verifies non-expired TTL
        - Prevents request replay
        - Validates tenant boundary matching
        """
        if not raw_token:
            return False, "MISSING_SERVICE_TOKEN", None

        try:
            envelope = json.loads(raw_token)
            payload = envelope["payload"]
            signature = envelope["signature"]
        except Exception:
            return False, "MALFORMED_SERVICE_TOKEN", None

        token_env = payload.get("environment", "production")

        # DEP-TEST-007: Reject staging credential when engine runs in production
        if enforce_environment and self._current_env == "production" and token_env != "production":
            return False, "STAGING_CREDENTIAL_IN_PRODUCTION_REJECTED", None

        secret = self._prod_secret if token_env == "production" else self._staging_secret
        canonical_str = json.dumps(payload, sort_keys=True, separators=(",", ":"))
        expected_sig = hmac.new(secret, canonical_str.encode("utf-8"), hashlib.sha256).hexdigest()

        if not hmac.compare_digest(signature, expected_sig):
            return False, "INVALID_SERVICE_SIGNATURE", None

        # Expiration check
        try:
            exp = datetime.fromisoformat(payload["expires_at"])
            if datetime.now(timezone.utc) > exp:
                return False, "SERVICE_TOKEN_EXPIRED", None
        except Exception:
            return False, "INVALID_EXPIRATION_TIMESTAMP", None

        # Tenant matching
        if expected_tenant_id and payload.get("tenant_id") != expected_tenant_id:
            return False, "TENANT_BOUNDARY_MISMATCH", None

        # Operation matching
        if expected_operation and payload.get("operation") != expected_operation:
            return False, "OPERATION_MISMATCH", None

        # Request replay prevention
        req_id = payload.get("request_id")
        if req_id in self._consumed_request_ids:
            return False, "REPLAYED_REQUEST_ID", None
        self._consumed_request_ids.add(req_id)

        # Quota reservation one-time consumption check
        res_id = payload.get("quota_reservation_id")
        if res_id:
            if res_id in self._consumed_reservations:
                return False, "QUOTA_RESERVATION_ALREADY_CONSUMED", None
            self._consumed_reservations.add(res_id)

        return True, None, payload

    def reset_replays(self) -> None:
        """Resets replay state (for test isolation)."""
        self._consumed_request_ids.clear()
        self._consumed_reservations.clear()


service_auth_manager = GatewayServiceAuth()
