"""
AEGIS-DocIntel Evaluation Gateway — Activation & Registration Service
Handles evaluation instance registration, issuance of signed 14-day evaluation licenses,
and brute-force/anti-scraping protection.
"""

from __future__ import annotations

import time
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .license import issue_evaluation_license, export_license_token, load_public_key, load_private_key
from cryptography.hazmat.primitives import serialization

@dataclass
class ClientActivationRecord:
    client_id: str
    machine_name: str
    platform: str
    first_activated_at: float
    last_activated_at: float
    activation_count: int


class ActivationService:
    def __init__(self, max_activations_per_ip_hour: int = 10):
        self.max_activations_per_ip_hour = max_activations_per_ip_hour
        self._ip_activation_timestamps: Dict[str, List[float]] = defaultdict(list)
        self._clients: Dict[str, ClientActivationRecord] = {}

    def _check_ip_rate_limit(self, client_ip: str) -> None:
        now = time.time()
        cutoff = now - 3600.0
        self._ip_activation_timestamps[client_ip] = [
            ts for ts in self._ip_activation_timestamps[client_ip] if ts >= cutoff
        ]
        if len(self._ip_activation_timestamps[client_ip]) >= self.max_activations_per_ip_hour:
            raise PermissionError(
                f"Too many activation attempts from IP {client_ip}. Please wait before requesting another demo license."
            )
        self._ip_activation_timestamps[client_ip].append(now)

    def activate_instance(
        self,
        client_id: str,
        machine_name: str = "local-workstation",
        platform: str = "windows",
        client_ip: str = "127.0.0.1",
        hardware_fingerprint: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Registers a demo instance and returns a cryptographically signed evaluation license.
        """
        self._check_ip_rate_limit(client_ip)
        now = time.time()

        if client_id in self._clients:
            rec = self._clients[client_id]
            rec.last_activated_at = now
            rec.activation_count += 1
        else:
            rec = ClientActivationRecord(
                client_id=client_id,
                machine_name=machine_name,
                platform=platform,
                first_activated_at=now,
                last_activated_at=now,
                activation_count=1
            )
            self._clients[client_id] = rec

        # Issue 14-day signed evaluation license
        license_doc = issue_evaluation_license(
            user_id=client_id,
            duration_days=14,
            hardware_fingerprint=hardware_fingerprint or f"{machine_name}-{platform}"
        )
        token = export_license_token(license_doc)

        pub_key = load_public_key()
        pub_pem = pub_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode("ascii")

        return {
            "status": "ACTIVATED",
            "client_id": client_id,
            "license_id": license_doc["payload"]["license_id"],
            "issued_at": license_doc["payload"]["issued_at"],
            "expires_at": license_doc["payload"]["expires_at"],
            "tier": license_doc["payload"]["tier"],
            "features": license_doc["payload"]["features"],
            "quotas": license_doc["payload"]["quotas"],
            "license_token": token,
            "public_key_pem": pub_pem
        }


activation_service = ActivationService()
