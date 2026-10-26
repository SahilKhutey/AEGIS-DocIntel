"""
tests/security/test_auth_guard_acceptance.py
============================================
Phase 3.1 Work Package A — Authentication Guard Acceptance:
Exercises the Fail-Closed AuthGuardMiddleware in an isolated application environment.
Verifies that:
1. Newly introduced routes are protected by default (deny-by-default).
2. Missing or invalid credentials fail closed with HTTP 401.
3. Health and operational probe paths remain accessible without credentials.
4. Metrics access follows explicit operational allowlist policy.
5. Valid credentials successfully populate request tenant context.
"""
from __future__ import annotations

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from src.api.auth_guard import PUBLIC_PATHS, PUBLIC_PREFIXES, AuthGuardMiddleware


@pytest.fixture
def guarded_app(monkeypatch):
    """Small isolated app to exercise the actual global authentication guard."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    app = FastAPI()
    app.add_middleware(AuthGuardMiddleware)

    @app.get("/protected")
    async def protected(request: Request):
        context = request.state.tenant_context
        return {
            "tenant_id": getattr(context, "tenant_id", "unknown"),
            "principal_id": getattr(context, "principal_id", "unknown"),
        }

    @app.get("/newly-introduced-route")
    async def new_route():
        return {"data": "sensitive-data"}

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.get("/metrics")
    async def metrics():
        return {"test_metric": 1}

    return app


def test_newly_introduced_route_protected_by_default(guarded_app):
    """Any new HTTP route not in PUBLIC_PATHS/PUBLIC_PREFIXES fails closed without auth."""
    client = TestClient(guarded_app)
    response = client.get("/newly-introduced-route")
    assert response.status_code == 401
    assert "Missing authentication" in response.json().get("detail", "")


def test_missing_credentials_fail_closed(guarded_app):
    """Protected routes strictly reject requests without credentials."""
    client = TestClient(guarded_app)
    response = client.get("/protected")
    assert response.status_code == 401
    assert response.headers.get("WWW-Authenticate") == "Bearer"


def test_invalid_bearer_token_fail_closed(guarded_app):
    """Protected routes reject invalid or malformed Bearer tokens."""
    client = TestClient(guarded_app)
    response = client.get("/protected", headers={"Authorization": "Bearer invalid.fake.token"})
    assert response.status_code == 401


def test_invalid_api_key_fail_closed(guarded_app):
    """Protected routes reject unknown or invalid API keys."""
    client = TestClient(guarded_app)
    response = client.get("/protected", headers={"X-API-Key": "nonexistent-secret-key"})
    assert response.status_code == 401


def test_health_endpoint_publicly_accessible(guarded_app):
    """Liveness probe /health is allow-listed for container orchestration systems."""
    client = TestClient(guarded_app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_metrics_endpoint_public_behavior(guarded_app):
    """Metrics endpoint is allow-listed per operational configuration for Prometheus scrape."""
    client = TestClient(guarded_app)
    response = client.get("/metrics")
    assert response.status_code == 200
    assert response.json() == {"test_metric": 1}


def test_valid_development_credentials_allow_access(guarded_app):
    """Valid credentials authenticate successfully and inject TenantContext into request state."""
    client = TestClient(guarded_app)
    response = client.get("/protected", headers={"Authorization": "Bearer dev-tenant-alpha"})
    assert response.status_code == 200
    data = response.json()
    assert data["tenant_id"] == "tenant-alpha"
    assert data["principal_id"] == "dev-user"


def test_cors_options_preflight_bypasses_auth(guarded_app):
    """OPTIONS requests bypass the authentication guard to allow browser CORS preflight."""
    client = TestClient(guarded_app)
    response = client.options("/protected")
    assert response.status_code != 401
