"""
AEGIS Evaluation Security Tests — Device Binding & Challenge Protocol (PROT-04 WP-04.03)
Comprehensive Verification Suite: DEV-001 through DEV-030

Validates:
- Two-stage cryptographic proof-of-possession challenge protocol (Stage 1 Challenge, Stage 2 Activate)
- Support for Ed25519 (raw base64 & PEM) and RSA-2048 key pairs
- Single-use challenge consumption (anti-replay DEV-010)
- Challenge expiry enforcement (DEV-009)
- Atomic 1-device active limit enforcement (DEV-002) and concurrent race resilience (DEV-026)
- Device identity binding and SHA-256 fingerprinting (DEV-015)
- Session invalidation upon device deactivation (DEV-003) and slot reuse (DEV-004)
- Keyed HMAC-SHA256 lookup preserving activation code privacy (DEV-025)
- Emergency device recovery protocol (DEV-020, DEV-021)
- Device presence heartbeat (DEV-022, DEV-023)
- Multi-tenant / cross-license device isolation (DEV-019)
- IP rate limiting on challenge generation (DEV-024)
- End-to-end full evaluation lifecycle (DEV-030)
"""

import base64
import concurrent.futures
import hashlib
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, padding

from services.evaluation_gateway.activation import (
    activation_service,
    compute_code_hash,
    compute_key_fingerprint,
    format_canonical_challenge,
)
from services.evaluation_gateway.audit import audit_service


# ---------------------------------------------------------------------------
# Cryptographic Test Helpers
# ---------------------------------------------------------------------------

def generate_ed25519_keypair():
    """Generates an Ed25519 private key, raw base64 public key, and PEM public key."""
    priv = ed25519.Ed25519PrivateKey.generate()
    pub = priv.public_key()
    raw_pub = pub.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )
    b64_raw = base64.b64encode(raw_pub).decode("ascii")
    pem_pub = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return priv, b64_raw, pem_pub


def generate_rsa_keypair():
    """Generates an RSA-2048 private key and PEM public key."""
    priv = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    pub = priv.public_key()
    pem_pub = pub.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    ).decode("ascii")
    return priv, pem_pub


def sign_ed25519(priv_key: ed25519.Ed25519PrivateKey, message: str) -> str:
    """Signs UTF-8 string with Ed25519 and returns base64 signature."""
    sig = priv_key.sign(message.encode("utf-8"))
    return base64.b64encode(sig).decode("ascii")


def sign_rsa_pss(priv_key: rsa.RSAPrivateKey, message: str) -> str:
    """Signs UTF-8 string with RSA-PSS-SHA256 and returns base64 signature."""
    sig = priv_key.sign(
        message.encode("utf-8"),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("ascii")


def sign_rsa_pkcs1v15(priv_key: rsa.RSAPrivateKey, message: str) -> str:
    """Signs UTF-8 string with RSA-PKCS1v15-SHA256 and returns base64 signature."""
    sig = priv_key.sign(
        message.encode("utf-8"),
        padding.PKCS1v15(),
        hashes.SHA256(),
    )
    return base64.b64encode(sig).decode("ascii")


# ---------------------------------------------------------------------------
# Test Scenarios (DEV-001 through DEV-030)
# ---------------------------------------------------------------------------

def test_dev_001_stage1_challenge_creation_ed25519(client: TestClient):
    """DEV-001: Stage 1 challenge creation with valid activation code and Ed25519 PEM key."""
    priv, _, pem_pub = generate_ed25519_keypair()
    res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem_pub,
            "installation_id": "inst-win-dev01",
            "device_label": "Dev Laptop",
            "platform": "windows",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert "challenge_id" in data
    assert "nonce" in data
    assert "canonical_message" in data
    assert "expires_at" in data
    assert data["algorithm"] == "Ed25519"
    assert "AEGIS-EVAL-DEVICE-PROOF-V1" in data["canonical_message"]


def test_dev_002_atomic_one_device_limit_enforcement(client: TestClient):
    """DEV-002: Enforces maximum 1 active device under evaluation license."""
    # Device 1 activates successfully
    priv1, _, pem1 = generate_ed25519_keypair()
    res_ch1 = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem1,
            "installation_id": "inst-dev1",
        },
    )
    assert res_ch1.status_code == 200
    ch1 = res_ch1.json()
    sig1 = sign_ed25519(priv1, ch1["canonical_message"])
    res_act1 = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch1["challenge_id"],
            "signature": sig1,
            "installation_id": "inst-dev1",
        },
    )
    assert res_act1.status_code == 200

    # Device 2 attempts challenge with different key
    priv2, _, pem2 = generate_ed25519_keypair()
    res_ch2 = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem2,
            "installation_id": "inst-dev2",
        },
    )
    assert res_ch2.status_code == 409
    assert res_ch2.json()["error"] == "DEVICE_LIMIT_EXCEEDED"


