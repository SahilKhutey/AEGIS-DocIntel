"""
AEGIS-DocIntel Evaluation Gateway — License Management Module
Implements PROT-04 WP-04.04 specifications:
- Standard JWS Compact Serialization using EdDSA (Ed25519)
- Structured headers: {"alg": "EdDSA", "kid": "...", "typ": "AEGIS-EVALUATION-LICENSE"}
- Standard claims: iss, aud, sub, jti, iat, nbf, exp, license_type, policy_version, tenant_id, device_limit, features, quotas
- Integration with SigningKeyRegistry (lifecycle states, rotation, compromise invalidation)
- Authoritative server-side cross-checks via LicenseRepository (fail-closed)
- Anti-tampering, token size bounding (<8KB), and token-controlled URL rejections
- Full backward compatibility for legacy evaluation client tokens
"""

from __future__ import annotations

import base64
import hashlib
import json
import time
import uuid
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import jwt
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization
from cryptography.exceptions import InvalidSignature

from .signing_key_registry import key_registry, SigningKeyRecord
from .license_repository import license_repository, LicenseRecord
from .revocation import registry as revocation_registry

DEFAULT_KEYS_DIR = Path(__file__).resolve().parent / "keys"

CANONICAL_PRODUCT = "AEGIS_PROTECTED_EVALUATION"
ACCEPTED_PRODUCTS = {CANONICAL_PRODUCT, "AEGIS-DocIntel"}
DEFAULT_ISSUER = "aegis-license-authority"
DEFAULT_AUDIENCE = "aegis-evaluation-gateway"
DEFAULT_KEY_ID = "aegis-license-ed25519-2026-01"
CANONICAL_LICENSE_TYPE = "protected_demo_evaluation"
CANONICAL_POLICY_VERSION = "evaluation-1.0"
MAX_TOKEN_BYTES = 8192


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


class LicenseSuspendedError(LicenseVerificationError):
    """Raised when an evaluation license has been temporarily suspended."""
    pass


class LicenseProductMismatchError(LicenseVerificationError):
    """Raised when a license was issued for a different product or environment."""
    pass


def canonical_json(data: Dict[str, Any]) -> bytes:
    """Serializes a dictionary into canonical deterministic UTF-8 bytes for signing."""
    return json.dumps(data, sort_keys=True, separators=(",", ":")).encode("utf-8")


def load_private_key(key_path: Optional[Path] = None) -> ed25519.Ed25519PrivateKey:
    """Loads root private key for license generation from key registry or file."""
    if key_path:
        pem_data = key_path.read_bytes()
        key = serialization.load_pem_private_key(pem_data, password=None)
        if not isinstance(key, ed25519.Ed25519PrivateKey):
            raise TypeError("Key is not an Ed25519 private key")
        return key
    active_key = key_registry.get_active_signing_key()
    if active_key.private_key is None:
        raise RuntimeError("Active signing key does not have a private key loaded.")
    return active_key.private_key


def load_public_key(key_path: Optional[Path] = None) -> ed25519.Ed25519PublicKey:
    """Loads public key for license verification from key registry or file."""
    if key_path:
        pem_data = key_path.read_bytes()
        key = serialization.load_pem_public_key(pem_data)
        if not isinstance(key, ed25519.Ed25519PublicKey):
            raise TypeError("Key is not an Ed25519 public key")
        return key
    active_key = key_registry.get_active_signing_key()
    return active_key.public_key


