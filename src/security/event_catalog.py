"""
AEGIS-DocIntel Security Event Catalog & Classification Register (PROT-04 WP-04.08)
Centralized registry of approved event categories, names, and default severities.
"""

from __future__ import annotations

from typing import Dict, Optional, Set
from .event_schema import Severity

# Canonical Security Event Registry (Category -> Event Names -> Default Severity)
EVENT_TAXONOMY: Dict[str, Severity] = {
    # Authentication
    "AUTH_SUCCESS": Severity.INFO,
    "AUTH_FAILURE": Severity.WARNING,
    "AUTH_TOKEN_REJECTED": Severity.WARNING,
    "DEV_TOKEN_ATTEMPT": Severity.CRITICAL,
    # Activation
    "ACTIVATION_SUCCESS": Severity.INFO,
    "ACTIVATION_FAILURE": Severity.WARNING,
    "ACTIVATION_RATE_LIMITED": Severity.HIGH,
    "ACTIVATION_CODE_INVALID": Severity.WARNING,
    # Device
    "DEVICE_REGISTERED": Severity.INFO,
    "DEVICE_DEACTIVATED": Severity.INFO,
    "DEVICE_RECOVERY_REQUESTED": Severity.WARNING,
    "DEVICE_LIMIT_EXCEEDED": Severity.WARNING,
    # License
    "LICENSE_ISSUED": Severity.INFO,
    "LICENSE_VALIDATION_FAILED": Severity.HIGH,
    "LICENSE_REVOKED": Severity.HIGH,
    "LICENSE_SUSPENDED": Severity.WARNING,
    "LICENSE_SIGNATURE_INVALID": Severity.CRITICAL,
    # Session
    "SESSION_CREATED": Severity.INFO,
    "SESSION_REFRESHED": Severity.INFO,
    "SESSION_LOGGED_OUT": Severity.INFO,
    "SESSION_REVOKED": Severity.HIGH,
    "REFRESH_REUSE_DETECTED": Severity.CRITICAL,
    "SESSION_EXPIRED": Severity.INFO,
    # Entitlement
    "ENTITLEMENT_GRANTED": Severity.INFO,
    "ENTITLEMENT_DENIED": Severity.HIGH,
    "POLICY_CHANGED": Severity.HIGH,
    "PRIVILEGE_ESCALATION_ATTEMPT": Severity.CRITICAL,
    # Quota
    "QUOTA_EXCEEDED": Severity.WARNING,
    "RESERVATION_FAILED": Severity.WARNING,
    "USAGE_RECONCILIATION_FAILED": Severity.HIGH,
    "COUNTER_DRIFT_DETECTED": Severity.HIGH,
    # API & Boundary
    "API_AUTHORIZATION_DENIED": Severity.HIGH,
    "API_RATE_LIMITED": Severity.WARNING,
    "CROSS_TENANT_ACCESS_ATTEMPT": Severity.CRITICAL,
    "CORS_ORIGIN_DENIED": Severity.HIGH,
    "CSRF_MISMATCH": Severity.HIGH,
    # WebSocket
    "WS_TICKET_ISSUED": Severity.INFO,
    "WS_AUTH_FAILED": Severity.HIGH,
    "WS_SESSION_REVOKED": Severity.HIGH,
    # Distribution & Integrity
    "ARTIFACT_SCAN_FAILED": Severity.CRITICAL,
    "UNSAFE_CONFIGURATION_DETECTED": Severity.CRITICAL,
    "AUDIT_INTEGRITY_FAILED": Severity.CRITICAL,
    "AUDIT_TAMPERING_DETECTED": Severity.CRITICAL,
    # Administration
    "ADMIN_ACTION": Severity.HIGH,
    "SECRET_ROTATION": Severity.HIGH,
    "KEY_ROTATION": Severity.HIGH,
    "KEY_COMPROMISE_REPORTED": Severity.CRITICAL,
    # Operations
    "BACKUP_COMPLETED": Severity.INFO,
    "BACKUP_FAILED": Severity.HIGH,
    "RESTORE_COMPLETED": Severity.HIGH,
    "RESTORE_VERIFICATION_FAILED": Severity.CRITICAL,
}


def is_known_event_type(event_type: str) -> bool:
    """Verifies whether an event type is recognized in the official catalog."""
    return event_type in EVENT_TAXONOMY


def get_default_severity(event_type: str) -> Severity:
    """Returns the default severity for an event type, falling back to WARNING if uncatalogued."""
    return EVENT_TAXONOMY.get(event_type, Severity.WARNING)
