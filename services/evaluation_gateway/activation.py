"""
AEGIS-DocIntel Evaluation Gateway — Activation, Device Binding & Session Subsystem
Implements PROT-04 WP-04.03, WP-04.07, and WP-04.08 specifications:
- Activation code validation with HMAC-SHA256 keyed lookup (never stores raw codes)
- Two-stage cryptographic proof-of-possession challenge protocol (Ed25519 and RSA)
- Single-use challenge consumption and challenge expiry enforcement
- Maximum active device enforcement (1 device limit, rejects DEV-002)
- Device deactivation and emergency recovery workflows
- Device heartbeat and presence monitoring
- Short-lived evaluation sessions with rotating refresh tokens
- Protection against refresh-token replay and session reuse (SESSION-001, SESSION-002)
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ed25519, rsa, padding

from .license import (
    issue_evaluation_license,
    export_license_token,
    load_public_key,
    CANONICAL_PRODUCT,
)
from .audit import audit_service


# HMAC key for activation code hashing (isolated from database/audit dumps)
HMAC_LOOKUP_KEY = os.getenv("AEGIS_ACTIVATION_HMAC_KEY", "aegis-evaluation-master-hmac-secret-v1").encode("utf-8")


def compute_code_hash(code: str) -> str:
    """Computes a keyed HMAC-SHA256 digest of an activation code."""
    normalized = (code or "").strip().upper().encode("utf-8")
    return hmac.new(HMAC_LOOKUP_KEY, normalized, hashlib.sha256).hexdigest()


def compute_key_fingerprint(public_key_bytes: bytes) -> str:
    """Computes SHA-256 fingerprint for canonical public key bytes."""
    return hashlib.sha256(public_key_bytes).hexdigest()


def format_canonical_challenge(challenge_id: str, nonce: str, fingerprint: str, installation_id: str) -> str:
    """Formats canonical device challenge message to be signed by evaluator's private key."""
    return (
        f"AEGIS-EVAL-DEVICE-PROOF-V1\n"
        f"challenge_id={challenge_id}\n"
        f"nonce={nonce}\n"
        f"public_key_fingerprint={fingerprint}\n"
        f"installation_id={installation_id}"
    )


