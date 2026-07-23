"""
AMDI-OS Export Engine
=====================

Exports AMDI-OS processed documents into formats consumable by
AI agents (ChatGPT, Gemini, Claude, DeepSeek, Qwen, local models)
and humans (Markdown, JSON, YAML).

Supported Formats:
    - JSON                  structured serialization
    - Markdown              human-readable
    - YAML                  configuration / metadata
    - Universal Export Object (UEO) — agent-ready context

Mathematical Foundation:
    UEO = {
        system:        str,
        context:       str,
        summary:       str,
        citations:     List[str],
        metadata:      Dict[str, Any],
        total_tokens:  int,
        confidence:    float,
        agent_specific: Dict[str, Any]
    }

Agent-specific formatting:
    ChatGPT   → { system, context, citations }
    Gemini    → { text, tables, graphs, images }
    Claude    → { summary, relationships, references }
    DeepSeek  → { system, content }
    Qwen      → { system, context, metadata }
    Local     → raw markdown / JSON

Author : AMDI-OS Development Team
Version: 1.0.0
"""

from .export_engine import ExportEngine, ExportReport
from .json_exporter import JSONExporter, JSONConfig
from .markdown_exporter import MarkdownExporter, MarkdownConfig
from .yaml_exporter import YAMLExporter, YAMLConfig
from .llm_optimized_exporter import LLMTokenOptimizedExporter, LLMExportConfig
from .universal_exporter import (
    UniversalExporter,
    UniversalExportObject,
    AgentFormatter,
)
from .formatters import (
    format_citation,
    format_table,
    format_metadata,
)
from .token_budget import ExportTokenBudget, TokenAllocator
from .verification import ExportVerifier, VerificationResult
from .exceptions import (
    ExportEngineError,
    InvalidContextError,
    FormatError,
    VerificationError,
)

__all__ = [
    "ExportEngine",
    "ExportReport",
    "JSONExporter",
    "JSONConfig",
    "MarkdownExporter",
    "MarkdownConfig",
    "YAMLExporter",
    "YAMLConfig",
    "LLMTokenOptimizedExporter",
    "LLMExportConfig",
    "UniversalExporter",
    "UniversalExportObject",
    "AgentFormatter",
    "format_citation",
    "format_table",
    "format_metadata",
    "ExportTokenBudget",
    "TokenAllocator",
    "ExportVerifier",
    "VerificationResult",
    "ExportEngineError",
    "InvalidContextError",
    "FormatError",
    "VerificationError",
]

__version__ = "1.0.0"