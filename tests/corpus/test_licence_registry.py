"""
tests/corpus/test_licence_registry.py
====================================
Tests verifying licence registry loading, permission evaluations,
and attribution requirements.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.corpus.models import PermissionValue, ReviewStatus
from aegis.corpus.registry.licence_registry import LicenceRegistry

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LICENCES_CONFIG = REPO_ROOT / "configs" / "corpus" / "licences.yaml"


@pytest.fixture
def licence_registry():
    return LicenceRegistry(LICENCES_CONFIG)


def test_lic_reg_001_load_all_licences(licence_registry):
    """LIC-REG-001: Registry successfully loads all declared licences."""
    licences = licence_registry.list_all()
    assert len(licences) >= 8
    assert licence_registry.get("LIC-CDLA-PERMISSIVE-001") is not None
    assert licence_registry.get("LIC-CC-BY-4-001") is not None
    assert licence_registry.get("LIC-USGOV-PD-001") is not None
    assert licence_registry.get("LIC-GODL-INDIA-001") is not None


def test_lic_reg_002_fine_grained_permissions(licence_registry):
    """LIC-REG-002: Permissive licence grants all standard activities."""
    assert licence_registry.has_permission("LIC-CDLA-PERMISSIVE-001", "download_and_retain")
    assert licence_registry.has_permission("LIC-CDLA-PERMISSIVE-001", "parse_and_extract")
    assert licence_registry.has_permission("LIC-CDLA-PERMISSIVE-001", "use_in_evaluation")
    assert licence_registry.has_permission("LIC-CDLA-PERMISSIVE-001", "redistribute_transformed")


def test_lic_reg_003_restricted_academic_licence(licence_registry):
    """LIC-REG-003: FUNSD academic licence denies raw document redistribution."""
    assert licence_registry.has_permission("LIC-FUNSD-ACAD-001", "use_in_evaluation")
    # Redistribution of original is NO, so has_permission should return False
    assert not licence_registry.has_permission("LIC-FUNSD-ACAD-001", "redistribute_original")


def test_lic_reg_004_pending_licence_blocks_all(licence_registry):
    """LIC-REG-004: Unreviewed/pending licence denies all permissions."""
    assert not licence_registry.has_permission("LIC-UNKNOWN-001", "use_in_evaluation")
    assert not licence_registry.has_permission("LIC-UNKNOWN-001", "download_and_retain")


def test_lic_reg_005_attribution_obligations(licence_registry):
    """LIC-REG-005: Licences with attribution mandate attribution text."""
    assert licence_registry.requires_attribution("LIC-GODL-INDIA-001") is True
    assert "data.gov.in" in licence_registry.get_attribution_text("LIC-GODL-INDIA-001")

    # US Government Public Domain does not require attribution
    assert licence_registry.requires_attribution("LIC-USGOV-PD-001") is False


def test_lic_reg_006_missing_licence_returns_none(licence_registry):
    """LIC-REG-006: Non-existent licence ID returns None and denies permission."""
    assert licence_registry.get("LIC-NONEXISTENT-999") is None
    assert not licence_registry.has_permission("LIC-NONEXISTENT-999", "use_in_evaluation")
