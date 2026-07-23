"""
JSON Exporter
=============

Exports UniversalExportObject as JSON.

Configuration:
- indent: indentation spaces
- sort_keys: alphabetical key ordering
- ensure_ascii: ASCII-safe output
- include_metadata: include metadata block
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .exceptions import FormatError, InvalidContextError
from .universal_exporter import UniversalExportObject


@dataclass
class JSONConfig:
    """JSON export configuration."""

    indent: Optional[int] = 2
    sort_keys: bool = False
    ensure_ascii: bool = False
    include_metadata: bool = True
    include_citations: bool = True
    pretty: bool = True


class JSONExporter:
    """JSON format exporter."""

    def __init__(self, config: Optional[JSONConfig] = None) -> None:
        self.config = config or JSONConfig()

    def export(self, ueo: UniversalExportObject) -> str:
        """Export UEO as JSON string."""
        data = self._to_dict(ueo)
        try:
            if self.config.pretty:
                return json.dumps(
                    data,
                    indent=self.config.indent,
                    sort_keys=self.config.sort_keys,
                    ensure_ascii=self.config.ensure_ascii,
                    default=str,
                )
            return json.dumps(
                data, ensure_ascii=self.config.ensure_ascii, default=str
            )
        except (TypeError, ValueError) as exc:
            raise FormatError(f"JSON serialization failed: {exc}") from exc

    def export_dict(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        """Export UEO as Python dict."""
        return self._to_dict(ueo)

    def export_to_file(self, ueo: UniversalExportObject, filepath: str) -> None:
        """Export to file."""
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export(ueo))

    def _to_dict(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "system": ueo.system,
            "context": ueo.context,
            "summary": ueo.summary,
            "total_tokens": ueo.total_tokens,
            "confidence": ueo.confidence,
        }
        if self.config.include_citations:
            data["citations"] = ueo.citations
        if self.config.include_metadata:
            data["metadata"] = ueo.metadata
        if ueo.agent_specific:
            data["agent_specific"] = ueo.agent_specific
        if ueo.engine_reports:
            data["engine_reports"] = ueo.engine_reports
        return data