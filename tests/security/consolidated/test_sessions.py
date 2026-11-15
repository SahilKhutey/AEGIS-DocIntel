"""
Consolidated Security Audit: Session Lifecycle, Rotation & Revocation (SEC-013, SEC-014)
"""

import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.revocation import registry as revocation_registry


def test_session_001_refresh_token_rotation_succeeds(client: TestClient, keypair):
    """SEC-013.1: Presenting active refresh token rotates credentials successfully."""
    priv, _, pem, _ = keypair
    act_res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    rt1 = act_res.json()["session"]["refresh_token"]

    ref_res = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res.status_code == 200
    rt2 = ref_res.json()["refresh_token"]
    assert rt2 != rt1


def test_session_002_refresh_token_replay_revokes_token_family(client: TestClient, keypair):
    """SEC-013.2: Replaying an already-consumed refresh token revokes entire token family."""
    priv, _, pem, _ = keypair
    act_res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    rt1 = act_res.json()["session"]["refresh_token"]

    # Legitimate first refresh
    ref_res1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res1.status_code == 200
    rt2 = ref_res1.json()["refresh_token"]

    # Attacker replays rt1
    ref_res2 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert ref_res2.status_code in (400, 401)

    # Family is now revoked: subsequent attempts with rt2 are denied
    ref_res3 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt2})
    assert ref_res3.status_code in (400, 401)


def test_session_003_logout_revokes_session(client: TestClient, keypair):
    """SEC-014.1: Explicit logout invalidates access token immediately."""
    priv, _, pem, _ = keypair
    act_res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = act_res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {at}"}

    # Verify active
    assert client.get("/v1/evaluation/session", headers=headers).status_code == 200

    # Logout
    logout_res = client.post("/v1/evaluation/session/logout", headers=headers)
    assert logout_res.status_code == 200

    # Subsequent request is denied
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)


def test_session_004_logout_all_terminates_all_evaluator_sessions(client: TestClient):
    """SEC-014.2: Logout-all revokes all sessions belonging to evaluator."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "sess_key_1"},
    )
    at1 = res1.json()["session"]["access_token"]
    headers1 = {"Authorization": f"Bearer {at1}"}

    # Logout all
    client.post("/v1/evaluation/session/logout-all", headers=headers1)

    # Access token is invalid
    assert client.get("/v1/evaluation/session", headers=headers1).status_code in (401, 403)


def test_session_005_license_revocation_cascades_to_session(client: TestClient, keypair):
    """SEC-014.3: Revoking the underlying license immediately terminates session access."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    at = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {at}"}

    revocation_registry.revoke(lic_id, "Immediate breach lockdown")
    assert client.get("/v1/evaluation/session", headers=headers).status_code in (401, 403)
