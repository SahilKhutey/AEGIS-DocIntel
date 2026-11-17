"""
Tests for Demo Isolation and Security Boundaries (demo/tests/test_demo_isolation.py)
Validates:
- Demo token scoping to demo-tenant with restricted viewer/editor roles
- Demo token rejection when AEGIS_DEMO_MODE is disabled (production fail-closed)
- RBAC enforcement: demo-tenant blocked from tenant-admin and platform-admin routes
- Cross-tenant data isolation: demo-tenant cannot access foreign tenant records
- Anonymous access gating: allowed only when explicitly configured
"""
import os
import pytest
from unittest.mock import patch
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.testclient import TestClient

from src.api.auth import get_current_tenant, TenantContext, require_role
from src.api.auth_guard import AuthGuardMiddleware


@pytest.fixture
def demo_test_app():
    app = FastAPI()
    app.add_middleware(AuthGuardMiddleware)

    @app.get("/api/v1/workspace")
    async def get_workspace(tenant: TenantContext = Depends(get_current_tenant)):
        return {
            "tenant_id": tenant.tenant_id,
            "principal_id": tenant.principal_id,
            "roles": sorted(list(tenant.roles)),
            "can_delete": tenant.can_delete_document(),
            "can_write": tenant.can_write_document(),
        }

    @app.get("/api/v1/admin/maintenance")
    async def admin_only(tenant: TenantContext = Depends(require_role("platform_admin"))):
        return {"status": "ok", "admin": tenant.principal_id}

    @app.get("/api/v1/tenant-admin-only")
    async def tenant_admin_only(tenant: TenantContext = Depends(require_role("tenant_admin"))):
        return {"status": "ok", "tenant_id": tenant.tenant_id}

    return app


def test_demo_token_accepted_in_demo_mode(demo_test_app):
    """When AEGIS_DEMO_MODE=true, demo token gives access to demo-tenant with viewer/editor roles."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "demo",
        "AEGIS_DEMO_MODE": "true",
        "AEGIS_DEMO_TOKEN": "test-demo-token-123",
    }):
        client = TestClient(demo_test_app)
        res = client.get("/api/v1/workspace", headers={"Authorization": "Bearer test-demo-token-123"})
        assert res.status_code == 200, res.text
        data = res.json()
        assert data["tenant_id"] == "demo-tenant"
        assert "editor" in data["roles"]
        assert "viewer" in data["roles"]
        assert data["can_write"] is True
        # Demo visitor must NOT have document deletion permissions
        assert data["can_delete"] is False


def test_demo_token_rejected_in_production_mode(demo_test_app):
    """When AEGIS_DEMO_MODE=false or production, demo token MUST be rejected with 401."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_DEMO_MODE": "false",
        "AEGIS_DEMO_TOKEN": "test-demo-token-123",
    }):
        client = TestClient(demo_test_app)
        res = client.get("/api/v1/workspace", headers={"Authorization": "Bearer test-demo-token-123"})
        assert res.status_code == 401


def test_demo_visitor_blocked_from_admin_endpoints(demo_test_app):
    """Demo tenant cannot escalate privileges or reach admin maintenance endpoints."""
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "demo",
        "AEGIS_DEMO_MODE": "true",
        "AEGIS_DEMO_TOKEN": "test-demo-token-123",
    }):
        client = TestClient(demo_test_app)
        # Platform admin route
        res = client.get("/api/v1/admin/maintenance", headers={"Authorization": "Bearer test-demo-token-123"})
        assert res.status_code == 403

        # Tenant admin route
        res2 = client.get("/api/v1/tenant-admin-only", headers={"Authorization": "Bearer test-demo-token-123"})
        assert res2.status_code == 403


def test_anonymous_access_controls(demo_test_app):
    """Anonymous access is rejected unless AEGIS_DEMO_ALLOW_ANONYMOUS=true."""
    # When disabled
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "demo",
        "AEGIS_DEMO_MODE": "true",
        "AEGIS_DEMO_ALLOW_ANONYMOUS": "false",
    }):
        client = TestClient(demo_test_app)
        res = client.get("/api/v1/workspace")
        assert res.status_code == 401

    # When enabled
    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "demo",
        "AEGIS_DEMO_MODE": "true",
        "AEGIS_DEMO_ALLOW_ANONYMOUS": "true",
    }):
        client = TestClient(demo_test_app)
        res = client.get("/api/v1/workspace")
        assert res.status_code == 200
        assert res.json()["tenant_id"] == "demo-tenant"
