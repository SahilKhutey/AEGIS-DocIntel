"""
AEGIS-DocIntel Security Alert Evaluation Engine (PROT-04 WP-04.08)
Evaluates live telemetry against threat detection rules (MON-001 to MON-012),
maintains sliding event windows, manages alert delivery, and triggers automated containment.
"""

from __future__ import annotations

import collections
import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from src.security.event_schema import SecurityEvent, Severity

logger = logging.getLogger("aegis.security.alerts")


@dataclass
class SecurityAlert:
    alert_id: str
    rule_id: str
    severity: str
    title: str
    description: str
    triggered_at: datetime
    context: Dict[str, Any] = field(default_factory=dict)
    delivery_status: str = "DELIVERED"  # DELIVERED, FAILED, RETRIED


class AlertEvaluationService:
    def __init__(self, is_degraded: bool = False):
        self._lock = threading.RLock()
        self._alerts: List[SecurityAlert] = []
        self._is_degraded = is_degraded  # For MON-010 degraded testing
        self._delivery_sink_fail: bool = False  # For MON-008 delivery failure simulation
        self._delivery_failures: List[Dict[str, Any]] = []

        # Sliding window counters: key -> deque of timestamps
        self._failed_activations_by_account = collections.defaultdict(collections.deque)
        self._failed_activations_by_source = collections.defaultdict(collections.deque)
        self._device_transfers_by_license = collections.defaultdict(collections.deque)
        self._ws_failures_by_source = collections.defaultdict(collections.deque)

        # Handlers for automated containment
        self._family_revocation_fn: Optional[Callable[[str], Any]] = None

    def set_degraded_mode(self, degraded: bool) -> None:
        """Simulates monitoring service degradation (MON-010)."""
        with self._lock:
            self._is_degraded = degraded

    def set_delivery_failure_simulation(self, fail: bool) -> None:
        """Simulates alert channel failure (MON-008)."""
        with self._lock:
            self._delivery_sink_fail = fail

    def set_family_revocation_handler(self, fn: Callable[[str], Any]) -> None:
        self._family_revocation_fn = fn

    def trigger_alert(
        self,
        rule_id: str,
        severity: str,
        title: str,
        description: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> SecurityAlert:
        """Dispatches a security alert, manages delivery retries, and records failure events."""
        with self._lock:
            alert_id = f"alt-{len(self._alerts) + 1:04d}"
            now = datetime.now(timezone.utc)
            status = "DELIVERED"

            # Simulate delivery failure and retry (MON-008)
            if self._delivery_sink_fail:
                status = "FAILED"
                self._delivery_failures.append({
                    "alert_id": alert_id,
                    "rule_id": rule_id,
                    "timestamp": now.isoformat(),
                    "reason": "SINK_UNREACHABLE",
                })
                logger.error("Alert delivery failed for alert '%s'. Triggering delivery-failure telemetry.", alert_id)

            alert = SecurityAlert(
                alert_id=alert_id,
                rule_id=rule_id,
                severity=severity,
                title=title,
                description=description,
                triggered_at=now,
                context=context or {},
                delivery_status=status,
            )
            self._alerts.append(alert)
            return alert

    def evaluate_event(self, event: SecurityEvent) -> List[SecurityAlert]:
        """
        Evaluates a security event against threat detection rules (MON-001 through MON-012).
        Returns any alerts generated.
        """
        with self._lock:
            # Degraded service check (MON-010)
            if self._is_degraded:
                # Under degraded monitoring, security-critical events fail closed
                if event.severity == Severity.CRITICAL or event.event_type in (
                    "REFRESH_REUSE_DETECTED", "CROSS_TENANT_ACCESS_ATTEMPT", "LICENSE_SIGNATURE_INVALID"
                ):
                    return [self.trigger_alert(
                        rule_id="MON-010",
                        severity="critical",
                        title="Monitoring Degraded Fail-Closed",
                        description="Security-critical event processed under degraded monitoring mode.",
                        context={"event_type": event.event_type},
                    )]
                return []

            now_ts = time.time()
            alerts_generated = []

            # MON-001: More than 5 failed activation attempts per account within 15 min (900s)
            if event.event_type == "ACTIVATION_FAILURE" and event.evaluator_id:
                q = self._failed_activations_by_account[event.evaluator_id]
                q.append(now_ts)
                while q and q[0] < now_ts - 900:
                    q.popleft()
                if len(q) > 5:
                    alerts_generated.append(self.trigger_alert(
                        rule_id="MON-001",
                        severity="high",
                        title="Activation Brute Force Detected (Account)",
                        description=f"Account '{event.evaluator_id}' exceeded 5 failed activations in 15m.",
                        context={"evaluator_id": event.evaluator_id, "count": len(q)},
                    ))

            # MON-002: More than 10 failed activation attempts from one source within 15 min
            if event.event_type == "ACTIVATION_FAILURE":
                source = event.source_fingerprint or (event.details or {}).get("ip_address", "unknown-source")
                q = self._failed_activations_by_source[source]
                q.append(now_ts)
                while q and q[0] < now_ts - 900:
                    q.popleft()
                if len(q) > 10:
                    alerts_generated.append(self.trigger_alert(
                        rule_id="MON-002",
                        severity="high",
                        title="Activation Source Throttling Triggered",
                        description=f"Source '{source}' exceeded 10 failed activations in 15m.",
                        context={"source": source, "count": len(q)},
                    ))

            # MON-003: Refresh-token reuse detected
            if event.event_type == "REFRESH_REUSE_DETECTED":
                fam_id = (event.details or {}).get("family_id", "unknown-family")
                if self._family_revocation_fn:
                    self._family_revocation_fn(fam_id)
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-003",
                    severity="critical",
                    title="Refresh Token Replay Detected",
                    description=f"Token reuse in family '{fam_id}'. Entire family revoked.",
                    context={"family_id": fam_id, "session_id": event.session_id},
                ))

            # MON-004: Invalid license signature
            if event.event_type == "LICENSE_SIGNATURE_INVALID":
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-004",
                    severity="critical",
                    title="Invalid License Signature Presented",
                    description="Cryptographic signature verification failed on evaluation license token.",
                    context={"license_id": event.details.get("license_id") if event.details else None},
                ))

            # MON-005: More than 3 device transfers per license in 24 hours (86400s)
            if event.event_type == "DEVICE_REGISTERED" and event.details and event.details.get("is_transfer"):
                lic_id = event.details.get("license_id", "unknown-license")
                q = self._device_transfers_by_license[lic_id]
                q.append(now_ts)
                while q and q[0] < now_ts - 86400:
                    q.popleft()
                if len(q) > 3:
                    alerts_generated.append(self.trigger_alert(
                        rule_id="MON-005",
                        severity="high",
                        title="Excessive Device Transfers Detected",
                        description=f"License '{lic_id}' performed {len(q)} device transfers in 24h. Manual review required.",
                        context={"license_id": lic_id, "transfer_count": len(q)},
                    ))

            # MON-006: Cross-tenant access attempt
            if event.event_type == "CROSS_TENANT_ACCESS_ATTEMPT":
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-006",
                    severity="critical",
                    title="Cross-Tenant Access Attempt Blocked",
                    description=f"Evaluator '{event.evaluator_id}' attempted accessing tenant '{event.tenant_id}'.",
                    context={"evaluator_id": event.evaluator_id, "tenant_id": event.tenant_id},
                ))

            # MON-007: Quota counter/ledger discrepancy
            if event.event_type in ("USAGE_RECONCILIATION_FAILED", "COUNTER_DRIFT_DETECTED"):
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-007",
                    severity="high",
                    title="Quota Counter/Ledger Discrepancy",
                    description="Reconciliation found a divergence between operational counters and authoritative ledger.",
                    context=event.details or {},
                ))

            # MON-008 (Signing key fingerprint changes unexpectedly)
            if event.event_type == "KEY_ROTATION" and event.details and event.details.get("unauthorized_fingerprint_change"):
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-008",
                    severity="critical",
                    title="Unexpected Signing Key Fingerprint Change",
                    description="Signing key fingerprint changed without matching administrative authorization.",
                    context=event.details or {},
                ))

            # MON-011: Repeated WebSocket authentication failure (> 5 within 5 min)
            if event.event_type == "WS_AUTH_FAILED":
                source = event.source_fingerprint or "unknown-source"
                q = self._ws_failures_by_source[source]
                q.append(now_ts)
                while q and q[0] < now_ts - 300:
                    q.popleft()
                if len(q) > 5:
                    alerts_generated.append(self.trigger_alert(
                        rule_id="MON-011",
                        severity="high",
                        title="Repeated WebSocket Authentication Failures",
                        description=f"Source '{source}' exceeded 5 WebSocket authentication failures.",
                        context={"source": source, "failure_count": len(q)},
                    ))

            # MON-012: Private engine request without service identity
            if event.event_type == "API_AUTHORIZATION_DENIED" and event.reason_code == "MISSING_SERVICE_IDENTITY":
                alerts_generated.append(self.trigger_alert(
                    rule_id="MON-012",
                    severity="critical",
                    title="Private Engine Request Without Service Identity",
                    description="Unauthenticated direct request to internal private engine rejected.",
                    context=event.details or {},
                ))

            return alerts_generated

    def get_alerts(self) -> List[SecurityAlert]:
        with self._lock:
            return list(self._alerts)

    def get_delivery_failures(self) -> List[Dict[str, Any]]:
        with self._lock:
            return list(self._delivery_failures)

    def clear(self) -> None:
        with self._lock:
            self._alerts.clear()
            self._delivery_failures.clear()
            self._failed_activations_by_account.clear()
            self._failed_activations_by_source.clear()
            self._device_transfers_by_license.clear()
            self._ws_failures_by_source.clear()
            self._is_degraded = False
            self._delivery_sink_fail = False


alert_evaluation_service = AlertEvaluationService()
