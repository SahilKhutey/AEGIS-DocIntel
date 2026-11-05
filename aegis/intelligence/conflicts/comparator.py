"""
aegis.intelligence.conflicts.comparator
=======================================
8-Stage Comparative Conflict Detection Engine across multi-document facts.
"""

from __future__ import annotations

import math
import uuid
from typing import Any, Dict, List, Optional, Tuple

from aegis.intelligence.models import (
    ConflictClassification,
    ConflictFactRef,
    ConflictItem,
    FactItem,
)


class ConflictComparator:
    """Evaluates cross-document fact pairs through the 8-stage comparative conflict protocol."""

    @classmethod
    def compare_facts(
        cls,
        fact1: FactItem,
        fact2: FactItem,
    ) -> Optional[ConflictItem]:
        """
        Compare two facts and determine if they represent a genuine conflict,
        a scope/temporal divergence, or agreement.
        """
        # Stage 1: Are subjects the same entity?
        s1 = fact1.subject.name.lower().strip()
        s2 = fact2.subject.name.lower().strip()
        if s1 != s2 and s1 not in s2 and s2 not in s1:
            return None  # Unrelated entities

        # Stage 2: Are predicates semantically equivalent?
        p1 = fact1.predicate.lower().strip()
        p2 = fact2.predicate.lower().strip()
        if p1 != p2:
            return None  # Different attributes

        v1 = fact1.object.value
        v2 = fact2.object.value
        u1 = fact1.object.unit
        u2 = fact2.object.unit
        period1 = fact1.qualifiers.reporting_period
        period2 = fact2.qualifiers.reporting_period
        scope1 = fact1.qualifiers.geographic_scope
        scope2 = fact2.qualifiers.geographic_scope

        cid = f"CONF-{uuid.uuid4().hex[:8].upper()}"
        f1_ref = ConflictFactRef(
            fact_id=fact1.fact_id,
            value=v1,
            raw_value=fact1.object.raw_value,
            unit=u1,
            period=period1,
            document_id=fact1.evidence[0].document_id if fact1.evidence else "DOC-1",
            page_number=fact1.evidence[0].page_number if fact1.evidence else 1,
        )
        f2_ref = ConflictFactRef(
            fact_id=fact2.fact_id,
            value=v2,
            raw_value=fact2.object.raw_value,
            unit=u2,
            period=period2,
            document_id=fact2.evidence[0].document_id if fact2.evidence else "DOC-2",
            page_number=fact2.evidence[0].page_number if fact2.evidence else 1,
        )

        # Stage 3: Do facts refer to the same period?
        if period1 and period2 and period1 != period2:
            return ConflictItem(
                conflict_id=cid,
                subject=fact1.subject.name,
                predicate=fact1.predicate,
                facts=[f1_ref, f2_ref],
                classification=ConflictClassification.TEMPORAL_DIFFERENCE,
                reason=f"Values apply to different reporting periods ({period1} vs {period2}).",
                resolution_status="RESOLVED_DIFFERENT_SCOPE",
            )

        # Stage 4: Are geographic scopes different?
        if scope1 and scope2 and scope1 != scope2:
            return ConflictItem(
                conflict_id=cid,
                subject=fact1.subject.name,
                predicate=fact1.predicate,
                facts=[f1_ref, f2_ref],
                classification=ConflictClassification.SCOPE_DIFFERENCE,
                reason=f"Values apply to different geographic scopes ({scope1} vs {scope2}).",
                resolution_status="RESOLVED_DIFFERENT_SCOPE",
            )

        # Stage 5: Are units and currencies comparable?
        if u1 and u2 and u1 != u2:
            return ConflictItem(
                conflict_id=cid,
                subject=fact1.subject.name,
                predicate=fact1.predicate,
                facts=[f1_ref, f2_ref],
                classification=ConflictClassification.UNIT_DIFFERENCE,
                reason=f"Values use incompatible units or currencies ({u1} vs {u2}).",
                resolution_status="NEEDS_HUMAN_REVIEW",
            )

        # Stage 6 & 7: Check value compatibility
        values_equal = False
        if isinstance(v1, (int, float)) and isinstance(v2, (int, float)):
            values_equal = math.isclose(float(v1), float(v2), rel_tol=1e-4)
        else:
            values_equal = str(v1).strip().lower() == str(v2).strip().lower()

        if values_equal:
            return ConflictItem(
                conflict_id=cid,
                subject=fact1.subject.name,
                predicate=fact1.predicate,
                facts=[f1_ref, f2_ref],
                classification=ConflictClassification.NO_CONFLICT,
                reason="Corroborating values match across sources.",
                resolution_status="RESOLVED_SUPERSEDED",
            )

        # Stage 8: Incompatible values on same subject, predicate, and period -> DIRECT CONFLICT
        return ConflictItem(
            conflict_id=cid,
            subject=fact1.subject.name,
            predicate=fact1.predicate,
            facts=[f1_ref, f2_ref],
            classification=ConflictClassification.DIRECT_CONFLICT,
            reason=f"Incompatible reported values for {fact1.predicate}: '{v1}' vs '{v2}' in overlapping periods.",
            resolution_status="UNRESOLVED",
        )
