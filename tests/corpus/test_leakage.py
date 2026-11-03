"""
tests/corpus/test_leakage.py
============================
Tests PAR-007 through PAR-010 verifying leakage detection mechanisms
(exact IDs, content SHA256 hashes, family contamination, near-duplicate text).
"""

import json
from pathlib import Path
import pytest

from aegis.corpus.partition import (
    DeterministicSplitter,
    GroupableDocument,
    LeakageDetector,
    PartitionManifest,
    PartitionSets,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
LEAKAGE_REPORT_FILE = REPO_ROOT / "artifacts" / "corpus" / "reports" / "holdout_leakage_report.json"


def test_par_007_exact_id_leakage_detection():
    """Verify detector catches exact ID overlap across partitions."""
    manifest = PartitionManifest(
        split_id="TEST-SPLIT",
        algorithm="test",
        seed=42,
        grouping_key="doc_id",
        partitions=PartitionSets(
            development=["DOC_001", "DOC_002"],
            validation=["DOC_003"],
            holdout=["DOC_001", "DOC_004"],  # Contamination! DOC_001 in dev & holdout
        ),
    )
    docs = [
        GroupableDocument(document_id="DOC_001", source_id="SRC-1", sha256="h1"),
        GroupableDocument(document_id="DOC_002", source_id="SRC-1", sha256="h2"),
        GroupableDocument(document_id="DOC_003", source_id="SRC-1", sha256="h3"),
        GroupableDocument(document_id="DOC_004", source_id="SRC-1", sha256="h4"),
    ]

    detector = LeakageDetector()
    report = detector.audit_partitions(manifest, docs)

    assert report.status == "FAILED"
    assert any("Exact ID overlap between dev and holdout" in v for v in report.violations)


def test_par_008_sha256_hash_leakage_detection():
    """Verify detector catches identical content hashes under different document IDs."""
    manifest = PartitionManifest(
        split_id="TEST-SPLIT",
        algorithm="test",
        seed=42,
        grouping_key="doc_id",
        partitions=PartitionSets(
            development=["DOC_A"],
            validation=["DOC_B"],
            holdout=["DOC_C"],
        ),
    )
    docs = [
        GroupableDocument(document_id="DOC_A", source_id="SRC-1", sha256="SAME_CONTENT_HASH"),
        GroupableDocument(document_id="DOC_B", source_id="SRC-1", sha256="DIFF_HASH_B"),
        GroupableDocument(document_id="DOC_C", source_id="SRC-2", sha256="SAME_CONTENT_HASH"),  # Collision!
    ]

    detector = LeakageDetector()
    report = detector.audit_partitions(manifest, docs)

    assert report.status == "FAILED"
    assert any("Content hash collision between dev and holdout" in v for v in report.violations)


def test_par_009_family_contamination_detection():
    """Verify detector catches series/family contamination between dev and holdout."""
    manifest = PartitionManifest(
        split_id="TEST-SPLIT",
        algorithm="test",
        seed=42,
        grouping_key="family",
        partitions=PartitionSets(
            development=["WB_WDR_2022"],
            validation=["SEC_10K_2022"],
            holdout=["WB_WDR_2023"],  # Family WB_WDR in dev and holdout!
        ),
    )
    docs = [
        GroupableDocument(document_id="WB_WDR_2022", source_id="SRC-WB", sha256="h1", family="WB_WDR"),
        GroupableDocument(document_id="SEC_10K_2022", source_id="SRC-SEC", sha256="h2", family="SEC_10K"),
        GroupableDocument(document_id="WB_WDR_2023", source_id="SRC-WB", sha256="h3", family="WB_WDR"),
    ]

    detector = LeakageDetector()
    report = detector.audit_partitions(manifest, docs)

    assert report.status == "FAILED"
    assert any("Document family contamination" in v for v in report.violations)


def test_par_010_near_duplicate_text_detection():
    """Verify detector flags near duplicate text above similarity threshold."""
    text_a = "The executive summary of global financial stability outlines monetary policy impacts and credit spreads in developing markets."
    text_b = "The executive summary of global financial stability outlines monetary policy impacts and sovereign credit spreads in emerging markets."

    manifest = PartitionManifest(
        split_id="TEST-SPLIT",
        algorithm="test",
        seed=42,
        grouping_key="family",
        partitions=PartitionSets(
            development=["DOC_DEV_TEXT"],
            validation=["DOC_VAL_TEXT"],
            holdout=["DOC_HOLD_TEXT"],
        ),
    )
    docs = [
        GroupableDocument(document_id="DOC_DEV_TEXT", source_id="SRC-1", sha256="h1", family="FAM-1", text_content=text_a),
        GroupableDocument(document_id="DOC_VAL_TEXT", source_id="SRC-2", sha256="h2", family="FAM-2", text_content="Unrelated text"),
        GroupableDocument(document_id="DOC_HOLD_TEXT", source_id="SRC-3", sha256="h3", family="FAM-3", text_content=text_b),
    ]

    detector = LeakageDetector(similarity_threshold=0.30)  # low threshold to trigger warning
    report = detector.audit_partitions(manifest, docs, check_near_duplicates=True)

    assert len(report.warnings) > 0
    assert any("Near-duplicate text detected" in w for w in report.warnings)


def test_par_011_generated_leakage_report_clean():
    """Verify that the generated holdout_leakage_report.json is PASSED with 0 violations."""
    assert LEAKAGE_REPORT_FILE.exists(), f"Leakage report missing at {LEAKAGE_REPORT_FILE}"
    with open(LEAKAGE_REPORT_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)

    assert data["status"] == "PASSED"
    assert len(data["violations"]) == 0
    assert data["metrics"]["development_count"] == 150
    assert data["metrics"]["validation_count"] == 50
    assert data["metrics"]["holdout_count"] == 50