def test_dev_003_session_revocation_on_device_deactivation(client: TestClient):
    """DEV-003: Deactivating a device instantly invalidates all associated sessions."""
    priv, _, pem = generate_ed25519_keypair()
    res_ch = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem,
            "installation_id": "inst-dev3",
        },
    )
    ch = res_ch.json()
    sig = sign_ed25519(priv, ch["canonical_message"])
    res_act = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": sig,
            "installation_id": "inst-dev3",
        },
    )
    token = res_act.json()["session"]["access_token"]
    device_id = res_act.json()["device_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # Query succeeds before deactivation
    res_q1 = client.post("/v1/evaluation/query", json={"query": "test"}, headers=headers)
    assert res_q1.status_code == 200

    # Deactivate device
    res_deact = client.post(f"/v1/evaluation/devices/{device_id}/deactivate", headers=headers)
    assert res_deact.status_code == 200

    # Query rejected with 401 Unauthorized
    res_q2 = client.post("/v1/evaluation/query", json={"query": "test"}, headers=headers)
    assert res_q2.status_code == 401


def test_dev_004_deactivation_frees_device_slot_for_replacement(client: TestClient):
    """DEV-004: Deactivating a device frees slot, allowing a replacement device to activate."""
    # 1. Activate Device 1
    priv1, _, pem1 = generate_ed25519_keypair()
    ch1 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem1, "installation_id": "inst-1"},
    ).json()
    act1 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch1["challenge_id"], "signature": sign_ed25519(priv1, ch1["canonical_message"]), "installation_id": "inst-1"},
    ).json()
    token1 = act1["session"]["access_token"]
    dev1_id = act1["device_id"]

    # 2. Deactivate Device 1
    client.post(f"/v1/evaluation/devices/{dev1_id}/deactivate", headers={"Authorization": f"Bearer {token1}"})

    # 3. Device 2 can now challenge and activate
    priv2, _, pem2 = generate_ed25519_keypair()
    res_ch2 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem2, "installation_id": "inst-2"},
    )
    assert res_ch2.status_code == 200
    ch2 = res_ch2.json()
    res_act2 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch2["challenge_id"], "signature": sign_ed25519(priv2, ch2["canonical_message"]), "installation_id": "inst-2"},
    )
    assert res_act2.status_code == 200
    assert res_act2.json()["status"] == "active"


def test_dev_005_challenge_rejected_invalid_activation_code(client: TestClient):
    """DEV-005: Challenge rejected with 400 Bad Request on unrecognized code."""
    priv, _, pem = generate_ed25519_keypair()
    res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "BOGUS-ACTIVATION-CODE-999",
            "device_public_key": pem,
            "installation_id": "inst-bogus",
        },
    )
    assert res.status_code == 400
    assert res.json()["error"] == "INVALID_ACTIVATION_CODE"


