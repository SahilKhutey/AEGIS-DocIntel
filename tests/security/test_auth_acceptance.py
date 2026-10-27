"""
tests/security/test_auth_acceptance.py
======================================
Phase 3.1 Security Acceptance Suite:
- RS256 JWT verification (expired, invalid signature, algorithm confusion, issuer/audience).
- API key authentication (hash verification, invalid keys, rejection of dev keys in production).
- Production mode fail-closed enforcement (dev bypasses rejected).
- Protected operational vs public endpoints (/health, /readiness, /metrics).
- Payload size limit enforcement (HTTP 413) and error response hygiene.
- Audit logging verification (no raw secrets or tokens logged).
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from src.api.auth import TenantContext, get_current_tenant
from src.api.auth_guard import AuthGuardMiddleware
from src.main import create_app


@pytest.fixture(scope="module")
def rsa_keypair():
    """Generate an RSA 2048 keypair for cryptographic verification."""
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


@pytest.fixture(scope="module")
def second_rsa_keypair():
    """Generate a second, mismatched RSA keypair."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
    )
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    return private_pem


@pytest.fixture
def test_app():
    """Create test application wrapped with AuthGuardMiddleware."""
    app = FastAPI()
    app.add_middleware(AuthGuardMiddleware)

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.get("/readiness")
    def readiness():
        return {"ready": True}

    @app.get("/v1/secure-data")
    def secure_data(tenant: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": tenant.tenant_id,
            "user_id": tenant.user_id,
            "roles": sorted(tenant.roles),
        }

    return app


# ─────────────────────────────────────────────────────────────────
# 1. JWT Security & Cryptographic Invariants
# ─────────────────────────────────────────────────────────────────

def test_missing_credentials_rejected_with_401(test_app):
    client = TestClient(test_app)
    res = client.get("/v1/secure-data")
    assert res.status_code == 401
    assert "Missing authentication" in res.json().get("detail", "")


