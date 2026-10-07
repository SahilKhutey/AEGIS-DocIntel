import pytest
from fastapi import HTTPException
from unittest.mock import MagicMock

from src.api.auth import (
    TenantContext,
    get_current_tenant,
    get_current_tenant_ws,
    require_role,
    _validate_jwt,
    _validate_api_key,
)


@pytest.mark.asyncio
async def test_get_current_tenant_bearer():
    credentials = MagicMock()
    credentials.credentials = "dev-tenant-123"
    ctx = await get_current_tenant(bearer=credentials, api_key=None)
    assert ctx.tenant_id == "tenant-123"
    assert ctx.role == "admin"


@pytest.mark.asyncio
async def test_get_current_tenant_api_key():
    ctx = await get_current_tenant(bearer=None, api_key="aegis-dev-key")
    assert ctx.tenant_id == "default-tenant"
    assert ctx.role == "editor"


@pytest.mark.asyncio
async def test_get_current_tenant_missing_auth():
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant(bearer=None, api_key=None)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_get_current_tenant_ws_bearer():
    websocket = MagicMock()
    websocket.headers = {"authorization": "Bearer dev-ws-tenant"}
    ctx = await get_current_tenant_ws(websocket)
    assert ctx.tenant_id == "ws-tenant"
    assert ctx.user_id == "dev-user"
    assert ctx.role == "admin"


@pytest.mark.asyncio
async def test_get_current_tenant_ws_api_key():
    websocket = MagicMock()
    websocket.headers = {"x-api-key": "aegis-dev-key"}
    ctx = await get_current_tenant_ws(websocket)
    assert ctx.tenant_id == "default-tenant"
    assert ctx.user_id == "api-user"
    assert ctx.role == "editor"


@pytest.mark.asyncio
async def test_get_current_tenant_ws_missing_auth():
    websocket = MagicMock()
    websocket.headers = {}
    with pytest.raises(HTTPException) as exc_info:
        await get_current_tenant_ws(websocket)
    assert exc_info.value.status_code == 401


@pytest.mark.asyncio
async def test_require_role():
    check_admin = require_role("admin", "owner")
    tenant = TenantContext(tenant_id="t1", user_id="u1", role="admin")
    result = await check_admin(tenant=tenant)
    assert result == tenant

    tenant_viewer = TenantContext(tenant_id="t1", user_id="u1", role="viewer")
    with pytest.raises(HTTPException) as exc_info:
        await check_admin(tenant=tenant_viewer)
    assert exc_info.value.status_code == 403


def test_auth_bypass_rejected_in_production(monkeypatch):
    """CRITICAL SECURITY: In production mode, dev auth bypass tokens MUST be rejected."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "production")

    with pytest.raises(HTTPException) as jwt_exc:
        _validate_jwt("dev-tenant-123")
    assert jwt_exc.value.status_code == 401
    assert "JWT validation not configured" in jwt_exc.value.detail

    with pytest.raises(HTTPException) as key_exc:
        _validate_api_key("aegis-dev-key")
    assert key_exc.value.status_code == 401
    assert "Invalid API key" in key_exc.value.detail


def test_auth_bypass_rejected_when_environment_unset(monkeypatch):
    """CRITICAL SECURITY: When AEGIS_ENVIRONMENT is unset, fail-safe default is production."""
    monkeypatch.delenv("AEGIS_ENVIRONMENT", raising=False)

    with pytest.raises(HTTPException) as jwt_exc:
        _validate_jwt("dev-tenant-123")
    assert jwt_exc.value.status_code == 401

    with pytest.raises(HTTPException) as key_exc:
        _validate_api_key("aegis-dev-key")
    assert key_exc.value.status_code == 401


def test_auth_bypass_allowed_in_development(monkeypatch):
    """In explicit development mode, dev auth bypass tokens are accepted."""
    monkeypatch.setenv("AEGIS_ENVIRONMENT", "development")

    jwt_ctx = _validate_jwt("dev-tenant-xyz")
    assert jwt_ctx.tenant_id == "tenant-xyz"
    assert jwt_ctx.role == "admin"

    key_ctx = _validate_api_key("aegis-dev-key")
    assert key_ctx.tenant_id == "default-tenant"
    assert key_ctx.role == "editor"