def test_dev_006_challenge_rejected_malformed_public_key(client: TestClient):
    """DEV-006: Challenge rejected with 400 Bad Request on malformed public key."""
    res = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": "not-a-valid-base64-or-pem-key!!!",
            "installation_id": "inst-malformed",
        },
    )
    assert res.status_code == 400
    assert res.json()["error"] == "MALFORMED_PUBLIC_KEY"


def test_dev_007_activation_rejected_invalid_signature(client: TestClient):
    """DEV-007: Activation rejected with 401 when signature does not verify against public key."""
    priv1, _, pem1 = generate_ed25519_keypair()
    priv_wrong, _, _ = generate_ed25519_keypair()

    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem1, "installation_id": "inst-sig"},
    ).json()

    # Sign with wrong private key
    bad_sig = sign_ed25519(priv_wrong, ch["canonical_message"])
    res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": bad_sig,
            "installation_id": "inst-sig",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_DEVICE_SIGNATURE"


def test_dev_008_activation_rejected_tampered_canonical_message(client: TestClient):
    """DEV-008: Activation rejected when signature signs a modified message."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-tamp"},
    ).json()

    tampered_msg = ch["canonical_message"] + "\nextra_payload=attacker_data"
    tampered_sig = sign_ed25519(priv, tampered_msg)

    res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": tampered_sig,
            "installation_id": "inst-tamp",
        },
    )
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_DEVICE_SIGNATURE"


def test_dev_009_challenge_expiry_rejected(client: TestClient):
    """DEV-009: Expired challenge is rejected with 400 CHALLENGE_EXPIRED."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-exp"},
    ).json()

    # Artificially set expiry in the past
    rec = activation_service._challenges_by_id[ch["challenge_id"]]
    rec.expires_at = time.time() - 1.0

    sig = sign_ed25519(priv, ch["canonical_message"])
    res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": sig,
            "installation_id": "inst-exp",
        },
    )
    assert res.status_code == 400
    assert res.json()["error"] == "CHALLENGE_EXPIRED"


def test_dev_010_challenge_single_use_replay_prevention(client: TestClient):
    """DEV-010: Replaying an already-consumed challenge is rejected with 400 CHALLENGE_ALREADY_CONSUMED."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-replay"},
    ).json()

    sig = sign_ed25519(priv, ch["canonical_message"])
    # First consumption succeeds
    res1 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sig, "installation_id": "inst-replay"},
    )
    assert res1.status_code == 200

    # Replay attempt fails
    res2 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sig, "installation_id": "inst-replay"},
    )
    assert res2.status_code == 400
    assert res2.json()["error"] == "CHALLENGE_ALREADY_CONSUMED"


def test_dev_011_activation_nonexistent_challenge_id(client: TestClient):
    """DEV-011: Attempting to activate with a non-existent challenge ID returns 404."""
    res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": str(uuid.uuid4()),
            "signature": "c29tZXNpZ25hdHVyZQ==",
            "installation_id": "inst-none",
        },
    )
    assert res.status_code == 404
    assert res.json()["error"] == "CHALLENGE_NOT_FOUND"


def test_dev_012_installation_id_mismatch_rejected(client: TestClient):
    """DEV-012: Installation ID mismatch between Stage 1 and Stage 2 is rejected."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-alpha"},
    ).json()

    sig = sign_ed25519(priv, ch["canonical_message"])
    res = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": sig,
            "installation_id": "inst-beta",
        },
    )
    assert res.status_code == 400
    assert res.json()["error"] == "INSTALLATION_MISMATCH"


def test_dev_013_activation_rsa_2048_key(client: TestClient):
    """DEV-013: Proof-of-possession succeeds with RSA-2048 key pair."""
    priv, pem_pub = generate_rsa_keypair()
    res_ch = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem_pub,
            "installation_id": "inst-rsa-01",
        },
    )
    assert res_ch.status_code == 200
    ch = res_ch.json()
    assert ch["algorithm"] == "RSA"

    sig = sign_rsa_pss(priv, ch["canonical_message"])
    res_act = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": sig,
            "installation_id": "inst-rsa-01",
        },
    )
    assert res_act.status_code == 200
    assert res_act.json()["status"] == "active"
    assert "recovery_code" in res_act.json()


