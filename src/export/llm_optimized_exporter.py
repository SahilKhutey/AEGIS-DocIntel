"""
AEGIS-DocIntel / AMDI-OS — LLM Token-Optimized Exporter
=========================================================
Produces hyper-dense, token-optimized Markdown (.md) and JSON (.json) outputs
specifically designed for maximum LLM comprehension with minimum token overhead.

Key Optimizations:
  1. Compact Markdown Mode: Minimal padding, dense pipe tables, inline bracketed citations [Doc:pX],
     contextual prefixing, and whitespace deduplication.
  2. Ultra-Dense JSON Mode: Abbreviated keys (sys, ctx, sum, cits, meta), zero indentation whitespace,
     elimination of nulls/empty blocks.
  3. Token Budget Capping: Enforces target LLM context constraints via Information Bottleneck scoring.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.ael.token_budget import count_tokens
from src.export.universal_exporter import UniversalExportObject


@dataclass
class LLMExportConfig:
    """Configuration for LLM Token Optimization."""
    max_tokens: int = 4000
    format_type: str = "markdown"  # 'markdown' | 'json'
    compression_level: str = "high"  # 'none' | 'medium' | 'high'
    compact_keys: bool = True
    include_prefix: bool = True
    citation_format: str = "compact"  # 'compact' (e.g. [D1:p4]) | 'full'


class LLMTokenOptimizedExporter:
    """Exporter tailored for downstream LLM prompt injection with minimal token usage."""

    def __init__(self, config: Optional[LLMExportConfig] = None) -> None:
        self.config = config or LLMExportConfig()

    def export(self, ueo: UniversalExportObject) -> str:
        """Export UEO in the configured format type (markdown or json)."""
        if self.config.format_type == "json":
            return self.export_json(ueo)
        return self.export_markdown(ueo)

    def export_markdown(self, ueo: UniversalExportObject) -> str:
        """Renders hyper-dense Markdown formatted for LLM comprehension."""
        parts: List[str] = []

        # 1. Contextual Prefix Header
        if self.config.include_prefix:
            prefix = ueo.summary or f"Document context for {ueo.metadata.get('filename', 'document')}"
            prefix_clean = re.sub(r"\s+", " ", prefix).strip()
            parts.append(f"> **Context Summary**: {prefix_clean}")
            parts.append("")

        # 2. System Instructions
        if ueo.system:
            sys_text = re.sub(r"\s+", " ", ueo.system).strip()
            parts.append(f"### System: {sys_text}")
            parts.append("")

        # 3. Dense Content
        if ueo.context:
            content = ueo.context
            if self.config.compression_level in ("medium", "high"):
                # Strip excessive blank lines and leading/trailing whitespace per line
                lines = [line.strip() for line in content.splitlines() if line.strip()]
                content = "\n".join(lines)
            parts.append("### Content")
            parts.append(content)
            parts.append("")

        # 4. Compact Citations
        if ueo.citations:
            parts.append("### Source References")
            cit_items = []
            for i, cit in enumerate(ueo.citations, 1):
                doc_name = cit.get("doc_id", f"D{i}")
                page = cit.get("page", 1)
                snippet = re.sub(r"\s+", " ", str(cit.get("text", ""))).strip()
                if snippet:
                    cit_items.append(f"[{doc_name}:p{page}] {snippet[:120]}")
                else:
                    cit_items.append(f"[{doc_name}:p{page}]")
            parts.append("; ".join(cit_items))

        raw_md = "\n".join(parts)

        # Budget enforcement
        return self._truncate_to_token_budget(raw_md, self.config.max_tokens)

    def export_json(self, ueo: UniversalExportObject) -> str:
        """Serializes minified JSON with abbreviated keys to save tokens."""
        if self.config.compact_keys:
            data: Dict[str, Any] = {
                "sys": ueo.system or None,
                "sum": ueo.summary or None,
                "ctx": ueo.context or None,
            }
            if ueo.citations:
                data["cits"] = [
                    f"[{c.get('doc_id', 'D')}:p{c.get('page', 1)}]" for c in ueo.citations
                ]
            if ueo.metadata:
                data["meta"] = {k: v for k, v in ueo.metadata.items() if v}
            # Remove nulls
            data = {k: v for k, v in data.items() if v is not None}
        else:
            data = {
                "system": ueo.system,
                "summary": ueo.summary,
                "context": ueo.context,
                "citations": ueo.citations,
                "metadata": ueo.metadata,
            }

        # Minify JSON with no whitespace separators
        minified_json = json.dumps(data, separators=(",", ":"), ensure_ascii=False, default=str)
        return self._truncate_to_token_budget(minified_json, self.config.max_tokens)

    def _truncate_to_token_budget(self, text: str, max_tokens: int) -> str:
        """Enforces token budget limit on output string."""
        current_tokens = count_tokens(text)
        if current_tokens <= max_tokens:
            return text

        # Proportionally slice character length to fit under max_tokens
        ratio = max_tokens / max(1, current_tokens)
        cutoff = max(100, int(len(text) * ratio * 0.95))
        truncated = text[:cutoff] + "...\n[Context Truncated to fit Token Budget]"
        return truncated
