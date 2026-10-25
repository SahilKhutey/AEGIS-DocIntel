"""
Tests for production authentication in src/api/auth.py
Validates:
- RS256 JWT decoding with valid RSA public key
- Cryptographic verification that configured key is an RSA public key
- Expired RS256 JWT handling
- Invalid signature / wrong key handling
- Algorithm confusion rejection (HS256 presented to RS256 verifier)
- Configured issuer and audience validation
- Missing tenant_id claim handling
- Missing subject (user_id) claim handling
- Unsupported role rejection
- Production API key validation via hash-only (SHA-256) AEGIS_API_KEYS lookup
- Raw API key in configuration rejection
- Malformed API key configuration rejection
- Plaintext API key never logged in audit trail
- Development bypass preservation in dev mode & rejection in production mode
"""
import hashlib
import json
import os
import time
import pytest
from unittest.mock import patch

from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization
import jwt

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.auth import get_current_tenant, TenantContext, require_role
from src.observability.audit_logger import AuditLogger


@pytest.fixture(scope="module")
def rsa_keypair():
    """Generate an RSA 2048 keypair for RS256 JWT testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    public_pem = private_key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    return private_pem, public_pem


@pytest.fixture
def auth_app():
    """Create a minimal FastAPI app with auth-protected routes."""
    app = FastAPI()

    @app.get("/protected")
    async def protected_route(tenant: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": tenant.tenant_id,
            "user_id": tenant.user_id,
            "role": tenant.role,
        }

    @app.get("/admin-only")
    async def admin_route(tenant: TenantContext = Depends(require_role("admin"))):
        return {"status": "ok", "tenant_id": tenant.tenant_id}

    return app


def test_production_rs256_jwt_valid(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-prod-100",
        "sub": "user-42",
        "role": "admin",
        "exp": now + 3600,
        "iat": now,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["tenant_id"] == "tenant-prod-100"
        assert data["user_id"] == "user-42"
        assert data["role"] == "admin"

        admin_res = client.get("/admin-only", headers={"Authorization": f"Bearer {token}"})
        assert admin_res.status_code == 200


def test_production_rs256_jwt_expired(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-prod-100",
        "sub": "user-42",
        "exp": now - 300,  # 5 minutes expired
        "iat": now - 600,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert "expired" in res.text.lower()


def test_production_rs256_jwt_wrong_key(rsa_keypair, auth_app, tmp_path):
    # Generate another key to sign
    other_priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    other_priv_pem = other_priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    _, public_pem = rsa_keypair
    now = int(time.time())
    token = jwt.encode(
        {"tenant_id": "tenant-prod-100", "sub": "attacker", "exp": now + 3600},
        other_priv_pem,
        algorithm="RS256",
    )

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_production_rejects_algorithm_confusion_hs256(rsa_keypair, auth_app, tmp_path):
    """
    Ensure an attacker cannot forge an HS256 JWT using an arbitrary HMAC secret
    when RS256 is the configured algorithm (CVE-2015-9235 defense).
    """
    _, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-forged",
        "sub": "attacker",
        "role": "admin",
        "exp": now + 3600,
        "iat": now,
    }
    forged_token = jwt.encode(payload, "attacker-secret-key-that-is-long-enough-32bytes", algorithm="HS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {forged_token}"})
        assert res.status_code == 401
        assert "algorithm" in res.text.lower() or "invalid" in res.text.lower()


def test_production_jwt_issuer_and_audience(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    valid_payload = {
        "tenant_id": "tenant-prod-100",
        "sub": "user-42",
        "role": "editor",
        "iss": "https://auth.aegis.corp",
        "aud": "aegis-docintel-api",
        "exp": now + 3600,
    }
    valid_token = jwt.encode(valid_payload, private_pem, algorithm="RS256")

    wrong_iss_token = jwt.encode(
        {**valid_payload, "iss": "https://attacker.com"},
        private_pem,
        algorithm="RS256",
    )
    wrong_aud_token = jwt.encode(
        {**valid_payload, "aud": "other-api"},
        private_pem,
        algorithm="RS256",
    )

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-docintel-api",
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        # Valid issuer & audience
        ok_res = client.get("/protected", headers={"Authorization": f"Bearer {valid_token}"})
        assert ok_res.status_code == 200

        # Wrong issuer
        iss_res = client.get("/protected", headers={"Authorization": f"Bearer {wrong_iss_token}"})
        assert iss_res.status_code == 401

        # Wrong audience
        aud_res = client.get("/protected", headers={"Authorization": f"Bearer {wrong_aud_token}"})
        assert aud_res.status_code == 401


def test_production_rs256_jwt_missing_tenant_id(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "sub": "user-no-tenant",
        "role": "admin",
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert "tenant_id" in res.text


def test_production_jwt_missing_subject(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-prod-100",
        "role": "admin",
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_production_jwt_unsupported_role(rsa_keypair, auth_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-prod-100",
        "sub": "user-super",
        "role": "super-god-role",
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert "unsupported role" in res.text.lower()


def test_production_jwt_non_rsa_key_fails_closed(auth_app, tmp_path):
    """Symmetric string or non-RSA public key must fail closed."""
    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": "not-a-valid-rsa-pem-key",
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"Authorization": "Bearer some.jwt.token"})
        assert res.status_code == 401


def test_production_api_keys_hash_only(auth_app, tmp_path):
    raw_key1 = "sk-live-super-secret-key-1"
    raw_key2 = "sk-live-readonly-key-2"
    hash1 = hashlib.sha256(raw_key1.encode("utf-8")).hexdigest()
    hash2 = hashlib.sha256(raw_key2.encode("utf-8")).hexdigest()

    keys_config = {
        hash1: {
            "tenant_id": "tenant-corp",
            "user_id": "svc-integration",
            "role": "admin",
        },
        hash2: {
            "tenant_id": "tenant-corp",
            "user_id": "svc-monitoring",
            "role": "viewer",
        },
    }

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_API_KEYS": json.dumps(keys_config),
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        # Valid admin key -> matches hash1
        res = client.get("/protected", headers={"X-API-Key": raw_key1})
        assert res.status_code == 200
        assert res.json()["tenant_id"] == "tenant-corp"
        assert res.json()["role"] == "admin"

        # Valid admin key for admin endpoint
        res = client.get("/admin-only", headers={"X-API-Key": raw_key1})
        assert res.status_code == 200

        # Valid viewer key for admin endpoint -> 403 Forbidden
        res = client.get("/admin-only", headers={"X-API-Key": raw_key2})
        assert res.status_code == 403

        # Invalid key -> 401 Unauthorized
        res = client.get("/protected", headers={"X-API-Key": "sk-invalid-key-999"})
        assert res.status_code == 401

        # Empty key -> 401
        res = client.get("/protected", headers={"X-API-Key": ""})
        assert res.status_code == 401

    # Verify audit log never contains raw API key
    if audit_path.exists():
        log_content = audit_path.read_text(encoding="utf-8")
        assert raw_key1 not in log_content
        assert raw_key2 not in log_content


def test_production_api_keys_rejects_raw_keys_in_config(auth_app, tmp_path):
    """P0-4: Raw API keys in configuration must be rejected (only 64-char hex digests allowed)."""
    raw_key = "sk-live-raw-unhashed-key"
    keys_config = {
        raw_key: {  # Not a 64-char SHA256 hex digest
            "tenant_id": "tenant-corp",
            "user_id": "svc-raw",
            "role": "admin",
        }
    }

    audit_path = tmp_path / "audit.log"
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_API_KEYS": json.dumps(keys_config),
        "AEGIS_AUDIT_LOG_PATH": str(audit_path),
    }):
        client = TestClient(auth_app)
        res = client.get("/protected", headers={"X-API-Key": raw_key})
        # Fails closed because stored configuration key is not a valid SHA-256 hex digest
        assert res.status_code == 401


def test_development_bypass_preservation(auth_app):
    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "development"}):
        client = TestClient(auth_app)
        # Dev Bearer token
        res = client.get("/protected", headers={"Authorization": "Bearer dev-tenant-custom"})
        assert res.status_code == 200
        assert res.json()["tenant_id"] == "tenant-custom"

        # Dev API key
        res = client.get("/protected", headers={"X-API-Key": "aegis-dev-key"})
        assert res.status_code == 200
        assert res.json()["tenant_id"] == "default-tenant"

    # In production, dev bypass must return 401
    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "production"}):
        client = TestClient(auth_app)
        assert client.get("/protected", headers={"Authorization": "Bearer dev-tenant-custom"}).status_code == 401
        assert client.get("/protected", headers={"X-API-Key": "aegis-dev-key"}).status_code == 401
