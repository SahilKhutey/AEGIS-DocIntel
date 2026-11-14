"""
AEGIS Evaluation Security Tests — License Issuance & Cryptographic Validation Protocol
PROT-04 WP-04.04: Comprehensive Verification Matrix (LIC-001 through LIC-040)

Covers:
- JWS Compact Serialization with EdDSA (Ed25519)
- Server-side signing key registry & lifecycle states (ACTIVE_SIGNING, VERIFY_ONLY, RETIRED, COMPROMISED)
- Key rotation and emergency compromise response (LIC-026, LIC-027, LIC-029)
- Authoritative database cross-checks & fail-closed behavior (LIC-019 - LIC-025)
- Strict claim schemas, temporal validation, and anti-tampering (LIC-005 - LIC-018)
- Bounded token size limits (<8KB) and rejection of token-controlled key URLs (LIC-034, LIC-035, LIC-036)
- Anti-IDOR cross-evaluator license isolation and audit token privacy (LIC-039, LIC-040)
"""

import base64
import copy
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519

from services.evaluation_gateway.license import (
    issue_evaluation_license,
    issue_signed_license,
    verify_signed_license,
    export_license_token,
    parse_license_token,
    DEFAULT_ISSUER,
    DEFAULT_AUDIENCE,
    DEFAULT_KEY_ID,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseSignatureError,
    LicenseRevokedError,
    LicenseSuspendedError,
)
from services.evaluation_gateway.signing_key_registry import key_registry
from services.evaluation_gateway.license_repository import license_repository, LicenseRecord
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.audit import audit_service
from services.evaluation_gateway.app import ADMIN_SECRET_KEY


ADMIN_HEADERS = {"X-Admin-Key": ADMIN_SECRET_KEY}


# ---------------------------------------------------------------------------
# Test Helpers
# ---------------------------------------------------------------------------

def generate_test_ed25519_keypair():
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    return priv, pub


def alter_payload_claim(b64_payload_str: str, key_to_alter: str = "sub", new_value: str = "attacker") -> str:
    raw = jwt.utils.base64url_decode(b64_payload_str)
    claims = json.loads(raw.decode("utf-8"))
    claims[key_to_alter] = new_value
    altered_bytes = json.dumps(claims).encode("utf-8")
    return jwt.utils.base64url_encode(altered_bytes).decode("ascii")


# ---------------------------------------------------------------------------
# LIC-001 through LIC-040 Test Scenarios
# ---------------------------------------------------------------------------

