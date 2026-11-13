"""
AEGIS Distribution Security Tests — License Cryptographic Validation
Covers:
- SEC-DEMO-006: Valid Ed25519 evaluation license cryptographic acceptance
- SEC-DEMO-007: Tampered license signature verification rejection
- SEC-DEMO-008: Expired license rejection
- SEC-DEMO-018: Revoked license rejection
"""

import copy
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    verify_license,
    load_public_key,
    load_private_key,
    LicenseSignatureError,
    LicenseExpiredError,
    LicenseRevokedError,
    LicenseVerificationError,
)
from services.evaluation_gateway.revocation import RevocationRegistry

def test_sec_demo_006_valid_license_acceptance():
    """SEC-DEMO-006: Valid Ed25519-signed evaluation license verifies successfully."""
    lic = issue_evaluation_license(user_id="legitimate-evaluator", duration_days=14)
    pub_key = load_public_key()
    
    verified_payload = verify_license(license_doc=lic, public_key=pub_key)
    assert verified_payload["user_id"] == "legitimate-evaluator"
    assert verified_payload["tier"] == "evaluation"
    assert "ask_aegis" in verified_payload["features"]
    assert verified_payload["quotas"]["max_queries_per_day"] == 20


def test_sec_demo_007_tampered_license_signature_rejection():
    """SEC-DEMO-007: Modifying license payload (e.g. attempting to grant unlimited quota) breaks signature verification."""
    lic = issue_evaluation_license(user_id="evaluator", duration_days=14)
    tampered_lic = copy.deepcopy(lic)
    
    # Attacker attempts to grant unlimited queries and 1000 days
    tampered_lic["payload"]["quotas"]["max_queries_per_day"] = 999999
    
    pub_key = load_public_key()
    with pytest.raises(LicenseSignatureError) as exc_info:
        verify_license(license_doc=tampered_lic, public_key=pub_key)
        
    assert "signature verification failed" in str(exc_info.value).lower()


def test_sec_demo_008_expired_license_rejection():
    """SEC-DEMO-008: An evaluation license past its expiration timestamp is rejected."""
    # Create license that expired 1 day ago
    priv_key = load_private_key()
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    expired_lic = issue_evaluation_license(user_id="evaluator", duration_days=-1, private_key=priv_key)
    pub_key = load_public_key()
    
    with pytest.raises(LicenseExpiredError) as exc_info:
        verify_license(license_doc=expired_lic, public_key=pub_key)
        
    assert "license expired" in str(exc_info.value).lower()


def test_sec_demo_018_revoked_license_rejection(tmp_path: Path):
    """SEC-DEMO-018: A revoked license ID is rejected even if mathematically valid and unexpired."""
    reg = RevocationRegistry(storage_path=tmp_path / "revocation_test.json")
    lic = issue_evaluation_license(user_id="rogue-evaluator", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    
    # Revoke license
    reg.revoke(lic_id)
    assert reg.is_revoked(lic_id)
    
    pub_key = load_public_key()
    with pytest.raises(LicenseRevokedError) as exc_info:
        verify_license(
            license_doc=lic,
            public_key=pub_key,
            revocation_set=reg.get_revoked_set()
        )
        
    assert f"License {lic_id} has been revoked" in str(exc_info.value)
