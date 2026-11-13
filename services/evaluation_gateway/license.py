"""
AEGIS-DocIntel Evaluation Gateway — License Management Module
Provides cryptographic issuance, serialization, and verification of Ed25519-signed evaluation licenses.
"""

from __future__ import annotations

import base64
import json
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

DEFAULT_KEYS_DIR = Path(__file__).resolve().parent / "keys"

class LicenseVerificationError(Exception):
    """Raised when an evaluation license fails cryptographic or temporal validation."""
    pass

class LicenseExpiredError(LicenseVerificationError):
    """Raised when an evaluation license has passed its validity window."""
    pass

class LicenseSignatureError(LicenseVerificationError):
    """Raised when an evaluation license signature does not match public key."""
    pass

class LicenseRevokedError(LicenseVerificationError):
    """Raised when an evaluation license has been explicitly revoked."""
    pass


def canonical_json(data: Dict[str, Any]) -> bytes:
    """Serializes a dictionary into canonical deterministic UTF-8 bytes for signing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_private_key(key_path: Optional[Path] = None) -> ed25519.Ed25519PrivateKey:
    """Loads root private key for license generation (server-side only)."""
    p = key_path or (DEFAULT_KEYS_DIR / "private-key.pem")
    if not p.exists():
        raise FileNotFoundError(f"Root private key not found at: {p}")
    pem_data = p.read_bytes()
    key = serialization.load_pem_private_key(pem_data, password=None)
    if not isinstance(key, ed25519.Ed25519PrivateKey):
        raise TypeError("Key is not an Ed25519 private key")
    return key


def load_public_key(key_path: Optional[Path] = None) -> ed25519.Ed25519PublicKey:
    """Loads public key for license verification."""
    p = key_path or (DEFAULT_KEYS_DIR / "public-key.pem")
    if not p.exists():
        raise FileNotFoundError(f"Public key not found at: {p}")
    pem_data = p.read_bytes()
    key = serialization.load_pem_public_key(pem_data)
    if not isinstance(key, ed25519.Ed25519PublicKey):
        raise TypeError("Key is not an Ed25519 public key")
    return key


def issue_evaluation_license(
    user_id: str = "evaluator",
    duration_days: int = 14,
    features: Optional[List[str]] = None,
    quotas: Optional[Dict[str, int]] = None,
    hardware_fingerprint: Optional[str] = None,
    private_key: Optional[ed25519.Ed25519PrivateKey] = None,
) -> Dict[str, Any]:
    """
    Issues a cryptographically signed evaluation license.
    """
    if private_key is None:
        private_key = load_private_key()

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=duration_days)

    default_features = [
        "document_upload",
        "document_extraction",
        "ask_aegis",
        "citation_inspection",
        "document_comparison",
        "synthetic_ground_truth"
    ]
    default_quotas = {
        "max_documents": 5,
        "max_queries_per_day": 20,
        "max_comparisons_per_day": 5
    }

    payload = {
        "license_id": str(uuid.uuid4()),
        "product": "AEGIS-DocIntel",
        "tier": "evaluation",
        "version": "1.1.0",
        "user_id": user_id,
        "issued_at": now.isoformat(),
        "expires_at": expires.isoformat(),
        "hardware_fingerprint": hardware_fingerprint or "any",
        "features": features if features is not None else default_features,
        "quotas": quotas if quotas is not None else default_quotas
    }

    payload_bytes = canonical_json(payload)
    signature = private_key.sign(payload_bytes)
    sig_b64 = base64.b64encode(signature).decode("ascii")

    return {
        "payload": payload,
        "signature": sig_b64
    }


def export_license_token(license_doc: Dict[str, Any]) -> str:
    """Exports license document as a compact base64 URL-safe token."""
    raw = json.dumps(license_doc, sort_keys=True)
    return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")


def parse_license_token(token: str) -> Dict[str, Any]:
    """Parses a base64 license token into its JSON document."""
    try:
        raw = base64.urlsafe_b64decode(token.encode("ascii")).decode("utf-8")
        return json.loads(raw)
    except Exception as e:
        raise LicenseVerificationError(f"Invalid license token format: {e}") from e


def verify_license(
    license_doc: Dict[str, Any],
    public_key: Optional[ed25519.Ed25519PublicKey] = None,
    revocation_set: Optional[set[str]] = None,
    reference_time: Optional[datetime] = None
) -> Dict[str, Any]:
    """
    Cryptographically verifies the license payload against the signature,
    checks expiration date, and checks against the revocation list.
    Returns the validated payload.
    """
    if "payload" not in license_doc or "signature" not in license_doc:
        raise LicenseVerificationError("Malformed license structure: missing payload or signature")

    payload = license_doc["payload"]
    sig_b64 = license_doc["signature"]

    try:
        sig_bytes = base64.b64decode(sig_b64.encode("ascii"))
    except Exception as e:
        raise LicenseSignatureError(f"Invalid base64 signature encoding: {e}") from e

    if public_key is None:
        public_key = load_public_key()

    payload_bytes = canonical_json(payload)
    try:
        public_key.verify(sig_bytes, payload_bytes)
    except InvalidSignature as e:
        raise LicenseSignatureError("Cryptographic signature verification failed: license data has been altered or forged") from e

    # Check revocation
    license_id = payload.get("license_id")
    if revocation_set and license_id in revocation_set:
        raise LicenseRevokedError(f"License {license_id} has been revoked")

    # Check temporal expiration
    now = reference_time or datetime.now(timezone.utc)
    expires_str = payload.get("expires_at")
    if not expires_str:
        raise LicenseVerificationError("License payload missing 'expires_at' timestamp")

    try:
        expires_at = datetime.fromisoformat(expires_str)
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
    except Exception as e:
        raise LicenseVerificationError(f"Invalid 'expires_at' ISO format: {e}") from e

    if now > expires_at:
        raise LicenseExpiredError(f"License expired at {expires_str} (current time: {now.isoformat()})")

    return payload
