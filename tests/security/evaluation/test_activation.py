"""
AEGIS Evaluation Security Tests — Activation & Device Binding (PROT-04 WP-04.03)
Tests:
- LIC-001: Valid evaluation license activation succeeds
- DEV-001: First device activation accepted
- DEV-002: Second device beyond limit rejected
- DEV-003: Deactivated device reuses old session rejected
- DEV-004: Device deactivation allows subsequent device registration
"""

import pytest
from fastapi.testclient import TestClient


def test_lic_001_valid_evaluation_license_activation(client: TestClient):
    """LIC-001: Activating with an eligible code returns valid license and session."""
    res = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA0dev1pubkey==",
            "device_label": "Primary Evaluator Laptop",
            "client_version": "1.1.0",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["license"]["product"] == "AEGIS_PROTECTED_EVALUATION"
    assert "access_token" in data["session"]
    assert "refresh_token" in data["session"]
    assert data["entitlements"]["documents.read"] is True
    assert data["entitlements"]["users.manage"] is False


def test_dev_001_first_device_activation(client: TestClient):
    """DEV-001: First device registration binds successfully."""
    res = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-BETA-TEST",
            "device_public_key": "device_key_primary_alpha",
            "device_label": "Workstation 1",
            "platform": "windows",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "active"
    assert data["session"]["device_id"] is not None


def test_dev_002_second_device_beyond_limit_rejected(client: TestClient):
    """DEV-002: Second device activation beyond max_devices (1) is rejected with 409 Conflict."""
    # First device activates
    res1 = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-PROD-HUNT",
            "device_public_key": "device_key_device_one",
            "device_label": "Desktop-01",
        },
    )
    assert res1.status_code == 200

    # Second distinct device tries to activate the same license code
    res2 = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-PROD-HUNT",
            "device_public_key": "device_key_device_two",
            "device_label": "Laptop-02",
        },
    )
    assert res2.status_code == 409
    data = res2.json()
    assert data["error"] == "DEVICE_LIMIT_EXCEEDED"


def test_dev_003_deactivated_device_reuses_old_session_rejected(client: TestClient):
    """DEV-003: If a device is deactivated, its existing session access tokens are terminated."""
    res1 = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "dev3_key_1",
            "device_label": "Workstation",
        },
    )
    assert res1.status_code == 200
    token = res1.json()["session"]["access_token"]
    device_id = res1.json()["session"]["device_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Session works
    res_query1 = client.post("/v1/evaluation/query", json={"query": "What is the peak TFLOPS?"}, headers=headers)
    assert res_query1.status_code == 200

    # Deactivate the device
    res_deact = client.post("/v1/evaluation/device/deactivate", json={"device_id": device_id}, headers=headers)
    assert res_deact.status_code == 200

    # Session reuse is now rejected with 401
    res_query2 = client.post("/v1/evaluation/query", json={"query": "What is the peak TFLOPS?"}, headers=headers)
    assert res_query2.status_code == 401


def test_dev_004_device_deactivation_frees_slot_for_reactivation(client: TestClient):
    """DEV-004: Deactivating a device allows a replacement device to register successfully."""
    # 1. Activate device 1
    res1 = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "old_machine_key",
            "device_label": "Old Machine",
        },
    )
    token = res1.json()["session"]["access_token"]
    device_id = res1.json()["session"]["device_id"]

    # 2. Deactivate device 1
    client.post(
        "/v1/evaluation/device/deactivate",
        json={"device_id": device_id},
        headers={"Authorization": f"Bearer {token}"},
    )

    # 3. Activate replacement device 2
    res2 = client.post(
        "/v1/evaluation/activate",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "new_machine_key",
            "device_label": "New Replacement Machine",
        },
    )
    assert res2.status_code == 200
    assert res2.json()["status"] == "active"
