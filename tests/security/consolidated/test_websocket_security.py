"""
Consolidated Security Audit: WebSocket Authentication & Single-Use Tickets (SEC-015)
"""

import pytest
from fastapi.testclient import TestClient

from src.services.evaluation.websocket_ticket_service import websocket_ticket_service
from services.evaluation_gateway.revocation import registry as revocation_registry


def test_ws_001_ticket_issuance_requires_authenticated_session(client: TestClient, keypair):
    """SEC-015.1: Issuing WebSocket upgrade ticket requires valid authenticated evaluator session."""
    priv, _, pem, _ = keypair
    act_res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = act_res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    t_res = client.post("/v1/evaluation/ws/ticket", headers=headers)
    assert t_res.status_code == 200
    assert "ticket" in t_res.json()
    assert t_res.json()["ticket"].startswith("aegis_ws_tkt_")


def test_ws_002_ticket_is_single_use(client: TestClient):
    """SEC-015.2: Replaying an already-consumed WebSocket ticket is rejected."""
    tkt_data = websocket_ticket_service.issue_ticket(
        session_id="sess-ws-1",
        evaluator_id="eval-ws-user",
        license_id="lic-ws-1",
        device_id="dev-ws-1",
    )
    ticket_str = tkt_data["ticket"]

    # First consumption succeeds
    ok1, _, _ = websocket_ticket_service.consume_ticket(ticket_str)
    assert ok1 is True

    # Second consumption fails (anti-replay)
    ok2, _, reason2 = websocket_ticket_service.consume_ticket(ticket_str)
    assert ok2 is False
    assert "CONSUMED" in reason2 or "EXPIRED" in reason2


def test_ws_003_unauthenticated_ticket_request_denied(client: TestClient):
    """SEC-015.3: Anonymous ticket request returns HTTP 401."""
    res = client.post("/v1/evaluation/ws/ticket")
    assert res.status_code == 401


def test_ws_004_revocation_terminates_active_websocket_authorization():
    """SEC-015.4: License revocation terminates active WebSocket connection authorization."""
    from datetime import datetime, timezone, timedelta
    from src.schemas.evaluation.session import EvaluationSession
    from src.repositories.evaluation.session_repository import session_repository

    lic_id = "lic-ws-active-4"
    sess = EvaluationSession(
        session_id="sess-ws-4",
        evaluator_id="eval-ws-4",
        tenant_id="tenant-ws-4",
        license_id=lic_id,
        device_id="dev-ws-4",
        token_family_id="fam-ws-4",
        access_token_hash="fakehash-ws-4",
        idle_expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        absolute_expires_at=datetime.now(timezone.utc) + timedelta(days=1),
    )
    session_repository.save_session(sess)

    tkt_data = websocket_ticket_service.issue_ticket(
        session_id="sess-ws-4",
        evaluator_id="eval-ws-4",
        license_id=lic_id,
        device_id="dev-ws-4",
    )
    ok, tkt_obj, _ = websocket_ticket_service.consume_ticket(tkt_data["ticket"])
    assert ok is True

    # Register active connection
    conn_id = "conn-ws-4"
    websocket_ticket_service.register_connection(conn_id, "sess-ws-4")
    assert websocket_ticket_service.check_connection_authorized(conn_id) is True

    # Revoke license
    revocation_registry.revoke(lic_id, "Suspicious WebSocket flood")
    # Connection is now marked unauthorized or parent session revoked
    from src.services.evaluation.session_revocation_service import session_revocation_service
    session_revocation_service.revoke_license_sessions(lic_id)
    assert websocket_ticket_service.check_connection_authorized(conn_id) is False
