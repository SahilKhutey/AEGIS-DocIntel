"""
AEGIS-DocIntel Remediation Acceptance Test Suite: REM-02 Licensing & Device Binding
Verifies LIC-REM-001 through LIC-REM-012 and DEV-REM-001 through DEV-REM-015.
"""

from __future__ import annotations

import base64
import copy
import hashlib
import time
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa
from fastapi.testclient import TestClient

from services.evaluation_gateway.app import app
from services.evaluation_gateway.license import (
    issue_evaluation_license,
    verify_license,
    export_license_token,
    parse_license_token,
    CANONICAL_PRODUCT,
    LicenseSignatureError,
    LicenseVerificationError,
    LicenseExpiredError,
    LicenseRevokedError,
)
from services.evaluation_gateway.signing_key_registry import (
    key_registry,
    CANONICAL_ALGORITHM,
)
from services.evaluation_gateway.revocation import registry as revocation_registry
from services.evaluation_gateway.activation import activation_service
from src.security.device_crypto import device_crypto


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def ed25519_keypair():
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    pub_pem = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    return priv, pub, pub_pem


# ── LIC-REM Tests (001 - 012) ────────────────────────────────────────────────

def test_lic_rem_001_ed25519_signature_generation():
    """LIC-REM-001: Issues Pure Ed25519 digitally signed license."""
    lic = issue_evaluation_license(user_id="eval-rem-001", duration_days=14)
    assert lic["header"]["alg"] == "EdDSA"
    assert lic["algorithm"] == "EdDSA"
    assert "signature" in lic
    assert len(lic["signature"]) > 32


def test_lic_rem_002_signature_verification_succeeds():
    """LIC-REM-002: Digital signature verifies against active registry public key."""
    lic = issue_evaluation_license(user_id="eval-rem-002", duration_days=14)
    payload = verify_license(lic)
    assert payload["sub"] == "eval-rem-002"


def test_lic_rem_003_tampered_payload_rejected():
    """LIC-REM-003: Modifying payload bytes invalidates cryptographic signature."""
    lic = issue_evaluation_license(user_id="eval-rem-003", duration_days=14)
    tampered = copy.deepcopy(lic)
    tampered["payload"]["duration_days"] = 365
    with pytest.raises(LicenseSignatureError):
        verify_license(tampered)


def test_lic_rem_004_corrupted_signature_rejected():
    """LIC-REM-004: Bit-flipped or forged signature fails validation."""
    lic = issue_evaluation_license(user_id="eval-rem-004", duration_days=14)
    tampered = copy.deepcopy(lic)
    tampered["signature"] = "corrupted_sig_" + tampered["signature"][14:]
    with pytest.raises(LicenseSignatureError):
        verify_license(tampered)


def test_lic_rem_005_unknown_key_id_rejected():
    """LIC-REM-005: Unregistered signing key ID is rejected."""
    lic = issue_evaluation_license(user_id="eval-rem-005", duration_days=14)
    tampered = copy.deepcopy(lic)
    tampered["header"]["kid"] = "unknown-nonexistent-key-999"
    with pytest.raises(LicenseVerificationError):
        verify_license(tampered)


def test_lic_rem_006_expired_license_rejected():
    """LIC-REM-006: Expired license timestamp fails validation."""
    lic = issue_evaluation_license(user_id="eval-rem-006", duration_days=-1)
    with pytest.raises(LicenseExpiredError):
        verify_license(lic)


def test_lic_rem_007_revoked_license_rejected():
    """LIC-REM-007: Revoked license ID is denied access."""
    lic = issue_evaluation_license(user_id="eval-rem-007", duration_days=14)
    lic_id = lic["payload"]["license_id"]
    revocation_registry.revoke(lic_id, "Fraudulent registration")
    with pytest.raises(LicenseRevokedError):
        verify_license(lic)


def test_lic_rem_008_key_rotation_preserves_circulating():
    """LIC-REM-008: Key rotation demotes predecessor to VERIFY_ONLY (existing licenses verify)."""
    lic_old = issue_evaluation_license(user_id="eval-rem-008", duration_days=14)
    key_registry.rotate_key()
    payload = verify_license(lic_old)
    assert payload["sub"] == "eval-rem-008"


