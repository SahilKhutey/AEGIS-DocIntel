"""
aegis.intelligence.citations.citation_resolver
==============================================
Resolves citation references against WP-05 document metadata, page boundaries, and provenance records.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set

from aegis.intelligence.models import CitationRef


class CitationResolver:
    """Verifies syntactic and structural resolvability of citations against known document corpus."""

    def __init__(self, known_documents: Optional[Dict[str, Dict[str, Any]]] = None):
        """
        known_documents: mapping of doc_id -> {
            "page_count": int,
            "chunks": set[str],
            "regions": set[str]
        }
        """
        self.known_docs = known_documents or {}

    def register_document(
        self,
        document_id: str,
        page_count: int,
        chunks: Optional[Set[str]] = None,
        regions: Optional[Set[str]] = None,
    ) -> None:
        self.known_docs[document_id] = {
            "page_count": max(1, page_count),
            "chunks": set(chunks or []),
            "regions": set(regions or []),
        }

    def is_resolvable(self, citation: CitationRef) -> tuple[bool, Optional[str]]:
        """
        Check if citation references an authentic document, page, and chunk/region.
        Returns (is_valid, failure_reason).
        """
        doc_id = citation.document_id
        if not doc_id or doc_id.strip() == "":
            return False, "EMPTY_DOCUMENT_ID"

        if self.known_docs and doc_id not in self.known_docs:
            return False, f"UNKNOWN_DOCUMENT_ID: {doc_id}"

        doc_meta = self.known_docs.get(doc_id)
        if doc_meta:
            # Check page bounds
            if citation.page_number is not None:
                if citation.page_number < 1 or citation.page_number > doc_meta["page_count"]:
                    return False, f"PAGE_OUT_OF_BOUNDS: page {citation.page_number} > {doc_meta['page_count']}"

            # Check chunk existence if chunks registered
            if citation.chunk_id and doc_meta["chunks"]:
                if citation.chunk_id not in doc_meta["chunks"]:
                    return False, f"UNRESOLVABLE_CHUNK: {citation.chunk_id}"

            # Check region existence if regions registered
            if citation.region_id and doc_meta["regions"]:
                if citation.region_id not in doc_meta["regions"]:
                    return False, f"UNRESOLVABLE_REGION: {citation.region_id}"

        return True, None