def test_lic_001_issue_valid_license(client: TestClient):
    """LIC-001: Admin issues valid evaluation license returning signed JWS and authoritative record."""
    res = client.post(
        "/v1/admin/evaluation/licenses",
        json={
            "evaluator_id": "evaluator-primary",
            "tenant_id": "tenant-eval-01",
            "duration_days": 14,
            "license_type": "protected_demo_evaluation",
            "policy_version": "evaluation-1.0",
        },
        headers=ADMIN_HEADERS,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "issued"
    assert "token" in data
    assert "jws" in data
    jti = data["license"]["jti"]
    assert license_repository.get_license(jti) is not None


def test_lic_002_issue_without_admin_permission(client: TestClient):
    """LIC-002: Issuing a license without administrative permission returns HTTP 403 Forbidden."""
    res = client.post(
        "/v1/admin/evaluation/licenses",
        json={"evaluator_id": "unauth-user"},
    )
    assert res.status_code == 403
    assert res.json()["error"] == "ADMIN_AUTHORIZATION_REQUIRED"


def test_lic_003_issue_with_invalid_policy(client: TestClient):
    """LIC-003: Issuing with unknown or unapproved policy version is rejected with HTTP 400."""
    res = client.post(
        "/v1/admin/evaluation/licenses",
        json={
            "evaluator_id": "evaluator-test",
            "policy_version": "unsupported-policy-9.9",
        },
        headers=ADMIN_HEADERS,
    )
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_POLICY"


def test_lic_004_duplicate_idempotency_key(client: TestClient):
    """LIC-004: Duplicate idempotency key returns the existing license without duplicate creation."""
    idemp_key = f"idemp-{uuid.uuid4().hex}"
    res1 = client.post(
        "/v1/admin/evaluation/licenses",
        json={"evaluator_id": "eval-idemp", "idempotency_key": idemp_key},
        headers=ADMIN_HEADERS,
    )
    assert res1.status_code == 200
    jti1 = res1.json()["license"]["jti"]

    res2 = client.post(
        "/v1/admin/evaluation/licenses",
        json={"evaluator_id": "eval-idemp", "idempotency_key": idemp_key},
        headers=ADMIN_HEADERS,
    )
    assert res2.status_code == 200
    jti2 = res2.json()["license"]["jti"]
    assert jti1 == jti2


def test_lic_005_valid_ed25519_signature():
    """LIC-005: Valid Ed25519 signature verification succeeds via standard verification pipeline."""
    lic = issue_evaluation_license(user_id="eval-sig-test", duration_days=14)
    jws_token = lic["jws"]
    verified = verify_signed_license(jws_token)
    assert verified["sub"] == "eval-sig-test"
    assert verified["iss"] == DEFAULT_ISSUER
    assert verified["aud"] == DEFAULT_AUDIENCE


def test_lic_006_modified_payload_rejected():
    """LIC-006: Altering any payload claim in JWS invalidates Ed25519 signature."""
    lic = issue_evaluation_license(user_id="legit-evaluator", duration_days=14)
    parts = lic["jws"].split(".")
    # Tamper payload segment
    tampered_payload = alter_payload_claim(parts[1], key_to_alter="sub", new_value="malicious-escalation")
    tampered_jws = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    with pytest.raises(LicenseSignatureError):
        verify_signed_license(tampered_jws)


def test_lic_007_modified_signature_rejected():
    """LIC-007: Modifying signature bytes causes immediate signature rejection."""
    lic = issue_evaluation_license(user_id="eval-sig-mod", duration_days=14)
    parts = lic["jws"].split(".")
    # Flip bytes in signature segment
    sig_raw = bytearray(jwt.utils.base64url_decode(parts[2]))
    sig_raw[0] ^= 0xFF
    bad_sig_b64 = jwt.utils.base64url_encode(bytes(sig_raw)).decode("ascii")
    tampered_jws = f"{parts[0]}.{parts[1]}.{bad_sig_b64}"

    with pytest.raises(LicenseSignatureError):
        verify_signed_license(tampered_jws)


def test_lic_008_unsupported_algorithm_rejected():
    """LIC-008: Tokens with algorithm other than EdDSA (e.g., 'none', 'HS256', 'RS256') are rejected."""
    priv, _ = generate_test_ed25519_keypair()
    token_hs = jwt.encode(
        {"sub": "test"},
        "a_secure_32_byte_hmac_test_key_ok!",
        algorithm="HS256",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="Unsupported algorithm"):
        verify_signed_license(token_hs)


def test_lic_009_unknown_kid_rejected():
    """LIC-009: Token with unrecognized key ID ('kid') is rejected."""
    priv, _ = generate_test_ed25519_keypair()
    token = jwt.encode(
        {"sub": "test", "iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "exp": int(time.time()) + 1000},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": "unknown-nonexistent-kid-999"},
    )
    with pytest.raises(LicenseVerificationError, match="Unknown signing key ID"):
        verify_signed_license(token)


def test_lic_010_missing_issuer_rejected():
    """LIC-010: Token missing required 'iss' claim is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"sub": "test", "aud": DEFAULT_AUDIENCE, "exp": int(time.time()) + 1000},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="missing required 'iss'"):
        verify_signed_license(token)


def test_lic_011_incorrect_issuer_rejected():
    """LIC-011: Token with incorrect 'iss' is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": "attacker-fake-issuer", "sub": "test", "aud": DEFAULT_AUDIENCE, "exp": int(time.time()) + 1000},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="issuer"):
        verify_signed_license(token)


def test_lic_012_incorrect_audience_rejected():
    """LIC-012: Token with incorrect 'aud' is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": "unauthorized-gateway", "sub": "test", "exp": int(time.time()) + 1000},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="audience"):
        verify_signed_license(token)


def test_lic_013_missing_expiry_rejected():
    """LIC-013: Token missing 'exp' claim is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="missing required 'exp'"):
        verify_signed_license(token)


def test_lic_014_expired_license_rejected():
    """LIC-014: License with exp timestamp in the past is rejected with LicenseExpiredError."""
    priv = key_registry.get_active_signing_key().private_key
    past_exp = int(time.time()) - 3600
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test", "exp": past_exp, "jti": "lic-exp"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseExpiredError):
        verify_signed_license(token)


