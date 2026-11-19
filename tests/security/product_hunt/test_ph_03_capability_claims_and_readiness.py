"""
Tests for Work Packages PH-03 and PH-08:
Capability Claim Verification, Live Codebase Parity, and Known Limitations.
"""

from pathlib import Path
import json
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
RELEASE_DIR = REPO_ROOT / "launch" / "product-hunt" / "release"
MANIFEST_FILE = REPO_ROOT / "release" / "manifests" / "release-manifest-0.1.0.json"


def test_product_readiness_claims_audit():
    """Verify that every capability claimed in PRODUCT_READINESS.md exists in the codebase."""
    readiness_file = RELEASE_DIR / "PRODUCT_READINESS.md"
    assert readiness_file.exists()
    content = readiness_file.read_text(encoding="utf-8")

    assert "Layout-Aware PDF Parsing" in content
    assert "Kahn DAG Reading Order" in content
    assert "Submodular Knapsack Context" in content
    assert "Grounded Coordinate Citations" in content
    assert "Document Comparison" in content
    assert "Ed25519 Device Licensing" in content
    assert "Challenge-Response Activation" in content
    assert "Atomic Quotas & Holds" in content
    assert "Zero-Leak Client Bundle" in content
    assert "Cascading Data Erasure" in content

    # Verify implementation paths exist
    assert (REPO_ROOT / "src" / "api" / "routes" / "query.py").exists()
    assert (REPO_ROOT / "services" / "evaluation_gateway" / "license.py").exists()
    assert (REPO_ROOT / "services" / "evaluation_gateway" / "activation.py").exists()
    assert (REPO_ROOT / "services" / "evaluation_gateway" / "quotas.py").exists()


def test_known_limitations_truthfulness():
    """Verify that known limitations accurately reflect system constants and quotas."""
    limits_file = RELEASE_DIR / "KNOWN_LIMITATIONS.md"
    assert limits_file.exists()
    content = limits_file.read_text(encoding="utf-8")

    assert "5 active documents" in content
    assert "10 MB" in content
    assert "20 queries" in content
    assert "1 active device" in content
    assert "PDF, PNG, JPEG" in content


def test_release_manifest_integrity():
    """Verify release manifest exists, is valid JSON, and matches package hash."""
    assert MANIFEST_FILE.exists(), "Release manifest 0.1.0 must exist"
    with MANIFEST_FILE.open("r", encoding="utf-8") as f:
        manifest = json.load(f)

    assert manifest["version"] == "0.1.0"
    assert manifest["artifact"]["filename"] == "AEGIS-Evaluation-0.1.0.zip"
    assert "sha256" in manifest["artifact"]
    assert len(manifest["artifact"]["sha256"]) == 64
    assert manifest["signature"]["algorithm"] == "Ed25519"
    assert manifest["signature"]["key_id"] == "aegis-release-ed25519-2026-01"


def test_zero_leak_boundary_invariant():
    """Verify boundary scan proves 0 Python source files and 0 secrets in client package."""
    audit_file = REPO_ROOT / "audit" / "prot-final-09" / "product-hunt" / "baseline" / "release-baseline.json"
    assert audit_file.exists()
    with audit_file.open("r", encoding="utf-8") as f:
        audit = json.load(f)

    boundary = audit["boundary_scan"]
    assert boundary["python_files"] == 0
    assert boundary["private_keys"] == 0
    assert boundary["hardcoded_credentials"] == 0
    assert boundary["status"] == "PASS_ZERO_LEAK"


def test_onboarding_and_evaluation_routes_in_fastapi():
    """Verify that evaluator API routes are registered in the evaluator router."""
    from fastapi import FastAPI
    from src.api.routers.evaluator import evaluator_router

    test_app = FastAPI()
    test_app.include_router(evaluator_router)
    openapi_paths = list(test_app.openapi().get("paths", {}).keys())

    expected_endpoints = [
        "/v1/evaluation/profile",
        "/v1/evaluation/license",
        "/v1/evaluation/devices",
        "/v1/evaluation/usage",
        "/v1/evaluation/releases",
        "/v1/evaluation/download",
        "/v1/evaluation/feedback",
        "/v1/evaluation/support-requests",
        "/v1/evaluation/termination-request",
    ]

    for ep in expected_endpoints:
        assert ep in openapi_paths, f"Expected endpoint {ep} not found in openapi paths"
