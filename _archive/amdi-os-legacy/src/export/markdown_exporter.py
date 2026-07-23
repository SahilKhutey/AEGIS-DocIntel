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

    def export(self, ueo: UniversalExportObject) -> str:
        """Export UEO as Markdown string."""
        try:
            return self._render(ueo)
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
        sections.append(f"{h1} AMDI-OS Context Export")
        sections.append("")

        # Token summary
        sections.append(
            f"> **Total tokens:** {ueo.total_tokens} | "
            f"**Confidence:** {ueo.confidence:.4f}"
        )
        sections.append("")

        # System
        if self.config.include_system and ueo.system:
            sections.append(f"{h2} System")
            sections.append("")
            sections.append(ueo.system)
            sections.append("")

        # Summary
        if self.config.include_summary and ueo.summary:
            sections.append(f"{h2} Summary")
            sections.append("")
            sections.append(ueo.summary)
            sections.append("")

        # Content
        if self.config.include_content and ueo.context:
            sections.append(f"{h2} Content")
            sections.append("")
            sections.append(ueo.context)
            sections.append("")

        # Tables
        if self.config.include_tables and ueo.tables:
            sections.append(f"{h2} Tables")
            sections.append("")
            for i, table in enumerate(ueo.tables, start=1):
                sections.append(f"{h3} Table {i}")
                sections.append("")
                sections.append(format_table(table))
                sections.append("")

        # Citations
        if self.config.include_citations and ueo.citations:
            sections.append(f"{h2} Citations")
            sections.append("")
            for cit in ueo.citations:
                if isinstance(cit, dict):
                    sections.append(
                        "- " + format_citation(cit, self.config.citation_style)
                    )
                else:
                    sections.append(f"- {cit}")
            sections.append("")

        # Metadata
        if self.config.include_metadata and ueo.metadata:
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
            f"*Exported by AMDI-OS Export Engine v{ueo.version}*"
        )
        return "\n".join(sections)