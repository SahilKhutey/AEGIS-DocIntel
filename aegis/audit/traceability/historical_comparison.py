"""
aegis/audit/traceability/historical_comparison.py
=================================================
Compares historical audit executions, analyzing regressions, new findings,
and resolved defects based on stable finding fingerprints.
"""

from __future__ import annotations

from typing import Any, Dict, List, Set


class HistoricalComparison:
    """Computes differential analysis between two audit runs."""

    @classmethod
    def compare(
        cls,
        baseline_run: Dict[str, Any],
        current_run: Dict[str, Any],
    ) -> Dict[str, Any]:
        base_id = baseline_run.get("run_id", "BASELINE")
        curr_id = current_run.get("run_id", "CURRENT")

        # 1. Findings comparison
        base_findings = baseline_run.get("findings", [])
        curr_findings = current_run.get("findings", [])

        base_fp_map = {f.get("fingerprint", f.get("finding_id", "")): f for f in base_findings}
        curr_fp_map = {f.get("fingerprint", f.get("finding_id", "")): f for f in curr_findings}

        base_fps = set(base_fp_map.keys()) - {""}
        curr_fps = set(curr_fp_map.keys()) - {""}

        new_fps = curr_fps - base_fps
        resolved_fps = base_fps - curr_fps
        persistent_fps = base_fps & curr_fps

        new_findings = [curr_fp_map[fp] for fp in sorted(new_fps)]
        resolved_findings = [base_fp_map[fp] for fp in sorted(resolved_fps)]
        persistent_findings = [curr_fp_map[fp] for fp in sorted(persistent_fps)]

        # 2. Suite status regressions
        base_suites = {s.get("suite_id", "").lower(): s.get("status", "") for s in baseline_run.get("suites", [])}
        curr_suites = {s.get("suite_id", "").lower(): s.get("status", "") for s in current_run.get("suites", [])}

        suite_regressions = []
        for sid, curr_status in curr_suites.items():
            prev_status = base_suites.get(sid)
            if prev_status == "PASSED" and curr_status in {"FAILED", "ERROR", "TIMEOUT"}:
                suite_regressions.append({
                    "suite_id": sid,
                    "previous_status": prev_status,
                    "current_status": curr_status,
                })

        return {
            "baseline_run_id": base_id,
            "current_run_id": curr_id,
            "new_findings_count": len(new_findings),
            "resolved_findings_count": len(resolved_findings),
            "persistent_findings_count": len(persistent_findings),
            "reopened_findings_count": 0,
            "suite_regressions_count": len(suite_regressions),
            "new_findings": new_findings,
            "resolved_findings": resolved_findings,
            "persistent_findings": persistent_findings,
            "suite_regressions": suite_regressions,
        }
