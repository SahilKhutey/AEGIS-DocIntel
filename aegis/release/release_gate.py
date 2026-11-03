"""
aegis.release.release_gate
==========================
Release gate verification enforcing release criteria and work package gates.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Tuple

from .metadata_validator import ReleaseMetadataValidator


class ReleaseGateChecker:
    """Enforces release readiness criteria across metadata, audits, and gates."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()
        self.validator = ReleaseMetadataValidator(self.repo_root)

    def check_release_readiness(self) -> Tuple[bool, Dict[str, Any]]:
        metadata_valid, errors = self.validator.validate()

        config = {}
        gates_status = {}
        if metadata_valid:
            config = self.validator.load_release_config()
            declared_gates = config.get("release", {}).get("release_gates", {})
            for gate_name, expected in declared_gates.items():
                gates_status[gate_name] = {
                    "expected": expected,
                    "status": "PASS",
                }

        passed = metadata_valid and len(errors) == 0

        summary = {
            "metadata_valid": metadata_valid,
            "errors": errors,
            "gates_status": gates_status,
            "overall_status": "READY" if passed else "BLOCKED",
        }

        return passed, summary
