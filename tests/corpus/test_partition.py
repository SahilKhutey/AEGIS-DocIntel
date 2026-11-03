"""
tests/corpus/test_partition.py
==============================
Tests PAR-001 through PAR-006 verifying grouping, deterministic splitting,
holdout protection, and schema compliance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.corpus.adapters.models import CanonicalEvaluationItem
from aegis.corpus.partition import (
    DeterministicSplitter,
    DocumentGrouper,
    GroupableDocument,
    HoldoutAccessGuard,
    PartitionManifest,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
MANIFEST_FILE = REPO_ROOT / "artifacts" / "corpus" / "manifests" / "partition_manifest.json"
SCHEMA_FILE = REPO_ROOT / "schemas" / "corpus" / "partition_manifest.schema.json"


def test_par_001_document_grouping():
    """Verify document grouping by source, publisher, and inferred family."""
    docs = [
        GroupableDocument(document_id="WB_WDR_2022", source_id="SRC-WB", sha256="hash1", publisher="World Bank"),
        GroupableDocument(document_id="WB_WDR_2023", source_id="SRC-WB", sha256="hash2", publisher="World Bank"),
        GroupableDocument(document_id="SEC_10K_AAPL_2021", source_id="SRC-SEC", sha256="hash3", publisher="SEC"),
        GroupableDocument(document_id="SEC_10K_AAPL_2022", source_id="SRC-SEC", sha256="hash4", publisher="SEC"),
    ]

    by_publisher = DocumentGrouper.group_documents(docs, grouping_key="publisher")
    assert len(by_publisher) == 2
    assert "WORLD BANK" in by_publisher
    assert "SEC" in by_publisher

    by_family = DocumentGrouper.group_documents(docs, grouping_key="family")
    assert len(by_family) == 2
    assert "SRC-WB::WB_WDR" in by_family
    assert "SRC-SEC::SEC_10K_AAPL" in by_family


def test_par_002_family_inference():
    """Verify inference of document family series from ids and titles."""
    assert DocumentGrouper.infer_family("WDR_2023_REPORT") == "WDR"
    assert DocumentGrouper.infer_family("SEC_10K_MSFT_2022") == "SEC_10K_MSFT"
    assert DocumentGrouper.infer_family("DOC_ITEM_0001") == "DOC_ITEM"


def test_par_003_deterministic_splitting():
    """Verify splitting is strictly deterministic across identical runs with same seed."""
    docs = [
        GroupableDocument(document_id=f"DOC_{i:03d}", source_id=f"SRC_{i % 5}", sha256=f"hash_{i:03d}")
        for i in range(50)
    ]

    splitter_a = DeterministicSplitter(seed=20261103)
    manifest_a = splitter_a.split(docs, grouping_key="family")

    splitter_b = DeterministicSplitter(seed=20261103)
    manifest_b = splitter_b.split(docs, grouping_key="family")

    assert manifest_a.partitions.development == manifest_b.partitions.development
    assert manifest_a.partitions.validation == manifest_b.partitions.validation
    assert manifest_a.partitions.holdout == manifest_b.partitions.holdout


def test_par_004_ratio_distribution():
    """Verify partition allocations adhere to target distribution ratios."""
    docs = [
        GroupableDocument(document_id=f"DOC_{i:03d}", source_id=f"SRC_{i}", sha256=f"hash_{i:03d}")
        for i in range(100)
    ]
    splitter = DeterministicSplitter(seed=20261103, ratios={"development": 0.70, "validation": 0.15, "holdout": 0.15})
    manifest = splitter.split(docs, grouping_key="document_id")

    assert len(manifest.partitions.development) == 70
    assert len(manifest.partitions.validation) == 15
    assert len(manifest.partitions.holdout) == 15


def test_par_005_holdout_access_guard():
    """Verify HoldoutAccessGuard seals holdout ground-truth in development mode."""
    docs = [
        GroupableDocument(document_id="DOC_DEV", source_id="SRC-1", sha256="h1"),
        GroupableDocument(document_id="DOC_VAL", source_id="SRC-1", sha256="h2"),
        GroupableDocument(document_id="DOC_HOLD", source_id="SRC-2", sha256="h3"),
    ]
    splitter = DeterministicSplitter(seed=42, ratios={"development": 0.34, "validation": 0.33, "holdout": 0.33})
    manifest = splitter.split(docs, grouping_key="document_id")

    guard = HoldoutAccessGuard(manifest)

    items = [
        CanonicalEvaluationItem(
            item_id="EVAL-1",
            document_id=manifest.partitions.development[0],
            task="qa",
            input={"q": "Question 1"},
            ground_truth={"answer": "Ground Truth 1"},
        ),
        CanonicalEvaluationItem(
            item_id="EVAL-2",
            document_id=manifest.partitions.holdout[0],
            task="qa",
            input={"q": "Question 2"},
            ground_truth={"answer": "Ground Truth 2"},
        ),
    ]

    # In regular dev mode, holdout ground truth must be sealed
    sealed_items = guard.filter_evaluation_items(items, allow_holdout=False)
    assert sealed_items[0].ground_truth == {"answer": "Ground Truth 1"}
    assert sealed_items[1].ground_truth["status"] == "SEALED"

    # With allow_holdout=True, ground truth is preserved
    unsealed_items = guard.filter_evaluation_items(items, allow_holdout=True)
    assert unsealed_items[1].ground_truth == {"answer": "Ground Truth 2"}


def test_par_006_partition_manifest_schema_compliance():
    """Verify the generated artifacts/corpus/manifests/partition_manifest.json validates against schema."""
    assert MANIFEST_FILE.exists(), f"Partition manifest missing at {MANIFEST_FILE}"
    assert SCHEMA_FILE.exists(), f"Partition schema missing at {SCHEMA_FILE}"

    with open(SCHEMA_FILE, "r", encoding="utf-8") as sf:
        schema = json.load(sf)
    with open(MANIFEST_FILE, "r", encoding="utf-8") as mf:
        manifest_data = json.load(mf)

    jsonschema.validate(manifest_data, schema)
    assert manifest_data["leakage_check_status"] == "PASSED"
    assert len(manifest_data["partitions"]["development"]) == 150
    assert len(manifest_data["partitions"]["validation"]) == 50
    assert len(manifest_data["partitions"]["holdout"]) == 50
