"""
tests/corpus/test_source_registry.py
===================================
Tests verifying source registry loading, integrity validation,
and licence cross-referencing.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.corpus.registry.licence_registry import LicenceRegistry
from aegis.corpus.registry.source_registry import SourceRegistry

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SOURCES_CONFIG = REPO_ROOT / "configs" / "corpus" / "sources.yaml"
LICENCES_CONFIG = REPO_ROOT / "configs" / "corpus" / "licences.yaml"


@pytest.fixture
def source_registry():
    lic_reg = LicenceRegistry(LICENCES_CONFIG)
    return SourceRegistry(SOURCES_CONFIG, licence_registry=lic_reg)


def test_src_reg_001_load_sources(source_registry):
    """SRC-REG-001: Source registry loads candidate public sources."""
    sources = source_registry.list_all()
    assert len(sources) >= 10
    assert source_registry.get("SRC-DOCLAYNET-001") is not None
    assert source_registry.get("SRC-PUBLAYNET-001") is not None
    assert source_registry.get("SRC-FUNSD-001") is not None
    assert source_registry.get("SRC-SEC-EDGAR-001") is not None
    assert source_registry.get("SRC-OGD-INDIA-001") is not None


def test_src_reg_002_integrity_validation_clean(source_registry):
    """SRC-REG-002: Source registry passes cross-reference integrity with 0 errors."""
    valid, errors = source_registry.validate_integrity()
    assert valid is True
    assert len(errors) == 0


def test_src_reg_003_source_licence_binding(source_registry):
    """SRC-REG-003: Every source binds to an existing, valid licence record."""
    for s in source_registry.list_all():
        lic = source_registry.licence_registry.get(s.licence_id)
        assert lic is not None, f"Source '{s.source_id}' has dangling licence_id '{s.licence_id}'"


def test_src_reg_004_document_types_and_languages(source_registry):
    """SRC-REG-004: Sources declare document types and supported languages."""
    ogd = source_registry.get("SRC-OGD-INDIA-001")
    assert "government_report" in ogd.document_types
    assert "hi" in ogd.language
    assert "en" in ogd.language
