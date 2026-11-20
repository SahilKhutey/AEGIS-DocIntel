"""
AEGIS-DocIntel — Test Suite for Product Hunt MCP Launch Orchestrator
===================================================================
Validates the 10 workstreams (PH-MCP-01 through PH-MCP-10) and
the 12 Acceptance Criteria (PH-AC-01 through PH-AC-12).
"""

from __future__ import annotations

import base64
import json
from pathlib import Path

import pytest

from scripts.launch.mcp_product_hunt_orchestrator import (
    AUDIT_MCP_DIR,
    LAUNCH_DIR,
    MCP_SCHEMAS_DIR,
    PRODUCT_DESCRIPTION,
    PRODUCT_NAME,
    PRODUCT_TAGLINE,
    PRODUCT_URL,
    RAW_MAKER_COMMENT_PARAGRAPHS,
    LaunchAcceptanceReport,
    LaunchOrchestrator,
    format_maker_comment_html,
)


def test_html_maker_comment_formatting():
    """Verify HTML comment is properly formatted with <p>, <ul>, <li>, <strong> tags."""
    html = format_maker_comment_html(RAW_MAKER_COMMENT_PARAGRAPHS)
    assert html.startswith("<p>Hey Product Hunt! 👋</p>")
    assert "<ul>" in html
    assert "</ul>" in html
    assert "<li><strong>Spatial Reading Graph (Kahn DAG):</strong>" in html
    assert "<li><strong>Submodular Knapsack Optimizer:</strong>" in html
    assert "<p>Thanks for checking out AEGIS-DocIntel! 🚀</p>" in html
    assert len(html) <= 20000


def test_listing_fields_conform_to_limits():
    """Verify name, tagline, and description conform to Product Hunt character ceilings."""
    assert len(PRODUCT_NAME) <= 200
    assert len(PRODUCT_TAGLINE) <= 60, f"Tagline exceeds 60 chars: {len(PRODUCT_TAGLINE)}"
    assert len(PRODUCT_DESCRIPTION) <= 500, f"Description exceeds 500 chars: {len(PRODUCT_DESCRIPTION)}"


def test_acceptance_criteria_model():
    """Verify LaunchAcceptanceReport tracks all 12 criteria and gates publication."""
    report = LaunchAcceptanceReport()
    # Initially False
    assert report.all_prelaunch_passed() is False

    # Simulate passing criteria 1 through 7
    report.account_verified = True
    report.draft_created = True
    report.description_verified = True
    report.logo_gallery_uploaded = True
    report.makers_associated = True
    report.links_verified = True
    report.pricing_verified = True

    # Prelaunch criteria 1 through 11 should pass
    assert report.all_prelaunch_passed() is True
    # Publication confirmed remains False until explicit two-step approval
    assert report.publication_confirmed is False


def test_dry_run_pipeline_produces_audit_artifacts():
    """Verify orchestrator runs in dry-run mode and creates audit reports."""
    orchestrator = LaunchOrchestrator(dry_run=True)
    results = orchestrator.run_full_preparation_pipeline()

    assert results["all_prelaunch_passed"] is True
    assert results["PH-MCP-01"]["status"] == "SIMULATED_READY"
    assert results["PH-MCP-02"]["status"] == "SIMULATED_CREATED"
    assert results["PH-MCP-04"]["status"] == "SIMULATED_STAGED"
    assert results["PH-MCP-06"]["status"] == "READY"
    assert results["PH-MCP-07-PREVIEW"]["status"] == "NEEDS_USER_CONFIRMATION"

    acct_report = AUDIT_MCP_DIR / "account-readiness-report.md"
    assert acct_report.exists()
    assert "AEGIS-DocIntel" in acct_report.read_text(encoding="utf-8")

    prelaunch_report = AUDIT_MCP_DIR / "pre-launch-validation-report.md"
    assert prelaunch_report.exists()
    content = prelaunch_report.read_text(encoding="utf-8")
    assert "PH-AC-01" in content
    assert "PH-AC-12" in content
    assert "READY FOR SUBMISSION" in content


def test_launch_assets_readiness_for_mcp_staging():
    """Verify logo and gallery SVG files exist and are within 3MB decoded size limits."""
    logo_path = LAUNCH_DIR / "assets" / "logo" / "logo-512x512.svg"
    assert logo_path.exists()
    logo_b64 = base64.b64encode(logo_path.read_bytes()).decode("ascii")
    assert len(logo_b64) < 4066686, "Logo base64 exceeds Product Hunt MCP 3MB ceiling"

    gallery_dir = LAUNCH_DIR / "assets" / "gallery"
    gallery_files = sorted(list(gallery_dir.glob("gallery-*.svg")))
    assert len(gallery_files) >= 5, "Expected at least 5 gallery slides"

    for gf in gallery_files:
        g_b64 = base64.b64encode(gf.read_bytes()).decode("ascii")
        assert len(g_b64) < 4066686, f"Gallery slide {gf.name} exceeds 3MB ceiling"


def test_product_hunt_schema_field_compatibility():
    """Verify orchestrator values map directly to start_launch and update_launch schemas."""
    if not MCP_SCHEMAS_DIR.exists():
        pytest.skip(f"MCP schemas dir {MCP_SCHEMAS_DIR} not found")

    start_schema_path = MCP_SCHEMAS_DIR / "start_launch.json"
    assert start_schema_path.exists()
    start_schema = json.loads(start_schema_path.read_text(encoding="utf-8"))

    values_props = start_schema["parameters"]["properties"]["values"]["properties"]
    assert "name" in values_props
    assert "tagline" in values_props
    assert "description" in values_props
    assert "pricingType" in values_props
    assert "openSource" in values_props
    assert "commentBody" in values_props
    assert "mcpServerUrls" in values_props

    update_schema_path = MCP_SCHEMAS_DIR / "update_launch.json"
    assert update_schema_path.exists()
    update_schema = json.loads(update_schema_path.read_text(encoding="utf-8"))

    changes_props = update_schema["parameters"]["properties"]["changes"]["properties"]
    assert "thumbnailAssetId" in changes_props
    assert "galleryAssetIds" in changes_props
