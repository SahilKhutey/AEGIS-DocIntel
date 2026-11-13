"""
AEGIS-DocIntel Evaluation Gateway — Activation, Device Binding & Session Subsystem
Implements PROT-04 WP-04.03, WP-04.07, and WP-04.08 specifications:
- Activation code validation & device key pair binding
- Maximum active device enforcement (1 device limit, rejects DEV-002)
- Device deactivation and reactivation workflows
- Short-lived evaluation sessions with rotating refresh tokens
- Protection against refresh-token replay and session reuse (SESSION-001, SESSION-002)
"""

from __future__ import annotations

import hashlib
import secrets
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from .license import (
    issue_evaluation_license,
    export_license_token,
    load_public_key,
    CANONICAL_PRODUCT,
)
from .audit import audit_service
from cryptography.hazmat.primitives import serialization


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


# In-memory eligible activation codes: code -> metadata
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
        # activation_code -> license_doc
        self._licenses_by_code: Dict[str, Dict[str, Any]] = {}
        # client_id / user_id -> license_doc
        self._licenses_by_user: Dict[str, Dict[str, Any]] = {}
        
        # token_hash -> SessionRecord
        self._sessions_by_access_hash: Dict[str, SessionRecord] = {}
        # refresh_token_hash -> SessionRecord
        self._sessions_by_refresh_hash: Dict[str, SessionRecord] = {}
        # Used refresh token hashes -> family_id (for replay detection)
        self._used_refresh_hashes: Dict[str, str] = {}
        # family_id -> set of session_ids
        self._session_families: Dict[str, Set[str]] = defaultdict(set)
        
        self._lock = threading.Lock()

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
        Activates an evaluation license, binds the device public key, enforces device quota,
        and generates an initial authenticated session.
        """
        with self._lock:
            self._check_ip_rate_limit(client_ip)
            now = time.time()

            # Resolve activation code eligibility if provided
            code = (activation_code or "").strip()
            user_id = client_id
            max_devices = 1

            if code:
                if code not in ELIGIBLE_ACTIVATION_CODES and not code.startswith("AEGIS-EVAL-"):
                    audit_service.record_event(
                        event_type="activation.invalid_code",
                        status="FAILURE",
                        actor_id=client_id,
                        details={"code_prefix": code[:10]},
                    )
                    raise ValueError(f"Activation code '{code}' is unrecognized or invalid.")
                code_meta = ELIGIBLE_ACTIVATION_CODES.get(code, {})
                user_id = code_meta.get("user_id", client_id)
                max_devices = code_meta.get("max_devices", 1)

            # Resolve or issue evaluation license
            if code and code in self._licenses_by_code:
                license_doc = self._licenses_by_code[code]
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
                if code:
                    self._licenses_by_code[code] = license_doc
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
                # Revoke all sessions in this family immediately (compromise detected)
                for sid in self._session_families.get(fam_id, set()):
                    for s in list(self._sessions_by_access_hash.values()):
                        if s.session_id == sid:
                            s.is_revoked = True
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

            # Verify associated device is still active
            device = self._devices_by_id.get(record.device_id)
            if not device or not device.is_active:
                record.is_revoked = True
                raise PermissionError("Associated device has been deactivated.")

            # Mark old refresh token as consumed
            self._used_refresh_hashes[rt_hash] = record.family_id
            del self._sessions_by_refresh_hash[rt_hash]
            del self._sessions_by_access_hash[record.access_token_hash]

            # Issue rotated pair
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
            if time.time() > record.expires_at:
                return None
            # Check device active
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
                (d for d in devices if d.device_id == device_id_or_pubkey or d.public_key_b64 == device_id_or_pubkey),
                None,
            )
            if not target:
                return False

            target.is_active = False

            # Revoke all sessions for this device
            for sess in list(self._sessions_by_access_hash.values()):
                if sess.device_id == target.device_id:
                    sess.is_revoked = True

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
                }
                for d in self._devices_by_license.get(license_id, [])
            ]

    def reset(self) -> None:
        """Resets all activations and sessions (for test isolation)."""
        with self._lock:
            self._ip_activation_timestamps.clear()
            self._devices_by_license.clear()
            self._devices_by_id.clear()
            self._licenses_by_code.clear()
            self._licenses_by_user.clear()
            self._sessions_by_access_hash.clear()
            self._sessions_by_refresh_hash.clear()
            self._used_refresh_hashes.clear()
            self._session_families.clear()


# Global activation instance
activation_service = ActivationService()
