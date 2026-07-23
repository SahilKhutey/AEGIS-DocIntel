"""
Export Engine — Main Orchestrator
===================================

End-to-end export pipeline:

    ContextReport (from ContextBuilder)
         ↓
    UniversalExportObject (UEO)
         ↓
    Verification
         ↓
    ┌─────────┬──────────┬──────┬──────────────────┐
    │  JSON   │ Markdown │ YAML │ Agent-specific   │
    └─────────┴──────────┴──────┴──────────────────┘
         ↓
    ExportReport → User / AI Agent

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import (
    ExportEngineError,
    InvalidContextError,
    VerificationError,
)
from .json_exporter import JSONConfig, JSONExporter
from .markdown_exporter import MarkdownConfig, MarkdownExporter
from .token_budget import AGENT_TOKEN_LIMITS, ExportTokenBudget, TokenAllocator
from .universal_exporter import (
    AgentFormatter,
    UniversalExportObject,
    UniversalExporter,
)
from .verification import ExportVerifier, VerificationResult
from .yaml_exporter import YAMLConfig, YAMLExporter


@dataclass
class ExportReport:
    """Export operation report."""

    ueo: UniversalExportObject
    verification: VerificationResult
    formats: Dict[str, str] = field(default_factory=dict)
    file_paths: Dict[str, str] = field(default_factory=dict)
    agent_payloads: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "ueo": self.ueo.to_dict(),
            "verification": self.verification.to_dict(),
            "formats": list(self.formats.keys()),
            "file_paths": self.file_paths,
            "agent_payloads": self.agent_payloads,
            "metadata": self.metadata,
        }


class ExportEngine:
    """
    Main Export Engine orchestrator.
    """

    def __init__(
        self,
        version: str = "1.0.0",
        json_config: Optional[JSONConfig] = None,
        markdown_config: Optional[MarkdownConfig] = None,
        yaml_config: Optional[YAMLConfig] = None,
        verifier: Optional[ExportVerifier] = None,
        default_agent: str = "chatgpt",
    ) -> None:
        self.universal = UniversalExporter(version=version)
        self.json_exporter = JSONExporter(json_config)
        self.markdown_exporter = MarkdownExporter(markdown_config)
        self.yaml_exporter = YAMLExporter(yaml_config)
        self.verifier = verifier or ExportVerifier()
        self.default_agent = default_agent

    # =========================================================================
    # Direct UEO construction
    # =========================================================================

    def build_ueo(self, **kwargs) -> UniversalExportObject:
        return self.universal.build_ueo(**kwargs)

    def build_from_context_report(
        self,
        context_report: Any,
        agent: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        engine_reports: Optional[Dict[str, Any]] = None,
        confidence: float = 0.9,
        total_tokens: Optional[int] = None,
        tables: Optional[List[Any]] = None,
        images: Optional[List[Any]] = None,
        graphs: Optional[List[Any]] = None,
    ) -> UniversalExportObject:
        return self.universal.build_from_context_report(
            context_report=context_report,
            agent=agent or self.default_agent,
            metadata=metadata,
            engine_reports=engine_reports,
            confidence=confidence,
            total_tokens=total_tokens,
            tables=tables,
            images=images,
            graphs=graphs,
        )

    # =========================================================================
    # Export operations
    # =========================================================================

    def export_ueo(
        self,
        ueo: UniversalExportObject,
        formats: Optional[List[str]] = None,
        agents: Optional[List[str]] = None,
        verify: bool = True,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExportReport:
        """
        Export a UEO in one or more formats.

        Parameters
        ----------
        ueo : UniversalExportObject
        formats : Optional[List[str]]
            One or more of 'json', 'markdown', 'yaml', 'ueo'.
            Default: all four.
        agents : Optional[List[str]]
            If provided, also produce agent-specific payloads.
        verify : bool
            If True, run verification before export.
        """
        formats = formats or ["json", "markdown", "yaml", "ueo"]

        # verification
        verification = self.verifier.verify(ueo)
        if verify and not verification.is_valid:
            raise VerificationError(
                f"Verification failed: {verification.checks_failed}"
            )

        outputs: Dict[str, str] = {}
        agent_payloads: Dict[str, Dict[str, Any]] = {}

        if "json" in formats:
            outputs["json"] = self.json_exporter.export(ueo)
        if "markdown" in formats:
            outputs["markdown"] = self.markdown_exporter.export(ueo)
        if "yaml" in formats:
            outputs["yaml"] = self.yaml_exporter.export(ueo)
        if "ueo" in formats:
            import json
            outputs["ueo"] = json.dumps(ueo.to_dict(), indent=2, default=str)

        if agents:
            formatter = AgentFormatter()
            for agent in agents:
                agent_payloads[agent] = formatter.format_for_agent(ueo, agent)

        return ExportReport(
            ueo=ueo,
            verification=verification,
            formats=outputs,
            agent_payloads=agent_payloads,
            metadata=metadata or {},
        )

    def export_from_context_report(
        self,
        context_report: Any,
        formats: Optional[List[str]] = None,
        agents: Optional[List[str]] = None,
        agent_for_ueo: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        engine_reports: Optional[Dict[str, Any]] = None,
        confidence: float = 0.9,
        verify: bool = True,
    ) -> ExportReport:
        """
        End-to-end: build UEO from context report and export.
        """
        ueo = self.build_from_context_report(
            context_report=context_report,
            agent=agent_for_ueo,
            metadata=metadata,
            engine_reports=engine_reports,
            confidence=confidence,
        )
        return self.export_ueo(
            ueo=ueo,
            formats=formats,
            agents=agents,
            verify=verify,
            metadata=metadata,
        )

    def export_to_files(
        self,
        ueo: UniversalExportObject,
        output_dir: str,
        base_name: str = "context",
        formats: Optional[List[str]] = None,
    ) -> Dict[str, str]:
        """
        Export to files in `output_dir`.

        Returns dict: format → file path.
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        formats = formats or ["json", "markdown", "yaml"]
        paths: Dict[str, str] = {}
        for fmt in formats:
            path = os.path.join(output_dir, f"{base_name}.{fmt}")
            if fmt == "json":
                self.json_exporter.export_to_file(ueo, path)
            elif fmt == "markdown":
                self.markdown_exporter.export_to_file(ueo, path)
            elif fmt == "yaml":
                self.yaml_exporter.export_to_file(ueo, path)
            else:
                continue
            paths[fmt] = path
        return paths

    # =========================================================================
    # Convenience methods
    # =========================================================================

    def to_json(self, ueo: UniversalExportObject) -> str:
        return self.json_exporter.export(ueo)

    def to_markdown(self, ueo: UniversalExportObject) -> str:
        return self.markdown_exporter.export(ueo)

    def to_yaml(self, ueo: UniversalExportObject) -> str:
        return self.yaml_exporter.export(ueo)

    def to_chatgpt(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "chatgpt")

    def to_gemini(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "gemini")

    def to_claude(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "claude")

    def to_deepseek(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "deepseek")

    def to_qwen(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "qwen")

    def to_local(self, ueo: UniversalExportObject) -> Dict[str, Any]:
        return AgentFormatter().format_for_agent(ueo, "local")

    # =========================================================================
    # Token budget helpers
    # =========================================================================

    def get_token_budget(self, agent: str) -> ExportTokenBudget:
        """Get the token budget configuration for an agent."""
        return ExportTokenBudget.for_agent(agent)
