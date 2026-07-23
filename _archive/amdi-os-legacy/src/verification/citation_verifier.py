"""
Citation Verification
=====================

Verifies that citations in an AI response:
1. Exist in the source document
2. Are correctly formatted
3. Point to the actual content claimed
4. Page numbers / sections are accurate
5. Quotes match the source

Mathematical Foundation:
    Citation accuracy:
        CA = |citations_correct| / |citations_total|

    Citation precision:
        CP = |citations_correct| / |citations_retrieved|

    Citation recall:
        CR = |citations_used| / |citations_available|
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from .exceptions import CitationMissingError


class CitationMatchStatus(Enum):
    EXACT_MATCH = "exact_match"
    PARTIAL_MATCH = "partial_match"
    NO_MATCH = "no_match"
    MISSING = "missing"


@dataclass
class CitationMatch:
    """A single citation match check."""

    citation: Dict[str, Any]
    status: CitationMatchStatus
    score: float
    matched_excerpt: Optional[str] = None
    expected_excerpt: Optional[str] = None
    issues: List[str] = field(default_factory=list)

    @property
    def is_correct(self) -> bool:
        return self.status in (
            CitationMatchStatus.EXACT_MATCH,
            CitationMatchStatus.PARTIAL_MATCH,
        )


@dataclass
class CitationCheckResult:
    """Result of citation verification."""

    total_citations: int
    correct_citations: int
    partial_matches: int
    missing_citations: int
    no_match_citations: int
    accuracy: float
    precision: float
    recall: float
    matches: List[CitationMatch] = field(default_factory=list)
    issues: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "total_citations": self.total_citations,
            "correct_citations": self.correct_citations,
            "partial_matches": self.partial_matches,
            "missing_citations": self.missing_citations,
            "no_match_citations": self.no_match_citations,
            "accuracy": round(self.accuracy, 4),
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "issues": self.issues,
        }


class CitationVerifier:
    """
    Verify citations in AI-generated responses.

    Supports two modes:
        1. STRICT  — exact text match
        2. FUZZY   — partial / semantic match
    """

    CITATION_PATTERNS = [
        re.compile(r"\[([\w\-_]+),\s*p\.(\d+)(?:,\s*§([\w\-_]+))?\]\s*([^\[\]]*?)(?=\[|$)"),
        re.compile(r"\[(\d+)\](?!\s*[,\d])"),
    ]

    def __init__(
        self,
        strict: bool = False,
        fuzzy_threshold: float = 0.7,
    ) -> None:
        self.strict = strict
        self.fuzzy_threshold = fuzzy_threshold

    def verify(
        self,
        response_text: str,
        source_documents: Dict[str, Any],
    ) -> CitationCheckResult:
        """
        Verify citations in `response_text` against `source_documents`.

        Parameters
        ----------
        response_text : str
            The AI agent's response.
        source_documents : Dict[str, Any]
            Mapping doc_id → document data with 'pages' or 'excerpts'.

        Returns
        -------
        CitationCheckResult
        """
        citations = self._extract_citations(response_text)
        if not citations:
            return CitationCheckResult(
                total_citations=0,
                correct_citations=0,
                partial_matches=0,
                missing_citations=0,
                no_match_citations=0,
                accuracy=1.0,  # no citations → vacuously accurate
                precision=1.0,
                recall=1.0,
                issues=["no_citations_found"],
            )

        matches: List[CitationMatch] = []
        correct = 0
        partial = 0
        missing = 0
        no_match = 0
        issues: List[str] = []

        for cit in citations:
            doc_id = cit.get("doc_id")
            page = cit.get("page")
            excerpt = cit.get("excerpt", "")

            if not doc_id:
                matches.append(
                    CitationMatch(
                        citation=cit,
                        status=CitationMatchStatus.MISSING,
                        score=0.0,
                        issues=["missing_doc_id"],
                    )
                )
                missing += 1
                issues.append(f"citation_missing_doc_id:{cit}")
                continue

            # lookup in source
            doc = source_documents.get(doc_id)
            if doc is None:
                matches.append(
                    CitationMatch(
                        citation=cit,
                        status=CitationMatchStatus.MISSING,
                        score=0.0,
                        issues=[f"doc_not_found:{doc_id}"],
                    )
                )
                missing += 1
                issues.append(f"doc_not_found:{doc_id}")
                continue

            # verify excerpt match
            score, matched_text = self._match_excerpt(excerpt, doc, page)

            if score >= 0.95:
                status = CitationMatchStatus.EXACT_MATCH
                correct += 1
            elif score >= self.fuzzy_threshold and not self.strict:
                status = CitationMatchStatus.PARTIAL_MATCH
                partial += 1
                issues.append(f"partial_match:{doc_id}:p{page}")
            else:
                status = CitationMatchStatus.NO_MATCH
                no_match += 1
                issues.append(f"no_match:{doc_id}:p{page}")

            matches.append(
                CitationMatch(
                    citation=cit,
                    status=status,
                    score=score,
                    matched_excerpt=matched_text,
                    expected_excerpt=excerpt,
                )
            )

        total = len(citations)
        correct_total = correct + (0 if self.strict else partial)
        accuracy = correct_total / max(total, 1)
        precision = correct_total / max(total, 1)
        # recall: fraction of available citations used
        available_citations = self._count_available_citations(source_documents)
        recall = total / max(available_citations, 1)

        return CitationCheckResult(
            total_citations=total,
            correct_citations=correct,
            partial_matches=partial,
            missing_citations=missing,
            no_match_citations=no_match,
            accuracy=accuracy,
            precision=precision,
            recall=min(recall, 1.0),
            matches=matches,
            issues=issues,
        )

    def _extract_citations(self, text: str) -> List[Dict[str, Any]]:
        """Extract citations from response text."""
        citations: List[Dict[str, Any]] = []
        seen: Set[tuple] = set()
        # [doc_id, p.N, §section] excerpt
        for m in re.finditer(
            r"\[([\w\-_]+),\s*p\.(\d+)(?:,\s*§([\w\-_]+))?\]\s*([^\[\]]{0,500}?)(?=\[|\n|$)",
            text,
        ):
            doc_id, page, section, excerpt = m.groups()
            key = (doc_id, page)
            if key in seen:
                continue
            seen.add(key)
            citations.append({
                "doc_id": doc_id,
                "page": int(page),
                "section": section or "",
                "excerpt": (excerpt or "").strip(),
                "marker": m.group(0),
            })
        # numbered [N]
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

    def _match_excerpt(
        self,
        excerpt: str,
        doc: Any,
        page: Optional[int] = None,
    ) -> tuple:
        """
        Match excerpt against document content.

        Returns (score, matched_text).
        """
        if not excerpt:
            return 1.0, ""
        # build searchable text from doc
        if isinstance(doc, str):
            doc_text = doc
        elif isinstance(doc, dict):
            if page is not None and "pages" in doc:
                pages = doc["pages"]
                if isinstance(pages, dict) and str(page) in pages:
                    doc_text = pages[str(page)]
                elif isinstance(pages, list) and page < len(pages):
                    doc_text = pages[page]
                else:
                    doc_text = doc.get("text", "")
            else:
                doc_text = doc.get("text", "")
        else:
            doc_text = str(doc)
        if not doc_text:
            return 0.0, ""
        # normalize
        norm_excerpt = self._normalize(excerpt)
        norm_doc = self._normalize(doc_text)
        if not norm_excerpt:
            return 1.0, doc_text[:200]
        # exact substring match
        if norm_excerpt in norm_doc:
            return 1.0, excerpt
        # token overlap (Jaccard)
        excerpt_tokens = set(norm_excerpt.split())
        doc_tokens = set(norm_doc.split())
        if not excerpt_tokens:
            return 0.0, ""
        overlap = excerpt_tokens & doc_tokens
        jaccard = len(overlap) / len(excerpt_tokens | doc_tokens)
        # containment
        containment = len(overlap) / len(excerpt_tokens)
        score = max(jaccard * 2, containment)  # weight containment higher
        # find matched text
        matched = self._find_closest_span(excerpt, doc_text)
        return min(score, 1.0), matched

    def _find_closest_span(self, excerpt: str, doc_text: str, window: int = 200) -> str:
        """Find the span in doc_text most similar to excerpt."""
        if not excerpt:
            return ""
        norm_excerpt = self._normalize(excerpt)
        norm_doc = self._normalize(doc_text)
        # try sliding window
        best_score = 0
        best_span = ""
        tokens_doc = norm_doc.split()
        n = len(tokens_doc)
        k = len(norm_excerpt.split())
        if k == 0 or n < k:
            return ""
        for i in range(n - k + 1):
            window_text = " ".join(tokens_doc[i : i + k])
            overlap = len(set(window_text.split()) & set(norm_excerpt.split()))
            score = overlap / k
            if score > best_score:
                best_score = score
                best_span = " ".join(doc_text.split()[i : i + k])[:window]
        return best_span

    @staticmethod
    def _normalize(text: str) -> str:
        """Normalize text for comparison."""
        return re.sub(r"\s+", " ", text.lower().strip())

    def _count_available_citations(self, source_documents: Dict[str, Any]) -> int:
        """Estimate available citations in source."""
        count = 0
        for doc in source_documents.values():
            if isinstance(doc, dict):
                pages = doc.get("pages", [])
                if isinstance(pages, list):
                    count += len(pages)
                elif isinstance(pages, dict):
                    count += len(pages)
                else:
                    count += 1
            else:
                count += 1
        return count
