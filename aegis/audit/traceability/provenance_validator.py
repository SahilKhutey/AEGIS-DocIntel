"""
aegis/audit/traceability/provenance_validator.py
===============================================
Validates provenance manifests and enforces working-tree cleanliness in strict mode.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List
from aegis.audit.runner.exceptions import ProvenanceError


class ProvenanceValidator:
    """Validates provenance records and verifies policies."""

    @classmethod
    def validate(cls, provenance: Dict[str, Any], strict_mode: bool = False) -> List[str]:
        errors: List[str] = []

        if not isinstance(provenance, dict):
            return ["Provenance record must be an object"]

        source = provenance.get("source", {})
        commit_sha = source.get("commit_sha", "")
        if not re.match(r"^[a-f0-9]{40}$", commit_sha):
            errors.append(f"Invalid git commit SHA in provenance: '{commit_sha}'")

        # Strict mode check: Dirty working tree is strictly forbidden in release mode
        is_clean = bool(source.get("working_tree_clean", False))
        if strict_mode and not is_clean:
            errors.append(
                f"Dirty working tree rejected in strict release mode (modified: {source.get('modified_files_count')}, untracked: {source.get('untracked_files_count')})"
            )

        config = provenance.get("configuration", {})
        config_hash = config.get("sha256", "")
        if not re.match(r"^[a-f0-9]{64}$", config_hash):
            errors.append(f"Invalid configuration SHA-256 hash in provenance: '{config_hash}'")

        return errors
