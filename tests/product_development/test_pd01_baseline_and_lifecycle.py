"""
Tests for Work Package PD-01: Baseline Audit & Canonical Processing Lifecycle.
==============================================================================
Asserts completeness of baseline deliverables, strict classification rules in
the feature functionality matrix, state machine invariants, and opaque storage contracts.
"""
from pathlib import Path
import csv
import pytest

from src.models.document_lifecycle import (
    DocumentLifecycleManager,
    DocumentLifecycleState,
    InvalidLifecycleTransitionError,
    VALID_TRANSITIONS,
)
from src.models.processing_contract import (
    DocumentSource,
    ExtractedBlock,
    OpaqueStorageReferenceError,
    ProcessingResult,
    validate_opaque_storage_reference,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
BASELINE_DIR = REPO_ROOT / "audit" / "product-development" / "baseline"
DOCS_DIR = REPO_ROOT / "docs" / "engineering"


# ─────────────────────────────────────────────────────────────────
# 1. Audit Deliverable Completeness
# ─────────────────────────────────────────────────────────────────

def test_all_pd01_baseline_deliverables_exist():
    """Verify all 7 required deliverables are present and non-empty in audit/product-development/baseline/."""
    expected_files = [
        "BASELINE_REPORT.md",
        "SYSTEM_COMPONENT_INVENTORY.md",
        "FEATURE_FUNCTIONALITY_MATRIX.csv",
        "BROKEN_WORKFLOWS.md",
        "P0_P1_P2_BACKLOG.md",
        "BASELINE_TEST_REPORT.md",
        "PD01_SIGNOFF.md",
    ]
    for filename in expected_files:
        filepath = BASELINE_DIR / filename
        assert filepath.exists(), f"Missing required deliverable: {filename}"
        assert filepath.stat().st_size > 100, f"Deliverable is unexpectedly empty: {filename}"


def test_engineering_specifications_exist():
    """Verify engineering specifications exist in docs/engineering/."""
    lifecycle_doc = DOCS_DIR / "DOCUMENT_LIFECYCLE.md"
    contract_doc = DOCS_DIR / "PROCESSING_CONTRACTS.md"
    assert lifecycle_doc.exists()
    assert contract_doc.exists()
    assert "UPLOADED" in lifecycle_doc.read_text(encoding="utf-8")
    assert "DocumentSource" in contract_doc.read_text(encoding="utf-8")


# ─────────────────────────────────────────────────────────────────
# 2. Feature Functionality Matrix Integrity
# ─────────────────────────────────────────────────────────────────

def test_feature_functionality_matrix_schema_and_valid_statuses():
    """Verify FEATURE_FUNCTIONALITY_MATRIX.csv has valid columns and allowed status values."""
    matrix_file = BASELINE_DIR / "FEATURE_FUNCTIONALITY_MATRIX.csv"
    assert matrix_file.exists()

    allowed_statuses = {"WORKING", "PARTIAL", "BROKEN", "MISSING", "UNVERIFIED"}
    expected_headers = ["feature_id", "feature_name", "subsystem", "status", "evidence_test_file", "notes"]

    rows = []
    with open(matrix_file, mode="r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        assert reader.fieldnames == expected_headers, f"Invalid CSV headers: {reader.fieldnames}"
        for row in reader:
            rows.append(row)

    assert len(rows) >= 20, f"Expected at least 20 feature classifications, found {len(rows)}"

    for row in rows:
        status_val = row["status"].strip()
        assert status_val in allowed_statuses, (
            f"Invalid status '{status_val}' for feature '{row['feature_id']}'. "
            f"Must be one of {allowed_statuses}"
        )
        if status_val == "WORKING":
            evidence = row["evidence_test_file"].strip()
            assert evidence and evidence.lower() != "none", (
                f"Feature '{row['feature_id']}' classified as WORKING but lacks evidence test file"
            )


# ─────────────────────────────────────────────────────────────────
# 3. Canonical Document Lifecycle State Machine
# ─────────────────────────────────────────────────────────────────

def test_valid_forward_lifecycle_transitions():
    """Verify that a document can step forward along the happy path to READY."""
    mgr = DocumentLifecycleManager(document_id="doc_test_123", tenant_id="tenant_alpha")
    assert mgr.current_state is None

    mgr.transition_to(DocumentLifecycleState.UPLOADED, stage="intake")
    assert mgr.current_state == DocumentLifecycleState.UPLOADED

    mgr.transition_to(DocumentLifecycleState.VALIDATING, stage="magic_bytes")
    mgr.transition_to(DocumentLifecycleState.ACCEPTED, stage="intake_passed")
    mgr.transition_to(DocumentLifecycleState.QUEUED, stage="scheduler")
    mgr.transition_to(DocumentLifecycleState.EXTRACTING, stage="pdf_extraction")
    mgr.transition_to(DocumentLifecycleState.PARSING, stage="kahn_dag")
    mgr.transition_to(DocumentLifecycleState.NORMALIZING, stage="text_cleaning")
    mgr.transition_to(DocumentLifecycleState.INDEXING, stage="vector_store")
    mgr.transition_to(DocumentLifecycleState.READY, stage="complete")

    assert mgr.current_state == DocumentLifecycleState.READY
    assert mgr.current_state.is_queryable is True
    assert mgr.current_state.is_terminal is False
    assert len(mgr.history) == 9


def test_illegal_lifecycle_transitions_fail_closed():
    """Verify that skipping states or attempting illegal transitions raises an error."""
    mgr = DocumentLifecycleManager(document_id="doc_test_456", tenant_id="tenant_beta")
    mgr.transition_to(DocumentLifecycleState.UPLOADED, stage="intake")

    # Skipping directly from UPLOADED to READY is illegal
    with pytest.raises(InvalidLifecycleTransitionError) as exc_info:
        mgr.transition_to(DocumentLifecycleState.READY, stage="skip_fail")
    assert "Invalid document lifecycle transition" in str(exc_info.value)

    # Transitioning from REJECTED to READY is illegal (REJECTED is terminal)
    mgr_rej = DocumentLifecycleManager(document_id="doc_rej", tenant_id="tenant_beta")
    mgr_rej.transition_to(DocumentLifecycleState.UPLOADED, stage="intake")
    mgr_rej.transition_to(DocumentLifecycleState.VALIDATING, stage="validation")
    mgr_rej.transition_to(DocumentLifecycleState.REJECTED, stage="failed_intake")
    assert mgr_rej.current_state.is_terminal is True

    with pytest.raises(InvalidLifecycleTransitionError):
        mgr_rej.transition_to(DocumentLifecycleState.QUEUED, stage="retry_rejected")


def test_lifecycle_recoverable_failures_and_retries():
    """Verify recoverable failures can return to QUEUED state for retries."""
    mgr = DocumentLifecycleManager(document_id="doc_retry", tenant_id="tenant_gamma")
    mgr.transition_to(DocumentLifecycleState.UPLOADED, stage="intake")
    mgr.transition_to(DocumentLifecycleState.VALIDATING, stage="validation")
    mgr.transition_to(DocumentLifecycleState.ACCEPTED, stage="accepted")
    mgr.transition_to(DocumentLifecycleState.QUEUED, stage="queued")
    mgr.transition_to(DocumentLifecycleState.EXTRACTING, stage="extraction")
    mgr.transition_to(
        DocumentLifecycleState.EXTRACTION_FAILED,
        stage="extraction",
        sanitized_error_code="TIMEOUT",
    )
    assert mgr.current_state.is_error_state is True

    # Retry transition back to QUEUED
    mgr.transition_to(DocumentLifecycleState.QUEUED, stage="retry", attempt_number=2)
    assert mgr.current_state == DocumentLifecycleState.QUEUED


def test_lifecycle_cascading_deletion():
    """Verify documents can transition from READY to DELETION_PENDING to DELETED."""
    mgr = DocumentLifecycleManager(
        document_id="doc_del",
        tenant_id="tenant_delta",
        initial_state=DocumentLifecycleState.READY,
    )
    mgr.transition_to(DocumentLifecycleState.DELETION_PENDING, stage="user_request")
    mgr.transition_to(DocumentLifecycleState.DELETED, stage="cascading_purge")

    assert mgr.current_state == DocumentLifecycleState.DELETED
    assert mgr.current_state.is_terminal is True
    assert mgr.current_state.is_queryable is False


# ─────────────────────────────────────────────────────────────────
# 4. Canonical Processing Contracts & Opaque Storage References
# ─────────────────────────────────────────────────────────────────

def test_opaque_storage_reference_validation():
    """Verify that opaque storage references are enforced and local paths are rejected."""
    # Valid opaque storage identifiers
    valid_refs = [
        "blob://doc_12345/raw_bytes",
        "s3://aegis-documents/tenant_alpha/doc_9876",
        "opaque:e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        "urn:amdi:blob:4f2a89c1-1e9a-41ab-88be-9b378121f1e8",
        "sqlite:blob:doc_777",
    ]
    for ref in valid_refs:
        validate_opaque_storage_reference(ref)  # Should not raise

    # Prohibited filesystem and traversal references
    invalid_refs = [
        "../../etc/passwd",
        "..\\..\\Windows\\System32",
        "C:\\Users\\Admin\\secret.pdf",
        "D:/Data/documents/test.pdf",
        "/var/run/secrets/credentials.txt",
        "\\network-share\\confidential.docx",
        "random_unprefixed_path.pdf",
        "",
    ]
    for bad_ref in invalid_refs:
        with pytest.raises(OpaqueStorageReferenceError):
            validate_opaque_storage_reference(bad_ref)


def test_document_source_model_instantiation():
    """Verify DocumentSource instantiation with valid inputs and rejection of invalid hashes."""
    source = DocumentSource(
        document_id="doc_alpha_1",
        tenant_id="tenant_prod_1",
        filename="quarterly_report.pdf",
        media_type="application/pdf",
        checksum_sha256="a" * 64,
        storage_reference="blob://doc_alpha_1/content",
    )
    assert source.document_id == "doc_alpha_1"
    assert source.checksum_sha256 == "a" * 64

    # Invalid sha256 checksum length
    with pytest.raises(ValueError) as exc:
        DocumentSource(
            document_id="doc_bad",
            tenant_id="tenant_prod_1",
            filename="bad.pdf",
            media_type="application/pdf",
            checksum_sha256="short_hash",
            storage_reference="blob://doc_bad/content",
        )
    assert "must be a 64-character hex string" in str(exc.value)


def test_processing_result_contract_integrity():
    """Verify ProcessingResult serializes blocks and metadata correctly."""
    block1 = ExtractedBlock(
        block_id="blk_001",
        text="Section 1: Introduction",
        block_type="heading",
        page_number=1,
        section_path=["Root", "Introduction"],
    )
    block2 = ExtractedBlock(
        block_id="blk_002",
        text="AEGIS-DocIntel provides verifiable document intelligence.",
        block_type="paragraph",
        page_number=1,
        section_path=["Root", "Introduction"],
    )

    result = ProcessingResult(
        document_id="doc_res_1",
        pipeline_version="1.1.0",
        status="READY",
        blocks=[block1, block2],
        warnings=[],
        errors=[],
        metadata={"total_pages": 1, "kahn_dag_verified": True},
    )

    assert result.is_success is True
    d = result.to_dict()
    assert d["document_id"] == "doc_res_1"
    assert len(d["blocks"]) == 2
    assert d["blocks"][0]["block_type"] == "heading"
    assert d["metadata"]["kahn_dag_verified"] is True
