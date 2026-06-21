"""
Source Authenticity and Reliability Verifier
=============================================

Evaluates source document integrity and computes reliability metrics.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class SourceCheckResult:
    """Result of source authenticity checks."""

    is_authentic: bool
    source_reliability: float  # [0.0, 1.0]
    checked_sources: List[str] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "is_authentic": self.is_authentic,
            "source_reliability": round(self.source_reliability, 4),
            "checked_sources": self.checked_sources,
            "issues": self.issues,
            "metadata": self.metadata,
        }


class SourceVerifier:
    """Verifies authenticity and reliability of source documents."""

    def __init__(self, default_reliability: float = 1.0) -> None:
        self.default_reliability = default_reliability

    def verify(self, source_documents: Dict[str, Any]) -> SourceCheckResult:
        """Verify the given source documents."""
        if not source_documents:
            return SourceCheckResult(
                is_authentic=False,
                source_reliability=0.0,
                issues=["no_source_documents"],
            )

        checked: List[str] = []
        issues: List[str] = []
        reliability_scores: List[float] = []

        for doc_id, doc in source_documents.items():
            checked.append(doc_id)
            doc_reliability = self.default_reliability

            if isinstance(doc, dict):
                has_meta = "metadata" in doc or any(k in doc for k in ["title", "author", "url"])
                if not has_meta:
                    issues.append(f"missing_metadata:{doc_id}")
                    doc_reliability -= 0.1

                text = doc.get("text", "")
                if not text and isinstance(doc.get("pages"), dict):
                    text = "".join(doc["pages"].values())
                elif not text and isinstance(doc.get("pages"), list):
                    text = "".join(doc["pages"])

                if not text:
                    issues.append(f"empty_source_document:{doc_id}")
                    doc_reliability -= 0.3
                elif len(text) < 50:
                    issues.append(f"short_source_document:{doc_id}")
                    doc_reliability -= 0.1
            elif isinstance(doc, str):
                if not doc.strip():
                    issues.append(f"empty_source_document:{doc_id}")
                    doc_reliability -= 0.3
                elif len(doc) < 50:
                    issues.append(f"short_source_document:{doc_id}")
                    doc_reliability -= 0.1
            else:
                issues.append(f"unknown_source_type:{doc_id}")
                doc_reliability -= 0.2

            reliability_scores.append(max(0.0, doc_reliability))

        avg_reliability = sum(reliability_scores) / len(reliability_scores)
        is_authentic = avg_reliability >= 0.7

        return SourceCheckResult(
            is_authentic=is_authentic,
            source_reliability=avg_reliability,
            checked_sources=checked,
            issues=issues,
        )
