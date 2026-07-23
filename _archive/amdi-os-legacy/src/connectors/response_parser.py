"""
Unified Response Parser
========================

Parses responses from different AI agents into a uniform ParsedResponse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .exceptions import InvalidResponseError


@dataclass
class ParsedResponse:
    """Parsed, normalized response."""

    text: str
    citations: List[Dict[str, Any]] = field(default_factory=list)
    references: List[str] = field(default_factory=list)
    sections: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    confidence: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "text": self.text,
            "citations": self.citations,
            "references": self.references,
            "sections": self.sections,
            "metadata": self.metadata,
            "confidence": self.confidence,
        }


class ResponseParser:
    """
    Parses raw agent output into structured form.
    """

    CITATION_PATTERNS = [
        re.compile(r"\[(\d+)\]"),                              # [1], [2]
        re.compile(r"\[([\w\-_]+),\s*p\.(\d+)\]"),            # [doc_1, p.5]
        re.compile(r"\(([\w\-_]+),\s*p\.(\d+)\)"),            # (doc_1, p.5)
        re.compile(r"\[(\d+),\s*p\.(\d+)\]"),                 # [1, p.5]
    ]

    SECTION_HEADERS = re.compile(
        r"^(#{1,6})\s+(.+?)$", re.MULTILINE
    )

    def parse(
        self,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ParsedResponse:
        """
        Parse agent response text.

        Extracts:
            - Citations [1], [doc_1, p.5]
            - Section headers (#, ##, ###)
            - References section
            - Confidence markers
        """
        if text is None:
            raise InvalidResponseError("Response text is None.")
        citations = self._extract_citations(text)
        references = self._extract_references(text)
        sections = self._extract_sections(text)
        confidence = self._extract_confidence(text)
        return ParsedResponse(
            text=text,
            citations=citations,
            references=references,
            sections=sections,
            metadata=metadata or {},
            confidence=confidence,
        )

    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        citations: List[Dict[str, Any]] = []
        seen = set()
        # [doc_id, p.N] style
        for m in re.finditer(r"\[([\w\-_]+),\s*p\.(\d+)(?:,\s*§([\w\-_]+))?\]", text):
            doc_id, page, section = m.groups()
            key = (doc_id, page)
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "doc_id": doc_id,
                "page": int(page),
                "section": section or "",
                "marker": m.group(0),
            })
        # [N] numbered citation
        for m in re.finditer(r"\[(\d+)\](?!\s*[,\d])", text):
            num = m.group(1)
            key = ("num", num)
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "ref_number": int(num),
                "marker": m.group(0),
            })
        return citations

    def _extract_references(self, text: str) -> List[str]:
        """Extract reference list section."""
        ref_match = re.search(
            r"(?im)^#{1,3}\s+(references|bibliography|sources?)\s*$",
            text,
        )
        if not ref_match:
            return []
        ref_text = text[ref_match.end():]
        # stop at next header
        next_header = re.search(r"^#{1,3}\s+", ref_text, re.MULTILINE)
        if next_header:
            ref_text = ref_text[: next_header.start()]
        refs = [
            line.strip("- ").strip()
            for line in ref_text.splitlines()
            if line.strip() and line.strip().startswith(("-", "*", "•", "["))
        ]
        return refs

    def _extract_sections(self, text: str) -> Dict[str, str]:
        sections: Dict[str, str] = {}
        matches = list(self.SECTION_HEADERS.finditer(text))
        for i, m in enumerate(matches):
            header = m.group(2).strip()
            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
            sections[header] = text[start:end].strip()
        return sections

    def _extract_confidence(self, text: str) -> Optional[float]:
        """Try to extract a confidence percentage from the text."""
        m = re.search(
            r"(?i)(?:confidence|certainty)\s*[:\-]?\s*(\d+(?:\.\d+)?)\s*%?",
            text,
        )
        if m:
            try:
                val = float(m.group(1))
                if val > 1:
                    val = val / 100.0
                return val
            except ValueError:
                return None
        return None