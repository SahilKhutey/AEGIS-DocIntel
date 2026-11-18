"""
Tests for PROT-FINAL-05: Secrets Management & Manifest Auditing
Covers DEP-TEST-007, DEP-TEST-008
"""

import pytest

from src.gateway.request_context import TrustedInternalContext
from src.gateway.service_auth import GatewayServiceAuth
from infrastructure.secrets.secret_manager import SecretManager, SecretResolutionError
from infrastructure.scripts.validate_deployment_manifests import run_all_manifest_validations


def test_dep_007_staging_credential_in_production_rejected():
    """DEP-TEST-007: Staging credentials presented to a production environment are rejected."""
    # 1. Test GatewayServiceAuth
    auth = GatewayServiceAuth(current_env="production")
    
    # Issue a token tagged with environment=staging
    staging_ctx = TrustedInternalContext(
        principal_id="eval-staging-user",
        tenant_id="tenant-staging",
        license_id="lic-staging",
        session_id="sess-staging",
        device_id="dev-staging",
        operation="intelligence.query",
        environment="staging",
    )
    staging_token = auth.issue_token(staging_ctx)

    # In production, verify_token must reject the staging token
    valid, err, _ = auth.verify_token(staging_token, enforce_environment=True)
    assert not valid
    assert err == "STAGING_CREDENTIAL_IN_PRODUCTION_REJECTED"

    # 2. Test SecretManager
    mgr = SecretManager(current_env="production")
    with pytest.raises(SecretResolutionError, match="Staging or test secret detected in production"):
        mgr.resolve_secret("DATABASE_PASSWORD", default="test_staging_password_123")


def test_dep_008_no_plaintext_secrets_in_deployment_manifests():
    """DEP-TEST-008: Release is blocked if any deployment manifest exposes plaintext secrets."""
    passed = run_all_manifest_validations()
    assert passed, "Deployment manifests contain security violations or plaintext secrets!"


def test_key_purpose_segregation():
    """Verifies that separate purposes cannot reuse the same signing key."""
    mgr = SecretManager()
    
    # Distinct keys pass
    valid_keys = {
        "jwt_signing_key": "mock_jwt_signing_val",
        "license_signing_key": "mock_lic_signing_val",
        "internal_service_secret": "mock_srv_secret_val",
    }
    assert mgr.validate_key_separation(valid_keys)

    # Reused key fails
    reused_keys = {
        "jwt_signing_key": "mock_reused_val",
        "license_signing_key": "mock_reused_val",
    }
    with pytest.raises(SecretResolutionError, match="Key purpose violation"):
        mgr.validate_key_separation(reused_keys)
