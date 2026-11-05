"""
AEGIS-DocIntel — Release Freeze Verification Test Suite (WP-09.01)
==================================================================
Validates release candidate freeze invariants RC-001 through RC-010.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import pytest


ROOT = Path(__file__).parent.parent.parent


def test_rc001_git_commit_identity():
    """RC-001: Git commit identity is recorded in release manifest."""
    manifest_path = ROOT / "RELEASE_CANDIDATE_MANIFEST.json"
    assert manifest_path.exists(), "RELEASE_CANDIDATE_MANIFEST.json missing"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["git"]["commit_sha"] == "c34fe022cec225de516bf4d7997cecf848ea4a1d"
    assert data["release_id"] == "AEGIS-MVP-RC1"
    assert data["version"] == "1.0.0-rc.1"


def test_rc002_release_scope_definition():
    """RC-002: Release scope defines IN_SCOPE, OUT_OF_SCOPE, and DEFERRED items."""
    scope_path = ROOT / "RELEASE_SCOPE.md"
    assert scope_path.exists(), "RELEASE_SCOPE.md missing"
    content = scope_path.read_text(encoding="utf-8")
    assert "IN_SCOPE" in content
    assert "OUT_OF_SCOPE" in content
    assert "DEFERRED" in content


def test_rc003_dependency_snapshot_and_sbom():
    """RC-003: Dependency inventory and CycloneDX SBOM are populated."""
    dep_path = ROOT / "DEPENDENCY_INVENTORY.json"
    sbom_path = ROOT / "SBOM.json"
    assert dep_path.exists(), "DEPENDENCY_INVENTORY.json missing"
    assert sbom_path.exists(), "SBOM.json missing"

    with open(dep_path, "r", encoding="utf-8") as f:
        dep_data = json.load(f)
    with open(sbom_path, "r", encoding="utf-8") as f:
        sbom_data = json.load(f)

    assert (dep_data["python_packages_count"] + dep_data["node_packages_count"]) >= 50
    assert sbom_data["bomFormat"] == "CycloneDX"
    assert len(sbom_data["components"]) >= 50


def test_rc004_configuration_register():
    """RC-004: Configuration register hashes all configuration files."""
    cfg_path = ROOT / "RELEASE_CONFIGURATION_REGISTER.md"
    assert cfg_path.exists(), "RELEASE_CONFIGURATION_REGISTER.md missing"
    content = cfg_path.read_text(encoding="utf-8")
    assert "SHA-256" in content
    assert "pyproject.toml" in content


def test_rc005_dataset_version_register():
    """RC-005: Dataset version register confirms holdout integrity."""
    ds_path = ROOT / "DATASET_VERSION_REGISTER.json"
    assert ds_path.exists(), "DATASET_VERSION_REGISTER.json missing"
    with open(ds_path, "r", encoding="utf-8") as f:
        ds_data = json.load(f)
    assert ds_data["holdout_compromised"] is False
    assert ds_data["holdout_integrity_verified"] is True
    assert len(ds_data["datasets"]) >= 5


def test_rc006_build_artifact_identity():
    """RC-006: Build artifact identity is captured."""
    manifest_path = ROOT / "RELEASE_CANDIDATE_MANIFEST.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "build_id" in data["frontend"]
    assert data["frontend"]["build_status"] == "PASS"


def test_rc007_to_rc010_manifest_integrity_and_status():
    """RC-007..RC-010: Manifest status is FROZEN with complete metadata."""
    manifest_path = ROOT / "RELEASE_CANDIDATE_MANIFEST.json"
    with open(manifest_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["status"] == "FROZEN"
    assert data["database"]["schema_version"] == "v1.4.0-mvp"
    assert data["backend"]["endpoints_count"] == 76
