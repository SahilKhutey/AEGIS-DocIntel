"""
aegis/audit/traceability/finding_fingerprint.py
==============================================
Calculates stable, line-invariant cryptographic finding fingerprints for issue tracking.
"""

from __future__ import annotations

import hashlib
from pathlib import Path


class FindingFingerprint:
    """
    Computes invariant fingerprint:
    F = SHA256(suite_id || rule_id || normalized_file_path || normalized_identity)
    Line numbers are intentionally omitted so code movements do not change defect identity.
    """

    @staticmethod
    def compute(
        suite_id: str,
        rule_id: str,
        file_path: str = "",
        identity: str = "",
    ) -> str:
        norm_suite = suite_id.strip().upper()
        norm_rule = rule_id.strip().upper()
        norm_path = Path(file_path).as_posix().lower() if file_path else "GLOBAL"
        norm_id = identity.strip().lower()

        composite = f"{norm_suite}|{norm_rule}|{norm_path}|{norm_id}"
        return hashlib.sha256(composite.encode("utf-8")).hexdigest()