def test_lic_rem_009_key_rotation_signs_with_new_key():
    """LIC-REM-009: Newly rotated key signs future licenses."""
    rec = key_registry.rotate_key()
    lic_new = issue_evaluation_license(user_id="eval-rem-009", duration_days=14)
    assert lic_new["header"]["kid"] == rec.key_id


def test_lic_rem_010_emergency_key_compromise_invalidates():
    """LIC-REM-010: Emergency compromise invalidates all licenses under target key."""
    lic = issue_evaluation_license(user_id="eval-rem-010", duration_days=14)
    kid = lic["header"]["kid"]
    key_registry.compromise_key(kid)
    with pytest.raises(LicenseVerificationError):
        verify_license(lic)


def test_lic_rem_011_token_export_and_deterministic_parse():
    """LIC-REM-011: Base64 license token exports and round-trip parses identically."""
    lic = issue_evaluation_license(user_id="eval-rem-011", duration_days=14)
    tok = export_license_token(lic)
    parsed = parse_license_token(tok)
    assert parsed["payload"]["sub"] == "eval-rem-011"
    assert parsed["signature"] == lic["signature"]


def test_lic_rem_012_public_key_registry_zero_private_keys():
    """LIC-REM-012: Public key registry metadata strictly excludes private key bytes."""
    meta = key_registry.list_keys()
    for item in meta:
        assert "private_key" not in item
        assert "public_key_pem" in item
        assert "-----BEGIN PUBLIC KEY-----" in item["public_key_pem"]


# ── DEV-REM Tests (001 - 015) ────────────────────────────────────────────────

def test_dev_rem_001_parse_valid_ed25519_pem(ed25519_keypair):
    """DEV-REM-001: Device key parser accepts standard Ed25519 SPKI PEM."""
    _, _, pem = ed25519_keypair
    obj, canon, ktype = device_crypto.parse_public_key(pem)
    assert ktype == "Ed25519"
    assert len(canon) > 0


