"""
tests/corpus/test_manifest.py
=============================
Tests verifying full corpus checksum manifest generation and export.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aegis.corpus.independent.inventory import IndependentDocumentInventory
from aegis.corpus.integrity.manifest import ChecksumManifestGenerator

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_man_chk_001_generate_full_corpus_checksums(tmp_path):
    """MAN-CHK-001: Generate complete 250-artifact checksum manifest."""
    inv = IndependentDocumentInventory(REPO_ROOT)
    docs = inv.load_from_manifest_csv()
    assert len(docs) == 250

    generator = ChecksumManifestGenerator(REPO_ROOT)
    manifest = generator.generate_from_documents(docs, version="1.0.0")

    assert len(manifest.artifacts) == 250
    assert manifest.artifacts[0].sha256 == docs[0].sha256

    out_file = tmp_path / "corpus_checksums.json"
    generator.export_manifest(manifest, out_file)
    assert out_file.exists()

    with open(out_file, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert data["manifest_version"] == "1.0.0"
    assert len(data["artifacts"]) == 250