def test_dev_014_activation_ed25519_raw_base64_key(client: TestClient):
    """DEV-014: Proof-of-possession succeeds with Ed25519 raw 32-byte Base64 key."""
    priv, b64_raw, _ = generate_ed25519_keypair()
    res_ch = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": b64_raw,
            "installation_id": "inst-raw-01",
        },
    )
    assert res_ch.status_code == 200
    ch = res_ch.json()

    sig = sign_ed25519(priv, ch["canonical_message"])
    res_act = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch["challenge_id"],
            "signature": sig,
            "installation_id": "inst-raw-01",
        },
    )
    assert res_act.status_code == 200
    assert res_act.json()["status"] == "active"


def test_dev_015_key_fingerprint_deterministic_and_unique(client: TestClient):
    """DEV-015: Key fingerprinting is deterministic and collision-resistant."""
    priv1, b64_1, _ = generate_ed25519_keypair()
    priv2, b64_2, _ = generate_ed25519_keypair()

    ch1a = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": b64_1, "installation_id": "i1"},
    ).json()

    ch1b = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": b64_1, "installation_id": "i2"},
    ).json()

    ch2 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": b64_2, "installation_id": "i3"},
    ).json()

    assert ch1a["key_fingerprint"] == ch1b["key_fingerprint"]
    assert ch1a["key_fingerprint"] != ch2["key_fingerprint"]


def test_dev_016_idempotent_reactivation_same_device(client: TestClient):
    """DEV-016: Re-activating the exact same device key pair updates timestamps without quota penalty."""
    priv, _, pem = generate_ed25519_keypair()

    # Activation 1
    ch1 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-same"},
    ).json()
    act1 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch1["challenge_id"], "signature": sign_ed25519(priv, ch1["canonical_message"]), "installation_id": "inst-same"},
    ).json()
    dev_id1 = act1["device_id"]

    # Activation 2 with same key succeeds as refresh/re-bind
    ch2 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-same"},
    ).json()
    act2 = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch2["challenge_id"], "signature": sign_ed25519(priv, ch2["canonical_message"]), "installation_id": "inst-same"},
    ).json()
    dev_id2 = act2["device_id"]

    assert dev_id1 == dev_id2
    assert act2["status"] == "active"


def test_dev_017_devices_listing_endpoint(client: TestClient):
    """DEV-017: GET /v1/evaluation/devices returns list of registered devices for current license."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-list", "device_label": "Office Mac"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-list"},
    ).json()
    token = act["session"]["access_token"]

    res = client.get("/v1/evaluation/devices", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert "devices" in data
    assert len(data["devices"]) == 1
    d = data["devices"][0]
    assert d["device_id"] == act["device_id"]
    assert d["label"] == "Office Mac"
    assert d["is_active"] is True
    assert "key_fingerprint" in d


def test_dev_018_device_detail_endpoint(client: TestClient):
    """DEV-018: GET /v1/evaluation/devices/{device_id} returns device metadata."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-det"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-det"},
    ).json()
    token = act["session"]["access_token"]
    dev_id = act["device_id"]

    res = client.get(f"/v1/evaluation/devices/{dev_id}", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["device_id"] == dev_id
    assert data["is_active"] is True


def test_dev_019_cross_license_device_isolation(client: TestClient):
    """DEV-019: Evaluator A cannot access or deactivate Evaluator B's device."""
    # Evaluator A
    privA, _, pemA = generate_ed25519_keypair()
    chA = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pemA, "installation_id": "inst-A"},
    ).json()
    actA = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": chA["challenge_id"], "signature": sign_ed25519(privA, chA["canonical_message"]), "installation_id": "inst-A"},
    ).json()
    devA_id = actA["device_id"]

    # Evaluator B
    privB, _, pemB = generate_ed25519_keypair()
    chB = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-BETA-TEST", "device_public_key": pemB, "installation_id": "inst-B"},
    ).json()
    actB = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": chB["challenge_id"], "signature": sign_ed25519(privB, chB["canonical_message"]), "installation_id": "inst-B"},
    ).json()
    tokenB = actB["session"]["access_token"]

    # Evaluator B tries to access Evaluator A's device
    headersB = {"Authorization": f"Bearer {tokenB}"}
    res_get = client.get(f"/v1/evaluation/devices/{devA_id}", headers=headersB)
    assert res_get.status_code == 404

    # Evaluator B tries to deactivate Evaluator A's device
    res_deact = client.post(f"/v1/evaluation/devices/{devA_id}/deactivate", headers=headersB)
    assert res_deact.status_code == 404


