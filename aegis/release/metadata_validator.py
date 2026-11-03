"""
aegis.release.metadata_validator
================================
Validates release and status metadata consistency across repository configs,
pyproject.toml, STATUS.md, and release candidate manifests.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Tuple
import yaml

CANONICAL_BASELINE_COMMIT = "7c05522643e503396795d99e381d201268ebe7fe"
CANONICAL_BASELINE_TAG = "aegis-baseline-001"


class ReleaseMetadataValidator:
    """Validates repository-wide release metadata alignment."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or Path.cwd()

    def load_release_config(self) -> Dict[str, Any]:
        cfg_path = self.repo_root / "configs" / "release" / "release.yaml"
        if not cfg_path.exists():
            raise FileNotFoundError(f"Release config not found at {cfg_path}")
        with open(cfg_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)

    def load_pyproject_version(self) -> str:
        pyproj_path = self.repo_root / "pyproject.toml"
        if not pyproj_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {pyproj_path}")
        with open(pyproj_path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip().startswith("version ="):
                    # version = "0.1.0-alpha.1"
                    return line.split("=")[1].strip().strip('"\'')
        raise ValueError("Version declaration not found in pyproject.toml")

    def load_release_candidate(self) -> Dict[str, Any]:
        rc_path = self.repo_root / "audit" / "release-candidate.json"
        if not rc_path.exists():
            raise FileNotFoundError(f"release-candidate.json not found at {rc_path}")
        with open(rc_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def load_status_header(self) -> str:
        status_path = self.repo_root / "STATUS.md"
        if not status_path.exists():
            raise FileNotFoundError(f"STATUS.md not found at {status_path}")
        with open(status_path, "r", encoding="utf-8") as f:
            lines = [f.readline() for _ in range(5)]
            return "".join(lines)

    def validate(self) -> Tuple[bool, List[str]]:
        errors: List[str] = []

        # 1. Load release config
        try:
            rel_cfg = self.load_release_config()
        except Exception as e:
            return False, [f"Failed to load release.yaml: {e}"]

        rel_data = rel_cfg.get("release", {})
        expected_version = rel_data.get("version")
        if not expected_version:
            errors.append("release.yaml missing release.version")

        # 2. Check pyproject.toml
        try:
            pyproj_ver = self.load_pyproject_version()
            if pyproj_ver != expected_version:
                errors.append(
                    f"Version mismatch: pyproject.toml ({pyproj_ver}) != release.yaml ({expected_version})"
                )
        except Exception as e:
            errors.append(f"Failed to read pyproject.toml version: {e}")

        # 3. Check release-candidate.json
        try:
            rc_data = self.load_release_candidate()
            rc_ver = rc_data.get("release_candidate")
            if rc_ver != expected_version:
                errors.append(
                    f"Version mismatch: release-candidate.json ({rc_ver}) != release.yaml ({expected_version})"
                )

            rc_git = rc_data.get("git", {})
            canonical_sha = rc_git.get("canonical_commit")
            if canonical_sha != CANONICAL_BASELINE_COMMIT:
                errors.append(
                    f"Canonical commit mismatch in release-candidate.json: {canonical_sha} != {CANONICAL_BASELINE_COMMIT}"
                )
        except Exception as e:
            errors.append(f"Failed to read release-candidate.json: {e}")

        # 4. Check STATUS.md
        try:
            status_hdr = self.load_status_header()
            short_sha = CANONICAL_BASELINE_COMMIT[:7]
            if short_sha not in status_hdr and CANONICAL_BASELINE_COMMIT not in status_hdr:
                errors.append(f"STATUS.md does not reference canonical baseline commit {short_sha}")
            if expected_version not in status_hdr:
                errors.append(f"STATUS.md does not reference release version {expected_version}")
        except Exception as e:
            errors.append(f"Failed to read STATUS.md: {e}")

        # 5. Check Canonical Baseline in release.yaml
        cb = rel_data.get("canonical_baseline", {})
        if cb.get("commit_sha") != CANONICAL_BASELINE_COMMIT:
            errors.append(
                f"release.yaml canonical commit mismatch: {cb.get('commit_sha')} != {CANONICAL_BASELINE_COMMIT}"
            )
        if cb.get("tag") != CANONICAL_BASELINE_TAG:
            errors.append(
                f"release.yaml canonical tag mismatch: {cb.get('tag')} != {CANONICAL_BASELINE_TAG}"
            )

        return len(errors) == 0, errors
