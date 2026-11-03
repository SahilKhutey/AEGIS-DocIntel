"""
aegis.intelligence.reports.renderer
===================================
Renders validated ReportItem domain models into Markdown, HTML, and JSON representations.
"""

from __future__ import annotations

import json
from aegis.intelligence.models import ReportItem


class ReportRenderer:
    """Renders validated structured reports into output formats."""

    @classmethod
    def to_markdown(cls, report: ReportItem) -> str:
        """Render ReportItem to GitHub-flavored Markdown."""
        lines = [
            f"# {report.title}",
            "",
            f"> **Report Type**: `{report.report_type.value}`  ",
            f"> **Report ID**: `{report.report_id}`  ",
            f"> **Scope**: {', '.join([f'`{d}`' for d in report.scope.document_ids])}  ",
            f"> **Generated**: `{report.generation_metadata.generated_at}`  ",
            "",
            "---",
            "",
        ]

        for sec in report.sections:
            lines.append(f"## {sec.heading}")
            lines.append("")
            if sec.summary:
                lines.append(f"*{sec.summary}*")
                lines.append("")
            for claim in sec.claims:
                cits = [
                    f"[{c.document_id}#P{c.page_number or 1}]"
                    for c in claim.citations
                ]
                cit_str = f" {' '.join(cits)}" if cits else ""
                lines.append(f"- {claim.text}{cit_str}")
            lines.append("")

        if report.conflicts:
            lines.append("## Identified Source Conflicts")
            lines.append("")
            for conf in report.conflicts:
                lines.append(f"### Conflict: {conf.get('subject')} - {conf.get('predicate')}")
                lines.append(f"- **Classification**: `{conf.get('classification')}`")
                lines.append(f"- **Details**: {conf.get('reason')}")
                lines.append("")

        if report.limitations:
            lines.append("## Analytical Limitations")
            lines.append("")
            for lim in report.limitations:
                lines.append(f"- {lim}")
            lines.append("")

        return "\n".join(lines)

    @classmethod
    def to_html(cls, report: ReportItem) -> str:
        """Render ReportItem to clean HTML."""
        body = [f"<h1>{report.title}</h1>"]
        body.append(f"<p><strong>Report ID:</strong> {report.report_id}</p>")
        body.append(f"<p><strong>Scope:</strong> {', '.join(report.scope.document_ids)}</p>")

        for sec in report.sections:
            body.append(f"<h2>{sec.heading}</h2>")
            if sec.summary:
                body.append(f"<p><em>{sec.summary}</em></p>")
            body.append("<ul>")
            for claim in sec.claims:
                cits = [f"<cite>[{c.document_id} P.{c.page_number or 1}]</cite>" for c in claim.citations]
                cit_html = f" {' '.join(cits)}" if cits else ""
                body.append(f"<li>{claim.text}{cit_html}</li>")
            body.append("</ul>")

        return "\n".join(body)

    @classmethod
    def to_json(cls, report: ReportItem) -> str:
        """Render ReportItem to formatted JSON string."""
        return json.dumps(report.model_dump(), indent=2)