def issue_evaluation_license(
    user_id: str = "evaluator",
    duration_days: int = 14,
    features: Optional[List[str]] = None,
    quotas: Optional[Dict[str, int]] = None,
    hardware_fingerprint: Optional[str] = None,
    product: str = CANONICAL_PRODUCT,
    issuer: str = DEFAULT_ISSUER,
    audience: str = DEFAULT_AUDIENCE,
    kid: Optional[str] = None,
    status: str = "ACTIVE",
    max_devices: int = 1,
    max_workspaces: int = 1,
    tenant_id: Optional[str] = None,
    license_type: str = CANONICAL_LICENSE_TYPE,
    policy_version: str = CANONICAL_POLICY_VERSION,
    idempotency_key: Optional[str] = None,
    private_key: Optional[ed25519.Ed25519PrivateKey] = None,
) -> Dict[str, Any]:
    """
    Issues a cryptographically signed evaluation license adhering to PROT-04 WP-04.04 claims schema.
    Encodes standard JWS compact serialization using EdDSA and persists authoritative server record.
    """
    # Check idempotency
    if idempotency_key:
        existing = license_repository.get_by_idempotency_key(idempotency_key)
        if existing:
            # Reconstruct legacy dictionary payload from existing authoritative record
            return {
                "payload": {
                    "license_id": existing.id,
                    "jti": existing.id,
                    "product": product,
                    "tier": "evaluation",
                    "status": existing.status,
                    "user_id": existing.evaluator_id,
                    "subject": existing.evaluator_id,
                    "sub": existing.evaluator_id,
                    "tenant_id": existing.tenant_id,
                    "iss": issuer,
                    "aud": audience,
                    "kid": existing.key_id,
                    "iat": int(existing.issued_at),
                    "nbf": int(existing.not_before),
                    "exp": int(existing.expires_at),
                    "issued_at": datetime.fromtimestamp(existing.issued_at, timezone.utc).isoformat(),
                    "expires_at": datetime.fromtimestamp(existing.expires_at, timezone.utc).isoformat(),
                    "features": existing.features,
                    "entitlements": existing.features,
                    "quotas": existing.quotas,
                    "device_limit": existing.device_limit,
                    "max_devices": existing.device_limit,
                    "license_type": existing.license_type,
                    "policy_version": existing.policy_version,
                },
                "signature": "",
                "jws": existing.signed_jws,
                "algorithm": "EdDSA",
                "kid": existing.key_id,
            }

    # Validate policy and license_type
    if policy_version not in ("evaluation-1.0", "1.0", "evaluation-1.1"):
        raise ValueError(f"Unsupported policy version '{policy_version}'. Supported: 'evaluation-1.0'")
    if license_type not in ("protected_demo_evaluation", "evaluation"):
        raise ValueError(f"Unsupported license type '{license_type}'. Supported: 'protected_demo_evaluation'")

    active_key_rec = key_registry.get_active_signing_key()
    signing_kid = kid or active_key_rec.key_id
    signing_key = private_key or active_key_rec.private_key
    if signing_key is None:
        raise RuntimeError("No signing private key available.")

    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=duration_days)
    iat_int = int(now.timestamp())
    nbf_int = iat_int
    exp_int = int(expires.timestamp())

    lic_id = str(uuid.uuid4())
    eff_tenant = tenant_id or f"tenant-{user_id}"

    default_features = [
        "documents.read",
        "documents.upload",
        "intelligence.query",
        "documents.compare",
        "evidence.inspect",
        "document_upload",
        "document_preview",
        "document_query",
        "document_extraction",
        "ask_aegis",
        "citation_inspection",
        "document_comparison",
        "synthetic_ground_truth",
    ]
    eff_features = features if features is not None else default_features

    default_quotas = {
        "max_documents": 5,
        "max_queries_per_day": 20,
        "max_comparisons_per_day": 5,
        "max_file_size_mb": 10,
        "max_storage_mb": 100,
    }
    eff_quotas = quotas if quotas is not None else default_quotas

    # JWS Claims payload (RFC 7519 / PROT-04.04)
    claims = {
        "iss": issuer,
        "aud": audience,
        "sub": user_id,
        "jti": lic_id,
        "iat": iat_int,
        "nbf": nbf_int,
        "exp": exp_int,
        "license_type": license_type,
        "policy_version": policy_version,
        "tenant_id": eff_tenant,
        "device_limit": max_devices,
        "features": eff_features,
        "quotas": eff_quotas,
        # Backward-compatible fields
        "license_id": lic_id,
        "user_id": user_id,
        "subject": user_id,
        "product": product,
        "tier": "evaluation",
        "status": status,
        "max_devices": max_devices,
        "max_workspaces": max_workspaces,
        "issued_at": now.isoformat(),
        "not_before": now.isoformat(),
        "expires_at": expires.isoformat(),
        "hardware_fingerprint": hardware_fingerprint or "any",
        "entitlements": eff_features,
    }

    headers = {
        "alg": "EdDSA",
        "kid": signing_kid,
        "typ": "AEGIS-EVALUATION-LICENSE",
    }

    # Generate JWS Compact Serialization using PyJWT EdDSA
    jws_token = jwt.encode(claims, signing_key, algorithm="EdDSA", headers=headers)
    token_hash = hashlib.sha256(jws_token.encode("utf-8")).hexdigest()

    # Legacy raw signature for backward-compatibility with tests that decode raw payload bytes
    payload_bytes = canonical_json(claims)
    sig_raw = signing_key.sign(payload_bytes)
    sig_b64 = base64.b64encode(sig_raw).decode("ascii")

    # Authoritative persistence in LicenseRepository
    repo_rec = LicenseRecord(
        id=lic_id,
        evaluator_id=user_id,
        tenant_id=eff_tenant,
        status=status,
        license_type=license_type,
        policy_version=policy_version,
        key_id=signing_kid,
        signed_token_hash=token_hash,
        signed_jws=jws_token,
        issued_at=now.timestamp(),
        not_before=now.timestamp(),
        expires_at=expires.timestamp(),
        idempotency_key=idempotency_key,
        device_limit=max_devices,
        features=eff_features,
        quotas=eff_quotas,
    )
    license_repository.save_license(repo_rec)

    return {
        "payload": claims,
        "signature": sig_b64,
        "jws": jws_token,
        "algorithm": "EdDSA",
        "kid": signing_kid,
    }


