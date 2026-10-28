"""
src/engines/governance/feedback.py
==================================
Structured review feedback, error categories, and quality improvement metrics.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Dict, List, Optional, Sequence

from src.engines.governance.contracts import ReviewItem, ReviewStatus


class FeedbackCategory(StrEnum):
    WRONG_VALUE = "wrong_value"
    WRONG_TYPE = "wrong_type"
    WRONG_ENTITY = "wrong_entity"
    BAD_EVIDENCE = "bad_evidence"
    MISSING_FACT = "missing_fact"
    FALSE_CONFLICT = "false_conflict"
    MISSED_CONFLICT = "missed_conflict"
    AMBIGUOUS_SOURCE = "ambiguous_source"
    OTHER = "other"


@dataclass(frozen=True, slots=True)
class ReviewFeedback:
    """Structured quality assessment provided by a reviewer during or after decision."""

    feedback_id: str
    tenant_id: str
    review_id: str
    candidate_id: str
    category: FeedbackCategory
    reviewer_id: str
    notes: str = ""
    corrected_value_reference: Optional[str] = None
    schema_version: int = 1
    created_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "feedback_id": self.feedback_id,
            "tenant_id": self.tenant_id,
            "review_id": self.review_id,
            "candidate_id": self.candidate_id,
            "category": str(self.category),
            "reviewer_id": self.reviewer_id,
            "notes": self.notes,
            "corrected_value_reference": self.corrected_value_reference,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> ReviewFeedback:
        return cls(
            feedback_id=data["feedback_id"],
            tenant_id=data["tenant_id"],
            review_id=data["review_id"],
            candidate_id=data["candidate_id"],
            category=FeedbackCategory(data["category"]),
            reviewer_id=data["reviewer_id"],
            notes=data.get("notes", ""),
            corrected_value_reference=data.get("corrected_value_reference"),
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
        )


def compute_governance_metrics(
    reviews: Sequence[ReviewItem],
    feedback: Sequence[ReviewFeedback] = (),
) -> Dict[str, Any]:
    """
    Compute governance quality metrics across a set of review items and feedback.
    """
    total = len(reviews)
    if total == 0:
        return {
            "total_items": 0,
            "approval_rate": 0.0,
            "correction_rate": 0.0,
            "rejection_rate": 0.0,
            "evidence_failure_rate": 0.0,
            "decided_count": 0,
            "feedback_categories": {},
        }

    approved = sum(1 for r in reviews if r.status == ReviewStatus.APPROVED)
    corrected = sum(1 for r in reviews if r.status == ReviewStatus.CORRECTED)
    rejected = sum(1 for r in reviews if r.status == ReviewStatus.REJECTED)
    needs_evidence = sum(1 for r in reviews if r.status == ReviewStatus.NEEDS_EVIDENCE)
    decided = approved + corrected + rejected

    feedback_dist: Dict[str, int] = {}
    for fb in feedback:
        cat = str(fb.category)
        feedback_dist[cat] = feedback_dist.get(cat, 0) + 1

    return {
        "total_items": total,
        "decided_count": decided,
        "approval_rate": round(approved / decided, 4) if decided > 0 else 0.0,
        "correction_rate": round(corrected / decided, 4) if decided > 0 else 0.0,
        "rejection_rate": round(rejected / decided, 4) if decided > 0 else 0.0,
        "evidence_failure_rate": round(needs_evidence / total, 4),
        "feedback_categories": feedback_dist,
    }
