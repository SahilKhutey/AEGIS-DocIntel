"""
Security Engine Orchestrator
============================

The central coordinator class unifying the security framework sub-modules.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

from .encryption import EncryptionManager
from .access_control import AccessController
from .authentication import AuthenticationManager
from .audit_log import AuditLogger, AuditEventType
from .secret_manager import SecretManager
from .rate_limiter import RateLimiter
from .threat_detector import ThreatDetector
from .security_report import SecurityReportData, SecurityMetrics


class SecurityReport:
    """Helper class to generate and export security reports."""

    def __init__(self, engine: SecurityEngine) -> None:
        self.engine = engine

    def generate(self) -> SecurityReportData:
        """Compile and summarize security status and metrics."""
        # Compile recent violations from audit logs
        recent_violations = []
        for event in self.engine.audit_log.query(limit=50):
            if event.outcome in ("denied", "failure") or event.severity.value in ("error", "critical"):
                recent_violations.append(event.to_dict())

        # Determine overall security status
        status = "secure"
        if not self.engine.audit_log.verify_chain():
            status = "compromised"
        elif any(v.get("severity") == "critical" for v in recent_violations):
            status = "degraded"

        # Update metrics
        self.engine._metrics.active_users = len(
            [u for u in self.engine.authentication.users.values() if u.is_active]
        )
        self.engine._metrics.last_updated = time.time()

        return SecurityReportData(
            timestamp=time.time(),
            metrics=self.engine._metrics,
            threats=self.engine.threat_detector.indicators,
            recent_violations=recent_violations,
            status=status,
        )


class SecurityEngine:
    """The central orchestrator for the AMDI-OS Security Framework."""

    def __init__(
        self,
        encryption_manager: Optional[EncryptionManager] = None,
        access_controller: Optional[AccessController] = None,
        authentication_manager: Optional[AuthenticationManager] = None,
        audit_logger: Optional[AuditLogger] = None,
        secret_manager: Optional[SecretManager] = None,
        rate_limiter: Optional[RateLimiter] = None,
        threat_detector: Optional[ThreatDetector] = None,
    ) -> None:
        self.encryption = encryption_manager or EncryptionManager()
        self.access_control = access_controller or AccessController()
        self.authentication = authentication_manager or AuthenticationManager()
        self.audit_log = audit_logger or AuditLogger()
        self.secret_manager = secret_manager or SecretManager(
            self.encryption, self.access_control, self.audit_log
        )
        self.rate_limiter = rate_limiter or RateLimiter()
        self.threat_detector = threat_detector or ThreatDetector()

        # Initialize defaults
        self.access_control.create_default_roles()
        self._metrics = SecurityMetrics()

    def generate_report(self) -> SecurityReportData:
        """Create a new consolidated security report."""
        report_generator = SecurityReport(self)
        return report_generator.generate()
