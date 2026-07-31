"""
Contextual-Prefix Enrichment Engine (Task H-4).

Prepends situational document context (document title, section title, and summary)
to text chunks prior to embedding and scoring (Anthropic contextual retrieval pattern).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Dict, Any, Optional


@dataclass
class EnrichedChunk:
    chunk_id: str
    original_text: str
    enriched_text: str
    context_prefix: str
    metadata: Dict[str, Any]


class ContextualPrefixEnricher:
    """
    Enriches raw text chunks with situational context headers.
    """

    def __init__(self, include_section: bool = True, include_doc_title: bool = True):
        self.include_section = include_section
        self.include_doc_title = include_doc_title

    def build_prefix(
        self,
        doc_title: str = "",
        section_title: str = "",
        situational_summary: str = "",
    ) -> str:
        parts = []
        if self.include_doc_title and doc_title.strip():
            parts.append(f"Document: {doc_title.strip()}")
        if self.include_section and section_title.strip():
            parts.append(f"Section: {section_title.strip()}")
        if situational_summary.strip():
            parts.append(f"Context: {situational_summary.strip()}")

        if not parts:
            return ""
        return " | ".join(parts) + "\n\n"

    def enrich_chunk(
        self,
        chunk_id: str,
        text: str,
        doc_title: str = "",
        section_title: str = "",
        situational_summary: str = "",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> EnrichedChunk:
        prefix = self.build_prefix(doc_title, section_title, situational_summary)
        enriched_text = prefix + text
        return EnrichedChunk(
            chunk_id=chunk_id,
            original_text=text,
            enriched_text=enriched_text,
            context_prefix=prefix,
            metadata=metadata or {},
        )

    def enrich_chunks(
        self,
        chunks: List[Dict[str, Any]],
        doc_title: str = "",
        situational_summary: str = "",
    ) -> List[EnrichedChunk]:
        results = []
        for c in chunks:
            chunk_id = c.get("chunk_id", c.get("id", ""))
            text = c.get("text", c.get("content", ""))
            sec = c.get("section", c.get("section_title", ""))
            enriched = self.enrich_chunk(
                chunk_id=chunk_id,
                text=text,
                doc_title=doc_title,
                section_title=sec,
                situational_summary=situational_summary,
                metadata=c,
            )
            results.append(enriched)
        return results
