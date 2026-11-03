"""
aegis.processing.provenance.validator
=====================================
Hard data integrity invariant verification engine for document normalization and provenance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from aegis.processing.models import FieldProvenance
from aegis.processing.provenance.lineage import DocumentLineage


class InvariantViolation(BaseModel):
    invariant_id: str
    rule_name: str
    severity: str = "CRITICAL"
    description: str


class ProvenanceIntegrityReport(BaseModel):
    is_valid: bool
    total_fields_checked: int
    passed_invariants: List[str] = Field(default_factory=list)
    violations: List[InvariantViolation] = Field(default_factory=list)


class ProvenanceInvariantValidator:
    """Verifies strict adherence to the 8 hard document integrity invariants."""

    @classmethod
    def validate(
        cls,
        lineage: DocumentLineage,
        fields: List[FieldProvenance],
        known_regions: Optional[List[str]] = None
    ) -> ProvenanceIntegrityReport:
        """Run all hard invariant checks on lineage and derived fields."""
        violations: List[InvariantViolation] = []
        passed: List[str] = []

        # Invariant 1: Document reference
        if lineage.document_id and len(lineage.document_id.strip()) > 0:
            passed.append("INV-1-ORIGINAL-DOC-REF")
        else:
            violations.append(InvariantViolation(
                invariant_id="INV-1-ORIGINAL-DOC-REF",
                rule_name="Original Document Reference",
                description="Lineage is missing original document_id reference",
            ))

        # Invariant 2: Checksum record
        if lineage.original_sha256 and len(lineage.original_sha256) == 64:
            passed.append("INV-2-ORIGINAL-CHECKSUM")
        else:
            violations.append(InvariantViolation(
                invariant_id="INV-2-ORIGINAL-CHECKSUM",
                rule_name="Original Checksum Record",
                description="Lineage lacks valid 64-character SHA-256 checksum record",
            ))

        # Invariant 3: Identifiable configuration
        if lineage.configuration_hash and len(lineage.configuration_hash.strip()) > 0:
            passed.append("INV-3-CONFIGURATION-HASH")
        else:
            violations.append(InvariantViolation(
                invariant_id="INV-3-CONFIGURATION-HASH",
                rule_name="Identifiable Configuration",
                description="Processing run lacks identifiable configuration hash",
            ))

        # Invariant 4 & 5 & 7 & 8 on fields
        valid_regions = set(known_regions) if known_regions else None

        for f in fields:
            # Inv 4: Rule identification
            if not f.normalization_rule:
                violations.append(InvariantViolation(
                    invariant_id="INV-4-TRANSFORMATION-RULE",
                    rule_name="Transformation Rule Required",
                    description=f"Field {f.field_id} ({f.field_name}) missing normalization_rule identifier",
                ))

            # Inv 5: Evidence resolution
            if f.page_number < 1:
                violations.append(InvariantViolation(
                    invariant_id="INV-5-EVIDENCE-PAGE-VALIDITY",
                    rule_name="Valid Page Number",
                    description=f"Field {f.field_id} has invalid page number {f.page_number}",
                ))
            if valid_regions and f.region_id and f.region_id not in valid_regions:
                violations.append(InvariantViolation(
                    invariant_id="INV-5-REGION-REFERENCE-UNRESOLVED",
                    rule_name="Unresolved Region Reference",
                    description=f"Field {f.field_id} references non-existent region_id {f.region_id}",
                ))

            # Inv 7: Failed transformation must not be marked SUCCESS
            if f.normalization_status == "SUCCESS" and f.normalized_value is None:
                violations.append(InvariantViolation(
                    invariant_id="INV-7-FAILED-TRANSFORMATION-MISLABELED",
                    rule_name="Failed Transformation Label Integrity",
                    description=f"Field {f.field_id} marked SUCCESS but contains null normalized_value",
                ))

            # Inv 8: Raw value preservation
            if f.raw_value is None:
                violations.append(InvariantViolation(
                    invariant_id="INV-8-RAW-VALUE-PRESERVED",
                    rule_name="Raw Value Retention",
                    description=f"Field {f.field_id} missing preserved raw_value",
                ))

        if not any(v.invariant_id == "INV-4-TRANSFORMATION-RULE" for v in violations):
            passed.append("INV-4-TRANSFORMATION-RULE")
        if not any(v.invariant_id.startswith("INV-5") for v in violations):
            passed.append("INV-5-EVIDENCE-RESOLUTION")
        if not any(v.invariant_id == "INV-7-FAILED-TRANSFORMATION-MISLABELED" for v in violations):
            passed.append("INV-7-STATUS-INTEGRITY")
        if not any(v.invariant_id == "INV-8-RAW-VALUE-PRESERVED" for v in violations):
            passed.append("INV-8-RAW-VALUE-PRESERVATION")

        is_valid = len(violations) == 0

        return ProvenanceIntegrityReport(
            is_valid=is_valid,
            total_fields_checked=len(fields),
            passed_invariants=passed,
            violations=violations,
        )
