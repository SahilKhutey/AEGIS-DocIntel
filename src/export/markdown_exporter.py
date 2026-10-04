"""
Markdown Exporter
=================

Exports UniversalExportObject as Markdown.

Sections:
- # System
- ## Summary
- ## Content
- ## Tables
- ## Citations
- ## Metadata (as fenced code block)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from .exceptions import FormatError
from .formatters import (
    format_citation,
    format_metadata,
    format_table,
)
from .universal_exporter import UniversalExportObject


@dataclass
class MarkdownConfig:
    """Markdown export configuration."""

    include_system: bool = True
    include_summary: bool = True
    include_content: bool = True
    include_citations: bool = True
    include_metadata: bool = True
    include_tables: bool = True
    citation_style: str = "bracketed"
    heading_level: int = 1
    metadata_format: str = "yaml"  # 'yaml' | 'json' | 'table'


class MarkdownExporter:
    """Markdown format exporter."""

    def __init__(self, config: Optional[MarkdownConfig] = None) -> None:
        self.config = config or MarkdownConfig()

    @classmethod
    def export(cls_or_self, ueo: UniversalExportObject) -> str:
        """Export UEO as Markdown string (callable statically or on instance)."""
        instance = cls_or_self if not isinstance(cls_or_self, type) else cls_or_self()
        try:
            return instance._render(ueo)
        except Exception as exc:
            raise FormatError(f"Markdown export failed: {exc}") from exc

    def export_to_file(self, ueo: UniversalExportObject, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export(ueo))

    def _render(self, ueo: UniversalExportObject) -> str:
        h1 = "#" * self.config.heading_level
        h2 = "#" * (self.config.heading_level + 1)
        h3 = "#" * (self.config.heading_level + 2)
        sections: List[str] = []

        # Title
        title_text = ""
        if hasattr(ueo, "document_summary") and getattr(ueo.document_summary, "title", None):
            title_text = ueo.document_summary.title
        elif isinstance(getattr(ueo, "summary", None), dict) and ueo.summary.get("title"):
            title_text = ueo.summary.get("title")
        elif hasattr(getattr(ueo, "metadata", None), "document_name") and ueo.metadata.document_name:
            title_text = ueo.metadata.document_name
        elif isinstance(getattr(ueo, "metadata", None), dict) and ueo.metadata.get("document_name"):
            title_text = ueo.metadata.get("document_name")

        if title_text:
            sections.append(f"{h1} {title_text}")
        else:
            sections.append(f"{h1} AMDI-OS Context Export")
        sections.append("")

        # Confidence handling
        conf_overall = 1.0
        if hasattr(ueo, "confidence"):
            if hasattr(ueo.confidence, "overall"):
                conf_overall = float(ueo.confidence.overall)
            elif isinstance(ueo.confidence, (int, float)):
                conf_overall = float(ueo.confidence)

        # Token summary
        sections.append(
            f"> **Total tokens:** {getattr(ueo, 'total_tokens', None) or getattr(ueo, 'tokens_used', 0)} | "
            f"**Confidence:** {conf_overall:.4f}"
        )
        sections.append("")

        # Document metadata if AEL-style Metadata object
        if hasattr(ueo, "metadata") and hasattr(ueo.metadata, "document_name"):
            sections.append(f"{h2} Document Metadata")
            sections.append(f"- **Document**: {ueo.metadata.document_name}")
            sections.append(f"- **Pages**: {ueo.metadata.pages}")
            sections.append(f"- **Type**: {ueo.metadata.document_type}")
            sections.append(f"- **Language**: {ueo.metadata.language}")
            sections.append(f"- **Doc ID**: `{ueo.metadata.doc_id}`")
            sections.append("")

        # Query
        if getattr(ueo, "query", None):
            sections.append(f"{h2} Query")
            sections.append(f"> {ueo.query}")
            sections.append("")

        # System
        if self.config.include_system and getattr(ueo, "system", None):
            sections.append(f"{h2} System")
            sections.append("")
            sections.append(str(ueo.system))
            sections.append("")

        # Summary
        if hasattr(ueo, "document_summary") and ueo.document_summary and (
            getattr(ueo.document_summary, "abstract", None)
            or getattr(ueo.document_summary, "key_topics", None)
            or getattr(ueo.document_summary, "keywords", None)
        ):
            sections.append(f"{h2} Summary")
            if ueo.document_summary.abstract:
                sections.append(ueo.document_summary.abstract)
            if ueo.document_summary.key_topics:
                sections.append("")
                sections.append("**Key Topics**: " + ", ".join(ueo.document_summary.key_topics))
            if ueo.document_summary.keywords:
                sections.append("")
                sections.append("**Keywords**: " + ", ".join(ueo.document_summary.keywords))
            sections.append("")
        elif self.config.include_summary and getattr(ueo, "summary", None):
            sections.append(f"{h2} Summary")
            sections.append("")
            sections.append(str(ueo.summary))
            sections.append("")

        # Key findings / key points
        if getattr(ueo, "key_points", None):
            sections.append(f"{h2} Key Findings")
            for i, kp in enumerate(ueo.key_points, start=1):
                page_str = f" [p{getattr(kp, 'page', 1)}"
                if getattr(kp, "section", None):
                    page_str += f", §{kp.section}"
                page_str += "]"
                sections.append(f"{i}. {getattr(kp, 'text', str(kp))}{page_str}")
            sections.append("")

        # Content
        if self.config.include_content and getattr(ueo, "context", None):
            sections.append(f"{h2} Content")
            sections.append("")
            sections.append(str(ueo.context))
            sections.append("")

        # Tables
        matrix_tables = []
        if hasattr(ueo, "matrix") and getattr(ueo.matrix, "tables", None):
            matrix_tables = ueo.matrix.tables
        elif hasattr(ueo, "tables") and ueo.tables:
            matrix_tables = ueo.tables

        if self.config.include_tables and matrix_tables:
            sections.append(f"{h2} Tables")
            sections.append("")
            for i, table in enumerate(matrix_tables, start=1):
                if isinstance(table, dict) and "name" in table:
                    tbl_name = table.get("name", f"Table {i}")
                    tbl_page = table.get("page", "?")
                    sections.append(f"{h3} {tbl_name}")
                    sections.append(f"*Page {tbl_page}*")
                    sections.append("")
                    headers = table.get("headers", [])
                    data = table.get("data", [])
                    if headers:
                        sections.append("| " + " | ".join(str(h) for h in headers) + " |")
                        sections.append("|" + "|".join("---" for _ in headers) + "|")
                    for row in data[:20]:
                        sections.append("| " + " | ".join(str(c) for c in row) + " |")
                    if table.get("computed_metrics"):
                        sections.append("")
                        sections.append("**Computed metrics:**")
                        for k, v in table["computed_metrics"].items():
                            sections.append(f"- {k}: {v}")
                    sections.append("")
                else:
                    sections.append(f"{h3} Table {i}")
                    sections.append("")
                    sections.append(format_table(table))
                    sections.append("")

        # Key Relationships (Graph)
        if hasattr(ueo, "graph") and getattr(ueo.graph, "key_relationships", None):
            sections.append(f"{h2} Key Relationships")
            for rel in ueo.graph.key_relationships[:10]:
                src_val = rel.get("src", "")
                dst_val = rel.get("dst", "")
                type_val = rel.get("type", "")
                sections.append(f"- {src_val} → {dst_val} ({type_val})")
            sections.append("")

        # Document Templates
        if hasattr(ueo, "template") and getattr(ueo.template, "templates", None):
            sections.append(f"{h2} Document Templates")
            for tmpl in ueo.template.templates[:5]:
                tmpl_id = tmpl.get("id", "")
                tmpl_size = tmpl.get("cluster_size", 0)
                sections.append(f"- **{tmpl_id}**: {tmpl_size} pages")
            sections.append("")

        # Citations
        if self.config.include_citations and getattr(ueo, "citations", None):
            sections.append(f"{h2} Citations")
            sections.append("")
            for i, cit in enumerate(ueo.citations, start=1):
                if hasattr(cit, "page"):
                    cite = f"[{i}] Page {cit.page}"
                    if getattr(cit, "section", None):
                        cite += f", §{cit.section}"
                    c_conf = getattr(cit, "confidence", None)
                    if isinstance(c_conf, (int, float)):
                        cite += f" (confidence: {c_conf:.2f})"
                    sections.append(cite)
                    snippet_text = getattr(cit, "snippet", "") or getattr(cit, "text", "")
                    if snippet_text:
                        sections.append(f"    {snippet_text[:150]}")
                elif isinstance(cit, dict):
                    sections.append(
                        "- " + format_citation(cit, self.config.citation_style)
                    )
                else:
                    sections.append(f"- {cit}")
            sections.append("")

        # Confidence breakdown
        if hasattr(ueo, "confidence") and hasattr(ueo.confidence, "overall"):
            sections.append(f"{h2} Confidence")
            sections.append(f"- **Overall**: {ueo.confidence.overall:.3f}")
            sections.append(f"- **Semantic**: {ueo.confidence.semantic:.3f}")
            sections.append(f"- **Numerical**: {ueo.confidence.numerical:.3f}")
            sections.append(f"- **Structural**: {ueo.confidence.structural:.3f}")
            sections.append(f"- **Retrieval**: {ueo.confidence.retrieval:.3f}")
            sections.append("")

        # Metadata (dict form)
        if self.config.include_metadata and isinstance(ueo.metadata, dict) and ueo.metadata:
            sections.append(f"{h2} Metadata")
            sections.append("")
            if self.config.metadata_format == "json":
                import json
                sections.append("```json")
                sections.append(
                    json.dumps(ueo.metadata, indent=2, default=str)
                )
                sections.append("```")
            elif self.config.metadata_format == "table":
                sections.append("| Key | Value |")
                sections.append("| --- | --- |")
                for k, v in ueo.metadata.items():
                    sections.append(f"| {k} | {v} |")
            else:
                sections.append("```yaml")
                sections.append(format_metadata(ueo.metadata))
                sections.append("```")
            sections.append("")

        # Footer
        sections.append("---")
        sections.append(
            f"*Exported by AMDI-OS Export Engine v{getattr(ueo, 'version', '1.0.0')}*"
        )
        return "\n".join(sections)