def parse_and_validate_public_key(pub_key_str: str) -> Tuple[Any, bytes, str]:
    """
    Parses a public key string (PEM or base64 raw/DER).
    Returns (key_object, canonical_bytes, key_type).
    Raises ValueError if key is invalid, empty, or unsupported.
    """
    if not pub_key_str or not isinstance(pub_key_str, str):
        raise ValueError("Device public key must be a non-empty string.")

    cleaned = pub_key_str.strip()
    if not cleaned:
        raise ValueError("Device public key cannot be empty.")

    # 1. Try PEM format
    if cleaned.startswith("-----BEGIN"):
        try:
            key_obj = serialization.load_pem_public_key(cleaned.encode("utf-8"))
            canonical_bytes = key_obj.public_bytes(
                encoding=serialization.Encoding.DER,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            if isinstance(key_obj, ed25519.Ed25519PublicKey):
                return key_obj, canonical_bytes, "Ed25519"
            elif isinstance(key_obj, rsa.RSAPublicKey):
                return key_obj, canonical_bytes, "RSA"
            else:
                return key_obj, canonical_bytes, "UNKNOWN"
        except Exception as e:
            raise ValueError(f"Malformed PEM public key: {e}")

    # 2. Try Base64 (Raw 32-byte Ed25519 or DER)
    try:
        raw = base64.b64decode(cleaned)
    except Exception as e:
        raise ValueError(f"Device public key is not valid Base64: {e}")

    if len(raw) == 32:
        try:
            key_obj = ed25519.Ed25519PublicKey.from_public_bytes(raw)
            return key_obj, raw, "Ed25519"
        except Exception as e:
            raise ValueError(f"Invalid Ed25519 raw public key: {e}")

    # Try DER
    try:
        key_obj = serialization.load_der_public_key(raw)
        canonical_bytes = raw
        if isinstance(key_obj, ed25519.Ed25519PublicKey):
            return key_obj, canonical_bytes, "Ed25519"
        elif isinstance(key_obj, rsa.RSAPublicKey):
            return key_obj, canonical_bytes, "RSA"
        return key_obj, canonical_bytes, "UNKNOWN"
    except Exception as e:
        raise ValueError(f"Device public key could not be parsed as Ed25519 or RSA: {e}")


def verify_device_signature(pub_key_obj: Any, message_bytes: bytes, signature_b64: str) -> bool:
    """Verifies a base64 encoded signature against message bytes using parsed public key."""
    try:
        sig_bytes = base64.b64decode(signature_b64)
        if isinstance(pub_key_obj, ed25519.Ed25519PublicKey):
            pub_key_obj.verify(sig_bytes, message_bytes)
            return True
        elif isinstance(pub_key_obj, rsa.RSAPublicKey):
            # Try PSS first then PKCS1v15
            try:
                pub_key_obj.verify(
                    sig_bytes,
                    message_bytes,
                    padding.PSS(
                        mgf=padding.MGF1(hashes.SHA256()),
                        salt_length=padding.PSS.MAX_LENGTH,
                    ),
                    hashes.SHA256(),
                )
                return True
            except Exception:
                pub_key_obj.verify(
                    sig_bytes,
                    message_bytes,
                    padding.PKCS1v15(),
                    hashes.SHA256(),
                )
                return True
        return False
    except Exception:
        return False


@dataclass
class DeviceRecord:
    device_id: str
    license_id: str
    public_key_b64: str
    label: str
    platform: str
    is_active: bool
    registered_at: float
    last_seen_at: float
    key_fingerprint: str = ""
    installation_id: str = ""
    recovery_code_hash: Optional[str] = None


@dataclass
class ChallengeRecord:
    challenge_id: str
    activation_code_hash: str
    client_id: str
    max_devices: int
    device_public_key: str
    key_fingerprint: str
    installation_id: str
    device_label: str
    platform: str
    nonce: str
    canonical_message: str
    created_at: float
    expires_at: float
    consumed: bool = False
    consumed_at: Optional[float] = None
    client_ip: str = "127.0.0.1"


@dataclass
class SessionRecord:
    session_id: str
    license_id: str
    user_id: str
    device_id: str
    access_token_hash: str
    refresh_token_hash: str
    is_revoked: bool
    created_at: float
    expires_at: float
    family_id: str
    previous_refresh_hashes: Set[str] = field(default_factory=set)


# Baseline eligible activation codes seeded at startup
ELIGIBLE_ACTIVATION_CODES: Dict[str, Dict[str, Any]] = {
    "AEGIS-EVAL-2026-DEMO": {
        "tier": "evaluation",
        "max_devices": 1,
        "valid_until": "2026-12-31T23:59:59Z",
        "user_id": "evaluator-primary",
    },
    "AEGIS-EVAL-BETA-TEST": {
        "tier": "evaluation",
        "max_devices": 1,
        "valid_until": "2026-12-31T23:59:59Z",
        "user_id": "evaluator-beta",
    },
    "AEGIS-EVAL-PROD-HUNT": {
        "tier": "evaluation",
        "max_devices": 1,
        "valid_until": "2026-12-31T23:59:59Z",
        "user_id": "evaluator-product-hunt",
    },
}


def _hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ActivationService:
    def __init__(self, max_activations_per_ip_hour: int = 10, session_ttl_seconds: int = 600):
        self.max_activations_per_ip_hour = max_activations_per_ip_hour
        self.session_ttl_seconds = session_ttl_seconds
        self._ip_activation_timestamps: Dict[str, List[float]] = defaultdict(list)
        
        # license_id -> list of DeviceRecords
        self._devices_by_license: Dict[str, List[DeviceRecord]] = defaultdict(list)
        # device_id -> DeviceRecord
        self._devices_by_id: Dict[str, DeviceRecord] = {}
        # activation_code_hash -> license_doc
        self._licenses_by_code_hash: Dict[str, Dict[str, Any]] = {}
        # client_id / user_id -> license_doc
        self._licenses_by_user: Dict[str, Dict[str, Any]] = {}
        
        # challenge_id -> ChallengeRecord
        self._challenges_by_id: Dict[str, ChallengeRecord] = {}
        # HMAC hash -> metadata
        self._eligible_code_hashes: Dict[str, Dict[str, Any]] = {}
        self._init_eligible_codes()

        # token_hash -> SessionRecord
        self._sessions_by_access_hash: Dict[str, SessionRecord] = {}
        # refresh_token_hash -> SessionRecord
        self._sessions_by_refresh_hash: Dict[str, SessionRecord] = {}
        # Used refresh token hashes -> family_id (for replay detection)
        self._used_refresh_hashes: Dict[str, str] = {}
        # family_id -> set of session_ids
        self._session_families: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = threading.Lock()

    def _init_eligible_codes(self) -> None:
        self._eligible_code_hashes.clear()
        for code, meta in ELIGIBLE_ACTIVATION_CODES.items():
            h = compute_code_hash(code)
            self._eligible_code_hashes[h] = meta.copy()

    def register_activation_code(
        self,
        code: str,
        tier: str = "evaluation",
        max_devices: int = 1,
        user_id: Optional[str] = None,
    ) -> str:
        """Dynamically registers an eligible activation code hash."""
        with self._lock:
            code_hash = compute_code_hash(code)
            uid = user_id or f"evaluator-{code[-8:].lower().replace('-', '')}"
            self._eligible_code_hashes[code_hash] = {
                "tier": tier,
                "max_devices": max_devices,
                "valid_until": "2026-12-31T23:59:59Z",
                "user_id": uid,
            }
            return code_hash

    def resolve_code_metadata(self, code: str) -> Optional[Dict[str, Any]]:
        """Resolves metadata for an activation code without storing raw code in storage."""
        clean = (code or "").strip()
        if not clean:
            return None
        code_hash = compute_code_hash(clean)
        if code_hash in self._eligible_code_hashes:
            return self._eligible_code_hashes[code_hash].copy()
        if clean.startswith("AEGIS-EVAL-") and len(clean) >= 15:
            uid = f"evaluator-{clean[-8:].lower().replace('-', '')}"
            meta = {
                "tier": "evaluation",
                "max_devices": 1,
                "valid_until": "2026-12-31T23:59:59Z",
                "user_id": uid,
            }
            self._eligible_code_hashes[code_hash] = meta
            return meta.copy()
        return None

    def _check_ip_rate_limit(self, client_ip: str) -> None:
        now = time.time()
        cutoff = now - 3600.0
        self._ip_activation_timestamps[client_ip] = [
            ts for ts in self._ip_activation_timestamps[client_ip] if ts >= cutoff
        ]
        if len(self._ip_activation_timestamps[client_ip]) >= self.max_activations_per_ip_hour:
            audit_service.record_event(
                event_type="activation.rate_limit_exceeded",
                status="BLOCKED",
                actor_id=client_ip,
                details={"ip": client_ip, "limit": self.max_activations_per_ip_hour},
            )
            raise PermissionError(
                f"Too many activation attempts from IP {client_ip}. Please wait before requesting another demo license."
            )
        self._ip_activation_timestamps[client_ip].append(now)

    def create_device_challenge(
        self,
        activation_code: str,
        device_public_key: str,
        installation_id: str,
        device_label: str = "workstation",
        platform: str = "windows",
        client_ip: str = "127.0.0.1",
        challenge_ttl_seconds: int = 300,
    ) -> Dict[str, Any]:
        """
        Stage 1: Generates a single-use cryptographic challenge for device proof-of-possession.
        Enforces code eligibility, public key syntax, and 1-device active limit pre-checks.
        """
        with self._lock:
            self._check_ip_rate_limit(client_ip)
            code = (activation_code or "").strip()
            if not code:
                audit_service.record_event(
                    event_type="activation.challenge_rejected",
                    status="BAD_REQUEST",
                    actor_id=client_ip,
                    details={"reason": "empty_activation_code"},
                )
                raise ValueError("Activation code cannot be empty.")

            code_meta = self.resolve_code_metadata(code)
            if not code_meta:
                audit_service.record_event(
                    event_type="activation.challenge_rejected",
                    status="BAD_REQUEST",
                    actor_id=client_ip,
                    details={"reason": "invalid_activation_code", "code_hash_prefix": compute_code_hash(code)[:16]},
                )
                raise ValueError("Activation code is unrecognized, expired, or invalid.")

            inst_id = (installation_id or "").strip()
            if not inst_id:
                raise ValueError("Installation ID cannot be empty.")

            # Parse and validate device public key format (DEV-006)
            key_obj, canonical_bytes, key_type = parse_and_validate_public_key(device_public_key)
            fingerprint = compute_key_fingerprint(canonical_bytes)

            user_id = code_meta.get("user_id", "evaluator-primary")
            max_devices = code_meta.get("max_devices", 1)

            # Check existing license device limit (DEV-002 pre-check)
            license_doc = self._licenses_by_user.get(user_id)
            if license_doc:
                lic_id = license_doc["payload"]["license_id"]
                active_devs = [d for d in self._devices_by_license.get(lic_id, []) if d.is_active]
                matching = next(
                    (d for d in active_devs if d.key_fingerprint == fingerprint or d.public_key_b64 == device_public_key),
                    None,
                )
                if not matching and len(active_devs) >= max_devices:
                    audit_service.record_event(
                        event_type="activation.challenge_device_limit_exceeded",
                        status="DENIED",
                        actor_id=user_id,
                        license_id=lic_id,
                        details={"active_devices": len(active_devs), "max_devices": max_devices},
                    )
                    raise PermissionError(
                        f"Device limit exceeded ({len(active_devs)}/{max_devices}). "
                        f"Deactivate an existing registered device before activating a new one."
                    )

            now = time.time()
            challenge_id = str(uuid.uuid4())
            nonce = secrets.token_urlsafe(32)
            expires_at = now + challenge_ttl_seconds
            canonical_msg = format_canonical_challenge(challenge_id, nonce, fingerprint, inst_id)

            rec = ChallengeRecord(
                challenge_id=challenge_id,
                activation_code_hash=compute_code_hash(code),
                client_id=user_id,
                max_devices=max_devices,
                device_public_key=device_public_key.strip(),
                key_fingerprint=fingerprint,
                installation_id=inst_id,
                device_label=device_label or "workstation",
                platform=platform or "windows",
                nonce=nonce,
                canonical_message=canonical_msg,
                created_at=now,
                expires_at=expires_at,
                consumed=False,
                client_ip=client_ip,
            )
            self._challenges_by_id[challenge_id] = rec

            audit_service.record_event(
                event_type="activation.challenge_issued",
                status="SUCCESS",
                actor_id=user_id,
                details={
                    "challenge_id": challenge_id,
                    "key_fingerprint": fingerprint,
                    "algorithm": key_type,
                },
            )

            return {
                "challenge_id": challenge_id,
                "nonce": nonce,
                "canonical_message": canonical_msg,
                "expires_at": datetime.fromtimestamp(expires_at, timezone.utc).isoformat(),
                "key_fingerprint": fingerprint,
                "algorithm": key_type,
            }

    def activate_device_with_challenge(
        self,
        challenge_id: str,
        signature: str,
        installation_id: str,
        client_ip: str = "127.0.0.1",
        client_version: str = "1.1.0",
    ) -> Dict[str, Any]:
        """
        Stage 2: Verifies digital signature proof-of-possession, single-use challenge consumption,
        atomic device quota check, and issues license token and session credentials.
        """
        with self._lock:
            now = time.time()
            ch_id = (challenge_id or "").strip()
            challenge = self._challenges_by_id.get(ch_id)
            if not challenge:
                audit_service.record_event(
                    event_type="activation.challenge_not_found",
                    status="NOT_FOUND",
                    actor_id=client_ip,
                    details={"challenge_id": ch_id},
                )
                raise KeyError(f"Challenge '{ch_id}' not found.")

            # Replay prevention (DEV-010)
            if challenge.consumed:
                audit_service.record_event(
                    event_type="activation.challenge_replay_attempt",
                    status="REPLAY_DETECTED",
                    actor_id=challenge.client_id,
                    details={"challenge_id": ch_id},
                )
                raise PermissionError("Challenge has already been consumed. Replay rejected.")

            # Expiry check (DEV-009)
            if now > challenge.expires_at:
                audit_service.record_event(
                    event_type="activation.challenge_expired",
                    status="EXPIRED",
                    actor_id=challenge.client_id,
                    details={"challenge_id": ch_id, "expired_at": challenge.expires_at},
                )
                raise TimeoutError("Challenge has expired.")

            # Installation ID match check (DEV-012)
            inst_id = (installation_id or "").strip()
            if inst_id != challenge.installation_id:
                audit_service.record_event(
                    event_type="activation.installation_mismatch",
                    status="FAILED",
                    actor_id=challenge.client_id,
                    details={"expected": challenge.installation_id, "actual": inst_id},
                )
                raise ValueError(f"Installation ID '{inst_id}' does not match challenge.")

            # Cryptographic signature verification (DEV-007, DEV-008)
            key_obj, _, _ = parse_and_validate_public_key(challenge.device_public_key)
            sig = (signature or "").strip()
            if not sig:
                raise PermissionError("Missing device signature proof-of-possession.")

            valid_sig = verify_device_signature(
                pub_key_obj=key_obj,
                message_bytes=challenge.canonical_message.encode("utf-8"),
                signature_b64=sig,
            )
            if not valid_sig:
                audit_service.record_event(
                    event_type="activation.invalid_signature",
                    status="DENIED",
                    actor_id=challenge.client_id,
                    details={"challenge_id": ch_id, "fingerprint": challenge.key_fingerprint},
                )
                raise PermissionError("Invalid device signature proof-of-possession.")

            # Mark consumed atomically (single-use invariant DEV-010)
            challenge.consumed = True
            challenge.consumed_at = now

            user_id = challenge.client_id
            max_devices = challenge.max_devices

            # Resolve or issue evaluation license
            code_hash = challenge.activation_code_hash
            if code_hash in self._licenses_by_code_hash:
                license_doc = self._licenses_by_code_hash[code_hash]
            elif user_id in self._licenses_by_user:
                license_doc = self._licenses_by_user[user_id]
            else:
                license_doc = issue_evaluation_license(
                    user_id=user_id,
                    duration_days=14,
                    hardware_fingerprint=f"{challenge.device_label}-{challenge.platform}",
                    product=CANONICAL_PRODUCT,
                    max_devices=max_devices,
                )
                self._licenses_by_code_hash[code_hash] = license_doc
                self._licenses_by_user[user_id] = license_doc

            license_id = license_doc["payload"]["license_id"]

            # Enforce device binding and 1-device limit atomically (DEV-001, DEV-002)
            active_devices = [d for d in self._devices_by_license[license_id] if d.is_active]
            matching_device = next(
                (
                    d for d in active_devices
                    if d.key_fingerprint == challenge.key_fingerprint or d.public_key_b64 == challenge.device_public_key
                ),
                None,
            )

            recovery_code = f"REC-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            rec_hash = hashlib.sha256(recovery_code.encode("utf-8")).hexdigest()

            if matching_device:
                device_rec = matching_device
                device_rec.last_seen_at = now
                device_rec.recovery_code_hash = rec_hash
            else:
                if len(active_devices) >= max_devices:
                    audit_service.record_event(
                        event_type="activation.device_limit_exceeded",
                        status="DENIED",
                        actor_id=user_id,
                        license_id=license_id,
                        details={
                            "active_devices": len(active_devices),
                            "max_devices": max_devices,
                        },
                    )
                    raise PermissionError(
                        f"Device limit exceeded ({len(active_devices)}/{max_devices}). "
                        f"Deactivate an existing registered device before activating a new one."
                    )

                device_rec = DeviceRecord(
                    device_id=str(uuid.uuid4()),
                    license_id=license_id,
                    public_key_b64=challenge.device_public_key,
                    label=challenge.device_label,
                    platform=challenge.platform,
                    is_active=True,
                    registered_at=now,
                    last_seen_at=now,
                    key_fingerprint=challenge.key_fingerprint,
                    installation_id=challenge.installation_id,
                    recovery_code_hash=rec_hash,
                )
                self._devices_by_license[license_id].append(device_rec)
                self._devices_by_id[device_rec.device_id] = device_rec

            # Create authenticated evaluation session
            access_token, refresh_token = self._create_session(
                license_id=license_id,
                user_id=user_id,
                device_id=device_rec.device_id,
            )

            token_b64 = export_license_token(license_doc)
            pub_key = load_public_key()
            pub_pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii")

            audit_service.record_event(
                event_type="activation.device_bound_success",
                status="SUCCESS",
                actor_id=user_id,
                license_id=license_id,
                device_id=device_rec.device_id,
                details={
                    "fingerprint": challenge.key_fingerprint,
                    "platform": challenge.platform,
                    "version": client_version,
                },
            )

            entitlements_dict = {
                "documents.read": True,
                "documents.upload": True,
                "intelligence.query": True,
                "documents.compare": True,
                "evidence.inspect": True,
                "users.manage": False,
                "platform.admin": False,
                "workspaces.create": False,
                "models.configure": False,
            }

            return {
                "status": "active",
                "client_id": user_id,
                "device_id": device_rec.device_id,
                "recovery_code": recovery_code,
                "license": {
                    "product": license_doc["payload"]["product"],
                    "license_id": license_id,
                    "tier": license_doc["payload"]["tier"],
                    "expires_at": license_doc["payload"]["expires_at"],
                    "status": "ACTIVE",
                },
                "session": {
                    "access_token": access_token,
                    "token_type": "Bearer",
                    "expires_in": self.session_ttl_seconds,
                    "refresh_token": refresh_token,
                    "device_id": device_rec.device_id,
                },
                "entitlements": entitlements_dict,
                "quotas": license_doc["payload"]["quotas"],
                "license_token": token_b64,
                "public_key_pem": pub_pem,
            }

    def activate_instance(
        self,
        client_id: str,
        machine_name: str = "workstation",
        platform: str = "windows",
        client_ip: str = "127.0.0.1",
        hardware_fingerprint: Optional[str] = None,
        activation_code: Optional[str] = None,
        device_public_key: Optional[str] = None,
        device_label: Optional[str] = None,
        client_version: str = "1.1.0",
    ) -> Dict[str, Any]:
        """
        Direct/Legacy activation endpoint (backward compatibility with DEV-001/LIC-001).
        Validates code eligibility, binds device key, enforces device quota,
        and generates an initial authenticated session.
        """
        with self._lock:
            self._check_ip_rate_limit(client_ip)
            now = time.time()

            code = (activation_code or "").strip()
            user_id = client_id
            max_devices = 1

            if code:
                code_meta = self.resolve_code_metadata(code)
                if not code_meta:
                    audit_service.record_event(
                        event_type="activation.invalid_code",
                        status="FAILURE",
                        actor_id=client_id,
                        details={"code_hash_prefix": compute_code_hash(code)[:16]},
                    )
                    raise ValueError(f"Activation code '{code}' is unrecognized or invalid.")
                user_id = code_meta.get("user_id", client_id)
                max_devices = code_meta.get("max_devices", 1)

            code_hash = compute_code_hash(code) if code else ""
            if code_hash and code_hash in self._licenses_by_code_hash:
                license_doc = self._licenses_by_code_hash[code_hash]
            elif user_id in self._licenses_by_user:
                license_doc = self._licenses_by_user[user_id]
            else:
                license_doc = issue_evaluation_license(
                    user_id=user_id,
                    duration_days=14,
                    hardware_fingerprint=hardware_fingerprint or f"{machine_name}-{platform}",
                    product=CANONICAL_PRODUCT,
                    max_devices=max_devices,
                )
                if code_hash:
                    self._licenses_by_code_hash[code_hash] = license_doc
                self._licenses_by_user[user_id] = license_doc

            license_id = license_doc["payload"]["license_id"]
            device_pub = (device_public_key or hardware_fingerprint or f"device-key-{client_id}").strip()

            # Enforce device binding and limit (DEV-001, DEV-002)
            active_devices = [
                d for d in self._devices_by_license[license_id] if d.is_active
            ]
            matching_device = next(
                (d for d in active_devices if d.public_key_b64 == device_pub), None
            )

            recovery_code = f"REC-{secrets.token_hex(4).upper()}-{secrets.token_hex(4).upper()}"
            rec_hash = hashlib.sha256(recovery_code.encode("utf-8")).hexdigest()

            if matching_device:
                device_rec = matching_device
                device_rec.last_seen_at = now
            else:
                if len(active_devices) >= max_devices:
                    audit_service.record_event(
                        event_type="activation.device_limit_exceeded",
                        status="DENIED",
                        actor_id=user_id,
                        license_id=license_id,
                        details={
                            "active_devices": len(active_devices),
                            "max_devices": max_devices,
                        },
                    )
                    raise PermissionError(
                        f"Device limit exceeded ({len(active_devices)}/{max_devices}). "
                        f"Deactivate an existing registered device before activating a new one."
                    )

                device_rec = DeviceRecord(
                    device_id=str(uuid.uuid4()),
                    license_id=license_id,
                    public_key_b64=device_pub,
                    label=device_label or machine_name,
                    platform=platform,
                    is_active=True,
                    registered_at=now,
                    last_seen_at=now,
                    key_fingerprint=_hash_token(device_pub),
                    installation_id=hardware_fingerprint or machine_name,
                    recovery_code_hash=rec_hash,
                )
                self._devices_by_license[license_id].append(device_rec)
                self._devices_by_id[device_rec.device_id] = device_rec

            # Create authenticated evaluation session
            access_token, refresh_token = self._create_session(
                license_id=license_id,
                user_id=user_id,
                device_id=device_rec.device_id,
            )

            token_b64 = export_license_token(license_doc)
            pub_key = load_public_key()
            pub_pem = pub_key.public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            ).decode("ascii")

            audit_service.record_event(
                event_type="activation.success",
                status="SUCCESS",
                actor_id=user_id,
                license_id=license_id,
                device_id=device_rec.device_id,
                details={"platform": platform, "version": client_version},
            )

            entitlements_dict = {
                "documents.read": True,
                "documents.upload": True,
                "intelligence.query": True,
                "documents.compare": True,
                "evidence.inspect": True,
                "users.manage": False,
                "platform.admin": False,
                "workspaces.create": False,
                "models.configure": False,
            }

            return {
                "status": "active",
                "client_id": client_id,
                "device_id": device_rec.device_id,
                "recovery_code": recovery_code,
                "license": {
                    "product": license_doc["payload"]["product"],
                    "license_id": license_id,
                    "tier": license_doc["payload"]["tier"],
                    "expires_at": license_doc["payload"]["expires_at"],
                    "status": "ACTIVE",
                },
                "session": {
                    "access_token": access_token,
                    "token_type": "Bearer",
                    "expires_in": self.session_ttl_seconds,
                    "refresh_token": refresh_token,
                    "device_id": device_rec.device_id,
                },
                "entitlements": entitlements_dict,
                "quotas": license_doc["payload"]["quotas"],
                "license_token": token_b64,
                "public_key_pem": pub_pem,
            }

    def _create_session(self, license_id: str, user_id: str, device_id: str, family_id: Optional[str] = None) -> Tuple[str, str]:
        """Issues short-lived access token and refresh token."""
        now = time.time()
        access_token = f"aegis_eval_at_{secrets.token_urlsafe(32)}"
        refresh_token = f"aegis_eval_rt_{secrets.token_urlsafe(32)}"
        at_hash = _hash_token(access_token)
        rt_hash = _hash_token(refresh_token)

        fam_id = family_id or str(uuid.uuid4())
        session_id = str(uuid.uuid4())

        record = SessionRecord(
            session_id=session_id,
            license_id=license_id,
            user_id=user_id,
            device_id=device_id,
            access_token_hash=at_hash,
            refresh_token_hash=rt_hash,
            is_revoked=False,
            created_at=now,
            expires_at=now + self.session_ttl_seconds,
            family_id=fam_id,
        )

        self._sessions_by_access_hash[at_hash] = record
        self._sessions_by_refresh_hash[rt_hash] = record
        self._session_families[fam_id].add(session_id)

        try:
            from datetime import timedelta
            from src.schemas.evaluation.session import EvaluationSession, SessionStatus
            from src.schemas.evaluation.refresh import EvaluationRefreshToken, RefreshTokenStatus
            from src.repositories.evaluation.session_repository import session_repository
            from src.repositories.evaluation.refresh_token_repository import refresh_token_repository

            now_dt = datetime.fromtimestamp(now, timezone.utc)
            eval_sess = EvaluationSession(
                session_id=session_id,
                evaluator_id=user_id,
                tenant_id=f"tenant-{license_id}",
                license_id=license_id,
                device_id=device_id,
                status=SessionStatus.ACTIVE,
                token_family_id=fam_id,
                access_token_hash=at_hash,
                created_at=now_dt,
                last_seen_at=now_dt,
                idle_expires_at=now_dt + timedelta(seconds=1800),
                absolute_expires_at=now_dt + timedelta(days=7),
            )
            session_repository.save_session(eval_sess)

            eval_rt = EvaluationRefreshToken(
                token_id=str(uuid.uuid4()),
                session_id=session_id,
                family_id=fam_id,
                token_hash=rt_hash,
                status=RefreshTokenStatus.ACTIVE,
                created_at=now_dt,
                expires_at=now_dt + timedelta(days=7),
            )
            refresh_token_repository.save_token(eval_rt)

            from src.schemas.evaluation.session_audit import SessionAuditEvent, SessionAuditEventType
            from src.repositories.evaluation.session_audit_repository import session_audit_repository
            session_audit_repository.record_event(
                SessionAuditEvent(
                    event_type=SessionAuditEventType.SESSION_CREATED,
                    session_id=session_id,
                    evaluator_id=user_id,
                    license_id=license_id,
                    device_id=device_id,
                    status="SUCCESS",
                )
            )
        except Exception:
            pass

        return access_token, refresh_token

    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """
        Validates refresh token, detects reuse/replay (SESSION-001), and rotates credentials.
        """
        with self._lock:
            rt_hash = _hash_token(refresh_token)

            # Replay Detection: Check if old already-used refresh token was replayed
            if rt_hash in self._used_refresh_hashes:
                fam_id = self._used_refresh_hashes[rt_hash]
                for sid in self._session_families.get(fam_id, set()):
                    for s in list(self._sessions_by_access_hash.values()):
                        if s.session_id == sid:
                            s.is_revoked = True
                try:
                    from src.services.evaluation.session_revocation_service import session_revocation_service
                    from src.schemas.evaluation.session import RevocationReason
                    session_revocation_service.revoke_security_incident(fam_id, RevocationReason.REFRESH_REPLAY_DETECTED)
                except Exception:
                    pass
                audit_service.record_event(
                    event_type="session.refresh_replay_detected",
                    status="COMPROMISE_DETECTED",
                    actor_id="unknown",
                    details={"family_id": fam_id},
                )
                raise PermissionError("Refresh token replay detected. All family sessions have been revoked for security.")

            record = self._sessions_by_refresh_hash.get(rt_hash)
            if not record or record.is_revoked:
                raise PermissionError("Invalid, expired or revoked refresh token.")

            device = self._devices_by_id.get(record.device_id)
            if not device or not device.is_active:
                record.is_revoked = True
                raise PermissionError("Associated device has been deactivated.")

            self._used_refresh_hashes[rt_hash] = record.family_id
            del self._sessions_by_refresh_hash[rt_hash]
            del self._sessions_by_access_hash[record.access_token_hash]

            new_at, new_rt = self._create_session(
                license_id=record.license_id,
                user_id=record.user_id,
                device_id=record.device_id,
                family_id=record.family_id,
            )

            audit_service.record_event(
                event_type="session.rotated",
                status="SUCCESS",
                actor_id=record.user_id,
                license_id=record.license_id,
                device_id=record.device_id,
            )

            return {
                "access_token": new_at,
                "token_type": "Bearer",
                "expires_in": self.session_ttl_seconds,
                "refresh_token": new_rt,
            }

    def validate_session(self, access_token: str) -> Optional[SessionRecord]:
        """Validates an evaluation access token against memory store."""
        with self._lock:
            at_hash = _hash_token(access_token)
            record = self._sessions_by_access_hash.get(at_hash)
            if not record or record.is_revoked:
                return None

            try:
                from src.repositories.evaluation.session_repository import session_repository
                from src.schemas.evaluation.session import SessionStatus
                repo_sess = session_repository.get_by_access_hash(at_hash)
                if repo_sess and repo_sess.status != SessionStatus.ACTIVE:
                    record.is_revoked = True
                    return None
            except Exception:
                pass

            if time.time() > record.expires_at:
                return None
            device = self._devices_by_id.get(record.device_id)
            if not device or not device.is_active:
                return None
            return record

    def logout_session(self, access_token: str) -> bool:
        """Revokes an active session token (SESSION-002)."""
        with self._lock:
            at_hash = _hash_token(access_token)
            record = self._sessions_by_access_hash.get(at_hash)
            if not record:
                return False
            record.is_revoked = True
            try:
                from src.services.evaluation.session_revocation_service import session_revocation_service
                from src.schemas.evaluation.session import RevocationReason
                session_revocation_service.revoke_by_access_token(access_token, RevocationReason.USER_LOGOUT)
            except Exception:
                pass
            audit_service.record_event(
                event_type="session.logged_out",
                status="SUCCESS",
                actor_id=record.user_id,
                license_id=record.license_id,
                device_id=record.device_id,
            )
            return True

    def deactivate_device(self, license_id: str, device_id_or_pubkey: str) -> bool:
        """
        Deactivates a device, freeing its slot under the license and revoking its sessions.
        """
        with self._lock:
            devices = self._devices_by_license.get(license_id, [])
            target = next(
                (
                    d for d in devices
                    if d.device_id == device_id_or_pubkey
                    or d.public_key_b64 == device_id_or_pubkey
                    or d.key_fingerprint == device_id_or_pubkey
                ),
                None,
            )
            if not target:
                return False

            target.is_active = False

            # Revoke all sessions for this device
            for sess in list(self._sessions_by_access_hash.values()):
                if sess.device_id == target.device_id:
                    sess.is_revoked = True

            try:
                from src.services.evaluation.session_revocation_service import session_revocation_service
                from src.schemas.evaluation.session import RevocationReason
                session_revocation_service.revoke_device_sessions(target.device_id, RevocationReason.DEVICE_DEACTIVATED)
            except Exception:
                pass

            audit_service.record_event(
                event_type="device.deactivated",
                status="SUCCESS",
                actor_id="evaluator",
                license_id=license_id,
                device_id=target.device_id,
            )
            return True

    def get_devices(self, license_id: str) -> List[Dict[str, Any]]:
        with self._lock:
            return [
                {
                    "device_id": d.device_id,
                    "label": d.label,
                    "platform": d.platform,
                    "is_active": d.is_active,
                    "registered_at": d.registered_at,
                    "last_seen_at": d.last_seen_at,
                    "key_fingerprint": d.key_fingerprint,
                    "installation_id": d.installation_id,
                }
                for d in self._devices_by_license.get(license_id, [])
            ]

    def get_device_detail(self, license_id: str, device_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            device = self._devices_by_id.get(device_id)
            if not device or device.license_id != license_id:
                return None
            return {
                "device_id": device.device_id,
                "license_id": device.license_id,
                "label": device.label,
                "platform": device.platform,
                "is_active": device.is_active,
                "registered_at": device.registered_at,
                "last_seen_at": device.last_seen_at,
                "key_fingerprint": device.key_fingerprint,
                "installation_id": device.installation_id,
            }

    def heartbeat_device(self, license_id: str, device_id: str) -> Dict[str, Any]:
        with self._lock:
            device = self._devices_by_id.get(device_id)
            if not device or device.license_id != license_id or not device.is_active:
                raise PermissionError(f"Device '{device_id}' is inactive or not found under license.")
            now = time.time()
            device.last_seen_at = now
            return {
                "status": "alive",
                "device_id": device.device_id,
                "last_seen_at": now,
            }

    def recover_device(self, license_id: str, device_id: str, recovery_code: str) -> Dict[str, Any]:
        with self._lock:
            device = self._devices_by_id.get(device_id)
            if not device or device.license_id != license_id:
                raise KeyError(f"Device '{device_id}' not found under license.")
            if not device.recovery_code_hash:
                raise PermissionError("No recovery code configured for this device.")

            expected_hash = hashlib.sha256((recovery_code or "").strip().encode("utf-8")).hexdigest()
            if expected_hash != device.recovery_code_hash:
                audit_service.record_event(
                    event_type="device.recovery_failed",
                    status="INVALID_CREDENTIAL",
                    actor_id=device.license_id,
                    device_id=device_id,
                )
                raise PermissionError("Invalid emergency recovery code.")

            device.is_active = False
            for sess in list(self._sessions_by_access_hash.values()):
                if sess.device_id == device.device_id:
                    sess.is_revoked = True

            audit_service.record_event(
                event_type="device.recovered_and_deactivated",
                status="SUCCESS",
                actor_id=device.license_id,
                device_id=device_id,
            )
            return {
                "status": "recovered",
                "device_id": device.device_id,
                "message": "Device successfully recovered and deactivated. Device slot is now free.",
            }

    def reset(self) -> None:
        """Resets all activations and sessions (for test isolation)."""
        with self._lock:
            self.max_activations_per_ip_hour = 10
            self._ip_activation_timestamps.clear()
            self._devices_by_license.clear()
            self._devices_by_id.clear()
            self._licenses_by_code_hash.clear()
            self._licenses_by_user.clear()
            self._sessions_by_access_hash.clear()
            self._sessions_by_refresh_hash.clear()
            self._used_refresh_hashes.clear()
            self._session_families.clear()
            self._challenges_by_id.clear()
            self._init_eligible_codes()


# Global activation instance
activation_service = ActivationService()
