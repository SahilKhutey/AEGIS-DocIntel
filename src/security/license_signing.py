"""
AEGIS-DocIntel Evaluation License Signing & Verification (PROT-FINAL-02 / REM-02)
Implements Pure Ed25519 (EdDSA, RFC 8032) digital signing, verification,
tamper detection, key rotation, and authoritative revocation integration.
"""

from __future__ import annotations

import base64
import json
from typing import Any, Dict, Optional, Tuple

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    verify_license,
    export_license_token,
    CANONICAL_PRODUCT,
)
from services.evaluation_gateway.signing_key_registry import (
    key_registry,
    SigningKeyRegistry,
    CANONICAL_ALGORITHM,
)
from services.evaluation_gateway.revocation import (
    registry as revocation_registry,
    RevocationRegistry,
)


class EvaluationLicenseSigner:
    """Server-side Pure Ed25519 cryptographic license authority."""

    def __init__(
        self,
        key_reg: Optional[SigningKeyRegistry] = None,
        rev_reg: Optional[RevocationRegistry] = None,
    ):
        self._key_registry = key_reg or key_registry
        self._revocation_registry = rev_reg or revocation_registry

    def issue_license(
        self,
        evaluator_id: str,
        tenant_id: str,
        duration_days: int = 14,
        device_limit: int = 1,
        features: Optional[list[str]] = None,
        quotas: Optional[dict[str, int]] = None,
        key_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Issues an Ed25519 digitally signed evaluation license."""
        return issue_evaluation_license(
            user_id=evaluator_id,
            tenant_id=tenant_id,
            duration_days=duration_days,
            device_limit=device_limit,
            features=features,
            quotas=quotas,
            key_id=key_id,
        )

    def verify_license_doc(
        self,
        license_doc: Dict[str, Any],
        expected_user_id: Optional[str] = None,
        expected_device_id: Optional[str] = None,
    ) -> Tuple[bool, Optional[str], Optional[Dict[str, Any]]]:
        """
        Cryptographically verifies Ed25519 digital signature, expiry,
        and authoritative server-side revocation status.
        """
        lic_id = license_doc.get("license_id")
        if lic_id and self._revocation_registry.is_revoked(lic_id):
            return False, "LICENSE_REVOKED", None

        return verify_license(
            license_doc,
            expected_user_id=expected_user_id,
            expected_device_id=expected_device_id,
        )

    def export_token(self, license_doc: Dict[str, Any]) -> str:
        """Serializes signed license document into portable Base64 format."""
        return export_license_token(license_doc)


license_signer = EvaluationLicenseSigner()
