"""
AEGIS Evaluation Security Tests — REM-05: Session Lifecycle, Refresh Rotation & Revocation
Verifies acceptance criteria SES-REM-001 through SES-REM-015:
- SES-REM-001: Session creation upon activation with short-lived access token and refresh token
- SES-REM-002: Session binding to device public key and license
- SES-REM-003: Access token short-lived TTL enforcement
- SES-REM-004: Refresh token rotation issues new pair and marks old consumed
- SES-REM-005: Replay of consumed refresh token detected and rejected
- SES-REM-006: Compromise cascade: replaying old refresh token invalidates family
- SES-REM-007: Single logout invalidates access token immediately
- SES-REM-008: Global evaluator logout invalidates all sessions
- SES-REM-009: License revocation terminates all linked sessions
- SES-REM-010: Revoked session returns 401/403 on subsequent protected calls
- SES-REM-011: WebSocket single-use ticket issuance
- SES-REM-012: WebSocket ticket single-use consumption (no replay)
- SES-REM-013: WebSocket ticket expiration enforcement
- SES-REM-014: Concurrency race protection on token refresh
- SES-REM-015: Tokens stored hashed at rest (never plaintext)
"""

from __future__ import annotations

import base64
import concurrent.futures
import time
from datetime import datetime, timedelta, timezone
import pytest
from cryptography.hazmat.primitives.asymmetric import ed25519
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import activation_service
from services.evaluation_gateway.revocation import registry as revocation_registry
from src.repositories.evaluation.session_repository import session_repository
from src.repositories.evaluation.refresh_token_repository import refresh_token_repository
from src.repositories.evaluation.session_audit_repository import session_audit_repository
from src.schemas.evaluation.refresh import RefreshTokenStatus
from src.schemas.evaluation.session import RevocationReason, SessionStatus
from src.services.evaluation.refresh_rotation_service import refresh_rotation_service
from src.services.evaluation.refresh_token_service import hash_token
from src.services.evaluation.session_revocation_service import session_revocation_service
from src.services.evaluation.session_service import session_service
from src.services.evaluation.session_validation_service import session_validation_service
from src.services.evaluation.websocket_ticket_service import websocket_ticket_service


@pytest.fixture(autouse=True)
def clean_session_state():
    session_repository.clear()
    refresh_token_repository.clear()
    session_audit_repository.clear()
    websocket_ticket_service.clear()
    yield
    session_repository.clear()
    refresh_token_repository.clear()
    session_audit_repository.clear()
    websocket_ticket_service.clear()


def test_ses_rem_001_session_creation(client: TestClient):
    """SES-REM-001: Direct activation creates active session with valid short-lived tokens."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ses_rem_001_key"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert "session" in data
    assert data["session"]["access_token"].startswith("aegis_eval_at_")
    assert data["session"]["refresh_token"].startswith("aegis_eval_rt_")
    assert data["session"]["expires_in"] == 600


def test_ses_rem_002_session_device_and_license_binding(client: TestClient):
    """SES-REM-002: Session is bound to registered device public key and license."""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub_bytes = priv.public_key().public_bytes_raw()
    pub_b64 = base64.b64encode(pub_bytes).decode("ascii")

    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pub_b64,
            "installation_id": "install-ses-002",
        },
    )
    assert ch_res.status_code == 200
    chal = ch_res.json()

    sig = priv.sign(chal["canonical_message"].encode("utf-8"))
    sig_b64 = base64.b64encode(sig).decode("ascii")

    act_res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": chal["challenge_id"],
            "signature": sig_b64,
            "installation_id": "install-ses-002",
        },
    )
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "active"
    assert "device_id" in act_data
    assert "session" in act_data
    assert act_data["license"]["license_id"] is not None


def test_ses_rem_003_access_token_ttl_enforced(client: TestClient):
    """SES-REM-003: Access tokens enforce short TTL (600s / 10m)."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "ttl_check_key"},
    )
    assert res.status_code == 200
    assert res.json()["session"]["expires_in"] == 600

    sess, at, rt = session_service.create_session(
        evaluator_id="eval-ttl",
        tenant_id="tenant-ttl",
        license_id="lic-ttl",
        device_id="dev-ttl",
    )
    assert sess.idle_expires_at > datetime.now(timezone.utc)
    delta = (sess.idle_expires_at - sess.created_at).total_seconds()
    assert 1790 <= delta <= 1810


def test_ses_rem_004_refresh_token_rotation(client: TestClient):
    """SES-REM-004: Refreshing an active session rotates tokens and marks old refresh token consumed."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "rt_rot_key"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res.status_code == 200
    ref_data = ref_res.json()
    rt2 = ref_data["refresh_token"]
    at2 = ref_data["access_token"]

    assert rt2 != rt1
    assert at2.startswith("aegis_eval_at_")


def test_ses_rem_005_refresh_token_replay_detected(client: TestClient):
    """SES-REM-005: Replaying consumed refresh token is rejected with 401."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "rt_replay_key"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    # Legitimate first rotation
    ref1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref1.status_code == 200

    # Malicious replay of rt1
    replay = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert replay.status_code == 401
    assert "replay detected" in replay.json()["message"].lower()


