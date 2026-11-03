"""
aegis/audit/traceability/run_identity.py
========================================
Generates human-readable, globally unique run identifiers with UUID backing.
"""

from __future__ import annotations

import datetime
import random
import string
import uuid
from typing import Any, Dict


class RunIdentity:
    """Produces unique, sortable, compliant run identifiers."""

    @classmethod
    def generate(cls, prefix: str = "AG", baseline_id: str = "AEGIS-BASELINE-001", trigger: str = "CLI") -> Dict[str, Any]:
        now = datetime.datetime.now(datetime.timezone.utc)
        ts_str = now.strftime("%Y%m%d-%H%M%S")
        rand_suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        run_id = f"{prefix}-{ts_str}-{rand_suffix}"
        run_uuid = str(uuid.uuid4())

        return {
            "run_id": run_id,
            "run_uuid": run_uuid,
            "project": "AEGIS-DocIntel",
            "baseline_id": baseline_id,
            "trigger": trigger,
            "created_at": now.isoformat(),
        }
