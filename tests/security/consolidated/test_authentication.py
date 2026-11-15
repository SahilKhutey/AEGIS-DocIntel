"""
Consolidated Security Audit: Authentication & Ingress Hardening (SEC-005)
"""

import pytest
import time
import jwt
from fastapi.testclient import TestClient

from services.evaluation_gateway.activation import activation_service


def test_auth_001_missing_bearer_token_rejected(client: TestClient):
    """SEC-005.1: Missing authentication header returns HTTP 401."""
    res = client.get("/v1/evaluation/session")
    assert res.status_code == 401
    assert res.json()["error"] == "MISSING_EVALUATION_TOKEN"


def test_auth_002_malformed_token_rejected(client: TestClient):
    """SEC-005.2: Malformed JWT token structure returns HTTP 400 or 401."""
    res = client.get("/v1/evaluation/session", headers={"Authorization": "Bearer not-a-valid-jwt"})
    assert res.status_code in (400, 401)


def test_auth_003_dev_token_in_production_rejected(client: TestClient):
    """SEC-005.3: Presentation of dev-* mock tokens strictly rejected in production."""
    res = client.get("/v1/evaluation/session", headers={"Authorization": "Bearer dev-admin-token-1234"})
    assert res.status_code in (400, 401)


def test_auth_004_forged_jwt_signature_rejected(client: TestClient):
    """SEC-005.4: JWT signed with untrusted secret key is rejected."""
    forged_jwt = jwt.encode(
        {"sub": "evaluator-attacker", "exp": int(time.time()) + 3600, "role": "admin"},
        "attacker-untrusted-secret-key-12345",
        algorithm="HS256",
    )
    res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {forged_jwt}"})
    assert res.status_code in (400, 401)


def test_auth_005_expired_session_token_rejected(client: TestClient, keypair):
    """SEC-005.5: Expired evaluation session token returns HTTP 401."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    assert res.status_code == 200
    at = res.json()["session"]["access_token"]

    # Expire session in gateway memory
    import hashlib
    at_hash = hashlib.sha256(at.strip().encode("utf-8")).hexdigest()
    with activation_service._lock:
        if at_hash in activation_service._sessions_by_access_hash:
            activation_service._sessions_by_access_hash[at_hash].expires_at = time.time() - 100

    check_res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at}"})
    assert check_res.status_code == 401


def test_auth_006_valid_activation_authenticates_session(client: TestClient, keypair):
    """SEC-005.6: Valid activation produces a functioning authenticated session."""
    priv, _, pem, _ = keypair
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem},
    )
    assert res.status_code == 200
    at = res.json()["session"]["access_token"]
    assert at.startswith("aegis_eval_at_")

    sess_res = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at}"})
    assert sess_res.status_code == 200
    assert sess_res.json()["authenticated"] is True
    assert sess_res.json()["role"] == "evaluator"