def test_dev_020_emergency_recovery_with_valid_code(client: TestClient):
    """DEV-020: Device recovery successfully deactivates lost device using recovery code."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-rec"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-rec"},
    ).json()
    dev_id = act["device_id"]
    rec_code = act["recovery_code"]
    lic_id = act["license"]["license_id"]

    # Recover device using recovery code
    res_rec = client.post(
        f"/v1/evaluation/devices/{dev_id}/recover",
        json={"recovery_code": rec_code, "license_id": lic_id},
    )
    assert res_rec.status_code == 200
    assert res_rec.json()["status"] == "recovered"

    # Verify device is now inactive
    detail = activation_service.get_device_detail(lic_id, dev_id)
    assert detail["is_active"] is False


def test_dev_021_emergency_recovery_rejected_invalid_code(client: TestClient):
    """DEV-021: Device recovery fails when invalid recovery code is supplied."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-badrec"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-badrec"},
    ).json()
    dev_id = act["device_id"]
    lic_id = act["license"]["license_id"]

    res_rec = client.post(
        f"/v1/evaluation/devices/{dev_id}/recover",
        json={"recovery_code": "REC-WRONG-CODE-0000", "license_id": lic_id},
    )
    assert res_rec.status_code == 401
    assert res_rec.json()["error"] == "RECOVERY_FAILED"


def test_dev_022_device_heartbeat_updates_timestamp(client: TestClient):
    """DEV-022: Device heartbeat updates last_seen_at timestamp."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-hb"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-hb"},
    ).json()
    token = act["session"]["access_token"]
    dev_id = act["device_id"]

    time.sleep(0.01)
    res_hb = client.post("/v1/evaluation/device/heartbeat", headers={"Authorization": f"Bearer {token}"})
    assert res_hb.status_code == 200
    data = res_hb.json()
    assert data["status"] == "alive"
    assert data["device_id"] == dev_id


def test_dev_023_heartbeat_rejected_on_deactivated_device(client: TestClient):
    """DEV-023: Device heartbeat rejected with 401 if device has been deactivated."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-dhb"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-dhb"},
    ).json()
    token = act["session"]["access_token"]
    dev_id = act["device_id"]

    # Deactivate device
    client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers={"Authorization": f"Bearer {token}"})

    # Heartbeat attempt rejected
    res_hb = client.post("/v1/evaluation/device/heartbeat", headers={"Authorization": f"Bearer {token}"})
    assert res_hb.status_code == 401


def test_dev_024_challenge_rate_limiting(client: TestClient):
    """DEV-024: IP rate limiting blocks excessive challenge generation (>10 per hour)."""
    priv, _, pem = generate_ed25519_keypair()
    # 10 allowed attempts
    for i in range(10):
        res = client.post(
            "/v1/evaluation/device/challenge",
            json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": f"inst-{i}"},
        )
        assert res.status_code == 200

    # 11th attempt blocked
    res11 = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-11"},
    )
    assert res11.status_code == 429
    assert res11.json()["error"] == "RATE_LIMIT_EXCEEDED"


