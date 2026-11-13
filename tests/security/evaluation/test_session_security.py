"""
AEGIS Evaluation Security Tests — Session Lifecycle & Token Security (PROT-04 WP-04.01, WP-04.02, WP-04.07)
Tests:
- AUTH-001: Missing token returns 401
- AUTH-002: Malformed token returns 400/401
- AUTH-003: Forged token returns 401
- AUTH-004: Expired token returns 401/403
- AUTH-008: Development token 'dev-*' rejected in production
- SESSION-001: Refresh-token replay detection and family revocation
- SESSION-002: Logout then reuse session token rejected
- SESSION-003: License revocation terminates active session immediately
"""

import os
import pytest
from fastapi.testclient import TestClient

from services.evaluation_gateway.revocation import registry as revocation_registry


def test_auth_001_no_session_token(client: TestClient):
    """AUTH-001: Requests to protected evaluation endpoints without token return 401."""
    res = client.get("/v1/evaluation/license")
    assert res.status_code == 401
    assert res.json()["error"] == "MISSING_EVALUATION_TOKEN"


def test_auth_002_malformed_token(client: TestClient):
    """AUTH-002: Malformed or unparseable token returns 400 Bad Request."""
    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": "not-base64-json!!!"})
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_LICENSE"


def test_auth_003_forged_token_signature(client: TestClient):
    """AUTH-003: Forged token signature returns 401 Unauthorized."""
    import base64, json
    bogus_doc = {
        "payload": {"license_id": "fake", "user_id": "hacker", "expires_at": "2099-01-01T00:00:00Z"},
        "signature": base64.b64encode(b"invalid_signature_bytes_32_bytes!").decode("ascii"),
    }
    bogus_token = base64.urlsafe_b64encode(json.dumps(bogus_doc).encode()).decode()
    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": bogus_token})
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_SIGNATURE"


def test_auth_004_expired_jwt():
    """AUTH-004: Backend RS256 token verification rejects expired tokens."""
    import time
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from src.api.auth import _validate_jwt
    from fastapi import HTTPException
    from unittest.mock import patch

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    now = int(time.time())
    expired_token = jwt.encode(
        {"tenant_id": "tenant-1", "sub": "user-1", "exp": now - 300},
        priv_pem,
        algorithm="RS256",
    )

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub_pem,
    }):
        with pytest.raises(HTTPException) as exc:
            _validate_jwt(expired_token)
        assert exc.value.status_code == 401
        assert "expired" in str(exc.value.detail).lower()


def test_auth_005_incorrect_issuer():
    """AUTH-005: Backend RS256 token verification rejects incorrect issuer."""
    import time
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from src.api.auth import _validate_jwt
    from fastapi import HTTPException
    from unittest.mock import patch

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    now = int(time.time())
    token = jwt.encode(
        {"tenant_id": "tenant-1", "sub": "user-1", "iss": "https://untrusted-issuer.com", "exp": now + 3600},
        priv_pem,
        algorithm="RS256",
    )

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub_pem,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
    }):
        with pytest.raises(HTTPException) as exc:
            _validate_jwt(token)
        assert exc.value.status_code == 401


def test_auth_006_incorrect_audience():
    """AUTH-006: Backend RS256 token verification rejects incorrect audience."""
    import time
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from src.api.auth import _validate_jwt
    from fastapi import HTTPException
    from unittest.mock import patch

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode("utf-8")

    now = int(time.time())
    token = jwt.encode(
        {"tenant_id": "tenant-1", "sub": "user-1", "aud": "wrong-audience", "exp": now + 3600},
        priv_pem,
        algorithm="RS256",
    )

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub_pem,
        "AEGIS_JWT_AUDIENCE": "aegis-docintel-api",
    }):
        with pytest.raises(HTTPException) as exc:
            _validate_jwt(token)
        assert exc.value.status_code == 401


