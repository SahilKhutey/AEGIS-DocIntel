"""
YAML Exporter
==============

Exports UniversalExportObject as YAML.

YAML is the preferred format for configuration / metadata-only exports.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

from .exceptions import FormatError
from .universal_exporter import UniversalExportObject


@dataclass
class YAMLConfig:
    """YAML export configuration."""

    default_flow_style: bool = False
    allow_unicode: bool = True
    sort_keys: bool = False
    indent: int = 2
    include_metadata: bool = True


class YAMLExporter:
    """YAML format exporter."""

    def __init__(self, config: Optional[YAMLConfig] = None) -> None:
        self.config = config or YAMLConfig()
        try:
            import yaml
            self._yaml = yaml
        except ImportError:
            self._yaml = None

    def export(self, ueo: UniversalExportObject) -> str:
        """Export UEO as YAML string."""
        data = self._to_dict(ueo)
        if self._yaml is not None:
            try:
                return self._yaml.dump(
                    data,
                    default_flow_style=self.config.default_flow_style,
                    allow_unicode=self.config.allow_unicode,
                    sort_keys=self.config.sort_keys,
                    indent=self.config.indent,
                )
            except Exception as exc:
                raise FormatError(f"YAML serialization failed: {exc}") from exc
        # fallback: manual YAML-like serialization
        return self._manual_yaml(data)

    def export_to_file(self, ueo: UniversalExportObject, filepath: str) -> None:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(self.export(ueo))

    def _to_dict(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "system": ueo.system,
            "context": ueo.context,
            "summary": ueo.summary,
            "total_tokens": ueo.total_tokens,
            "confidence": ueo.confidence,
            "citations": ueo.citations,
        }
        if self.config.include_metadata:
            data["metadata"] = ueo.metadata
        if ueo.agent_specific:
            data["agent_specific"] = ueo.agent_specific
        if ueo.engine_reports:
            data["engine_reports"] = ueo.engine_reports
        data["version"] = ueo.version
        return data

    @staticmethod
    def _manual_yaml(data: Dict[str, Any], indent: int = 0) -> str:
        """Minimal YAML serializer for when PyYAML is not available."""
        lines = []
        prefix = "  " * indent
        for k, v in data.items():
            if isinstance(v, dict):
                lines.append(f"{prefix}{k}:")
                lines.append(YAMLExporter._manual_yaml(v, indent + 1))
            elif isinstance(v, list):
                lines.append(f"{prefix}{k}:")
                for item in v:
                    if isinstance(item, dict):
                        lines.append(f"{prefix}  -")
                        lines.append(
                            YAMLExporter._manual_yaml(item, indent + 2)
                        )
                    else:
                        lines.append(f"{prefix}  - {item}")
            elif v is None:
                lines.append(f"{prefix}{k}: null")
            elif isinstance(v, bool):
                lines.append(f"{prefix}{k}: {'true' if v else 'false'}")
            elif isinstance(v, (int, float)):
                lines.append(f"{prefix}{k}: {v}")
            else:
                # quote string
                s = str(v).replace('"', '\\"')
                lines.append(f'{prefix}{k}: "{s}"')
        return "\n".join(lines)