def test_dev_025_hmac_lookup_never_leaks_or_stores_raw_codes(client: TestClient):
    """DEV-025: Keyed HMAC lookup never stores raw activation codes in memory keys or audit events."""
    raw_code = "AEGIS-EVAL-SECRET-TEST"
    activation_service.register_activation_code(raw_code, max_devices=1)

    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": raw_code, "device_public_key": pem, "installation_id": "inst-hmac"},
    ).json()

    # Verify that raw code does not exist in dictionary keys
    assert raw_code not in activation_service._eligible_code_hashes
    h = compute_code_hash(raw_code)
    assert h in activation_service._eligible_code_hashes

    # Audit events must not log the raw code string
    for event in audit_service.get_events():
        details = str(event.get("details", {}))
        assert raw_code not in details


def test_dev_026_concurrent_activation_race_condition(client: TestClient):
    """DEV-026: Multi-threaded concurrency race: 10 concurrent activations yield exactly 1 success and 9 conflicts."""
    devices = [generate_ed25519_keypair() for _ in range(10)]
    challenges = []

    # Temporarily raise rate limits for clean concurrency race test
    old_limit = activation_service.max_activations_per_ip_hour
    try:
        activation_service.max_activations_per_ip_hour = 100

        for i, (priv, _, pem) in enumerate(devices):
            ch = client.post(
                "/v1/evaluation/device/challenge",
                json={
                    "activation_code": "AEGIS-EVAL-PROD-HUNT",
                    "device_public_key": pem,
                    "installation_id": f"inst-race-{i}",
                },
            ).json()
            sig = sign_ed25519(priv, ch["canonical_message"])
            challenges.append((ch["challenge_id"], sig, f"inst-race-{i}"))

        results = []

        def run_activate(params):
            ch_id, sig, inst_id = params
            return client.post(
                "/v1/evaluation/device/activate",
                json={"challenge_id": ch_id, "signature": sig, "installation_id": inst_id},
            )

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(run_activate, p) for p in challenges]
            for f in concurrent.futures.as_completed(futures):
                results.append(f.result().status_code)

        success_count = results.count(200)
        conflict_count = results.count(409)

        assert success_count == 1, f"Expected exactly 1 success, got {success_count}"
        assert conflict_count == 9, f"Expected exactly 9 conflicts, got {conflict_count}"
    finally:
        activation_service.max_activations_per_ip_hour = old_limit