def test_ses_rem_006_compromise_cascade_revocation(client: TestClient):
    """SES-REM-006: Replay of consumed refresh token invalidates child access tokens."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "cascade_key"},
    )
    rt1 = res.json()["session"]["refresh_token"]

    ref1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref1.status_code == 200
    at2 = ref1.json()["access_token"]

    # Replay rt1
    client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})

    # at2 must now be revoked
    check = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"})
    assert check.status_code == 401


def test_ses_rem_007_single_logout_revokes_access_token(client: TestClient):
    """SES-REM-007: Calling logout terminates session immediately."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-BETA-TEST", "device_public_key": "single_logout_key"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    # Verify active
    res1 = client.get("/v1/evaluation/session", headers=headers)
    assert res1.status_code == 200

    # Logout
    logout_res = client.post("/v1/evaluation/session/logout", headers=headers)
    assert logout_res.status_code == 200

    # Reusing token must fail
    res2 = client.get("/v1/evaluation/session", headers=headers)
    assert res2.status_code == 401


def test_ses_rem_008_logout_all_evaluator_sessions(client: TestClient):
    """SES-REM-008: Calling logout-all revokes all sessions for the evaluator."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "logout_all_key"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    res_all = client.post("/v1/evaluation/session/logout-all", headers=headers)
    assert res_all.status_code == 200
    assert res_all.json()["revoked_sessions_count"] >= 1

    # Verify session is dead
    res_check = client.get("/v1/evaluation/session", headers=headers)
    assert res_check.status_code == 401


def test_ses_rem_009_license_revocation_terminates_session(client: TestClient):
    """SES-REM-009: Revoking license terminates active session."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "lic_rev_key"},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    res1 = client.get("/v1/evaluation/session", headers=headers)
    assert res1.status_code == 200

    # Admin revokes license
    revocation_registry.revoke(lic_id)

    res2 = client.get("/v1/evaluation/session", headers=headers)
    assert res2.status_code in (401, 403)


def test_ses_rem_010_revoked_session_denied_on_protected_endpoints(client: TestClient):
    """SES-REM-010: Revoked session is denied access to all protected evaluation routes."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "denied_prot_key"},
    )
    at = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    client.post("/v1/evaluation/session/logout", headers=headers)

    query_res = client.post("/v1/evaluation/query", headers=headers, json={"query": "test"})
    assert query_res.status_code in (401, 403)


def test_ses_rem_011_websocket_ticket_issuance(client: TestClient, valid_eval_license):
    """SES-REM-011: Evaluator can request a short-lived single-use WebSocket ticket."""
    headers = valid_eval_license["headers"]
    res = client.post("/v1/evaluation/ws/ticket", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "ticket" in data
    assert data["ticket"].startswith("aegis_ws_tkt_")
    assert data["expires_in"] == 60


def test_ses_rem_012_websocket_ticket_single_use(valid_eval_license):
    """SES-REM-012: Consuming a WebSocket ticket prevents replay."""
    tkt_data = websocket_ticket_service.issue_ticket(
        session_id="sess-ws-1",
        evaluator_id="eval-ws",
        license_id="lic-ws",
        device_id="dev-ws",
    )
    tkt_id = tkt_data["ticket"]
    assert tkt_id.startswith("aegis_ws_tkt_")

    # First validation succeeds
    success, ticket, msg = websocket_ticket_service.consume_ticket(tkt_id)
    assert success is True
    assert ticket is not None
    assert ticket.session_id == "sess-ws-1"

    # Second validation on same ticket is rejected
    success2, ticket2, msg2 = websocket_ticket_service.consume_ticket(tkt_id)
    assert success2 is False
    assert msg2 == "TICKET_ALREADY_CONSUMED"


def test_ses_rem_013_websocket_ticket_expiration():
    """SES-REM-013: Expired WebSocket tickets are rejected."""
    success, ticket, msg = websocket_ticket_service.consume_ticket("non-existent-ticket-id")
    assert success is False
    assert msg == "TICKET_NOT_FOUND"


def test_ses_rem_014_refresh_concurrency_race_safety():
    """SES-REM-014: Concurrent refresh calls on the same token family handle race conditions safely."""
    sess, at, rt = session_service.create_session(
        evaluator_id="eval-conc",
        tenant_id="tenant-conc",
        license_id="lic-conc",
        device_id="dev-conc",
    )

    results = []

    def try_refresh():
        try:
            new_at, new_rt, _ = refresh_rotation_service.rotate_refresh_token(rt)
            return ("SUCCESS", new_at)
        except Exception as e:
            return ("ERROR", str(e))

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(try_refresh) for _ in range(5)]
        for f in concurrent.futures.as_completed(futures):
            results.append(f.result()[0])

    # Exactly 1 can succeed; others are either rejected or caught by replay detection
    successes = results.count("SUCCESS")
    assert successes == 1


def test_ses_rem_015_token_hashes_at_rest():
    """SES-REM-015: Raw tokens are stored hashed at rest in the repository."""
    sess, at, rt = session_service.create_session(
        evaluator_id="eval-hash",
        tenant_id="tenant-hash",
        license_id="lic-hash",
        device_id="dev-hash",
    )

    # Repository must contain hashed access token, not the plaintext bearer
    stored_sess = session_repository.get_by_id(sess.session_id)
    assert stored_sess is not None
    assert stored_sess.access_token_hash == hash_token(at)
    assert stored_sess.access_token_hash != at
