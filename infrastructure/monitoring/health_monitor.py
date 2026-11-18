"""
AEGIS-DocIntel Health & Availability Monitor
PROT-FINAL-05: Workstream DEP-09

Audits health probes and metrics endpoints to ensure they expose operational
liveness without disclosing internal infrastructure topology (DEP-TEST-015):
- Tests /health/live
- Tests /health/ready
- Verifies redaction of internal IPs, DB credentials, hostnames, and stack traces
"""

from __future__ import annotations

import re
from typing import Any, Dict, Tuple

FORBIDDEN_DISCLOSURES = [
    re.compile(r"postgres(?:ql)?://", re.IGNORECASE),
    re.compile(r"\b10\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"\b172\.(?:1[6-9]|2[0-9]|3[01])\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"\b192\.168\.\d{1,3}\.\d{1,3}\b"),
    re.compile(r"password|secret|apikey|token", re.IGNORECASE),
    re.compile(r"Traceback \(most recent call last\):"),
]


class HealthAuditResult:
    def __init__(self, is_safe: bool, details: Dict[str, Any], violations: list[str]):
        self.is_safe = is_safe
        self.details = details
        self.violations = violations


def audit_health_response(payload: Dict[str, Any]) -> HealthAuditResult:
    """
    Scans a health probe JSON payload for accidental information leakage (DEP-TEST-015).
    """
    raw_text = str(payload)
    violations = []

    for pattern in FORBIDDEN_DISCLOSURES:
        matches = pattern.findall(raw_text)
        if matches:
            violations.append(f"Forbidden disclosure matched pattern: {pattern.pattern} ({len(matches)} occurrences)")

    # Explicit check for DB host exposure
    if "db_host" in payload or "database_host" in payload or "connection_string" in payload:
        violations.append("Database internal host key found in health response payload.")

    is_safe = len(violations) == 0
    return HealthAuditResult(is_safe=is_safe, details=payload, violations=violations)