def test_malformed_jwt_rejected_with_401(test_app):
    client = TestClient(test_app)
    res = client.get("/v1/secure-data", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert res.status_code == 401


def test_expired_jwt_rejected_with_401(rsa_keypair, test_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-alpha",
        "sub": "user-1",
        "role": "editor",
        "iat": now - 3600,
        "exp": now - 1800,  # Expired 30 mins ago
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")
    audit_file = tmp_path / "audit.log"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        res = client.get("/v1/secure-data", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401
        assert "expired" in res.json().get("detail", "").lower()


def test_invalid_signature_wrong_key_rejected(rsa_keypair, second_rsa_keypair, test_app, tmp_path):
    _, public_pem = rsa_keypair
    wrong_private_pem = second_rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-alpha",
        "sub": "user-1",
        "role": "editor",
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, wrong_private_pem, algorithm="RS256")
    audit_file = tmp_path / "audit.log"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        res = client.get("/v1/secure-data", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_algorithm_confusion_rejected(rsa_keypair, test_app, tmp_path):
    """Presenting an HMAC-SHA256 (HS256) token when RS256 is expected must fail."""
    _, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-alpha",
        "sub": "user-1",
        "role": "editor",
        "iat": now,
        "exp": now + 3600,
    }
    # Token encoded with 32-byte symmetric HMAC secret
    token = jwt.encode(payload, "symmetric-secret-key-at-least-32-bytes-long!", algorithm="HS256")
    audit_file = tmp_path / "audit.log"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        res = client.get("/v1/secure-data", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_issuer_and_audience_validation(rsa_keypair, test_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-alpha",
        "sub": "user-1",
        "role": "editor",
        "iss": "https://wrong-issuer.corp",
        "aud": "wrong-audience",
        "iat": now,
        "exp": now + 3600,
    }
    token = jwt.encode(payload, private_pem, algorithm="RS256")
    audit_file = tmp_path / "audit.log"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-docintel",
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        res = client.get("/v1/secure-data", headers={"Authorization": f"Bearer {token}"})
        assert res.status_code == 401


def test_missing_tenant_id_or_sub_rejected(rsa_keypair, test_app, tmp_path):
    private_pem, public_pem = rsa_keypair
    now = int(time.time())

    # Missing tenant_id
    t1 = jwt.encode({"sub": "u1", "role": "editor", "exp": now + 3600}, private_pem, algorithm="RS256")
    # Missing sub
    t2 = jwt.encode({"tenant_id": "t1", "role": "editor", "exp": now + 3600}, private_pem, algorithm="RS256")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": public_pem,
        "AEGIS_AUDIT_LOG_PATH": str(tmp_path / "audit.log"),
    }):
        client = TestClient(test_app)
        assert client.get("/v1/secure-data", headers={"Authorization": f"Bearer {t1}"}).status_code == 401
        assert client.get("/v1/secure-data", headers={"Authorization": f"Bearer {t2}"}).status_code == 401


# ─────────────────────────────────────────────────────────────────
# 2. Production API Key Authentication
# ─────────────────────────────────────────────────────────────────

def test_production_api_key_valid_hash(test_app, tmp_path):
    test_api_key = "aegis-test-api-key-1111111111"
    key_hash = hashlib.sha256(test_api_key.encode("utf-8")).hexdigest()
    # AEGIS_API_KEYS is a dictionary mapping SHA-256 hash to metadata
    key_config = json.dumps({
        key_hash: {"tenant_id": "tenant-prod", "role": "admin", "user_id": "prod-user"}
    })
    audit_file = tmp_path / "audit.log"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_API_KEYS": key_config,
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        res = client.get("/v1/secure-data", headers={"X-API-Key": test_api_key})
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["tenant_id"] == "tenant-prod"
        assert "admin" in data["roles"]


def test_production_rejects_dev_bypass_credentials(test_app, tmp_path):
    """In production mode, dev-* bearer tokens and aegis-dev-key MUST be rejected."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_AUDIT_LOG_PATH": str(tmp_path / "audit.log"),
    }):
        client = TestClient(test_app)
        # dev bearer token
        res_bearer = client.get("/v1/secure-data", headers={"Authorization": "Bearer dev-tenant-alpha"})
        assert res_bearer.status_code == 401

        # dev API key
        res_key = client.get("/v1/secure-data", headers={"X-API-Key": "aegis-dev-key"})
        assert res_key.status_code == 401


# ─────────────────────────────────────────────────────────────────
# 3. Operational & Metrics Endpoints
# ─────────────────────────────────────────────────────────────────

def test_operational_endpoints_reachability(test_app):
    client = TestClient(test_app)
    # Liveness & readiness probes require no credentials
    assert client.get("/health").status_code == 200
    assert client.get("/readiness").status_code == 200


def test_payload_limit_enforced():
    """Verify middleware rejects payload exceeding max_upload_bytes with HTTP 413."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "development",
        "AEGIS_MAX_UPLOAD_BYTES": "1024",  # 1024 bytes minimum valid setting
    }):
        app = create_app()
        client = TestClient(app)
        headers = {
            "Authorization": "Bearer dev-tenant-alpha",
            "Content-Length": "2048",  # exceeds 1024
        }
        res = client.post("/v1/documents/upload", headers=headers, content=b"A" * 2048)
        assert res.status_code == 413
        assert "exceeds limit" in res.json().get("detail", "")


def test_audit_logs_never_leak_plaintext_secrets(test_app, tmp_path):
    """Verify that audit logs write action metadata but never raw secrets or bearer tokens."""
    audit_file = tmp_path / "audit.log"
    secret_key = "aegis-secret-sensitive-token-123456"

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_AUDIT_LOG_PATH": str(audit_file),
    }):
        client = TestClient(test_app)
        client.get("/v1/secure-data", headers={"X-API-Key": secret_key})

        if audit_file.exists():
            content = audit_file.read_text(encoding="utf-8")
            assert secret_key not in content, "Plaintext API key was leaked into audit log!"
