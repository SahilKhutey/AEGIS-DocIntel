"""
aegis.intelligence.reports.content_builder
==========================================
Constructs structured reports conforming to schemas/intelligence/report.schema.json.
"""

from __future__ import annotations

import uuid
from typing import Any, Dict, List, Optional

from aegis.intelligence.models import (
    ReportCitation,
    ReportClaim,
    ReportItem,
    ReportMetadata,
    ReportScope,
    ReportSection,
    ReportType,
)


class ReportContentBuilder:
    """Builds typed structured report envelopes."""

    @classmethod
    def build_document_summary(
        cls,
        title: str,
        document_id: str,
        summary_text: str,
        claims: List[ReportClaim],
        limitations: Optional[List[str]] = None,
    ) -> ReportItem:
        sec = ReportSection(
            section_id="SEC-01",
            heading="Executive Summary",
            summary=summary_text,
            claims=claims,
        )
        return ReportItem(
            report_id=f"RPT-{uuid.uuid4().hex[:8].upper()}",
            report_type=ReportType.DOCUMENT_SUMMARY,
            title=title,
            scope=ReportScope(document_ids=[document_id]),
            sections=[sec],
            limitations=limitations or ["Analysis limited to verified corpus document."],
            conflicts=[],
            generation_metadata=ReportMetadata(),
        )

    @classmethod
    def build_comparative_report(
        cls,
        title: str,
        document_ids: List[str],
        sections: List[ReportSection],
        conflicts: Optional[List[Dict[str, Any]]] = None,
        limitations: Optional[List[str]] = None,
    ) -> ReportItem:
        return ReportItem(
            report_id=f"RPT-{uuid.uuid4().hex[:8].upper()}",
            report_type=ReportType.COMPARATIVE_REPORT,
            title=title,
            scope=ReportScope(document_ids=document_ids),
            sections=sections,
            limitations=limitations or [],
            conflicts=conflicts or [],
            generation_metadata=ReportMetadata(),
        )
