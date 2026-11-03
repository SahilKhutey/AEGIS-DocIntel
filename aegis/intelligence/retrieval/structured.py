"""
aegis.intelligence.retrieval.structured
======================================
Independent Structured Retrieval mode matching entity metadata, date ranges,
numeric filters, and table schemas.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from aegis.intelligence.models import (
    RetrievalItem,
    RetrievalMode,
)
from aegis.intelligence.retrieval.base import BaseRetriever


class StructuredRetriever(BaseRetriever):
    """Structured Metadata, Table, and Numeric Filter Retriever."""

    def __init__(self):
        super().__init__(mode=RetrievalMode.STRUCTURED)
        self.docs: List[Dict[str, Any]] = []

    def index_document(
        self,
        document_id: str,
        chunk_id: str,
        text: str,
        page_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        meta = metadata or {}
        # Auto-extract numbers from text if not provided
        numbers = [float(n.replace(",", "")) for n in re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", text)]
        doc_entry = {
            "document_id": document_id,
            "chunk_id": chunk_id,
            "text": text,
            "page_number": page_number,
            "metadata": meta,
            "numbers": numbers,
            "is_table": meta.get("is_table", "table" in text.lower() or "|" in text),
            "entities": meta.get("entities", []),
            "year": meta.get("year"),
        }
        self.docs.append(doc_entry)

    def _execute_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalItem]:
        flt = filters or {}
        scores: List[tuple[int, float]] = []

        q_lower = query.lower()
        # Detect numeric queries like "above 500", "for 2024", etc.
        query_numbers = [float(n.replace(",", "")) for n in re.findall(r"\b\d+(?:,\d{3})*(?:\.\d+)?\b", query)]

        for idx, doc in enumerate(self.docs):
            score = 0.0
            meta = doc["metadata"]

            # 1. Explicit Filter Matching
            filter_match = True
            for k, expected_v in flt.items():
                actual_v = meta.get(k, doc.get(k))
                if isinstance(expected_v, (list, tuple, set)):
                    if actual_v not in expected_v:
                        filter_match = False
                        break
                elif isinstance(expected_v, dict) and "$gte" in expected_v:
                    if actual_v is None or actual_v < expected_v["$gte"]:
                        filter_match = False
                        break
                elif isinstance(expected_v, dict) and "$lte" in expected_v:
                    if actual_v is None or actual_v > expected_v["$lte"]:
                        filter_match = False
                        break
                elif actual_v != expected_v:
                    filter_match = False
                    break
            
            if not filter_match:
                continue

            # Base score for passing explicit filters
            score += 0.5

            # 2. Query Entity & Field Alignment
            for entity in doc["entities"]:
                if entity.lower() in q_lower:
                    score += 0.25

            # 3. Numeric query overlap
            for q_num in query_numbers:
                if q_num in doc["numbers"]:
                    score += 0.35

            # 4. Table query boost
            if "table" in q_lower and doc["is_table"]:
                score += 0.20

            if score > 0.0:
                scores.append((idx, min(1.0, score)))

        scores.sort(key=lambda x: x[1], reverse=True)

        items: List[RetrievalItem] = []
        for rank, (doc_idx, score) in enumerate(scores[:top_k], start=1):
            doc = self.docs[doc_idx]
            items.append(
                RetrievalItem(
                    document_id=doc["document_id"],
                    chunk_id=doc["chunk_id"],
                    page_number=doc["page_number"],
                    text=doc["text"],
                    rank=rank,
                    score=round(score, 4),
                    retrieval_method="structured_filter",
                    source_reference=f"{doc['document_id']}:PAGE-{doc['page_number']}",
                    metadata=doc["metadata"],
                )
            )
        return items
