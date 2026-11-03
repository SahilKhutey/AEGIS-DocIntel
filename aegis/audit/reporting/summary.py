"""
aegis/audit/reporting/summary.py
================================
Computes consolidated run summaries with mathematical completion ratios and duration.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict
from aegis.audit.evidence.models import AuditSummary


def compute_summary(run_data: Dict[str, Any], planned_count: int) -> AuditSummary:
    run_id = run_data.get("run_id", "UNKNOWN")
    exec_data = run_data.get("execution", {})
    started_at = exec_data.get("started_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    completed_at = exec_data.get("completed_at", datetime.datetime.now(datetime.timezone.utc).isoformat())
    
    # Calculate duration
    duration = exec_data.get("duration_seconds")
    if duration is None:
        try:
            t0 = datetime.datetime.fromisoformat(started_at)
            t1 = datetime.datetime.fromisoformat(completed_at)
            duration = max(0.0, (t1 - t0).total_seconds())
        except Exception:
            duration = 0.0

    suites = run_data.get("suites", [])
    executed_count = len(suites)
    passed_count = sum(1 for s in suites if s.get("status") == "PASSED")
    failed_count = sum(1 for s in suites if s.get("status") in {"FAILED", "ERROR", "TIMEOUT"})

    # Completion ratio: C = (N_terminal / N_planned) * 100
    if planned_count > 0:
        completion_ratio = min(100.0, round((executed_count / planned_count) * 100.0, 2))
    else:
        completion_ratio = 100.0 if executed_count > 0 else 0.0

    findings = run_data.get("findings", [])
    total_findings = len(findings)
    crit = sum(1 for f in findings if f.get("severity") == "CRITICAL")
    high = sum(1 for f in findings if f.get("severity") == "HIGH")

    overall_status = exec_data.get("status", "PASSED")

    return AuditSummary(
        run_id=run_id,
        status=overall_status,
        started_at=started_at,
        completed_at=completed_at,
        duration_seconds=round(duration, 4),
        planned_suites=planned_count,
        executed_suites=executed_count,
        passed_suites=passed_count,
        failed_suites=failed_count,
        completion_ratio=completion_ratio,
        total_findings=total_findings,
        critical_findings=crit,
        high_findings=high,
    )
