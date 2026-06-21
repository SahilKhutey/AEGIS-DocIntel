"""
Security Report Data Structures
===============================

Data classes representing consolidated security metrics and audit report summaries.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List

from .threat_detector import ThreatIndicator


@dataclass
class SecurityMetrics:
    """Tracks performance and event volume metrics of the security layer."""

    total_requests: int = 0
    failed_authentications: int = 0
    access_denied_count: int = 0
    threats_detected: int = 0
    rate_limits_triggered: int = 0
    active_users: int = 0
    last_updated: float = field(default_factory=time.time)

    def to_dict(self) -> dict:
        return {
            "total_requests": self.total_requests,
            "failed_authentications": self.failed_authentications,
            "access_denied_count": self.access_denied_count,
            "threats_detected": self.threats_detected,
            "rate_limits_triggered": self.rate_limits_triggered,
            "active_users": self.active_users,
            "last_updated": self.last_updated,
        }


@dataclass
class SecurityReportData:
    """Unified report containing current system security state and recent history."""

    timestamp: float
    metrics: SecurityMetrics
    threats: List[ThreatIndicator] = field(default_factory=list)
    recent_violations: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "secure"  # secure / degraded / compromised

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "metrics": self.metrics.to_dict(),
            "threats": [
                {
                    "indicator_type": t.indicator_type,
                    "description": t.description,
                    "severity": t.severity.value,
                    "matched_pattern": t.matched_pattern,
                }
                for t in self.threats
            ],
            "recent_violations": self.recent_violations,
            "status": self.status,
        }
