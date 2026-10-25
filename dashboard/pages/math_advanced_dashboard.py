"""
Math & Advanced Features Dashboard Page
=======================================
Backend API contract and view data structures for the Advanced Features & Mathematical Intelligence Dashboard:
  1. PII Redaction & Compliance Filter
  2. Cross-Document Entity Resolution
  3. Structural Version Diff Engine
  4. Ingestion Anomaly & Prompt Injection Gate
  5. Quantity & Currency Unit Normalizer
  6. Query Decomposition DAG
  7. Master Unified Math Engine (16 Mathematical Domains)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PIIRedactionViewData:
    element_id: str
    original_text: str
    redacted_text: str
    entities_found: List[str] = field(default_factory=list)
    redactions_applied: int = 0

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "original_text": self.original_text,
            "redacted_text": self.redacted_text,
            "entities_found": self.entities_found,
            "redactions_applied": self.redactions_applied,
        }


@dataclass
class EntityResolutionViewData:
    canonical_id: str
    canonical_name: str
    mentions_count: int
    confidence: float = 1.0

    def to_dict(self) -> dict:
        return {
            "canonical_id": self.canonical_id,
            "canonical_name": self.canonical_name,
            "mentions_count": self.mentions_count,
            "confidence": round(self.confidence, 4),
        }


@dataclass
class StructuralDiffViewData:
    from_version: str
    to_version: str
    edit_distance: int
    num_inserts: int = 0
    num_deletes: int = 0
    num_updates: int = 0

    def to_dict(self) -> dict:
        return {
            "from_version": self.from_version,
            "to_version": self.to_version,
            "edit_distance": self.edit_distance,
            "num_inserts": self.num_inserts,
            "num_deletes": self.num_deletes,
            "num_updates": self.num_updates,
        }


@dataclass
class AnomalyGateViewData:
    document_id: str
    action: str  # "allow", "inspect", "reject"
    outlier_score: float = 0.0
    flags_count: int = 0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "action": self.action,
            "outlier_score": round(self.outlier_score, 4),
            "flags_count": self.flags_count,
        }


@dataclass
class MathDomainViewData:
    domain_name: str
    score: float
    status: str = "active"
    details: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "domain_name": self.domain_name,
            "score": round(self.score, 4),
            "status": self.status,
            "details": self.details,
        }


@dataclass
class AdvancedMathDashboardData:
    document_id: str
    pii_scans: List[PIIRedactionViewData] = field(default_factory=list)
    entities: List[EntityResolutionViewData] = field(default_factory=list)
    diffs: List[StructuralDiffViewData] = field(default_factory=list)
    anomaly_status: Optional[AnomalyGateViewData] = None
    math_domains: List[MathDomainViewData] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "pii_scans": [p.to_dict() for p in self.pii_scans],
            "entities": [e.to_dict() for e in self.entities],
            "diffs": [d.to_dict() for d in self.diffs],
            "anomaly_status": self.anomaly_status.to_dict() if self.anomaly_status else None,
            "math_domains": [m.to_dict() for m in self.math_domains],
        }


class MathAdvancedDashboard:
    """Advanced Features & Mathematical Intelligence Dashboard Backend API."""

    def __init__(self) -> None:
        self.dashboards: Dict[str, AdvancedMathDashboardData] = {}

    def get_or_create(self, document_id: str) -> AdvancedMathDashboardData:
        if document_id not in self.dashboards:
            self.dashboards[document_id] = AdvancedMathDashboardData(document_id=document_id)
        return self.dashboards[document_id]

    def add_pii_scan(self, document_id: str, scan: PIIRedactionViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.pii_scans.append(scan)

    def add_entity(self, document_id: str, entity: EntityResolutionViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.entities.append(entity)

    def add_structural_diff(self, document_id: str, diff: StructuralDiffViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.diffs.append(diff)

    def set_anomaly_status(self, document_id: str, status: AnomalyGateViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.anomaly_status = status

    def add_math_domain(self, document_id: str, domain: MathDomainViewData) -> None:
        dash = self.get_or_create(document_id)
        dash.math_domains.append(domain)

    def render_dashboard(self, document_id: str) -> dict:
        dash = self.get_or_create(document_id)
        return dash.to_dict()
