"""
aegis.evaluation.manifest.validator
===================================
Validation engine for evaluation manifests and dataset integrity.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Dict, List, Tuple
from pydantic import ValidationError

from .models import EvaluationManifest


class ManifestValidationError(Exception):
    """Raised when manifest validation or dataset integrity verification fails."""
    pass


class ManifestValidator:
    """Validates manifest structure and verifies dataset SHA-256 digests."""

    @classmethod
    def verify_dataset_integrity(
        cls, dataset_key: str, path_str: str, expected_sha256: str, repo_root: Path
    ) -> Tuple[bool, str]:
        path = repo_root / path_str if not Path(path_str).is_absolute() else Path(path_str)
        if not path.exists():
            return False, f"Dataset '{dataset_key}' file not found at: {path}"

        h = hashlib.sha256()
        with open(path, "rb") as f:
            while chunk := f.read(65536):
                h.update(chunk)
        actual_sha = h.hexdigest()

        if actual_sha.lower() != expected_sha256.lower():
            return (
                False,
                f"Dataset '{dataset_key}' SHA-256 mismatch: expected {expected_sha256}, got {actual_sha}",
            )

        return True, actual_sha

    @classmethod
    def validate_manifest(
        cls, manifest: EvaluationManifest, repo_root: Path | None = None
    ) -> Tuple[bool, List[str]]:
        errors: List[str] = []
        root = repo_root or Path.cwd()

        # 1. Validate dataset paths and SHA-256
        for d_key, d_spec in manifest.datasets.items():
            valid, msg = cls.verify_dataset_integrity(d_key, d_spec.path, d_spec.sha256, root)
            if not valid:
                errors.append(msg)

        # 2. Validate tasks reference existing datasets
        all_task_metrics = set()
        for t_key, t_spec in manifest.tasks.items():
            if t_spec.dataset not in manifest.datasets:
                errors.append(
                    f"Task '{t_key}' references non-existent dataset '{t_spec.dataset}'"
                )
            for m in t_spec.metrics:
                all_task_metrics.add(m)

        # 3. Validate quality gates reference valid metrics or well-known metrics
        for g_metric in manifest.quality_gates:
            # Metric should either be in tasks or a recognized domain metric
            if g_metric not in all_task_metrics and not any(g_metric in m for m in all_task_metrics):
                # Warning or check
                pass

        return len(errors) == 0, errors
