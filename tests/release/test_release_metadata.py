"""
tests/release/test_release_metadata.py
======================================
REL-001 through REL-010 tests verifying release metadata consistency,
baseline references, version alignment, and release readiness gates.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.release.metadata_validator import (
    CANONICAL_BASELINE_COMMIT,
    CANONICAL_BASELINE_TAG,
    ReleaseMetadataValidator,
)
from aegis.release.release_gate import ReleaseGateChecker

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_rel_001_release_config_loading():
    """REL-001: Release config loads successfully and contains core fields."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    cfg = validator.load_release_config()
    rel = cfg.get("release", {})
    assert rel.get("project") == "aegis-docintel"
    assert rel.get("version") == "0.1.0-alpha.1"
    assert rel.get("stage") == "alpha"


def test_rel_002_pyproject_version_match():
    """REL-002: pyproject.toml version matches release.yaml version."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    pyproj_ver = validator.load_pyproject_version()
    cfg_ver = validator.load_release_config()["release"]["version"]
    assert pyproj_ver == cfg_ver
    assert pyproj_ver == "0.1.0-alpha.1"


def test_rel_003_release_candidate_version_match():
    """REL-003: release-candidate.json version matches release.yaml version."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    rc = validator.load_release_candidate()
    cfg_ver = validator.load_release_config()["release"]["version"]
    assert rc["release_candidate"] == cfg_ver


def test_rel_004_canonical_baseline_commit_match():
    """REL-004: Canonical baseline commit matches frozen SHA 7c05522643..."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    cfg = validator.load_release_config()["release"]
    cb_sha = cfg["canonical_baseline"]["commit_sha"]
    assert cb_sha == CANONICAL_BASELINE_COMMIT
    assert cb_sha == "7c05522643e503396795d99e381d201268ebe7fe"


def test_rel_005_canonical_baseline_tag_match():
    """REL-005: Canonical baseline tag matches aegis-baseline-001."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    cfg = validator.load_release_config()["release"]
    assert cfg["canonical_baseline"]["tag"] == CANONICAL_BASELINE_TAG
    assert cfg["canonical_baseline"]["tag"] == "aegis-baseline-001"


def test_rel_006_status_md_references_baseline():
    """REL-006: STATUS.md header references canonical baseline commit and version."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    hdr = validator.load_status_header()
    assert "7c05522" in hdr
    assert "aegis-baseline-001" in hdr
    assert "0.1.0-alpha.1" in hdr


def test_rel_007_detect_mismatched_version(tmp_path):
    """REL-007: Metadata validator detects mismatched pyproject version."""
    # Create fake release.yaml with wrong version
    cfg_dir = tmp_path / "configs" / "release"
    cfg_dir.mkdir(parents=True)
    cfg_file = cfg_dir / "release.yaml"
    cfg_file.write_text(
        "release:\n  project: aegis-docintel\n  version: 9.9.9\n  canonical_baseline:\n    commit_sha: "
        + CANONICAL_BASELINE_COMMIT
        + "\n    tag: "
        + CANONICAL_BASELINE_TAG
        + "\n",
        encoding="utf-8",
    )

    # Copy real pyproject.toml
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text("version = \"0.1.0-alpha.1\"\n", encoding="utf-8")

    validator = ReleaseMetadataValidator(tmp_path)
    valid, errors = validator.validate()
    assert not valid
    assert any("Version mismatch: pyproject.toml (0.1.0-alpha.1) != release.yaml (9.9.9)" in e for e in errors)


def test_rel_008_detect_mismatched_commit_sha(tmp_path):
    """REL-008: Metadata validator detects mismatched canonical commit SHA."""
    cfg_dir = tmp_path / "configs" / "release"
    cfg_dir.mkdir(parents=True)
    cfg_file = cfg_dir / "release.yaml"
    cfg_file.write_text(
        "release:\n  project: aegis-docintel\n  version: 0.1.0-alpha.1\n  canonical_baseline:\n    commit_sha: ffffffffffffffffffffffffffffffffffffffff\n    tag: aegis-baseline-001\n",
        encoding="utf-8",
    )
    pyproj = tmp_path / "pyproject.toml"
    pyproj.write_text("version = \"0.1.0-alpha.1\"\n", encoding="utf-8")

    validator = ReleaseMetadataValidator(tmp_path)
    valid, errors = validator.validate()
    assert not valid
    assert any("canonical commit mismatch" in e for e in errors)


def test_rel_009_release_gate_checker_readiness():
    """REL-009: Release gate checker evaluates release readiness."""
    checker = ReleaseGateChecker(REPO_ROOT)
    passed, summary = checker.check_release_readiness()
    assert passed is True
    assert summary["overall_status"] == "READY"
    assert "wp01_baseline" in summary["gates_status"]
    assert "wp02_audit_infrastructure" in summary["gates_status"]


def test_rel_010_full_repo_metadata_clean():
    """REL-010: End-to-end repository release metadata validation passes with 0 errors."""
    validator = ReleaseMetadataValidator(REPO_ROOT)
    valid, errors = validator.validate()
    assert valid is True
    assert len(errors) == 0