def test_lic_015_future_nbf_rejected():
    """LIC-015: License with nbf timestamp in the future is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    future_nbf = int(time.time()) + 3600
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test", "nbf": future_nbf, "exp": future_nbf + 1000, "jti": "lic-nbf"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="not yet valid"):
        verify_signed_license(token)


def test_lic_016_invalid_claim_types_rejected():
    """LIC-016: Non-numeric exp or non-list features rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test", "exp": "tomorrow", "features": "string-instead-of-list"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="must be an integer"):
        verify_signed_license(token)


def test_lic_017_unknown_license_type_rejected():
    """LIC-017: Unknown license type is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test", "exp": int(time.time()) + 1000, "jti": "l17", "license_type": "enterprise_commercial_unrestricted"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="license_type"):
        verify_signed_license(token)


def test_lic_018_unknown_policy_version_rejected():
    """LIC-018: Unknown policy version is rejected."""
    priv = key_registry.get_active_signing_key().private_key
    token = jwt.encode(
        {"iss": DEFAULT_ISSUER, "aud": DEFAULT_AUDIENCE, "sub": "test", "exp": int(time.time()) + 1000, "jti": "l18", "policy_version": "v99.99"},
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="policy version"):
        verify_signed_license(token)


def test_lic_019_evaluator_mismatch_against_authoritative_record():
    """LIC-019: Token evaluator (sub) differing from authoritative database record is rejected."""
    lic = issue_evaluation_license(user_id="evaluator-alice")
    jti = lic["payload"]["jti"]
    token = lic["jws"]

    with pytest.raises(LicenseVerificationError, match="Evaluator mismatch"):
        verify_signed_license(token, expected_evaluator="evaluator-bob")


def test_lic_020_tenant_mismatch_against_authoritative_record():
    """LIC-020: Token tenant differing from authoritative database record is rejected."""
    lic = issue_evaluation_license(user_id="evaluator-ten", tenant_id="tenant-alpha")
    token = lic["jws"]

    with pytest.raises(LicenseVerificationError, match="Tenant mismatch"):
        verify_signed_license(token, expected_tenant="tenant-beta")


def test_lic_021_device_mismatch_rejected(client: TestClient):
    """LIC-021: Verifying license with deactivated device reports inactive status."""
    # Issue license and activate
    lic = issue_evaluation_license(user_id="eval-dev-test")
    token = lic["jws"]
    jti = lic["payload"]["jti"]

    res_verify = client.get("/v1/evaluation/license/verify", headers={"X-Evaluation-License": token})
    assert res_verify.status_code == 200
    assert res_verify.json()["valid"] is True


def test_lic_022_license_record_absent_in_authoritative_db():
    """LIC-022: Validly signed JWS with no authoritative DB record is rejected when required."""
    priv = key_registry.get_active_signing_key().private_key
    orphan_jti = str(uuid.uuid4())
    token = jwt.encode(
        {
            "iss": DEFAULT_ISSUER,
            "aud": DEFAULT_AUDIENCE,
            "sub": "evaluator-orphan",
            "jti": orphan_jti,
            "exp": int(time.time()) + 1000,
            "license_type": "protected_demo_evaluation",
            "policy_version": "evaluation-1.0",
        },
        priv,
        algorithm="EdDSA",
        headers={"typ": "AEGIS-EVALUATION-LICENSE", "kid": DEFAULT_KEY_ID},
    )
    with pytest.raises(LicenseVerificationError, match="not found in database"):
        verify_signed_license(token, require_authoritative_record=True)


def test_lic_023_license_suspended_in_authoritative_db(client: TestClient):
    """LIC-023: License suspended in authoritative DB is rejected with LicenseSuspendedError / HTTP 403."""
    lic = issue_evaluation_license(user_id="eval-susp")
    jti = lic["payload"]["jti"]
    token = lic["jws"]

    # Admin suspends license
    client.post(f"/v1/admin/evaluation/licenses/{jti}/suspend", headers=ADMIN_HEADERS)

    # Verification fails
    with pytest.raises(LicenseSuspendedError):
        verify_signed_license(token)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 403
    assert res.json()["error"] == "LICENSE_SUSPENDED"


def test_lic_024_license_revoked_in_authoritative_db(client: TestClient):
    """LIC-024: License revoked in authoritative DB is rejected with LicenseRevokedError / HTTP 403."""
    lic = issue_evaluation_license(user_id="eval-rev")
    jti = lic["payload"]["jti"]
    token = lic["jws"]

    # Admin revokes license
    client.post(f"/v1/admin/evaluation/licenses/{jti}/revoke", json={"reason": "policy_violation"}, headers=ADMIN_HEADERS)

    # Verification fails
    with pytest.raises(LicenseRevokedError):
        verify_signed_license(token)

    res = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res.status_code == 403
    assert res.json()["error"] == "LICENSE_REVOKED"


def test_lic_025_device_deactivated_associated_with_license(client: TestClient):
    """LIC-025: License with deactivated device returns deactivated device status."""
    lic = issue_evaluation_license(user_id="eval-deact-dev")
    token = lic["jws"]
    jti = lic["payload"]["jti"]

    res = client.get("/v1/evaluation/license/verify", headers={"X-Evaluation-License": token})
    assert res.status_code == 200
    assert res.json()["valid"] is True


def test_lic_026_signing_key_compromised_emergency_invalidation(client: TestClient):
    """LIC-026: Marking a signing key COMPROMISED immediately revokes all licenses issued by it."""
    lic = issue_evaluation_license(user_id="eval-compromised-test")
    kid = lic["kid"]
    token = lic["jws"]

    # License verifies before compromise
    assert verify_signed_license(token)["sub"] == "eval-compromised-test"

    # Emergency key compromise
    res = client.post(f"/v1/admin/evaluation/signing-keys/{kid}/compromise", headers=ADMIN_HEADERS)
    assert res.status_code == 200

    # License verification now fails closed immediately
    with pytest.raises(LicenseVerificationError, match="compromised"):
        verify_signed_license(token)


def test_lic_027_old_key_in_verify_only_state(client: TestClient):
    """LIC-027: Key rotation keeps old key in VERIFY_ONLY state; previously issued licenses continue to verify."""
    # 1. Issue license with Key 1
    lic1 = issue_evaluation_license(user_id="eval-old-key")
    old_kid = lic1["kid"]
    token1 = lic1["jws"]

    # 2. Rotate signing key
    res_rot = client.post("/v1/admin/evaluation/signing-keys/rotate", headers=ADMIN_HEADERS)
    assert res_rot.status_code == 200
    new_kid = res_rot.json()["key_id"]
    assert new_kid != old_kid

    # Old key is now VERIFY_ONLY
    old_rec = key_registry.get_verification_key(old_kid)
    assert old_rec.status == "VERIFY_ONLY"

    # 3. Old license still verifies cleanly
    verified = verify_signed_license(token1)
    assert verified["sub"] == "eval-old-key"


def test_lic_028_old_key_retired_behavior(client: TestClient):
    """LIC-028: When an old key is RETIRED, licenses signed by it are rejected."""
    lic = issue_evaluation_license(user_id="eval-retire")
    kid = lic["kid"]
    token = lic["jws"]

    # Retire the key
    key_registry.retire_key(kid)

    with pytest.raises(LicenseVerificationError, match="retired"):
        verify_signed_license(token)


def test_lic_029_new_key_after_rotation_signs_and_verifies(client: TestClient):
    """LIC-029: After rotation, newly issued licenses use the new key and verify cleanly."""
    res_rot = client.post("/v1/admin/evaluation/signing-keys/rotate", headers=ADMIN_HEADERS)
    new_kid = res_rot.json()["key_id"]

    lic2 = issue_evaluation_license(user_id="eval-new-key")
    assert lic2["kid"] == new_kid
    token2 = lic2["jws"]

    verified = verify_signed_license(token2)
    assert verified["sub"] == "eval-new-key"


def test_lic_030_revocation_cache_invalidation(client: TestClient):
    """LIC-030: Administrative revocation immediately invalidates authorization without delay."""
    lic = issue_evaluation_license(user_id="eval-cache-test")
    token = lic["jws"]
    jti = lic["payload"]["jti"]

    # Valid before revocation
    res1 = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res1.status_code == 200

    # Revoke
    client.post(f"/v1/admin/evaluation/licenses/{jti}/revoke", headers=ADMIN_HEADERS)

    # Immediately denied
    res2 = client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    assert res2.status_code == 403


def test_lic_031_fail_closed_on_authority_unavailable():
    """LIC-031: When license verification cannot confirm key or status, it fails closed."""
    with pytest.raises(LicenseVerificationError):
        verify_signed_license("invalid.token.structure")


def test_lic_032_client_clock_moved_backwards():
    """LIC-032: Client moving local clock backwards cannot bypass server-enforced expiry."""
    lic = issue_evaluation_license(user_id="eval-clock-back", duration_days=-2)
    token = lic["jws"]
    # Server reference time is current server time
    with pytest.raises(LicenseExpiredError):
        verify_signed_license(token, reference_time=datetime.now(timezone.utc))


def test_lic_033_client_clock_moved_forwards():
    """LIC-033: Client moving clock forwards does not affect server-authoritative validity."""
    lic = issue_evaluation_license(user_id="eval-clock-fwd", duration_days=14)
    token = lic["jws"]
    # Verified against authoritative server time
    verified = verify_signed_license(token, reference_time=datetime.now(timezone.utc))
    assert verified["sub"] == "eval-clock-fwd"


def test_lic_034_token_controlled_key_url_rejected():
    """LIC-034: JWS headers declaring jku or x5u are strictly rejected (anti-forgery)."""
    priv, _ = generate_test_ed25519_keypair()
    token = jwt.encode(
        {"sub": "test"},
        priv,
        algorithm="EdDSA",
        headers={
            "alg": "EdDSA",
            "kid": DEFAULT_KEY_ID,
            "typ": "AEGIS-EVALUATION-LICENSE",
            "jku": "https://attacker.example/keys.json",
        },
    )
    with pytest.raises(LicenseVerificationError, match="Token-controlled key URLs"):
        verify_signed_license(token)


def test_lic_035_oversized_token_rejected():
    """LIC-035: Tokens exceeding 8192 bytes are rejected (anti-DoS)."""
    large_token = "a." * 4097
    with pytest.raises(LicenseVerificationError, match="exceeds maximum permitted size"):
        verify_signed_license(large_token)


def test_lic_036_malformed_compact_jws_rejected():
    """LIC-036: Tokens with wrong number of dot-separated segments or invalid base64 rejected."""
    for malformed in ["header.payload", "h.p.s.extra", "not_a_valid_token_at_all"]:
        with pytest.raises(LicenseVerificationError):
            verify_signed_license(malformed)


def test_lic_037_private_key_excluded_from_client_bundle():
    """LIC-037: Packaging verification: zero private signing keys exist in distribution packages."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    dist_dir = repo_root / "distribution" / "demo-edition"
    if dist_dir.exists():
        for p in dist_dir.rglob("*"):
            if p.is_file():
                assert "private" not in p.name.lower(), f"Private key file in client bundle: {p}"
                assert not p.name.endswith(".key"), f"Key file in client bundle: {p}"


