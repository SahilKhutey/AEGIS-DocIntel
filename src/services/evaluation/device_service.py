"""
AEGIS-DocIntel Evaluation Device Service (PROT-FINAL-02 / REM-02)
Manages device registration, presence heartbeats, unbinding, and emergency recovery.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from services.evaluation_gateway.activation import activation_service as gateway_activation_service


class EvaluationDeviceService:
    def __init__(self, inner=None):
        self._inner = inner or gateway_activation_service

    def get_devices(self, license_id: str) -> List[Dict[str, Any]]:
        return self._inner.get_registered_devices(license_id)

    def deactivate_device(self, license_id: str, device_id: str) -> bool:
        return self._inner.deactivate_device(license_id, device_id)

    def heartbeat_device(self, license_id: str, device_id: str) -> Dict[str, Any]:
        return self._inner.heartbeat_device(license_id, device_id)

    def recover_device(self, license_id: str, device_id: str, recovery_code: str) -> Dict[str, Any]:
        return self._inner.recover_device(license_id, device_id, recovery_code)


device_service = EvaluationDeviceService()
