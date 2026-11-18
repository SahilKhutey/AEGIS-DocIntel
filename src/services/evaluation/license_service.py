"""
AEGIS-DocIntel Evaluation License Service (PROT-FINAL-02 / REM-02)
Manages evaluation license lifecycles, Ed25519 issuance, verification,
key rotation, and status lookups.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    verify_license,
    export_license_token,
    parse_license_token,
    CANONICAL_PRODUCT,
)
from services.evaluation_gateway.signing_key_registry import key_registry
from services.evaluation_gateway.revocation import registry as revocation_registry


class EvaluationLicenseService:
    def issue_license(
        self,
        evaluator_id: str,
        tenant_id: str,
        duration_days: int = 14,
        device_limit: int = 1,
        features: Optional[List[str]] = None,
        quotas: Optional[Dict[str, int]] = None,
        key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return issue_evaluation_license(
            user_id=evaluator_id,
            duration_days=duration_days,
            max_devices=device_limit,
            features=features,
            quotas=quotas,
            kid=key_id,
        )

    def verify_license(
        self,
        license_doc: Dict[str, Any],
        expected_user_id: Optional[str] = None,
        expected_device_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        lic_id = license_doc.get("license_id")
        if lic_id and revocation_registry.is_revoked(lic_id):
            return False, "LICENSE_REVOKED", None
        return verify_license(
            license_doc,
            expected_user_id=expected_user_id,
            expected_device_id=expected_device_id,
        )

    def revoke_license(self, license_id: str, reason: str = "Admin manual revocation") -> None:
        revocation_registry.revoke(license_id, reason=reason)

    def is_revoked(self, license_id: str) -> bool:
        return revocation_registry.is_revoked(license_id)

    def get_public_keys(self) -> List[Dict[str, Any]]:
        return key_registry.get_public_keys_metadata()


license_service = EvaluationLicenseService()