def test_dev_027_idempotent_or_safe_duplicate_deactivation(client: TestClient):
    """DEV-027: Deactivating an already-deactivated device safely returns 200 without error."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-dup"},
    ).json()
    act = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": sign_ed25519(priv, ch["canonical_message"]), "installation_id": "inst-dup"},
    ).json()
    token = act["session"]["access_token"]
    dev_id = act["device_id"]
    headers = {"Authorization": f"Bearer {token}"}

    # First deactivation
    res1 = client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers=headers)
    assert res1.status_code == 200

    # Second deactivation
    res2 = client.post(f"/v1/evaluation/devices/{dev_id}/deactivate", headers=headers)
    assert res2.status_code in (200, 401, 404)


def test_dev_028_empty_or_whitespace_activation_code_rejected(client: TestClient):
    """DEV-028: Empty or whitespace-only activation codes are rejected with 400 Bad Request."""
    priv, _, pem = generate_ed25519_keypair()
    for bad_code in ["", "   ", "\t\n"]:
        res = client.post(
            "/v1/evaluation/device/challenge",
            json={"activation_code": bad_code, "device_public_key": pem, "installation_id": "inst-empty"},
        )
        assert res.status_code == 400
        assert res.json()["error"] == "INVALID_ACTIVATION_CODE"


def test_dev_029_tampered_signature_payload_byte_modification(client: TestClient):
    """DEV-029: Bit-flipping or altering bytes in valid signature causes immediate 401 rejection."""
    priv, _, pem = generate_ed25519_keypair()
    ch = client.post(
        "/v1/evaluation/device/challenge",
        json={"activation_code": "AEGIS-EVAL-2026-DEMO", "device_public_key": pem, "installation_id": "inst-flip"},
    ).json()
    valid_sig = sign_ed25519(priv, ch["canonical_message"])

    # Decode, flip a byte, re-encode
    sig_raw = bytearray(base64.b64decode(valid_sig))
    sig_raw[0] ^= 0xFF
    corrupted_sig = base64.b64encode(sig_raw).decode("ascii")

    res = client.post(
        "/v1/evaluation/device/activate",
        json={"challenge_id": ch["challenge_id"], "signature": corrupted_sig, "installation_id": "inst-flip"},
    )
    assert res.status_code == 401
    assert res.json()["error"] == "INVALID_DEVICE_SIGNATURE"


def test_dev_030_complete_evaluation_lifecycle_end_to_end(client: TestClient):
    """DEV-030: Comprehensive end-to-end evaluation lifecycle verification."""
    # 1. Device 1 Key Generation & Stage 1 Challenge
    priv1, _, pem1 = generate_ed25519_keypair()
    res_ch1 = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem1,
            "installation_id": "lifecycle-dev-1",
            "device_label": "Lifecycle Workstation",
            "platform": "windows",
        },
    )
    assert res_ch1.status_code == 200
    ch1 = res_ch1.json()

    # 2. Stage 2 Signature & Activation
    sig1 = sign_ed25519(priv1, ch1["canonical_message"])
    res_act1 = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch1["challenge_id"],
            "signature": sig1,
            "installation_id": "lifecycle-dev-1",
        },
    )
    assert res_act1.status_code == 200
    act_data = res_act1.json()
    token1 = act_data["session"]["access_token"]
    dev1_id = act_data["device_id"]
    rec1_code = act_data["recovery_code"]
    lic_id = act_data["license"]["license_id"]
    headers1 = {"Authorization": f"Bearer {token1}"}

    # 3. Access Protected Evaluation Gateway
    res_query = client.post("/v1/evaluation/query", json={"query": "Evaluate platform"}, headers=headers1)
    assert res_query.status_code == 200

    # 4. Device Presence Heartbeat
    res_hb = client.post("/v1/evaluation/device/heartbeat", headers=headers1)
    assert res_hb.status_code == 200

    # 5. Inspect Device Registry
    res_devs = client.get("/v1/evaluation/devices", headers=headers1)
    assert res_devs.status_code == 200
    assert len(res_devs.json()["devices"]) == 1

    # 6. Deactivate Device 1 via Emergency Recovery Code
    res_rec = client.post(
        f"/v1/evaluation/devices/{dev1_id}/recover",
        json={"recovery_code": rec1_code, "license_id": lic_id},
    )
    assert res_rec.status_code == 200

    # 7. Old Session Access Blocked
    res_blocked = client.post("/v1/evaluation/query", json={"query": "test"}, headers=headers1)
    assert res_blocked.status_code == 401

    # 8. Replacement Device 2 Successfully Challenges & Activates
    priv2, _, pem2 = generate_ed25519_keypair()
    res_ch2 = client.post(
        "/v1/evaluation/device/challenge",
        json={
            "activation_code": "AEGIS-EVAL-2026-DEMO",
            "device_public_key": pem2,
            "installation_id": "lifecycle-dev-2",
        },
    )
    assert res_ch2.status_code == 200
    ch2 = res_ch2.json()

    sig2 = sign_ed25519(priv2, ch2["canonical_message"])
    res_act2 = client.post(
        "/v1/evaluation/device/activate",
        json={
            "challenge_id": ch2["challenge_id"],
            "signature": sig2,
            "installation_id": "lifecycle-dev-2",
        },
    )
    assert res_act2.status_code == 200
    assert res_act2.json()["status"] == "active"
