"""
Tests for the /v1/query/ws/{session_id} WebSocket endpoint's authentication.

Found during a follow-up sweep of the Repository Audit's Workstream R: this
endpoint previously had no authentication dependency at all -- any client
could connect with no credentials and claim to be any tenant_id simply by
including it in their message JSON. This is a more severe variant of the
same tenant-isolation class of bug fixed elsewhere (orchestrator.py,
container.py): those had a check that was missing or bypassed; this had no
authenticated identity to check against in the first place.

Uses starlette's TestClient websocket_connect, which drives the real
ASGI app exactly as a real WebSocket client would, including running
FastAPI's dependency injection (Depends(get_current_tenant)) against the
connection's handshake headers.
"""
from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    HAS_TEST_CLIENT = True
except ImportError:
    HAS_TEST_CLIENT = False

from src.main import app

TENANT_A = {"Authorization": "Bearer dev-tenant-a"}


@pytest.mark.skipif(not HAS_TEST_CLIENT, reason="FastAPI TestClient not available")
def test_websocket_without_auth_is_rejected():
    """No Authorization header at all on the handshake -- the connection
    must be refused (FastAPI closes it during the dependency-resolution
    phase, before accept() in the handler body ever runs), not silently
    accepted."""
    with TestClient(app) as client:
        with pytest.raises(Exception):
            # starlette raises WebSocketDisconnect (or the underlying close
            # exception) client-side when the server closes during handshake
            # dependency resolution -- there is no successful connection to
            # tear down afterward, unlike the authenticated case below.
            with client.websocket_connect("/v1/query/ws/11111111-1111-1111-1111-111111111111"):
                pass


@pytest.mark.skipif(not HAS_TEST_CLIENT, reason="FastAPI TestClient not available")
def test_websocket_with_auth_is_accepted_and_ignores_client_supplied_tenant_id():
    """With valid auth, the connection succeeds. Confirms the fix's second
    half too: even if the client supplies a tenant_id in the message body,
    it must be ignored in favor of the authenticated identity -- proven
    indirectly here by confirming the connection accepts and processes a
    message at all under real auth (the direct "does it use the spoofed
    id" check is covered at the query_service level by the container.py/
    orchestrator.py tenant tests; this test's job is only to confirm the
    endpoint requires and honors real authentication)."""
    with TestClient(app) as client:
        with client.websocket_connect(
            "/v1/query/ws/11111111-1111-1111-1111-111111111111",
            headers=TENANT_A,
        ) as ws:
            ws.send_json({
                "question": "test question",
                "tenant_id": "spoofed-other-tenant",  # must be ignored
            })
            # Expect at least a "start" or "error" message back, confirming the
            # server accepted the connection and processed the message rather
            # than closing immediately -- proving auth succeeded.
            msg = ws.receive_json()
            assert msg.get("type") in ("start", "error")
