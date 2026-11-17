"""
AEGIS-DocIntel Remediation Acceptance Test Suite: REM-01 Authentication Hardening
Verifies AUTH-REM-001 through AUTH-REM-010.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from fastapi import FastAPI, Depends, Request
from fastapi.testclient import TestClient
import jwt

from src.api.auth import get_current_tenant, validate_token_roles, ALLOWED_ROLES
from src.api.auth_guard import AuthGuardMiddleware
from src.core.security_context import TenantContext


@pytest.fixture(scope="module")
def rsa_keypair():
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv_pem, pub_pem


@pytest.fixture
def auth_app():
    app = FastAPI()
    app.add_middleware(AuthGuardMiddleware)

    @app.get("/api/protected")
    async def protected_route(context: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": context.tenant_id,
            "principal_id": context.principal_id,
            "roles": list(context.roles),
        }

    @app.get("/api/admin-only")
    async def admin_only_route(context: TenantContext = Depends(get_current_tenant)):
        if "admin" not in context.roles and "tenant_admin" not in context.roles:
            from fastapi import HTTPException
            raise HTTPException(status_code=403, detail="Admin role required")
        return {"status": "admin_granted"}

    @app.get("/metrics")
    async def metrics_endpoint():
        return {"metrics": "prometheus"}

    @app.websocket("/ws/data")
    async def ws_endpoint(websocket):
        from src.api.auth import get_current_tenant_ws
        await websocket.accept()
        ctx = await get_current_tenant_ws(websocket)
        await websocket.send_json({"tenant_id": ctx.tenant_id})
        await websocket.close()

    return app


def test_auth_rem_001_dev_token_rejected_in_production(auth_app):
    """AUTH-REM-001: Development token is rejected with HTTP 401 in production."""
    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "production"}):
        client = TestClient(auth_app)
        res = client.get("/api/protected", headers={"Authorization": "Bearer dev-sample-tenant"})
        assert res.status_code == 401


def test_auth_rem_002_missing_issuer_rejected(rsa_keypair, auth_app):
    """AUTH-REM-002: Token missing required issuer is rejected with HTTP 401."""
    priv, pub = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-001",
        "sub": "user-001",
        "role": "analyst",
        "aud": "aegis-api",
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_EVALUATION_MODE": "true",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get("/api/protected", headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 401


def test_auth_rem_003_missing_audience_rejected(rsa_keypair, auth_app):
    """AUTH-REM-003: Token missing required audience is rejected with HTTP 401."""
    priv, pub = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-001",
        "sub": "user-001",
        "role": "operator",
        "iss": "https://auth.aegis.corp",
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_EVALUATION_MODE": "true",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get("/api/protected", headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 401


def test_auth_rem_004_expired_token_rejected(rsa_keypair, auth_app):
    """AUTH-REM-004: Expired token is rejected with HTTP 401."""
    priv, pub = rsa_keypair
    past = int(time.time()) - 3600
    payload = {
        "tenant_id": "tenant-001",
        "sub": "user-001",
        "role": "evaluation_user",
        "iss": "https://auth.aegis.corp",
        "aud": "aegis-api",
        "exp": past,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get("/api/protected", headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 401


def test_auth_rem_005_invalid_role_rejected(rsa_keypair, auth_app):
    """AUTH-REM-005: Token carrying unapproved role is rejected with HTTP 401."""
    priv, pub = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-001",
        "sub": "user-001",
        "role": "super_root_hacker",
        "iss": "https://auth.aegis.corp",
        "aud": "aegis-api",
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get("/api/protected", headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 401


def test_auth_rem_006_tenant_header_manipulation_rejected(rsa_keypair, auth_app):
    """AUTH-REM-006: Injected X-Tenant-ID differing from token tenant is rejected with HTTP 403."""
    priv, pub = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "legit-tenant-alpha",
        "sub": "user-001",
        "role": "viewer",
        "iss": "https://auth.aegis.corp",
        "aud": "aegis-api",
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get(
            "/api/protected",
            headers={
                "Authorization": f"Bearer {tok}",
                "X-Tenant-ID": "forged-victim-tenant-beta",
            },
        )
        assert res.status_code == 403
        assert "Tenant header manipulation rejected" in res.json().get("detail", "")


def test_auth_rem_007_admin_privilege_escalation_rejected(rsa_keypair, auth_app):
    """AUTH-REM-007: Evaluator attempting to invoke admin route is denied HTTP 403."""
    priv, pub = rsa_keypair
    now = int(time.time())
    payload = {
        "tenant_id": "tenant-eval-007",
        "sub": "user-eval-007",
        "role": "evaluation_user",
        "iss": "https://auth.aegis.corp",
        "aud": "aegis-api",
        "exp": now + 3600,
    }
    tok = jwt.encode(payload, priv, algorithm="RS256")
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        client = TestClient(auth_app)
        res = client.get("/api/admin-only", headers={"Authorization": f"Bearer {tok}"})
        assert res.status_code == 403


def test_auth_rem_008_public_metrics_access_restricted_in_hardened_mode(auth_app):
    """AUTH-REM-008: In hardened evaluation mode, /metrics rejects unauthenticated access."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_RESTRICT_OPERATIONAL_ENDPOINTS": "true",
    }):
        client = TestClient(auth_app)
        res = client.get("/metrics")
        assert res.status_code == 401


def test_auth_rem_009_websocket_authentication_required(auth_app):
    """AUTH-REM-009: Unauthenticated WebSocket handshake is rejected with 401."""
    client = TestClient(auth_app)
    with pytest.raises(Exception):
        with client.websocket_connect("/ws/data") as ws:
            pass


def test_auth_rem_010_production_build_contains_no_dev_fallback():
    """AUTH-REM-010: Static scan verifies zero dev- tokens or bypass keys in web/src."""
    web_src = Path("web/src")
    if not web_src.exists():
        pytest.skip("web/src directory not present")

    violations = []
    for f in web_src.rglob("*"):
        if f.is_file() and f.suffix in (".ts", ".tsx", ".js", ".jsx", ".json"):
            c = f.read_text(encoding="utf-8", errors="ignore")
            if "NEXT_PUBLIC_AEGIS_DEV_TOKEN" in c or "dev-admin-token" in c:
                violations.append(str(f))

    assert len(violations) == 0, f"Found dev token fallback in production build: {violations}"
