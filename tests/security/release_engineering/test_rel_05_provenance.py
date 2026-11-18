"""
Release Engineering Test Suite — Build Provenance & Traceability (REL-001, REL-009, GATE-01, GATE-10)
PROT-FINAL-04: Workstream REL-08
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROVENANCE_PATH = REPO_ROOT / "release" / "provenance" / "build-provenance.json"
MANIFEST_PATH = REPO_ROOT / "release" / "manifests" / "manifest.json"


def test_rel_051_provenance_file_exists():
    """REL-009.1: Confirms build provenance statement is generated."""
    assert PROVENANCE_PATH.exists(), f"Provenance file missing: {PROVENANCE_PATH}"


def test_rel_052_slsa_v1_compliance():
    """REL-009.2: Confirms provenance adheres to in-toto Statement v1 and SLSA v1.0 specifications."""
    data = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    assert data.get("_type") == "https://in-toto.io/Statement/v1"
    assert data.get("predicateType") == "https://slsa.dev/provenance/v1"
    
    subjects = data.get("subject", [])
    assert len(subjects) >= 2
    subject_names = {s["name"] for s in subjects}
    assert "AEGIS-DocIntel-Demo-Edition.zip" in subject_names
    assert "manifest.json" in subject_names


def test_rel_053_source_commit_traceability():
    """REL-001 / GATE-01: Confirms release provenance traces directly to a valid Git commit SHA."""
    data = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    ext_params = data.get("predicate", {}).get("buildDefinition", {}).get("externalParameters", {})
    source_digest = ext_params.get("source", {}).get("digest", {})
    
    commit_sha = source_digest.get("sha1")
    assert commit_sha is not None and len(commit_sha) == 40, f"Invalid source commit SHA: {commit_sha}"