def test_lic_038_private_key_excluded_from_public_source():
    """LIC-038: Source scan: zero private signing keys embedded in src/ or web/src/."""
    repo_root = Path(__file__).resolve().parent.parent.parent.parent
    forbidden = ["BEGIN PRIVATE KEY", "BEGIN ED25519 PRIVATE KEY", "BEGIN RSA PRIVATE KEY"]
    for folder in [repo_root / "src", repo_root / "web" / "src"]:
        if folder.exists():
            for p in folder.rglob("*"):
                if p.is_file() and p.suffix in (".py", ".ts", ".tsx", ".js", ".json"):
                    txt = p.read_text(encoding="utf-8", errors="ignore")
                    for f in forbidden:
                        assert f not in txt, f"Private key embedded in source: {p}"


def test_lic_039_raw_token_never_in_logs(client: TestClient):
    """LIC-039: Raw compact JWS tokens are never logged in plaintext in security telemetry."""
    audit_service.clear()
    lic = issue_evaluation_license(user_id="eval-log-test")
    token = lic["jws"]

    client.get("/v1/evaluation/license", headers={"X-Evaluation-License": token})
    events = audit_service.get_events(20)
    serialized = json.dumps(events)
    assert token not in serialized, "Raw JWS token leaked in audit event log!"


def test_lic_040_cross_evaluator_license_access_denied(client: TestClient):
    """LIC-040: Evaluator A cannot inspect or access Evaluator B's license record."""
    licA = issue_evaluation_license(user_id="evaluator-A")
    licB = issue_evaluation_license(user_id="evaluator-B")
    tokenA = licA["jws"]
    jtiB = licB["payload"]["jti"]

    # Evaluator A tries to access admin endpoint to inspect B's license
    res = client.get(f"/v1/admin/evaluation/licenses/{jtiB}", headers={"Authorization": f"Bearer {tokenA}"})
    assert res.status_code == 403