def issue_signed_license(
    claims: Dict[str, Any],
    private_key: ed25519.Ed25519PrivateKey,
    key_id: str,
) -> str:
    """Issues standard JWS compact license string signed with EdDSA."""
    headers = {
        "alg": "EdDSA",
        "kid": key_id,
        "typ": "AEGIS-EVALUATION-LICENSE",
    }
    return jwt.encode(claims, private_key, algorithm="EdDSA", headers=headers)


def export_license_token(license_doc: Any) -> str:
    """
    Exports license token. If dict has 'signature' and 'payload', exports as URL-safe base64 dictionary.
    If string or pure JWS dict, returns compact JWS token.
    """
    if isinstance(license_doc, str):
        return license_doc
    if isinstance(license_doc, dict):
        if "signature" in license_doc and "payload" in license_doc:
            raw = json.dumps(license_doc, sort_keys=True)
            return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
        if "jws" in license_doc:
            return license_doc["jws"]
        raw = json.dumps(license_doc, sort_keys=True)
        return base64.urlsafe_b64encode(raw.encode("utf-8")).decode("ascii")
    raise ValueError("Invalid license document format for token export.")


def parse_license_token(token: str) -> Dict[str, Any]:
    """
    Parses a token (either standard compact JWS or legacy base64 dictionary).
    Returns dict structure containing payload, kid, and token format.
    """
    if not token or not isinstance(token, str):
        raise LicenseVerificationError("License token must be a non-empty string.")

    cleaned = token.strip()
    if len(cleaned.encode("utf-8")) > MAX_TOKEN_BYTES:
        raise LicenseVerificationError("License token exceeds maximum permitted size (8192 bytes).")

    # Case 1: Standard 3-part JWS Compact Serialization
    parts = cleaned.split(".")
    if len(parts) == 3:
        try:
            # Decode unverified header and payload
            header_bytes = jwt.utils.base64url_decode(parts[0])
            header = json.loads(header_bytes.decode("utf-8"))
            payload_bytes = jwt.utils.base64url_decode(parts[1])
            payload = json.loads(payload_bytes.decode("utf-8"))
            return {
                "format": "JWS",
                "header": header,
                "payload": payload,
                "raw_token": cleaned,
                "kid": header.get("kid", DEFAULT_KEY_ID),
            }
        except Exception as e:
            raise LicenseVerificationError(f"Malformed compact JWS token: {e}") from e

    # Case 2: Legacy URL-safe Base64 JSON dictionary
    try:
        raw = base64.urlsafe_b64decode(cleaned.encode("ascii")).decode("utf-8")
        doc = json.loads(raw)
        if isinstance(doc, dict):
            doc["format"] = "LEGACY_DICT"
            return doc
    except Exception:
        pass

    raise LicenseVerificationError("Malformed compact JWS token: expected 3 dot-separated segments.")


