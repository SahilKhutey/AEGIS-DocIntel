"""
AEGIS-DocIntel Disaster Recovery Verification Suite
PROT-FINAL-05: Workstream DEP-12

Validates that backup and restoration fulfill target recovery objectives:
- Recovery Point Objective (RPO) < 24 hours
- Recovery Time Objective (RTO) < 4 hours
- Revocation state integrity post-restoration (DEP-TEST-012, DEP-TEST-017)
"""

from __future__ import annotations

import time
from datetime import datetime, timezone, timedelta
from typing import Any, Dict


def verify_recovery_objectives(
    snapshot_timestamp: datetime,
    restoration_duration_seconds: float,
    revoked_license_ids: list[str],
    restored_license_status_map: Dict[str, str],
) -> Dict[str, Any]:
    """
    Evaluates restoration metrics against operational recovery targets.
    """
    now = datetime.now(timezone.utc)
    data_age_hours = (now - snapshot_timestamp).total_seconds() / 3600.0

    rpo_compliant = data_age_hours <= 24.0
    rto_compliant = (restoration_duration_seconds / 3600.0) <= 4.0

    # Ensure none of the revoked licenses became ACTIVE
    resurrected = [
        lic_id for lic_id in revoked_license_ids
        if restored_license_status_map.get(lic_id) == "ACTIVE"
    ]
    revocation_preserved = len(resurrected) == 0

    overall_pass = rpo_compliant and rto_compliant and revocation_preserved

    return {
        "overall_pass": overall_pass,
        "rpo_hours": round(data_age_hours, 2),
        "rpo_target_hours": 24.0,
        "rpo_compliant": rpo_compliant,
        "rto_seconds": round(restoration_duration_seconds, 2),
        "rto_target_hours": 4.0,
        "rto_compliant": rto_compliant,
        "revocation_preserved": revocation_preserved,
        "resurrected_licenses": resurrected,
        "evaluated_at": now.isoformat(),
    }
