"""
tests/test_mvp5_entity_resolution.py
====================================
Unit tests for deterministic entity label normalization and tenant-isolated entity resolution.
"""

from src.engines.intelligence.entity_resolution import (
    EntityResolver,
    normalize_entity_label,
    same_normalized_label,
)


def test_normalize_entity_label_stripping():
    assert normalize_entity_label("Acme Corp.") == "acme"
    assert normalize_entity_label("The Acme Corporation") == "acme"
    assert normalize_entity_label("Zenith LLC") == "zenith"
    assert normalize_entity_label("Apex Technologies, Inc.") == "apex technologies"
    assert normalize_entity_label("Global Logistics Ltd.") == "global logistics"
    assert normalize_entity_label("BioTech GmbH") == "biotech"
    assert normalize_entity_label("") == ""


def test_same_normalized_label():
    assert same_normalized_label("Acme Corp", "Acme Corporation") is True
    assert same_normalized_label("The Zenith LLC", "zenith co") is True
    assert same_normalized_label("Apex Corp", "Beta LLC") is False
    assert same_normalized_label("", "something") is False


def test_tenant_isolated_entity_resolver():
    resolver = EntityResolver()

    # Register alias in tenant-A
    resolver.register_alias("tenant-a", "Apex Systems", "Apex")
    resolver.register_alias("tenant-a", "Apex Systems", "Apex Global")

    # In tenant-A, "Apex" resolves to "Apex Systems"
    assert resolver.resolve("tenant-a", "Apex") == "Apex Systems"
    assert resolver.resolve("tenant-a", "Apex Global") == "Apex Systems"
    assert resolver.are_same_entity("tenant-a", "Apex", "Apex Systems") is True

    # In tenant-B, "Apex" MUST NOT resolve to "Apex Systems" (strict tenant boundary)
    assert resolver.resolve("tenant-b", "Apex") == "apex"
    assert resolver.list_aliases("tenant-b", "Apex Systems") == []

    # Verify alias listing in tenant-A
    aliases_a = resolver.list_aliases("tenant-a", "Apex Systems")
    assert "Apex" in aliases_a
    assert "Apex Global" in aliases_a
