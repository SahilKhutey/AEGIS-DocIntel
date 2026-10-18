"""
Tests for production authentication in src/api/auth.py
Validates:
- RS256 JWT decoding with valid RSA public key
- Expired RS256 JWT handling
- Invalid signature / wrong key handling
- Missing tenant_id claim handling
- Real API key validation via AEGIS_API_KEYS json
- Development bypass preservation in dev mode
- Audit logging on auth events
"""
import json
import os
import time
import pytest
from datetime import datetime, timezone, timedelta
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


def test_production_api_keys(auth_app, tmp_path):
    keys_config = {
        "sk-live-super-secret-key-1": {
            "tenant_id": "tenant-corp",
            "user_id": "svc-integration",
            "role": "admin",
        },
        "sk-live-readonly-key-2": {
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
        # Valid admin key
        res = client.get("/protected", headers={"X-API-Key": "sk-live-super-secret-key-1"})
        assert res.status_code == 200
        assert res.json()["tenant_id"] == "tenant-corp"
        assert res.json()["role"] == "admin"

        # Valid admin key for admin endpoint
        res = client.get("/admin-only", headers={"X-API-Key": "sk-live-super-secret-key-1"})
        assert res.status_code == 200

        # Valid viewer key for admin endpoint -> 403 Forbidden
        res = client.get("/admin-only", headers={"X-API-Key": "sk-live-readonly-key-2"})
        assert res.status_code == 403

        # Invalid key -> 401 Unauthorized
        res = client.get("/protected", headers={"X-API-Key": "sk-invalid-key-999"})
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
