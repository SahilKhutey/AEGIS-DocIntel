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


import uuid

@dataclass
class UniversalExportObject:
    """
    Canonical export container, agent-agnostic.
    Bridges pipeline mathematical layers and external AI agent formats.
    """

    system: str = ""
    context: str = ""
    summary: str = ""
    query: str = ""
    citations: List[Any] = field(default_factory=list)
    metadata: Any = field(default_factory=dict)
    tables: List[Any] = field(default_factory=list)
    images: List[Any] = field(default_factory=list)
    graphs: List[Any] = field(default_factory=list)
    confidence: Any = 0.0
    total_tokens: int = 0
    agent_specific: Dict[str, Any] = field(default_factory=dict)
    engine_reports: Dict[str, Any] = field(default_factory=dict)
    version: str = "1.0.0"

    # Layer representations (bridges pipeline state & workflows)
    document_summary: Any = None
    semantic: Any = None
    geometry: Any = None
    matrix: Any = None
    graph: Any = None
    template: Any = None
    key_points: List[Any] = field(default_factory=list)
    ueo_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    export_format: Any = "json"
    tokens_used: int = 0
    priority_log: List[dict] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        meta_dict = self.metadata if isinstance(self.metadata, dict) else (
            self.metadata.__dict__ if hasattr(self.metadata, "__dict__") else {}
        )
        if hasattr(self.confidence, "overall"):
            conf_val = {
                "overall": self.confidence.overall,
                "semantic": getattr(self.confidence, "semantic", 0.0),
                "numerical": getattr(self.confidence, "numerical", 0.0),
                "structural": getattr(self.confidence, "structural", 0.0),
                "retrieval": getattr(self.confidence, "retrieval", 0.0),
                "calibration_method": getattr(self.confidence, "calibration_method", "bayesian"),
            }
        elif isinstance(self.confidence, (int, float)):
            conf_val = self.confidence
        else:
            conf_val = 1.0

        res: Dict[str, Any] = {
            "ueo_id": self.ueo_id,
            "version": self.version,
            "system": self.system,
            "context": self.context,
            "summary": self.summary,
            "query": self.query,
            "citations": [
                c if isinstance(c, dict) else (c.__dict__ if hasattr(c, "__dict__") else str(c))
                for c in self.citations
            ],
            "metadata": meta_dict,
            "tables": self.tables,
            "images": self.images,
            "graphs": self.graphs,
            "confidence": conf_val,
            "total_tokens": self.total_tokens or self.tokens_used,
            "tokens_used": self.tokens_used or self.total_tokens,
            "agent_specific": self.agent_specific,
            "engine_reports": self.engine_reports,
        }
        if self.document_summary is not None:
            res["document_summary"] = (
                self.document_summary if isinstance(self.document_summary, dict)
                else getattr(self.document_summary, "__dict__", str(self.document_summary))
            )
        if self.key_points:
            res["key_points"] = [
                kp if isinstance(kp, dict) else getattr(kp, "__dict__", str(kp))
                for kp in self.key_points
            ]
        if self.semantic is not None:
            res["semantic"] = {
                "topics": getattr(self.semantic, "topics", []),
                "keywords": getattr(self.semantic, "keywords", []),
                "entities": getattr(self.semantic, "entities", []),
                "sentiment": getattr(self.semantic, "sentiment", {}),
            } if hasattr(self.semantic, "topics") else (
                self.semantic if isinstance(self.semantic, dict) else getattr(self.semantic, "__dict__", str(self.semantic))
            )
        if self.geometry is not None:
            res["geometry"] = {
                "important_regions": getattr(self.geometry, "important_regions", []),
                "section_locations": getattr(self.geometry, "section_locations", []),
            } if hasattr(self.geometry, "important_regions") else (
                self.geometry if isinstance(self.geometry, dict) else getattr(self.geometry, "__dict__", str(self.geometry))
            )
        if self.matrix is not None:
            raw_tables = getattr(self.matrix, "tables", [])
            res["matrix"] = {
                "tables": [t.to_dict() if hasattr(t, "to_dict") else (t if isinstance(t, dict) else getattr(t, "__dict__", {})) for t in raw_tables],
                "n_tables": getattr(self.matrix, "n_tables", len(raw_tables)),
            } if hasattr(self.matrix, "tables") else (
                self.matrix if isinstance(self.matrix, dict) else getattr(self.matrix, "__dict__", str(self.matrix))
            )
        if self.graph is not None:
            nodes = getattr(self.graph, "nodes", [])
            edges = getattr(self.graph, "edges", [])
            res["graph"] = {
                "nodes": nodes[:50],
                "edges": edges[:100],
                "n_nodes": getattr(self.graph, "n_nodes", len(nodes)),
                "n_edges": getattr(self.graph, "n_edges", len(edges)),
                "key_relationships": getattr(self.graph, "key_relationships", []),
            } if hasattr(self.graph, "nodes") else (
                self.graph if isinstance(self.graph, dict) else getattr(self.graph, "__dict__", str(self.graph))
            )
        if self.template is not None:
            res["template"] = {
                "templates": getattr(self.template, "templates", []),
                "n_templates": getattr(self.template, "n_templates", 0),
                "dominant_template_id": getattr(self.template, "dominant_template_id", ""),
            } if hasattr(self.template, "templates") else (
                self.template if isinstance(self.template, dict) else getattr(self.template, "__dict__", str(self.template))
            )
        return res

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "UniversalExportObject":
        return cls(
            system=data.get("system", ""),
            context=data.get("context", ""),
            summary=data.get("summary", ""),
            query=data.get("query", ""),
            citations=data.get("citations", []),
            metadata=data.get("metadata", {}),
            tables=data.get("tables", []),
            images=data.get("images", []),
            graphs=data.get("graphs", []),
            confidence=data.get("confidence", 0.0),
            total_tokens=int(data.get("total_tokens", data.get("tokens_used", 0))),
            tokens_used=int(data.get("tokens_used", data.get("total_tokens", 0))),
            agent_specific=data.get("agent_specific", {}),
            engine_reports=data.get("engine_reports", {}),
            version=data.get("version", "1.0.0"),
            ueo_id=data.get("ueo_id", str(uuid.uuid4())),
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