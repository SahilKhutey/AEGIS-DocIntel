"""
aegis/audit/runner/result_normalizer.py
======================================
Normalizes suite execution results into standardized, schema-compliant structures
with strict mathematical consistency checks.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional


class AuditResultNormalizer:
    """Normalizes raw suite output and captures error envelopes."""

    VALID_STATUSES = {
        "PENDING", "RUNNING", "PASSED", "FAILED",
        "ERROR", "TIMEOUT", "SKIPPED", "BLOCKED", "CANCELLED"
    }

    @classmethod
    def normalize(
        cls,
        suite_id: str,
        suite_version: str,
        raw_result: Optional[Dict[str, Any]] = None,
        status: str = "PASSED",
        started_at: Optional[str] = None,
        completed_at: Optional[str] = None,
        duration_seconds: Optional[float] = None,
        error_type: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        started_at = started_at or now_iso
        completed_at = completed_at or now_iso

        if duration_seconds is None:
            duration_seconds = 0.0

        if raw_result is None:
            raw_result = {}

        candidate_status = raw_result.get("status", status).upper()
        if candidate_status not in cls.VALID_STATUSES:
            candidate_status = "ERROR"

        # Statistics normalization with mathematical consistency
        raw_stats = raw_result.get("statistics", {})
        passed = int(raw_stats.get("passed", 0))
        failed = int(raw_stats.get("failed", 0))
        skipped = int(raw_stats.get("skipped", 0))
        errors = int(raw_stats.get("errors", 0))
        
        computed_total = passed + failed + skipped + errors
        declared_total = raw_stats.get("total")
        total = int(declared_total) if declared_total is not None else computed_total
        
        # Enforce consistency: N_total = N_passed + N_failed + N_skipped + N_errors
        if total != computed_total:
            total = computed_total

        # Normalize findings
        findings: List[Dict[str, Any]] = raw_result.get("findings", [])
        artifacts: List[Dict[str, Any]] = raw_result.get("artifacts", [])

        normalized = {
            "suite_id": suite_id,
            "suite_version": suite_version,
            "status": candidate_status,
            "started_at": started_at,
            "completed_at": completed_at,
            "duration_seconds": round(float(duration_seconds), 4),
            "statistics": {
                "total": total,
                "passed": passed,
                "failed": failed,
                "skipped": skipped,
                "errors": errors,
            },
            "findings": findings,
            "artifacts": artifacts,
        }

        if error_type or raw_result.get("error_type"):
            normalized["error_type"] = error_type or raw_result.get("error_type")
        if error_message or raw_result.get("error_message"):
            normalized["error_message"] = error_message or raw_result.get("error_message")

        return normalized