def test_auth_007_unsupported_signing_algorithm():
    """AUTH-007: Backend RS256 token verification strictly rejects algorithm confusion (e.g. HS256)."""
    import time
    import jwt
    from cryptography.hazmat.primitives.asymmetric import rsa
    from cryptography.hazmat.primitives import serialization
    from src.api.auth import _validate_jwt
    from fastapi import HTTPException
    from unittest.mock import patch

    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub_pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")

    now = int(time.time())
    forged_hs256_token = jwt.encode(
        {"tenant_id": "tenant-1", "sub": "user-1", "exp": now + 3600},
        "attacker-secret-key-that-is-long-enough-32bytes",
        algorithm="HS256",
    )

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub_pem,
    }):
        with pytest.raises(HTTPException) as exc:
            _validate_jwt(forged_hs256_token)
        assert exc.value.status_code == 401


def test_auth_008_development_token_in_production_rejected():
    """AUTH-008: Backend authentication fails closed on 'dev-*' tokens in production mode."""
    from src.api.auth import _validate_jwt
    from fastapi import HTTPException

    # Simulate production environment on backend
    old_env = os.environ.get("AEGIS_ENVIRONMENT")
    try:
        os.environ["AEGIS_ENVIRONMENT"] = "production"
        with pytest.raises(HTTPException) as exc_info:
            _validate_jwt("dev-attacker-tenant")
        # In production, dev token must NOT grant admin access; it must fail closed
        assert exc_info.value.status_code == 401
    finally:
        if old_env is not None:
            os.environ["AEGIS_ENVIRONMENT"] = old_env


def test_session_001_refresh_token_replay_rejected(client: TestClient):
    """SESSION-001: Attempting to replay an already consumed refresh token triggers compromise revocation."""
    # 1. Activate
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "rt_replay_dev_key"},
    )
    assert res.status_code == 200
    rt1 = res.json()["session"]["refresh_token"]

    # 2. First refresh (legitimate rotation)
    res_ref1 = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert res_ref1.status_code == 200
    rt2 = res_ref1.json()["refresh_token"]
    at2 = res_ref1.json()["access_token"]

    # 3. Attacker replays consumed rt1
    res_replay = client.post("/v1/evaluation/session/refresh", json={"refresh_token": rt1})
    assert res_replay.status_code == 401
    assert "replay detected" in res_replay.json()["message"].lower()

    # 4. Verify that compromise revocation invalidated at2 as well
    res_check = client.get("/v1/evaluation/session", headers={"Authorization": f"Bearer {at2}"})
    assert res_check.status_code == 401


def test_session_002_logout_then_reuse_session_rejected(client: TestClient):
    """SESSION-002: Calling logout immediately invalidates the access token."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-BETA-TEST", "device_public_key": "logout_dev_key"},
    )
    token = res.json()["session"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Verify active
    res1 = client.get("/v1/evaluation/session", headers=headers)
    assert res1.status_code == 200

    # Logout
    res_logout = client.post("/v1/evaluation/session/logout", headers=headers)
    assert res_logout.status_code == 200

    # Reusing logged-out session fails
    res2 = client.get("/v1/evaluation/session", headers=headers)
    assert res2.status_code == 401


def test_session_003_license_revoked_session_terminated(client: TestClient):
    """SESSION-003: An active session is immediately denied if the underlying license is revoked."""
    res = client.post(
        "/v1/evaluation/activate",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": "rev_sess_key"},
    )
    token = res.json()["session"]["access_token"]
    lic_id = res.json()["license"]["license_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Session is working
    res1 = client.get("/v1/evaluation/session", headers=headers)
    assert res1.status_code == 200

    # Admin revokes license
    revocation_registry.revoke(lic_id)

    # Subsequent protected action is rejected with 403
    res2 = client.get("/v1/evaluation/session", headers=headers)
    assert res2.status_code == 403
    assert res2.json()["error"] == "LICENSE_REVOKED"
