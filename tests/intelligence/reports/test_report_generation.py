"""
tests.intelligence.reports.test_report_generation
=================================================
Unit and regression tests for WP-06.06 Evidence-Backed Report Generation.
"""

import json
from pathlib import Path
import jsonschema
import pytest

from aegis.intelligence.models import (
    ReportCitation,
    ReportClaim,
    ReportSection,
    ReportType,
)
from aegis.intelligence.reports import (
    ReportContentBuilder,
    ReportRenderer,
    ReportValidator,
)


@pytest.fixture
def report_schema():
    return json.loads(Path("schemas/intelligence/report.schema.json").read_text(encoding="utf-8"))


def test_rpt_001_document_summary_construction():
    """RPT-001: Build document summary report with claims and citations."""
    claim = ReportClaim(
        claim_id="C1",
        text="Total revenue reached $450M in 2024.",
        citations=[ReportCitation(document_id="DOC-01", page_number=1)],
    )
    rep = ReportContentBuilder.build_document_summary(
        title="2024 Summary",
        document_id="DOC-01",
        summary_text="Executive summary of 2024.",
        claims=[claim],
    )
    assert rep.report_type == ReportType.DOCUMENT_SUMMARY
    assert len(rep.sections) == 1
    assert rep.scope.document_ids == ["DOC-01"]


def test_rpt_002_comparative_report_with_conflicts():
    """RPT-002: Build comparative report preserving multi-document scope and conflicts."""
    sec = ReportSection(
        section_id="S1",
        heading="Comparison",
        claims=[
            ReportClaim(
                claim_id="C1",
                text="Doc A and Doc B differ in reported budget.",
                citations=[
                    ReportCitation(document_id="DOC-A", page_number=1),
                    ReportCitation(document_id="DOC-B", page_number=2),
                ],
            )
        ],
    )
    conf = [{"subject": "Project", "predicate": "budget", "classification": "DIRECT_CONFLICT", "reason": "650 vs 700"}]
    rep = ReportContentBuilder.build_comparative_report(
        title="Comparative Report",
        document_ids=["DOC-A", "DOC-B"],
        sections=[sec],
        conflicts=conf,
    )
    assert rep.report_type == ReportType.COMPARATIVE_REPORT
    assert len(rep.conflicts) == 1


def test_rpt_003_validator_catches_scope_mismatch():
    """RPT-003: Validator detects citations referencing documents outside report scope."""
    claim_bad = ReportClaim(
        claim_id="C1",
        text="Foreign citation claim.",
        citations=[ReportCitation(document_id="DOC-OUTSIDE-SCOPE", page_number=1)],
    )
    rep = ReportContentBuilder.build_document_summary(
        title="Scoped Report",
        document_id="DOC-INSIDE-SCOPE",
        summary_text="Summary text",
        claims=[claim_bad],
    )
    val_res = ReportValidator.validate_report(rep)
    assert val_res.is_valid is False
    assert any("CITATION_SCOPE_MISMATCH" in err for err in val_res.errors)


def test_rpt_004_validator_catches_conflict_suppression():
    """RPT-004: Validator blocks reports that silently suppress known material conflicts."""
    sec = ReportSection(section_id="S1", heading="Findings", claims=[])
    # Known conflicts exist, but report.conflicts is empty!
    rep = ReportContentBuilder.build_comparative_report(
        title="Omitted Conflicts Report",
        document_ids=["DOC-A", "DOC-B"],
        sections=[sec],
        conflicts=[],
    )
    known = [{"subject": "Project", "predicate": "budget", "reason": "Discrepancy"}]
    val_res = ReportValidator.validate_report(rep, known_conflicts=known)
    assert val_res.is_valid is False
    assert any("SILENT_CONFLICT_SUPPRESSION" in err for err in val_res.errors)


def test_rpt_005_renderer_markdown_output():
    """RPT-005: Markdown renderer generates standard headings, claims, citations, and conflicts."""
    sec = ReportSection(
        section_id="S1",
        heading="Key Findings",
        summary="Summary note",
        claims=[ReportClaim(claim_id="C1", text="Revenue grew.", citations=[ReportCitation(document_id="DOC-1", page_number=2)])],
    )
    rep = ReportContentBuilder.build_comparative_report(
        title="Executive Report",
        document_ids=["DOC-1"],
        sections=[sec],
    )
    md = ReportRenderer.to_markdown(rep)
    assert "# Executive Report" in md
    assert "## Key Findings" in md
    assert "[DOC-1#P2]" in md


def test_rpt_006_renderer_html_output():
    """RPT-006: HTML renderer outputs clean HTML with cite tags."""
    claim = ReportClaim(claim_id="C1", text="Revenue grew.", citations=[ReportCitation(document_id="DOC-1", page_number=1)])
    rep = ReportContentBuilder.build_document_summary(title="HTML Report", document_id="DOC-1", summary_text="Summary", claims=[claim])
    html = ReportRenderer.to_html(rep)
    assert "<h1>HTML Report</h1>" in html
    assert "<cite>[DOC-1 P.1]</cite>" in html


def test_rpt_007_schema_conformance(report_schema):
    """RPT-007: Validates ReportItem matches report.schema.json."""
    claim = ReportClaim(claim_id="C1", text="Claim text", citations=[])
    rep = ReportContentBuilder.build_document_summary(title="Schema Valid", document_id="DOC-1", summary_text="Sum", claims=[claim])
    jsonschema.validate(rep.model_dump(), report_schema)
