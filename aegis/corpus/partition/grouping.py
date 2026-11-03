"""
aegis.corpus.partition.grouping
===============================
Multi-level document grouping mechanisms to prevent leakage across document families,
publishers, series, and editions.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Set
from pydantic import BaseModel, Field


class GroupableDocument(BaseModel):
    """Document attributes necessary for leakage-free group assignment."""
    document_id: str
    source_id: str
    sha256: str
    title: Optional[str] = None
    publisher: Optional[str] = None
    family: Optional[str] = None
    text_content: Optional[str] = None


class DocumentGrouper:
    """Groups documents based on publisher, source, or inferred family series."""

    @staticmethod
    def infer_family(doc_id: str, title: Optional[str] = None) -> str:
        """Infer series or document family from doc_id or title.
        
        Examples:
        - 'WB_WDR_2022' -> 'WB_WDR'
        - 'SEC_10K_AAPL_2021' -> 'SEC_10K_AAPL'
        - 'ARXIV_2301_0001' -> 'ARXIV_2301'
        """
        # Remove trailing year or numeric sequence
        clean_id = re.sub(r"[_\-](19|20)\d{2}.*$", "", doc_id, flags=re.IGNORECASE)
        clean_id = re.sub(r"[_\-]\d{4,}.*$", "", clean_id)
        if len(clean_id) > 2:
            return clean_id.upper()
        if title:
            # Fall back to title prefix
            clean_title = re.sub(r"[_\-\s](19|20)\d{2}.*$", "", title, flags=re.IGNORECASE)
            return re.sub(r"[^A-Za-z0-9]", "_", clean_title)[:24].upper()
        return doc_id.upper()

    @classmethod
    def group_documents(
        cls,
        documents: List[GroupableDocument],
        grouping_key: str = "family"
    ) -> Dict[str, List[GroupableDocument]]:
        """Group documents into buckets that must be kept intact within single partitions."""
        groups: Dict[str, List[GroupableDocument]] = {}

        for doc in documents:
            if grouping_key == "publisher":
                key = (doc.publisher or doc.source_id).strip().upper()
            elif grouping_key == "source_id":
                key = doc.source_id.strip().upper()
            elif grouping_key == "family":
                fam = doc.family or cls.infer_family(doc.document_id, doc.title)
                key = f"{doc.source_id}::{fam}".upper()
            else:
                key = doc.document_id

            groups.setdefault(key, []).append(doc)

        return groups
