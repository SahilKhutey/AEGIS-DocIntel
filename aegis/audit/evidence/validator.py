"""
aegis/audit/evidence/validator.py
================================
Validates audit evidence objects against schema contracts, statistical consistency,
and integrity invariants.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from aegis.audit.evidence.hashing import hash_file
from aegis.audit.runner.exceptions import EvidenceValidationError

VALID_SEVERITIES = {"CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"}
VALID_STATUSES = {
    "PENDING", "RUNNING", "PASSED", "FAILED",
    "ERROR", "TIMEOUT", "SKIPPED", "BLOCKED", "CANCELLED", "PARTIAL"
}
FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"ghp_[A-Za-z0-9_]{36}"),
    re.compile(r"sk-[A-Za-z0-9_-]{32,}"),
    re.compile(r"AIza[0-9A-Za-z-_]{35}"),
]


class EvidenceValidator:
    """Rigorous validator for evidence manifests, runs, suites, and artifacts."""

    @classmethod
    def validate_run(cls, run_data: Dict[str, Any], root_dir: Optional[Path] = None) -> List[str]:
        errors: List[str] = []

        # Required top-level keys
        for key in ["schema_version", "run_id", "baseline_id", "execution", "source", "configuration", "environment", "suites"]:
            if key not in run_data:
                errors.append(f"Missing required field in run data: '{key}'")

        run_id = run_data.get("run_id", "")
        if not re.match(r"^AG-[0-9]{8}-[0-9]{6}-[A-Za-z0-9]+$", run_id):
            errors.append(f"Invalid run_id format: '{run_id}' (must match AG-YYYYMMDD-HHMMSS-<SUFFIX>)")

        exec_data = run_data.get("execution", {})
        status = exec_data.get("status", "")
        if status not in VALID_STATUSES:
            errors.append(f"Invalid execution status: '{status}'")

        # Validate suites and statistics
        suites = run_data.get("suites", [])
        for idx, s in enumerate(suites):
            s_id = s.get("suite_id")
            if not s_id:
                errors.append(f"Suite at index {idx} has missing suite_id")
            
            s_status = s.get("status")
            if s_status not in VALID_STATUSES:
                errors.append(f"Suite '{s_id}' has invalid status: '{s_status}'")

            stats = s.get("statistics", {})
            total = stats.get("total", 0)
            passed = stats.get("passed", 0)
            failed = stats.get("failed", 0)
            skipped = stats.get("skipped", 0)
            errs = stats.get("errors", 0)
            if total != (passed + failed + skipped + errs):
                errors.append(
                    f"Suite '{s_id}' statistics mismatch: total={total} != passed({passed}) + failed({failed}) + skipped({skipped}) + errors({errs})"
                )

        # Validate findings
        findings = run_data.get("findings", [])
        for f in findings:
            fid = f.get("finding_id")
            sev = f.get("severity")
            if sev not in VALID_SEVERITIES:
                errors.append(f"Finding '{fid}' has invalid severity '{sev}'")

        # Validate artifacts & integrity
        artifacts = run_data.get("artifacts", [])
        for a in artifacts:
            rel_path = a.get("relative_path", "")
            if ".." in Path(rel_path).parts:
                errors.append(f"Unsafe artifact relative_path contains traversal (..): '{rel_path}'")

            sha = a.get("sha256", "")
            if not re.match(r"^[a-f0-9]{64}$", sha):
                errors.append(f"Artifact '{a.get('artifact_id')}' has invalid sha256 hash format: '{sha}'")

            if root_dir and rel_path:
                phys_path = root_dir / rel_path
                if phys_path.is_file():
                    computed_hash = hash_file(phys_path)
                    if computed_hash != sha:
                        errors.append(f"Artifact integrity failure for '{rel_path}': manifest {sha} != disk {computed_hash}")

        # Check for leaked secrets in string representation
        dumped = str(run_data)
        for pat in FORBIDDEN_SECRET_PATTERNS:
            if pat.search(dumped):
                errors.append("Sensitive API key or credential pattern detected in evidence payload")
                break

        return errors
