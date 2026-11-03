"""
tests/corpus/test_checksum.py
=============================
CHK-001 through CHK-008 tests verifying SHA-256 calculation,
manifest generation, tamper detection, missing-file detection, and unregistered file checks.
"""

from __future__ import annotations

import json
from pathlib import Path
import pytest

from aegis.corpus.integrity.checksum import calculate_sha256, hash_bytes
from aegis.corpus.integrity.manifest import (
    ArtifactChecksumRecord,
    ChecksumManifest,
    ChecksumManifestGenerator,
)
from aegis.corpus.integrity.verifier import ChecksumVerifier
from aegis.corpus.independent.inventory import DocumentRecord

REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def test_chk_001_sha256_bytes_and_file(tmp_path):
    """CHK-001: calculate_sha256 accurately computes SHA-256 hash of file."""
    test_file = tmp_path / "sample.txt"
    test_file.write_text("AEGIS Document Intelligence Corpus", encoding="utf-8")
    expected_hash = hash_bytes(b"AEGIS Document Intelligence Corpus")

    actual_hash = calculate_sha256(test_file)
    assert actual_hash == expected_hash
    assert len(actual_hash) == 64


def test_chk_002_manifest_generation():
    """CHK-002: ChecksumManifestGenerator creates manifest conforming to schema."""
    doc = DocumentRecord(
        document_id="DOC-001",
        source_id="SRC-OGD-INDIA-001",
        dataset_id="CORPUS-GOV",
        category="Government",
        title="Annual Report",
        publisher="Ministry",
        original_url="https://example.gov.in/doc.pdf",
        pages_estimate=10,
        sha256="a" * 64,
        licence_id="LIC-GODL-INDIA-001",
    )
    generator = ChecksumManifestGenerator(REPO_ROOT)
    manifest = generator.generate_from_documents([doc])

    assert manifest.manifest_version == "1.0.0"
    assert manifest.algorithm == "sha256"
    assert len(manifest.artifacts) == 1
    assert manifest.artifacts[0].document_id == "DOC-001"
    assert manifest.artifacts[0].sha256 == "a" * 64


def test_chk_003_tamper_detection(tmp_path):
    """CHK-003: ChecksumVerifier detects when a file's content has been tampered with."""
    test_file = tmp_path / "report.pdf"
    test_file.write_bytes(b"Original Content")
    original_sha = calculate_sha256(test_file)

    manifest = ChecksumManifest(
        manifest_version="1.0.0",
        algorithm="sha256",
        generated_at="2026-11-03T00:00:00Z",
        artifacts=[
            ArtifactChecksumRecord(
                document_id="DOC-001",
                filename="report.pdf",
                path="report.pdf",
                size_bytes=16,
                sha256=original_sha,
                source_id="SRC-001",
                dataset_id="DS-001",
                licence_id="LIC-001",
            )
        ],
    )

    # 1. Verification passes on clean file
    res_clean = ChecksumVerifier.verify_directory(manifest, tmp_path, detect_unregistered=False)
    assert res_clean.is_valid is True
    assert res_clean.verified_count == 1

    # 2. Modify one byte (tamper)
    test_file.write_bytes(b"Tampered Content")
    res_tampered = ChecksumVerifier.verify_directory(manifest, tmp_path, detect_unregistered=False)
    assert res_tampered.is_valid is False
    assert len(res_tampered.tampered_files) == 1
    assert res_tampered.tampered_files[0]["document_id"] == "DOC-001"


def test_chk_004_missing_file_detection(tmp_path):
    """CHK-004: ChecksumVerifier detects missing referenced files."""
    manifest = ChecksumManifest(
        manifest_version="1.0.0",
        algorithm="sha256",
        generated_at="2026-11-03T00:00:00Z",
        artifacts=[
            ArtifactChecksumRecord(
                document_id="DOC-GHOST",
                filename="missing.pdf",
                path="missing.pdf",
                size_bytes=100,
                sha256="b" * 64,
                source_id="SRC-001",
                dataset_id="DS-001",
                licence_id="LIC-001",
            )
        ],
    )
    result = ChecksumVerifier.verify_directory(manifest, tmp_path, detect_unregistered=False)
    assert result.is_valid is False
    assert len(result.missing_files) == 1
    assert "missing.pdf" in result.missing_files[0]


def test_chk_005_unregistered_file_detection(tmp_path):
    """CHK-005: ChecksumVerifier detects unregistered files in corpus directory."""
    test_file = tmp_path / "known.pdf"
    test_file.write_bytes(b"Known Content")
    sha = calculate_sha256(test_file)

    # Add an unexpected/unregistered file
    unreg_file = tmp_path / "rogue.pdf"
    unreg_file.write_bytes(b"Unexpected rogue file")

    manifest = ChecksumManifest(
        manifest_version="1.0.0",
        algorithm="sha256",
        generated_at="2026-11-03T00:00:00Z",
        artifacts=[
            ArtifactChecksumRecord(
                document_id="DOC-001",
                filename="known.pdf",
                path="known.pdf",
                size_bytes=len(b"Known Content"),
                sha256=sha,
                source_id="SRC-001",
                dataset_id="DS-001",
                licence_id="LIC-001",
            )
        ],
    )
    result = ChecksumVerifier.verify_directory(manifest, tmp_path, detect_unregistered=True)
    assert result.is_valid is False
    assert len(result.unregistered_files) == 1
    assert "rogue.pdf" in result.unregistered_files[0]
