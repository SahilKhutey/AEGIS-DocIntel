"""
tests/corpus/test_independent_documents.py
=========================================
Tests verifying independent public document catalog ingestion,
diversity analysis across 8+ domains, and schema compliance.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from aegis.corpus.independent.diversity import DiversityAuditor
from aegis.corpus.independent.inventory import IndependentDocumentInventory

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_ind_001_load_manifest_csv():
    """IND-001: IndependentDocumentInventory loads 250 records from manifest.csv."""
    inventory = IndependentDocumentInventory(REPO_ROOT)
    docs = inventory.load_from_manifest_csv()
    assert len(docs) == 250
    assert docs[0].document_id == "PUB-001"
    assert len(docs[0].sha256) == 64


def test_ind_002_source_licence_bindings():
    """IND-002: All loaded documents have valid source and licence bindings."""
    inventory = IndependentDocumentInventory(REPO_ROOT)
    docs = inventory.load_from_manifest_csv()
    for d in docs:
        assert d.source_id.startswith("SRC-")
        assert d.licence_id.startswith("LIC-")


def test_ind_003_diversity_auditor_evaluation():
    """IND-003: DiversityAuditor confirms multi-domain and multi-publisher representation."""
    inventory = IndependentDocumentInventory(REPO_ROOT)
    docs = inventory.load_from_manifest_csv()
    report = DiversityAuditor.evaluate_diversity(docs)

    assert report.total_documents == 250
    assert report.categories_covered_count >= 8
    assert len(report.publisher_distribution) >= 8
    assert report.is_diverse is True
    assert report.total_estimated_pages > 500


def test_ind_004_jsonl_export(tmp_path):
    """IND-004: JSONL export streams valid line-delimited records."""
    inventory = IndependentDocumentInventory(REPO_ROOT)
    inventory.load_from_manifest_csv()
    out_file = tmp_path / "document_inventory.jsonl"
    inventory.export_jsonl(out_file)

    assert out_file.exists()
    lines = out_file.read_text(encoding="utf-8").strip().split("\n")
    assert len(lines) == 250
