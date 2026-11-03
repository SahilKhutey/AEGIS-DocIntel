"""
tests/processing/normalization/test_normalization_provenance.py
===============================================================
Tests NORM-001 through NORM-008 verifying date/numeric normalization policies,
raw value preservation, field-level provenance, hard invariants, and schema conformance.
"""

import json
from pathlib import Path
import pytest
import jsonschema

from aegis.processing.models import FieldProvenance
from aegis.processing.normalization import DateNormalizer, NumberNormalizer
from aegis.processing.provenance import (
    DocumentLineage,
    FieldProvenanceTracker,
    ProvenanceInvariantValidator,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
PROVENANCE_SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "provenance.schema.json"


@pytest.fixture
def provenance_schema():
    with open(PROVENANCE_SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def test_norm_001_date_normalization():
    """NORM-001: Normalize unambiguous dates to ISO-8601 (YYYY-MM-DD) while preserving raw strings."""
    # ISO date
    norm_iso, status_iso, rule = DateNormalizer.normalize("2024-05-18")
    assert status_iso == "SUCCESS"
    assert norm_iso == "2024-05-18"

    # Explicit named month
    norm_named, status_named, _ = DateNormalizer.normalize("January 15, 2024")
    assert status_named == "SUCCESS"
    assert norm_named == "2024-01-15"

    norm_eu, status_eu, _ = DateNormalizer.normalize("15 January 2024")
    assert status_eu == "SUCCESS"
    assert norm_eu == "2024-01-15"


def test_norm_002_ambiguous_date_handling():
    """NORM-002: Verify ambiguous date (03/04/2025) without locale is marked AMBIGUOUS and not guessed."""
    norm_val, status, rule = DateNormalizer.normalize("03/04/2025", locale=None)
    assert status == "AMBIGUOUS"
    assert norm_val is None

    # With US locale -> March 4, 2025
    norm_us, status_us, _ = DateNormalizer.normalize("03/04/2025", locale="US")
    assert status_us == "SUCCESS"
    assert norm_us == "2025-03-04"

    # With EU locale -> April 3, 2025
    norm_eu, status_eu, _ = DateNormalizer.normalize("03/04/2025", locale="EU")
    assert status_eu == "SUCCESS"
    assert norm_eu == "2025-04-03"


def test_norm_003_numeric_and_currency():
    """NORM-003: Parse financial numbers with accounting negatives, currency symbols, and percentages."""
    # Accounting negative: ($1,250.50)
    res_neg, status_neg, _ = NumberNormalizer.normalize("($1,250.50)")
    assert status_neg == "SUCCESS"
    assert res_neg["value"] == -1250.50
    assert res_neg["currency"] == "USD"
    assert res_neg["raw_string"] == "($1,250.50)"

    # Euro figure
    res_eur, status_eur, _ = NumberNormalizer.normalize("€ 45,000.00")
    assert status_eur == "SUCCESS"
    assert res_eur["value"] == 45000.0
    assert res_eur["currency"] == "EUR"

    # Percentage
    res_pct, status_pct, _ = NumberNormalizer.normalize("29.8%")
    assert status_pct == "SUCCESS"
    assert res_pct["value"] == 29.8
    assert res_pct["is_percentage"] is True


def test_norm_004_field_provenance_tracking():
    """NORM-004: Track field provenance linking to page, block, bbox, and normalization rule."""
    tracker = FieldProvenanceTracker(processing_run_id="RUN-TEST-001", document_id="DOC-INVOICE-01")
    prov = tracker.record_field(
        field_name="total_amount",
        raw_value="$250.00",
        normalized_value=250.0,
        normalization_rule="financial_numeric_v1",
        page_number=1,
        region_id="REGION-01",
        text_block_id="BLOCK-05",
        bbox=[100.0, 200.0, 300.0, 230.0],
    )
    assert prov.field_id.startswith("FIELD-DOC-INVOICE-01-01-")
    assert prov.raw_value == "$250.00"
    assert prov.normalized_value == 250.0
    assert len(tracker.get_records()) == 1


def test_norm_005_provenance_hard_invariants_pass():
    """NORM-005: Lineage and fields meeting all 8 hard invariants evaluate to is_valid=True."""
    lineage = DocumentLineage(
        document_id="DOC-CLEAN-001",
        original_sha256="1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        source_id="SRC-TEST",
        licence_id="LIC-TEST",
        processing_run_id="RUN-01",
        configuration_hash="confhash123",
    )
    fields = [
        FieldProvenance(
            field_id="F1",
            field_name="period",
            raw_value="2024",
            normalized_value="2024",
            normalization_rule="year_rule_v1",
            document_id="DOC-CLEAN-001",
            page_number=1,
            region_id="REG-1",
            processing_run_id="RUN-01",
            normalization_status="SUCCESS",
        )
    ]
    report = ProvenanceInvariantValidator.validate(lineage, fields, known_regions=["REG-1"])
    assert report.is_valid is True
    assert len(report.violations) == 0


def test_norm_006_provenance_hard_invariants_catch_violation():
    """NORM-006: Invariant validator flags missing checksum or unresolved region references."""
    # Bad lineage: missing valid 64-char sha256
    with pytest.raises(Exception):
        DocumentLineage(
            document_id="DOC-BAD",
            original_sha256="short_hash",  # invalid SHA-256
            source_id="SRC-1",
            licence_id="LIC-1",
            processing_run_id="R1",
            configuration_hash="h",
        )

    lineage = DocumentLineage(
        document_id="DOC-OK",
        original_sha256="0" * 64,
        source_id="SRC-1",
        licence_id="LIC-1",
        processing_run_id="R1",
        configuration_hash="h",
    )
    # Field referencing non-existent region
    bad_fields = [
        FieldProvenance(
            field_id="F_BAD",
            field_name="val",
            raw_value="123",
            normalized_value=123,
            normalization_rule="rule1",
            document_id="DOC-OK",
            page_number=1,
            region_id="NON_EXISTENT_REGION",
            processing_run_id="R1",
        )
    ]
    report = ProvenanceInvariantValidator.validate(lineage, bad_fields, known_regions=["VALID_REGION_1"])
    assert report.is_valid is False
    assert any("Unresolved Region Reference" in v.rule_name for v in report.violations)


def test_norm_007_raw_values_unmodified():
    """NORM-007: Invariant check verifies raw values are not overwritten by normalization."""
    tracker = FieldProvenanceTracker(processing_run_id="R1", document_id="D1")
    f = tracker.record_field(
        field_name="revenue",
        raw_value="$1,234.56",
        normalized_value=1234.56,
        normalization_rule="numeric_v1",
        page_number=1,
    )
    assert f.raw_value == "$1,234.56"
    assert f.normalized_value == 1234.56


def test_norm_008_schema_conformance(provenance_schema):
    """NORM-008: Validate FieldProvenance model against provenance.schema.json."""
    field = FieldProvenance(
        field_id="FIELD-001",
        field_name="invoice_date",
        raw_value="12/04/2024",
        normalized_value="2024-04-12",
        normalization_rule="iso8601_date_v1",
        document_id="DOC-001",
        page_number=1,
        region_id="REGION-002",
        text_block_id="BLOCK-003",
        bbox=[100.0, 150.0, 250.0, 180.0],
        source_span={"start": 10, "end": 20},
        processing_run_id="RUN-999",
        normalization_status="SUCCESS",
    )
    jsonschema.validate(field.to_schema_dict(), provenance_schema)
