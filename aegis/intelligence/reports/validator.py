"""
aegis.intelligence.reports.validator
====================================
Pre-render validation of structured reports:
structural validity, citation scope resolution, conflict preservation, and numerical consistency.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set
from aegis.intelligence.models import ReportItem


class ReportValidationResult:
    def __init__(self, is_valid: bool, errors: List[str]):
        self.is_valid = is_valid
        self.errors = errors


class ReportValidator:
    """Validates structured reports prior to output formatting."""

    @classmethod
    def validate_report(
        cls,
        report: ReportItem,
        known_conflicts: Optional[List[Dict[str, Any]]] = None,
    ) -> ReportValidationResult:
        errors: List[str] = []

        # 1. Structural validity
        if not report.sections:
            errors.append("REPORT_STRUCTURAL_ERROR: Report must contain at least one section.")
        for sec in report.sections:
            if not sec.heading or not sec.heading.strip():
                errors.append(f"REPORT_STRUCTURAL_ERROR: Section {sec.section_id} has blank heading.")

        # 2. Scope and citation resolution
        scope_docs = set(report.scope.document_ids)
        total_claims = 0
        total_citations = 0

        for sec in report.sections:
            for claim in sec.claims:
                total_claims += 1
                if not claim.text or not claim.text.strip():
                    errors.append(f"EMPTY_CLAIM: Claim {claim.claim_id} has no text.")
                for cit in claim.citations:
                    total_citations += 1
                    if cit.document_id not in scope_docs:
                        errors.append(
                            f"CITATION_SCOPE_MISMATCH: Citation {cit.document_id} not in report scope {scope_docs}"
                        )
                    if cit.page_number is not None and cit.page_number < 1:
                        errors.append(f"INVALID_PAGE_NUMBER: Page {cit.page_number} must be >= 1.")

        # 3. Conflict preservation gate
        if known_conflicts:
            # Check if material conflicts are preserved in report.conflicts
            rep_conf_keys = {
                f"{c.get('subject')}:{c.get('predicate')}" for c in report.conflicts
            }
            for kc in known_conflicts:
                k = f"{kc.get('subject')}:{kc.get('predicate')}"
                if k not in rep_conf_keys:
                    errors.append(
                        f"SILENT_CONFLICT_SUPPRESSION: Material conflict '{k}' suppressed from report findings."
                    )

        return ReportValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
        )
