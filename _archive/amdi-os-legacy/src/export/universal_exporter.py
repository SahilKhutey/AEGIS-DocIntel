"""
Universal Export Object (UEO) & Agent-Specific Formatting
==========================================================

The UEO is the canonical, agent-agnostic representation of AMDI-OS output.

Each AI agent receives a UEO tailored to its input schema:

    ChatGPT   → { system, context, citations }        (text prompt)
    Gemini    → { text, tables, graphs, images }       (multimodal)
    Claude    → { summary, relationships, references } (long-context)
    DeepSeek  → { system, content }                    (chat)
    Qwen      → { system, context, metadata }          (chat)
    Local     → raw markdown / JSON
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import FormatError, InvalidContextError


@dataclass
class UniversalExportObject:
    """
    Canonical export container, agent-agnostic.

    Attributes
    ----------
    system : str
        System prompt.
    context : str
        Main content.
    summary : str
        Compressed summary.
    citations : List[Dict[str, Any]]
        Citations.
    metadata : Dict[str, Any]
        Document / session metadata.
    tables : List[Any]
        Tabular data.
    images : List[Any]
        Image references (paths or base64).
    graphs : List[Any]
        Graph data.
    confidence : float
        Aggregate confidence in [0, 1].
    total_tokens : int
        Token count.
    agent_specific : Dict[str, Any]
        Agent-specific extras.
    engine_reports : Dict[str, Any]
        Per-engine reports (optional, for debugging).
    version : str
        AMDI-OS version.
    """

    system: str
    context: str
    summary: str = ""
    citations: List[Dict[str, Any]] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    tables: List[Any] = field(default_factory=list)
    images: List[Any] = field(default_factory=list)
    graphs: List[Any] = field(default_factory=list)
    confidence: float = 0.0
    total_tokens: int = 0
    agent_specific: Dict[str, Any] = field(default_factory=dict)
    engine_reports: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "system": self.system,
            "context": self.context,
            "summary": self.summary,
            "citations": self.citations,
            "metadata": self.metadata,
            "tables": self.tables,
            "images": self.images,
            "graphs": self.graphs,
            "confidence": self.confidence,
            "total_tokens": self.total_tokens,
            "agent_specific": self.agent_specific,
            "engine_reports": self.engine_reports,
            "version": self.version,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversalExportObject":
        return cls(
            system=data.get("system", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            citations=data.get("citations", []),
            metadata=data.get("metadata", {}),
            tables=data.get("tables", []),
            images=data.get("images", []),
            graphs=data.get("graphs", []),
            confidence=float(data.get("confidence", 0.0)),
            total_tokens=int(data.get("total_tokens", 0)),
            agent_specific=data.get("agent_specific", {}),
            engine_reports=data.get("engine_reports", {}),
            version=data.get("version", "1.0.0"),
        )


class AgentFormatter:
    """
    Formats a UEO for a specific AI agent.
    """

    AGENT_SCHEMAS = ("chatgpt", "gemini", "claude", "deepseek", "qwen", "local")

    def format_for_agent(
        self,
        ueo: UniversalExportObject,
        agent: str,
    ) -> Dict[str, Any]:
        """
        Format UEO for the target agent.

        Parameters
        ----------
        ueo : UniversalExportObject
        agent : str
            One of 'chatgpt', 'gemini', 'claude', 'deepseek', 'qwen', 'local'.
        """
        agent = agent.lower()
        if agent == "chatgpt":
            return self._format_chatgpt(ueo)
        if agent == "gemini":
            return self._format_gemini(ueo)
        if agent == "claude":
            return self._format_claude(ueo)
        if agent == "deepseek":
            return self._format_deepseek(ueo)
        if agent == "qwen":
            return self._format_qwen(ueo)
        if agent == "local":
            return self._format_local(ueo)
        raise FormatError(f"Unknown agent: {agent}")

    @staticmethod
    def _format_chatgpt(ueo: UniversalExportObject) -> Dict[str, Any]:
        """ChatGPT-style: system + context + citations."""
        return {
            "system": ueo.system,
            "context": ueo.context,
            "citations": ueo.citations,
            "metadata": {
                "total_tokens": ueo.total_tokens,
                "confidence": ueo.confidence,
            },
        }

    @staticmethod
    def _format_gemini(ueo: UniversalExportObject) -> Dict[str, Any]:
        """Gemini-style: text + tables + graphs + images (multimodal)."""
        return {
            "text": f"{ueo.system}\n\n{ueo.summary}\n\n{ueo.context}",
            "tables": ueo.tables,
            "graphs": ueo.graphs,
            "images": ueo.images,
            "metadata": ueo.metadata,
            "total_tokens": ueo.total_tokens,
            "confidence": ueo.confidence,
        }

    @staticmethod
    def _format_claude(ueo: UniversalExportObject) -> Dict[str, Any]:
        """Claude-style: summary + relationships + references (long-context)."""
        return {
            "summary": ueo.summary,
            "context": ueo.context,
            "relationships": ueo.graphs,
            "references": ueo.citations,
            "metadata": ueo.metadata,
            "total_tokens": ueo.total_tokens,
            "confidence": ueo.confidence,
        }

    @staticmethod
    def _format_deepseek(ueo: UniversalExportObject) -> Dict[str, Any]:
        """DeepSeek-style: simple chat format."""
        return {
            "system": ueo.system,
            "content": ueo.context,
            "summary": ueo.summary,
            "citations": ueo.citations,
            "total_tokens": ueo.total_tokens,
        }

    @staticmethod
    def _format_qwen(ueo: UniversalExportObject) -> Dict[str, Any]:
        """Qwen-style: chat with metadata."""
        return {
            "system": ueo.system,
            "context": ueo.context,
            "metadata": ueo.metadata,
            "citations": ueo.citations,
            "total_tokens": ueo.total_tokens,
            "confidence": ueo.confidence,
        }

    @staticmethod
    def _format_local(ueo: UniversalExportObject) -> Dict[str, Any]:
        """Local-model style: raw content dump."""
        return ueo.to_dict()


class UniversalExporter:
    """
    Builds UEO from a ContextBuilder-style payload and formats per-agent.
    """

    def __init__(self, version: str = "1.0.0") -> None:
        self.version = version
        self.formatter = AgentFormatter()

    def build_ueo(
        self,
        system: str,
        context: str,
        summary: str = "",
        citations: Optional[List[Dict[str, Any]]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        tables: Optional[List[Any]] = None,
        images: Optional[List[Any]] = None,
        graphs: Optional[List[Any]] = None,
        confidence: float = 0.0,
        total_tokens: int = 0,
        engine_reports: Optional[Dict[str, Any]] = None,
    ) -> UniversalExportObject:
        """Build a UEO from explicit fields."""
        if system is None or context is None:
            raise InvalidContextError("system and context are required.")
        return UniversalExportObject(
            system=system,
            context=context,
            summary=summary,
            citations=citations or [],
            metadata=metadata or {},
            tables=tables or [],
            images=images or [],
            graphs=graphs or [],
            confidence=confidence,
            total_tokens=total_tokens,
            engine_reports=engine_reports or {},
            version=self.version,
        )

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
        """
        Build a UEO from a ContextReport (from backend.src.context).

        Parameters
        ----------
        context_report : ContextReport
            Output of ContextBuilder.build().
        agent : Optional[str]
            If provided, pre-fill agent_specific with formatted payload.
        """
        ctx = context_report.assembled_context
        ueo = UniversalExportObject(
            system=ctx.system_prompt,
            context=ctx.content,
            summary=ctx.summary,
            citations=[
                c if isinstance(c, dict) else {"raw": str(c)}
                for c in self._extract_citations(ctx.citations)
            ],
            metadata={**(ctx.metadata or {}), **(metadata or {})},
            tables=tables or [],
            images=images or [],
            graphs=graphs or [],
            confidence=confidence,
            total_tokens=total_tokens if total_tokens is not None else ctx.total_tokens,
            engine_reports=engine_reports or {},
            version=self.version,
        )
        if agent is not None:
            ueo.agent_specific[agent] = self.formatter.format_for_agent(
                ueo, agent
            )
        return ueo

    @staticmethod
    def _extract_citations(citations_raw: str) -> List[Dict[str, Any]]:
        """Parse the citations string into structured list."""
        if not citations_raw:
            return []
        results: List[Dict[str, Any]] = []
        for line in citations_raw.splitlines():
            line = line.strip()
            if not line or not line.startswith("["):
                continue
            # parse [doc_id, p.N, §section] excerpt
            try:
                bracket_end = line.find("]")
                if bracket_end < 0:
                    continue
                header = line[1:bracket_end]
                rest = line[bracket_end + 1:].strip()
                parts = [p.strip() for p in header.split(",")]
                doc_id = parts[0] if parts else ""
                page = None
                section = ""
                for p in parts[1:]:
                    if p.startswith("p."):
                        try:
                            page = int(p[2:].strip())
                        except ValueError:
                            page = p[2:]
                    elif p.startswith("§"):
                        section = p[1:]
                results.append({
                    "doc_id": doc_id,
                    "page": page,
                    "section": section,
                    "excerpt": rest,
                })
            except Exception:
                results.append({"raw": line})
        return results

    def format_for_agent(
        self,
        ueo: UniversalExportObject,
        agent: str,
    ) -> Dict[str, Any]:
        """Format UEO for a specific agent."""
        return self.formatter.format_for_agent(ueo, agent)