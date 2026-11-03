"""
aegis/audit/traceability/provenance_builder.py
=============================================
Builds authoritative provenance manifests connecting runs to source commits and configs.
"""

from __future__ import annotations

import datetime
from typing import Any, Dict


class ProvenanceBuilder:
    """Constructs verifiable provenance records."""

    @classmethod
    def build(
        cls,
        run_identity: Dict[str, Any],
        git_snapshot: Dict[str, Any],
        config_snapshot: Dict[str, Any],
        env_snapshot: Dict[str, Any],
        started_at: str,
        completed_at: str,
        artifact_count: int = 0,
    ) -> Dict[str, Any]:
        return {
            "provenance_version": "1.0",
            "run": {
                "run_id": run_identity.get("run_id"),
                "run_uuid": run_identity.get("run_uuid"),
                "baseline_id": run_identity.get("baseline_id"),
                "trigger": run_identity.get("trigger", "CLI"),
            },
            "source": {
                "repository": git_snapshot.get("repository", "AEGIS-DocIntel"),
                "remote_url": git_snapshot.get("remote_url", ""),
                "branch": git_snapshot.get("branch"),
                "commit_sha": git_snapshot.get("commit_sha", ""),
                "commit_timestamp": git_snapshot.get("commit_timestamp", ""),
                "working_tree_clean": bool(git_snapshot.get("working_tree_clean", False)),
                "modified_files_count": git_snapshot.get("modified_files_count", 0),
                "untracked_files_count": git_snapshot.get("untracked_files_count", 0),
            },
            "configuration": {
                "profile": config_snapshot.get("profile", "default"),
                "sha256": config_snapshot.get("sha256", ""),
                "resolved_at": config_snapshot.get("resolved_at", datetime.datetime.now(datetime.timezone.utc).isoformat()),
            },
            "environment": env_snapshot,
            "execution": {
                "runner_version": "1.0.0",
                "started_at": started_at,
                "completed_at": completed_at,
            },
            "integrity": {
                "manifest_algorithm": "SHA-256",
                "artifact_count": artifact_count,
            }
        }
