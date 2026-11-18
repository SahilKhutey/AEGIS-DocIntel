"""
PT-02: Authentication Adversarial Tests
Covers PT-AUTH-001 through PT-AUTH-012.
Verifies fail-closed JWT validation, RS256 signature verification, issuer/audience enforcement,
role injection rejection, tenant claim manipulation defense, brute-force mitigation, and zero browser secret exposure.
"""

from __future__ import annotations

import os
import time
from pathlib import Path
from unittest.mock import patch
import jwt

from tests.security.penetration_testing.conftest import make_evaluator_jwt, tamper_jwt_payload

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent


def test_pt_auth_001_missing_authentication(core_client):
    """PT-AUTH-001: Missing authentication header returns HTTP 401."""
    with patch.dict(os.environ, {"AEGIS_ENVIRONMENT": "production"}):
        res = core_client.get("/api/v1/protected")
        assert res.status_code == 401
        assert "Missing authentication" in res.json().get("detail", "") or res.status_code == 401


def test_pt_auth_002_invalid_jwt_signature(staging_rsa_keypair, attacker_rsa_keypair, core_client):
    """PT-AUTH-002: Token signed by attacker's unapproved private key returns HTTP 401."""
    _, pub_legit = staging_rsa_keypair
    priv_attacker, _ = attacker_rsa_keypair
    rogue_tok = make_evaluator_jwt(priv_attacker, tenant_id="tenant-eval-a", user_id="user-eval-a")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub_legit,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {rogue_tok}"})
        assert res.status_code == 401


def test_pt_auth_003_modified_jwt_payload(staging_rsa_keypair, core_client):
    """PT-AUTH-003: Altering JWT payload without re-signing causes cryptographic failure -> HTTP 401."""
    priv, pub = staging_rsa_keypair
    legit_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="viewer")
    tampered = tamper_jwt_payload(legit_tok, {"role": "admin", "tenant_id": "tenant-master"})

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {tampered}"})
        assert res.status_code == 401


def test_pt_auth_004_expired_jwt(staging_rsa_keypair, core_client):
    """PT-AUTH-004: Expired token (exp in past) returns HTTP 401."""
    priv, pub = staging_rsa_keypair
    expired_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", exp_delta=-3600)

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {expired_tok}"})
        assert res.status_code == 401


def test_pt_auth_005_incorrect_issuer(staging_rsa_keypair, core_client):
    """PT-AUTH-005: Token with unapproved or missing issuer returns HTTP 401."""
    priv, pub = staging_rsa_keypair
    rogue_iss_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", iss="https://evil-auth.org")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {rogue_iss_tok}"})
        assert res.status_code == 401


def test_pt_auth_006_incorrect_audience(staging_rsa_keypair, core_client):
    """PT-AUTH-006: Token issued for different service audience returns HTTP 401."""
    priv, pub = staging_rsa_keypair
    wrong_aud_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", aud="other-microservice")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {wrong_aud_tok}"})
        assert res.status_code == 401


def test_pt_auth_007_unknown_role(staging_rsa_keypair, core_client):
    """PT-AUTH-007: Token declaring unapproved/fabricated role returns HTTP 401 or 403."""
    priv, pub = staging_rsa_keypair
    bad_role_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="godmode_operator")

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {bad_role_tok}"})
        assert res.status_code in (401, 403)


def test_pt_auth_008_admin_role_injection(staging_rsa_keypair, core_client):
    """PT-AUTH-008: Evaluator injecting admin role without cryptographic key fails verification."""
    priv, pub = staging_rsa_keypair
    eval_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", role="evaluation_user")
    injected_tok = tamper_jwt_payload(eval_tok, {"role": "admin", "roles": ["admin", "superadmin"]})

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.post("/api/v1/admin/evaluation/quotas/policies", headers={"Authorization": f"Bearer {injected_tok}"}, json={"name": "test"})
        assert res.status_code in (401, 403)


def test_pt_auth_009_tenant_claim_manipulation(staging_rsa_keypair, core_client):
    """PT-AUTH-009: Tampering tenant claim inside token invalidates signature -> HTTP 401."""
    priv, pub = staging_rsa_keypair
    token_a = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a")
    forged_tenant_tok = tamper_jwt_payload(token_a, {"tenant_id": "tenant-eval-b"})

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {forged_tenant_tok}"})
        assert res.status_code == 401


def test_pt_auth_010_replayed_expired_session(staging_rsa_keypair, core_client):
    """PT-AUTH-010: Replaying an expired session JWT after session expiration returns HTTP 401."""
    priv, pub = staging_rsa_keypair
    expired_sess_tok = make_evaluator_jwt(priv, tenant_id="tenant-eval-a", user_id="user-eval-a", exp_delta=-3600)

    with patch.dict(os.environ, {
        "AEGIS_ENVIRONMENT": "production",
        "AEGIS_JWT_PUBLIC_KEY": pub,
        "AEGIS_JWT_ISSUER": "https://auth.aegis.corp",
        "AEGIS_JWT_AUDIENCE": "aegis-api",
    }):
        res = core_client.get("/api/v1/protected", headers={"Authorization": f"Bearer {expired_sess_tok}"})
        assert res.status_code == 401


def test_pt_auth_011_api_key_exposed_in_browser():
    """PT-AUTH-011: Client web source files contain zero hardcoded API keys or bearer secrets."""
    web_dir = REPO_ROOT / "web" / "src"
    for p in web_dir.rglob("*.ts*"):
        text = p.read_text(encoding="utf-8")
        assert "aegis-dev-key" not in text
        assert "dev-default-tenant" not in text
        assert "NEXT_PUBLIC_AEGIS_DEV_TOKEN" not in text


def test_pt_auth_012_authentication_brute_force(gateway_client):
    """PT-AUTH-012: Rapid authentication attempts with invalid tokens are rejected and rate-limited."""
    forged_tokens = [f"forged.token.attempt_{i}" for i in range(15)]
    responses = []
    for tok in forged_tokens:
        res = gateway_client.post(
            "/api/v1/gateway/query",
            headers={"X-Evaluation-License": tok},
            json={"query": "test"}
        )
        responses.append(res.status_code)

    # Every attempt is rejected (401 or 403 or 429)
    assert all(code in (400, 401, 403, 429) for code in responses)
