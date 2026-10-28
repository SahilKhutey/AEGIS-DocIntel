"""
src/engines/intelligence/conflict_detection.py
==============================================
Multi-document conflict and inconsistency detection preserving all conflicting evidence spans.
"""

from __future__ import annotations

import math
from typing import Dict, List, Optional, Sequence, Set, Tuple

from src.engines.intelligence.contracts import (
    ConflictReport,
    ConflictType,
    ExtractedFact,
)
from src.engines.intelligence.entity_resolution import (
    EntityResolver,
    normalize_entity_label,
)


class ConflictDetector:
    """
    Detects contradictions, quantity discrepancies, date mismatches, and opposing obligations
    across documents belonging to the same tenant.
    """

    def __init__(self, resolver: Optional[EntityResolver] = None) -> None:
        self.resolver = resolver or EntityResolver()

    def detect_conflicts(
        self,
        tenant_id: str,
        facts: Sequence[ExtractedFact],
        target_subject: Optional[str] = None,
    ) -> List[ConflictReport]:
        """
        Scan a collection of facts for conflicts across documents for a tenant.
        Strictly enforces tenant isolation: all facts must match tenant_id.
        """
        # Validate tenant isolation
        for f in facts:
            if f.tenant_id != tenant_id:
                raise PermissionError(
                    f"Fact tenant '{f.tenant_id}' violates isolation boundary for '{tenant_id}'"
                )

        # Group facts by (canonical_subject, attribute, period)
        grouped: Dict[Tuple[str, str, Optional[str]], List[ExtractedFact]] = {}
        for f in facts:
            canon_subj = self.resolver.resolve(tenant_id, f.subject)
            if target_subject and canon_subj != self.resolver.resolve(tenant_id, target_subject):
                continue
            key = (canon_subj, f.attribute.lower(), f.period)
            grouped.setdefault(key, []).append(f)

        conflicts: List[ConflictReport] = []

        for (subj, attr, period), group in grouped.items():
            # Group facts by distinct source document
            doc_to_facts: Dict[str, List[ExtractedFact]] = {}
            for f in group:
                doc_to_facts.setdefault(f.document_id, []).append(f)

            # Need at least two different documents to constitute a cross-document conflict
            if len(doc_to_facts) < 2:
                continue

            conflict_rep = self._evaluate_group_conflict(
                tenant_id=tenant_id,
                subject=subj,
                attribute=attr,
                period=period,
                facts_by_doc=doc_to_facts,
            )
            if conflict_rep:
                conflicts.append(conflict_rep)

        return conflicts

    def _evaluate_group_conflict(
        self,
        tenant_id: str,
        subject: str,
        attribute: str,
        period: Optional[str],
        facts_by_doc: Dict[str, List[ExtractedFact]],
    ) -> Optional[ConflictReport]:
        all_facts: List[ExtractedFact] = []
        doc_ids: Set[str] = set()

        for doc_id, facts in facts_by_doc.items():
            all_facts.extend(facts)
            doc_ids.add(doc_id)

        first_fact = all_facts[0]
        val_type = first_fact.value_type

        # Check for discrepancies among documents
        if val_type in ("decimal", "quantity", "integer"):
            # Numerical comparison
            ref_val = first_fact.value
            ref_unit = first_fact.unit
            discrepancy_found = False

            for f in all_facts[1:]:
                # Check unit compatibility
                if f.unit and ref_unit and f.unit != ref_unit:
                    continue  # Incompatible units aren't a direct numeric conflict
                if not isinstance(f.value, (int, float)) or not isinstance(ref_val, (int, float)):
                    continue
                if not math.isclose(float(f.value), float(ref_val), rel_tol=1e-5, abs_tol=1e-5):
                    discrepancy_found = True
                    break

            if discrepancy_found:
                period_desc = f" for period {period}" if period else ""
                values_summary = ", ".join(f"{f.document_id}: {f.value} {f.unit or ''}".strip() for f in all_facts)
                desc = f"Quantity discrepancy on '{attribute}' of '{subject}'{period_desc}. Values reported: {values_summary}."
                conflict_type: ConflictType = (
                    "obligation_conflict"
                    if "notice" in attribute or "payment" in attribute or "term" in attribute
                    else "quantity_discrepancy"
                )
                return ConflictReport(
                    tenant_id=tenant_id,
                    subject=subject,
                    attribute=attribute,
                    conflict_type=conflict_type,
                    description=desc,
                    participating_facts=tuple(all_facts),
                    conflicting_document_ids=tuple(sorted(doc_ids)),
                )

        elif val_type == "date":
            # Date comparison
            ref_val = str(first_fact.value).strip()
            date_mismatch = any(str(f.value).strip() != ref_val for f in all_facts[1:])
            if date_mismatch:
                values_summary = ", ".join(f"{f.document_id}: {f.value}" for f in all_facts)
                desc = f"Date mismatch on '{attribute}' of '{subject}'. Dates reported: {values_summary}."
                return ConflictReport(
                    tenant_id=tenant_id,
                    subject=subject,
                    attribute=attribute,
                    conflict_type="date_mismatch",
                    description=desc,
                    participating_facts=tuple(all_facts),
                    conflicting_document_ids=tuple(sorted(doc_ids)),
                )

        elif val_type == "boolean":
            # Opposing terms
            ref_val = bool(first_fact.value)
            term_mismatch = any(bool(f.value) != ref_val for f in all_facts[1:])
            if term_mismatch:
                values_summary = ", ".join(f"{f.document_id}: {f.value}" for f in all_facts)
                desc = f"Opposing obligation terms on '{attribute}' of '{subject}'. Terms reported: {values_summary}."
                return ConflictReport(
                    tenant_id=tenant_id,
                    subject=subject,
                    attribute=attribute,
                    conflict_type="obligation_conflict",
                    description=desc,
                    participating_facts=tuple(all_facts),
                    conflicting_document_ids=tuple(sorted(doc_ids)),
                )

        else:
            # String / text divergence
            ref_norm = normalize_entity_label(str(first_fact.value))
            text_mismatch = any(
                normalize_entity_label(str(f.value)) != ref_norm
                for f in all_facts[1:]
            )
            if text_mismatch:
                values_summary = ", ".join(f"{f.document_id}: '{f.value}'" for f in all_facts)
                desc = f"Diverging values for attribute '{attribute}' of '{subject}'. Values reported: {values_summary}."
                return ConflictReport(
                    tenant_id=tenant_id,
                    subject=subject,
                    attribute=attribute,
                    conflict_type="attribute_divergence",
                    description=desc,
                    participating_facts=tuple(all_facts),
                    conflicting_document_ids=tuple(sorted(doc_ids)),
                )

        return None
