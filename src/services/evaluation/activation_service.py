"""
AEGIS-DocIntel Evaluation Activation Service Adapter (PROT-FINAL-02 / REM-02)
Adapts gateway activation workflows into modular evaluation service layer.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from services.evaluation_gateway.activation import (
    activation_service as gateway_activation_service,
    ActivationService as GatewayActivationService,
    DeviceRecord,
    SessionRecord,
)


class EvaluationActivationService:
    def __init__(self, inner: Optional[GatewayActivationService] = None):
        self._inner = inner or gateway_activation_service

    def generate_challenge(
        self,
        client_id: str,
        machine_name: str,
        platform: str,
        client_ip: str,
        hardware_fingerprint: str,
        activation_code: str,
        installation_id: str,
        device_public_key: str,
    ) -> Dict[str, Any]:
        return self._inner.generate_challenge(
            client_id=client_id,
            machine_name=machine_name,
            platform=platform,
            client_ip=client_ip,
            hardware_fingerprint=hardware_fingerprint,
            activation_code=activation_code,
            installation_id=installation_id,
            device_public_key=device_public_key,
        )

    def verify_challenge_and_activate(
        self,
        challenge_id: str,
        signature: str,
        installation_id: str,
        client_version: str = "1.1.0",
        client_ip: str = "127.0.0.1",
    ) -> Dict[str, Any]:
        return self._inner.verify_challenge_and_activate(
            challenge_id=challenge_id,
            signature=signature,
            installation_id=installation_id,
            client_version=client_version,
            client_ip=client_ip,
        )

    def activate_instance(
        self,
        client_id: str,
        machine_name: str,
        platform: str,
        client_ip: str,
        hardware_fingerprint: str,
        activation_code: str,
        device_public_key: str,
        device_label: str = "Evaluation Device",
        client_version: str = "1.1.0",
    ) -> Dict[str, Any]:
        return self._inner.activate_instance(
            client_id=client_id,
            machine_name=machine_name,
            platform=platform,
            client_ip=client_ip,
            hardware_fingerprint=hardware_fingerprint,
            activation_code=activation_code,
            device_public_key=device_public_key,
            device_label=device_label,
            client_version=client_version,
        )


activation_service = EvaluationActivationService()