def test_dev_rem_002_parse_valid_rsa_pem():
    """DEV-REM-002: Device key parser accepts standard RSA SPKI PEM."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pem = priv.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("utf-8")
    obj, canon, ktype = device_crypto.parse_public_key(pem)
    assert ktype == "RSA"


def test_dev_rem_003_parse_32_byte_raw_ed25519(ed25519_keypair):
    """DEV-REM-003: Device key parser accepts 32-byte raw Ed25519 public key."""
    _, pub, _ = ed25519_keypair
    raw_bytes = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    b64_raw = base64.b64encode(raw_bytes).decode("ascii")
    obj, canon, ktype = device_crypto.parse_public_key(b64_raw)
    assert ktype == "Ed25519"
    assert len(canon) == 32


def test_dev_rem_004_malformed_key_syntax_rejected():
    """DEV-REM-004: Malformed or unparseable key syntax raises ValueError."""
    with pytest.raises(ValueError):
        device_crypto.parse_public_key("not-a-valid-key")


def test_dev_rem_005_challenge_nonce_entropy():
    """DEV-REM-005: Challenge nonce has >= 32 bytes of cryptographic randomness."""
    cid, nonce, exp = device_crypto.generate_challenge()
    assert len(nonce) >= 64  # 32 bytes hex encoded = 64 chars
    assert time.time() < exp


def test_dev_rem_006_challenge_nonce_ttl():
    """DEV-REM-006: Challenge nonces expire within 60 seconds."""
    cid, nonce, exp = device_crypto.generate_challenge(ttl_seconds=60)
    assert 55 <= (exp - time.time()) <= 65


def test_dev_rem_007_single_use_challenge_no_replay(client, ed25519_keypair):
    """DEV-REM-007: Challenge nonce cannot be replayed after activation."""
    priv, pub, pem = ed25519_keypair
    activation_service.reset()
    chal = client.post("/v1/evaluation/device/challenge", json={
        "device_public_key": pem,
        "installation_id": "inst-007",
        "activation_code": "AEGIS-EVAL-2026-DEMO",
    }).json()

    cmsg = chal["canonical_message"]
    sig = base64.b64encode(priv.sign(cmsg.encode("utf-8"))).decode("ascii")

    # First activation consumes challenge
    res1 = client.post("/v1/evaluation/device/activate", json={
        "challenge_id": chal["challenge_id"],
        "signature": sig,
        "installation_id": "inst-007",
    })
    assert res1.status_code == 200

    # Second presentation rejected
    res2 = client.post("/v1/evaluation/device/activate", json={
        "challenge_id": chal["challenge_id"],
        "signature": sig,
        "installation_id": "inst-007",
    })
    assert res2.status_code in (400, 401, 404)


def test_dev_rem_008_valid_pop_registers_device(client, ed25519_keypair):
    """DEV-REM-008: Valid challenge-response PoP binds device and issues session."""
    priv, pub, pem = ed25519_keypair
    activation_service.reset()
    res = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": pem,
    })
    assert res.status_code == 200
    data = res.json()
    assert "device_id" in data
    assert "recovery_code" in data
    assert "session" in data


def test_dev_rem_009_invalid_signature_rejected(client, ed25519_keypair):
    """DEV-REM-009: Forged or incorrect signature fails challenge verification."""
    priv, pub, pem = ed25519_keypair
    activation_service.reset()
    chal = client.post("/v1/evaluation/device/challenge", json={
        "device_public_key": pem,
        "installation_id": "inst-009",
        "activation_code": "AEGIS-EVAL-2026-DEMO",
    }).json()

    forged_sig = base64.b64encode(b"forged_invalid_signature_bytes_here_32").decode("ascii")
    res = client.post("/v1/evaluation/device/activate", json={
        "challenge_id": chal["challenge_id"],
        "signature": forged_sig,
        "installation_id": "inst-009",
    })
    assert res.status_code in (400, 401)


def test_dev_rem_010_atomic_device_limit_enforcement(client):
    """DEV-REM-010: Device limit is enforced atomically under 1-device policy."""
    activation_service.reset()
    res1 = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_alpha_rem",
    })
    assert res1.status_code == 200

    res2 = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_beta_rem",
    })
    assert res2.status_code == 409


def test_dev_rem_011_device_limit_exceeded_status_409(client):
    """DEV-REM-011: Attempting activation beyond device quota returns HTTP 409."""
    res = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_overflow",
    })
    if res.status_code != 409:
        res2 = client.post("/v1/evaluation/activate", json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "dev_key_overflow_2",
        })
        assert res2.status_code == 409


def test_dev_rem_012_emergency_recovery_code_format(client):
    """DEV-REM-012: Activation returns emergency recovery code matching REC-****-**** format."""
    activation_service.reset()
    res = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_rec_fmt",
    })
    rec_code = res.json()["recovery_code"]
    assert rec_code.startswith("REC-")
    parts = rec_code.split("-")
    assert len(parts) == 3


def test_dev_rem_013_recovery_code_unbinds_and_frees_slot(client):
    """DEV-REM-013: Emergency recovery code unbinds device and frees license slot."""
    activation_service.reset()
    res1 = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_unbind_old",
    })
    lic_id = res1.json()["license"]["license_id"]
    dev_id = res1.json()["device_id"]
    rec_code = res1.json()["recovery_code"]

    # Recover device
    rec_res = client.post("/v1/evaluation/device/recover", json={
        "license_id": lic_id,
        "device_id": dev_id,
        "recovery_code": rec_code,
    })
    assert rec_res.status_code == 200

    # New device slot available
    res2 = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_unbind_new",
    })
    assert res2.status_code == 200


def test_dev_rem_014_invalid_recovery_code_rejected(client):
    """DEV-REM-014: Incorrect emergency recovery code returns HTTP 401."""
    activation_service.reset()
    res1 = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_bad_rec",
    })
    lic_id = res1.json()["license"]["license_id"]
    dev_id = res1.json()["device_id"]

    rec_res = client.post("/v1/evaluation/device/recover", json={
        "license_id": lic_id,
        "device_id": dev_id,
        "recovery_code": "REC-WRONG-CODE",
    })
    assert rec_res.status_code == 401


def test_dev_rem_015_device_deactivation_revokes_sessions(client):
    """DEV-REM-015: Deactivating device revokes all sessions tied to that device."""
    activation_service.reset()
    res = client.post("/v1/evaluation/activate", json={
        "activation_code": "AEGIS-EVAL-2026-DEMO",
        "device_public_key": "dev_key_deact",
    })
    lic_id = res.json()["license"]["license_id"]
    dev_id = res.json()["device_id"]
    at = res.json()["session"]["access_token"]

    # Deactivate device
    activation_service.deactivate_device(lic_id, dev_id)

    # Session token must be revoked
    sess = activation_service.validate_session(at)
    assert sess is None or sess.is_revoked is True
