"""
aegis.processing.provenance
===========================
Field-level provenance tracking, document processing lineage, and hard invariant auditing.
"""

from aegis.processing.provenance.field_trace import FieldProvenanceTracker
from aegis.processing.provenance.lineage import DocumentLineage
from aegis.processing.provenance.validator import (
    InvariantViolation,
    ProvenanceIntegrityReport,
    ProvenanceInvariantValidator,
)

__all__ = [
    "FieldProvenanceTracker",
    "DocumentLineage",
    "ProvenanceInvariantValidator",
    "ProvenanceIntegrityReport",
    "InvariantViolation",
]
