"""
tests/test_mvp4_authentication.py
=================================
Unit and integration tests for authentication middleware, tenant derivation, and role security.
"""

from __future__ import annotations

import pytest
from fastapi import Depends, FastAPI, HTTPException
from fastapi.testclient import TestClient

from src.api.auth import get_current_tenant
from src.core.security_context import TenantContext


def make_auth_app() -> FastAPI:
    app = FastAPI()

    @app.get("/api/protected")
    async def protected_endpoint(tenant: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": tenant.tenant_id,
            "principal_id": tenant.principal_id,
            "role": tenant.role,
        }

    return app


def test_missing_credentials_rejected():
    client = TestClient(make_auth_app())
    resp = client.get("/api/protected")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_dev_bearer_token_derives_tenant(monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    client = TestClient(make_auth_app())
    headers = {"Authorization": "Bearer dev-tenant-corp"}
    resp = client.get("/api/protected", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == "tenant-corp"
    assert "principal_id" in data


def test_dev_api_key_derives_tenant(monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    client = TestClient(make_auth_app())
    headers = {"X-API-Key": "aegis-dev-key"}
    resp = client.get("/api/protected", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["tenant_id"] == "default-tenant"


def test_client_spoofed_tenant_header_ignored(monkeypatch):
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")
    client = TestClient(make_auth_app())
    # Attacker passes an arbitrary X-Tenant-ID header
    headers = {
        "Authorization": "Bearer dev-real-tenant",
        "X-Tenant-ID": "victim-tenant",
    }
    resp = client.get("/api/protected", headers=headers)
    assert resp.status_code == 200
    # Authority must be derived strictly from the authenticated token
    assert resp.json()["tenant_id"] == "real-tenant"
    assert resp.json()["tenant_id"] != "victim-tenant"