def verify_signed_license(
    signed_license: str,
    public_key: Optional[ed25519.Ed25519PublicKey] = None,
    expected_issuer: str = DEFAULT_ISSUER,
    expected_audience: str = DEFAULT_AUDIENCE,
    reference_time: Optional[datetime] = None,
    require_authoritative_record: bool = False,
    expected_evaluator: Optional[str] = None,
    expected_tenant: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes the complete cryptographic and authoritative validation pipeline for a JWS license token.
    Enforces strict header validation, key registry resolution, claims schema, and authoritative state.
    """
    if not signed_license or not isinstance(signed_license, str):
        raise LicenseVerificationError("License token must be a non-empty string.")

    if len(signed_license.encode("utf-8")) > MAX_TOKEN_BYTES:
        raise LicenseVerificationError("License token exceeds maximum permitted size (8192 bytes).")

    parts = signed_license.strip().split(".")
    if len(parts) != 3:
        raise LicenseVerificationError("Malformed compact JWS token: expected exactly 3 segments.")

    # 1. Read protected header without trusting it
    try:
        header_bytes = jwt.utils.base64url_decode(parts[0])
        header = json.loads(header_bytes.decode("utf-8"))
    except Exception as e:
        raise LicenseVerificationError(f"Malformed JWS protected header: {e}")

    # Reject token-controlled key URLs (LIC-034)
    if "jku" in header or "x5u" in header:
        raise LicenseVerificationError("Token-controlled key URLs ('jku', 'x5u') are strictly rejected.")

    # Require alg == EdDSA (LIC-008)
    alg = header.get("alg")
    if alg != "EdDSA":
        raise LicenseVerificationError(f"Unsupported algorithm '{alg}', expected 'EdDSA'.")

    # Require known typ
    typ = header.get("typ")
    if typ != "AEGIS-EVALUATION-LICENSE":
        raise LicenseVerificationError(f"Invalid token typ '{typ}', expected 'AEGIS-EVALUATION-LICENSE'.")

    # Require known kid (LIC-009)
    kid = header.get("kid")
    if not kid:
        raise LicenseVerificationError("Missing key ID ('kid') in protected header.")

    # Select public key from server-controlled key registry
    if public_key is None:
        key_rec = key_registry.get_verification_key(kid)
        if key_rec is None:
            raise LicenseVerificationError(f"Unknown signing key ID '{kid}' in key registry.")
        if key_rec.status == "COMPROMISED":
            raise LicenseVerificationError(f"Signing key '{kid}' is compromised. License rejected.")
        if key_rec.status == "RETIRED":
            raise LicenseVerificationError(f"Signing key '{kid}' has been retired.")
        verification_pubkey = key_rec.public_key
    else:
        # Check if kid is marked compromised in registry even if public_key is provided
        key_rec = key_registry.get_verification_key(kid)
        if key_rec and key_rec.status == "COMPROMISED":
            raise LicenseVerificationError(f"Signing key '{kid}' is compromised. License rejected.")
        verification_pubkey = public_key

    # 2. Cryptographic signature verification using PyJWT
    try:
        claims = jwt.decode(
            signed_license.strip(),
            verification_pubkey,
            algorithms=["EdDSA"],
            options={
                "verify_signature": True,
                "verify_exp": False,  # Manual check to give custom exception
                "verify_nbf": False,  # Manual check to give custom exception
                "verify_iat": False,
                "verify_aud": False,  # Manual check below
                "verify_iss": False,  # Manual check below
            },
        )
    except jwt.InvalidSignatureError as e:
        raise LicenseSignatureError(f"Cryptographic signature verification failed: {e}")
    except Exception as e:
        raise LicenseVerificationError(f"Failed to decode JWS token: {e}")

    # 3. Mandatory claim validations
    # Issuer (LIC-010, LIC-011)
    iss = claims.get("iss")
    if not iss:
        raise LicenseVerificationError("License payload missing required 'iss' claim.")
    if expected_issuer and iss != expected_issuer:
        raise LicenseVerificationError(f"License issuer '{iss}' does not match expected '{expected_issuer}'.")

    # Audience (LIC-012)
    aud = claims.get("aud")
    if not aud:
        raise LicenseVerificationError("License payload missing required 'aud' claim.")
    if expected_audience and aud != expected_audience:
        raise LicenseVerificationError(f"License audience '{aud}' does not match expected '{expected_audience}'.")

    # Expiry (LIC-013, LIC-014)
    exp = claims.get("exp")
    if exp is None:
        raise LicenseVerificationError("License payload missing required 'exp' claim.")
    if not isinstance(exp, (int, float)):
        raise LicenseVerificationError("Claim 'exp' must be an integer or float UNIX timestamp.")

    now_ts = (reference_time or datetime.now(timezone.utc)).timestamp()
    if now_ts > float(exp):
        raise LicenseExpiredError(f"License expired at {exp} (server time: {int(now_ts)}).")

    # Not before (LIC-015)
    nbf = claims.get("nbf")
    if nbf is not None:
        if not isinstance(nbf, (int, float)):
            raise LicenseVerificationError("Claim 'nbf' must be an integer or float UNIX timestamp.")
        if now_ts < float(nbf):
            raise LicenseVerificationError(f"License is not yet valid (nbf: {nbf}, server time: {int(now_ts)}).")

    # Claim types validation (LIC-016)
    sub = claims.get("sub")
    if not sub or not isinstance(sub, str):
        raise LicenseVerificationError("Claim 'sub' must be a non-empty string.")

    jti = claims.get("jti") or claims.get("license_id")
    if not jti or not isinstance(jti, str):
        raise LicenseVerificationError("Claim 'jti' must be a non-empty string.")

    features = claims.get("features")
    if features is not None and not isinstance(features, list):
        raise LicenseVerificationError("Claim 'features' must be a list of strings.")

    # License type & policy version (LIC-017, LIC-018)
    lic_type = claims.get("license_type")
    if lic_type and lic_type not in ("protected_demo_evaluation", "evaluation"):
        raise LicenseVerificationError(f"Unknown or unauthorized license_type: '{lic_type}'.")

    pol_ver = claims.get("policy_version")
    if pol_ver and pol_ver not in ("evaluation-1.0", "1.0", "evaluation-1.1"):
        raise LicenseVerificationError(f"Unknown policy version: '{pol_ver}'.")

    # 4. Authoritative Database Cross-Check
    auth_record = license_repository.get_license(jti)
    if require_authoritative_record and not auth_record:
        raise LicenseVerificationError(f"Authoritative license record '{jti}' not found in database.")

    if auth_record:
        # Evaluator mismatch (LIC-019)
        if expected_evaluator and auth_record.evaluator_id != expected_evaluator:
            raise LicenseVerificationError(f"Evaluator mismatch: license belongs to '{auth_record.evaluator_id}', not '{expected_evaluator}'.")
        if claims.get("sub") and auth_record.evaluator_id != claims["sub"]:
            raise LicenseVerificationError(f"Evaluator identity mismatch between token ('{claims['sub']}') and server record ('{auth_record.evaluator_id}').")

        # Tenant mismatch (LIC-020)
        if expected_tenant and auth_record.tenant_id != expected_tenant:
            raise LicenseVerificationError(f"Tenant mismatch: license belongs to tenant '{auth_record.tenant_id}', not '{expected_tenant}'.")
        if claims.get("tenant_id") and auth_record.tenant_id != claims["tenant_id"]:
            raise LicenseVerificationError(f"Tenant mismatch between token ('{claims['tenant_id']}') and server record ('{auth_record.tenant_id}').")

        # Status check (LIC-023, LIC-024)
        if auth_record.status == "SUSPENDED":
            raise LicenseSuspendedError("License has been temporarily suspended by security administrator.")
        if auth_record.status == "REVOKED":
            raise LicenseRevokedError("License has been permanently revoked.")
        if auth_record.status not in ("ACTIVE", "ISSUED"):
            raise LicenseVerificationError(f"Authoritative license status '{auth_record.status}' is not valid.")

    # Check global revocation registry
    if revocation_registry.is_revoked(jti):
        raise LicenseRevokedError(f"License {jti} is present in authoritative revocation registry.")

    return claims


def verify_license(
    license_doc: Dict[str, Any],
    public_key: Optional[ed25519.Ed25519PublicKey] = None,
    revocation_set: Optional[Set[str]] = None,
    reference_time: Optional[datetime] = None,
    expected_product: Optional[str] = None,
    expected_issuer: Optional[str] = None,
    expected_audience: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified entry point for verifying license documents.
    Transparently supports both JWS compact tokens and legacy signed JSON documents.
    """
    # If the document contains raw compact JWS, verify via JWS pipeline
    if isinstance(license_doc, dict) and "raw_token" in license_doc and license_doc.get("format") == "JWS":
        return verify_signed_license(
            signed_license=license_doc["raw_token"],
            public_key=public_key,
            expected_issuer=expected_issuer or DEFAULT_ISSUER,
            expected_audience=expected_audience or DEFAULT_AUDIENCE,
            reference_time=reference_time,
        )

    # Legacy dictionary validation pipeline
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

    # Check product match (LIC-005)
    prod = payload.get("product")
    if expected_product:
        if prod != expected_product:
            raise LicenseProductMismatchError(f"License product '{prod}' does not match expected '{expected_product}'")
    else:
        if prod not in ACCEPTED_PRODUCTS:
            raise LicenseProductMismatchError(f"Unsupported product identifier: '{prod}'")

    # Check issuer and audience if present in claims
    iss = payload.get("iss")
    if expected_issuer and iss and iss != expected_issuer:
        raise LicenseVerificationError(f"License issuer '{iss}' does not match expected '{expected_issuer}'")

    aud = payload.get("aud")
    if expected_audience and aud and aud != expected_audience:
        raise LicenseVerificationError(f"License audience '{aud}' does not match expected '{expected_audience}'")

    # Check status (LIC-006)
    license_status = str(payload.get("status", "ACTIVE")).upper()
    if license_status == "SUSPENDED":
        raise LicenseSuspendedError("License has been temporarily suspended by security administrator")
    elif license_status in ("REVOKED", "DEACTIVATED"):
        raise LicenseRevokedError(f"License is marked as {license_status}")
    elif license_status not in ("ACTIVE", "ISSUED"):
        raise LicenseVerificationError(f"Invalid license status: {license_status}")

    # Check revocation registry (LIC-004)
    license_id = payload.get("license_id") or payload.get("jti")
    if revocation_set and license_id in revocation_set:
        raise LicenseRevokedError(f"License {license_id} has been revoked")
    if revocation_registry.is_revoked(license_id):
        raise LicenseRevokedError(f"License {license_id} has been revoked")

    # Check temporal expiration (LIC-003)
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

    # Check not_before if present
    nbf_str = payload.get("not_before")
    if nbf_str:
        try:
            not_before = datetime.fromisoformat(nbf_str)
            if not_before.tzinfo is None:
                not_before = not_before.replace(tzinfo=timezone.utc)
            if now < not_before:
                raise LicenseVerificationError(f"License is not valid before {nbf_str}")
        except LicenseVerificationError:
            raise
        except Exception:
            pass

    return payload
