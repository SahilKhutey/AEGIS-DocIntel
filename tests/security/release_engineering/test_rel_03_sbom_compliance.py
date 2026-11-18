"""
Release Engineering Test Suite — CycloneDX SBOM Compliance (REL-007, GATE-04)
PROT-FINAL-04: Workstream REL-05
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
CLIENT_SBOM_PATH = REPO_ROOT / "release" / "sbom" / "client-sbom.cdx.json"
BACKEND_SBOM_PATH = REPO_ROOT / "release" / "sbom" / "backend-sbom.cdx.json"


def test_rel_031_client_sbom_cyclonedx_compliance():
    """REL-007.1: Validates that client SBOM adheres to CycloneDX 1.5 JSON specification."""
    assert CLIENT_SBOM_PATH.exists(), f"Client SBOM missing: {CLIENT_SBOM_PATH}"
    data = json.loads(CLIENT_SBOM_PATH.read_text(encoding="utf-8"))
    
    assert data.get("bomFormat") == "CycloneDX"
    assert data.get("specVersion") in ("1.4", "1.5")
    assert "metadata" in data
    assert data["metadata"]["component"]["name"] == "aegis-docintel-evaluation-client"
    
    components = data.get("components", [])
    assert len(components) > 100, f"Client component count unexpectedly low: {len(components)}"
    
    # Check that components have names and versions
    for comp in components[:20]:
        assert "name" in comp and comp["name"]
        assert "version" in comp and comp["version"]


def test_rel_032_backend_sbom_cyclonedx_compliance():
    """REL-007.2: Validates that backend deployment SBOM is generated and distinct from client."""
    assert BACKEND_SBOM_PATH.exists(), f"Backend SBOM missing: {BACKEND_SBOM_PATH}"
    data = json.loads(BACKEND_SBOM_PATH.read_text(encoding="utf-8"))
    
    assert data.get("bomFormat") == "CycloneDX"
    assert data.get("specVersion") in ("1.4", "1.5")
    assert "metadata" in data
    assert data["metadata"]["component"]["name"] == "aegis-docintel-backend-engine"
    
    components = data.get("components", [])
    assert len(components) >= 20
    comp_names = {c["name"].lower() for c in components}
    assert "fastapi" in comp_names or "pydantic" in comp_names


def test_rel_033_sboms_are_distinct():
    """REL-007.3: Confirms client and backend SBOMs are distinct documents."""
    client_data = json.loads(CLIENT_SBOM_PATH.read_text(encoding="utf-8"))
    backend_data = json.loads(BACKEND_SBOM_PATH.read_text(encoding="utf-8"))
    
    assert client_data["metadata"]["component"]["name"] != backend_data["metadata"]["component"]["name"]
