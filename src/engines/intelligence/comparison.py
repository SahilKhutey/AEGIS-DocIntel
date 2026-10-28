"""
src/engines/intelligence/comparison.py
======================================
Deterministic cross-document fact comparison enforcing tenant isolation,
unit compatibility, and temporal scope alignment.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Sequence, Tuple

from src.engines.intelligence.contracts import (
    ComparisonStatus,
    DocumentComparisonResult,
    ExtractedFact,
    PairComparison,
)
from src.engines.intelligence.entity_resolution import (
    EntityResolver,
    normalize_entity_label,
)


class CrossTenantComparisonError(PermissionError):
    """Raised when an attempt is made to compare documents across different tenants."""
    pass


class DocumentComparator:
    """
    Compares extracted facts across two documents belonging to the same tenant.
    """

    def __init__(self, resolver: Optional[EntityResolver] = None) -> None:
        self.resolver = resolver or EntityResolver()

    def compare_facts(
        self,
        tenant_id: str,
        left_doc_id: str,
        left_facts: Sequence[ExtractedFact],
        right_doc_id: str,
        right_facts: Sequence[ExtractedFact],
        target_attributes: Optional[Sequence[str]] = None,
    ) -> DocumentComparisonResult:
        """
        Compare facts between two documents for the specified tenant.
        Enforces tenant isolation: all facts must belong to tenant_id.
        """
        # 1. Enforce tenant boundaries
        for f in left_facts:
            if f.tenant_id != tenant_id:
                raise CrossTenantComparisonError(
                    f"Left fact tenant '{f.tenant_id}' does not match context tenant '{tenant_id}'"
                )
        for f in right_facts:
            if f.tenant_id != tenant_id:
                raise CrossTenantComparisonError(
                    f"Right fact tenant '{f.tenant_id}' does not match context tenant '{tenant_id}'"
                )

        target_attrs_set = set(target_attributes) if target_attributes else None

        # 2. Index facts by (canonical_subject, canonical_attribute)
        left_index: Dict[Tuple[str, str], List[ExtractedFact]] = {}
        for f in left_facts:
            subj = self.resolver.resolve(tenant_id, f.subject)
            attr = f.attribute.lower()
            if target_attrs_set and attr not in target_attrs_set:
                continue
            left_index.setdefault((subj, attr), []).append(f)

        right_index: Dict[Tuple[str, str], List[ExtractedFact]] = {}
        for f in right_facts:
            subj = self.resolver.resolve(tenant_id, f.subject)
            attr = f.attribute.lower()
            if target_attrs_set and attr not in target_attrs_set:
                continue
            right_index.setdefault((subj, attr), []).append(f)

        # 3. Pair facts matching key
        all_keys = set(left_index.keys()).union(right_index.keys())
        comparisons: List[PairComparison] = []
        summary_counts: Dict[str, int] = {
            "equal": 0,
            "different": 0,
            "potential_conflict": 0,
            "not_comparable": 0,
            "needs_review": 0,
        }

        for subj, attr in sorted(all_keys):
            left_list = left_index.get((subj, attr), [])
            right_list = right_index.get((subj, attr), [])

            for l_fact in left_list:
                for r_fact in right_list:
                    pair_comp = self._compare_pair(
                        tenant_id=tenant_id,
                        left_doc_id=left_doc_id,
                        left_fact=l_fact,
                        right_doc_id=right_doc_id,
                        right_fact=r_fact,
                    )
                    comparisons.append(pair_comp)
                    summary_counts[pair_comp.status] = summary_counts.get(pair_comp.status, 0) + 1

        return DocumentComparisonResult(
            tenant_id=tenant_id,
            left_doc_id=left_doc_id,
            right_doc_id=right_doc_id,
            comparisons=tuple(comparisons),
            summary=summary_counts,
        )

    def _compare_pair(
        self,
        tenant_id: str,
        left_doc_id: str,
        left_fact: ExtractedFact,
        right_doc_id: str,
        right_fact: ExtractedFact,
    ) -> PairComparison:
        subject = self.resolver.resolve(tenant_id, left_fact.subject)
        attribute = left_fact.attribute

        # 1. Check unit compatibility
        if left_fact.unit and right_fact.unit and left_fact.unit != right_fact.unit:
            return PairComparison(
                subject=subject,
                attribute=attribute,
                status="not_comparable",
                left_doc_id=left_doc_id,
                left_fact=left_fact,
                right_doc_id=right_doc_id,
                right_fact=right_fact,
                difference_summary=f"Incompatible units: {left_fact.unit} vs {right_fact.unit}",
                details={"left_unit": left_fact.unit, "right_unit": right_fact.unit},
            )

        # 2. Check temporal alignment
        period_mismatch = False
        if left_fact.period and right_fact.period and left_fact.period != right_fact.period:
            period_mismatch = True

        # 3. Check value equality
        status: ComparisonStatus = "equal"
        diff_summary: Optional[str] = None
        details: Dict[str, Any] = {
            "period_mismatch": period_mismatch,
            "left_period": left_fact.period,
            "right_period": right_fact.period,
        }

        l_val = left_fact.value
        r_val = right_fact.value

        if isinstance(l_val, (int, float)) and isinstance(r_val, (int, float)):
            if math.isclose(float(l_val), float(r_val), rel_tol=1e-5, abs_tol=1e-5):
                status = "equal"
                diff_summary = f"Numeric values match exactly ({l_val})"
            else:
                if period_mismatch:
                    status = "different"
                    diff_summary = f"Values differ over different periods ({left_fact.period}: {l_val} vs {right_fact.period}: {r_val})"
                else:
                    status = "potential_conflict"
                    diff_summary = f"Discrepancy for same period: {l_val} vs {r_val}"
                details["delta"] = float(r_val) - float(l_val)
        elif left_fact.value_type == "date":
            if str(l_val).strip() == str(r_val).strip():
                status = "equal"
                diff_summary = f"Dates match ({l_val})"
            else:
                status = "potential_conflict"
                diff_summary = f"Date discrepancy: {l_val} vs {r_val}"
        elif isinstance(l_val, bool) and isinstance(r_val, bool):
            if l_val == r_val:
                status = "equal"
                diff_summary = f"Boolean values match ({l_val})"
            else:
                status = "potential_conflict"
                diff_summary = f"Opposing terms: {l_val} vs {r_val}"
        else:
            # String or generic comparison
            s_left = normalize_entity_label(str(l_val))
            s_right = normalize_entity_label(str(r_val))
            if s_left == s_right:
                status = "equal"
                diff_summary = "Values match"
            else:
                status = "different" if period_mismatch else "potential_conflict"
                diff_summary = f"Different text values: '{l_val}' vs '{r_val}'"

        return PairComparison(
            subject=subject,
            attribute=attribute,
            status=status,
            left_doc_id=left_doc_id,
            left_fact=left_fact,
            right_doc_id=right_doc_id,
            right_fact=right_fact,
            difference_summary=diff_summary,
            details=details,
        )
