"""
Consolidated Security Audit: Device Binding & Challenge Replay Defense (SEC-009, SEC-010)
"""

import base64
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import activation_service


def test_device_001_valid_challenge_response_activates(client: TestClient, keypair):
    """SEC-009.1: Valid Ed25519 PoP signature over canonical challenge activates cleanly."""
    priv, _, pem, _ = keypair
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-dev-001"},
    )
    assert ch_res.status_code == 200
    cid = ch_res.json()["challenge_id"]
    can_msg = ch_res.json()["canonical_message"]

    sig_bytes = priv.sign(can_msg.encode("utf-8"))
    sig_b64 = base64.b64encode(sig_bytes).decode("ascii")

    act_res = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": sig_b64, "installation_id": "inst-dev-001"},
    )
    assert act_res.status_code == 200
    assert act_res.json()["status"] in ("active", "activated")


def test_device_002_replayed_challenge_response_rejected(client: TestClient, keypair):
    """SEC-009.2: Replaying an already-consumed challenge response returns HTTP 400."""
    priv, _, pem, _ = keypair
    ch_res = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-dev-002"},
    )
    cid = ch_res.json()["challenge_id"]
    can_msg = ch_res.json()["canonical_message"]
    sig_b64 = base64.b64encode(priv.sign(can_msg.encode("utf-8"))).decode("ascii")

    act_res1 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": sig_b64, "installation_id": "inst-dev-002"},
    )
    assert act_res1.status_code == 200

    # Replay identical response
    act_res2 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": cid, "signature": sig_b64, "installation_id": "inst-dev-002"},
    )
    assert act_res2.status_code == 400


def test_device_003_device_limit_enforced_atomically(client: TestClient):
    """SEC-010.1: Registering a second device exceeding license max_devices returns HTTP 409."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_alpha"},
    )
    assert res1.status_code == 200

    # Attempt second device activation on same license
    res2 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_beta"},
    )
    assert res2.status_code == 409
    assert res2.json()["error"] == "DEVICE_LIMIT_EXCEEDED"


def test_device_004_recovery_code_unbinds_and_frees_device_slot(client: TestClient):
    """SEC-010.2: Emergency recovery code successfully frees device slot allowing migration."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_old"},
    )
    lic_id = res1.json()["license"]["license_id"]
    dev_id = res1.json()["device_id"]
    rec_code = res1.json()["recovery_code"]

    # Recover / unbind device
    rec_res = client.post(
        "/v1/evaluation/device/recover",
        json={"license_id": lic_id, "device_id": dev_id, "recovery_code": rec_code},
    )
    assert rec_res.status_code == 200

    # New device can now activate successfully
    res2 = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "dev_key_new"},
    )
    assert res2.status_code == 200
