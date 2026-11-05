"""
aegis.intelligence.retrieval.hybrid
==================================
Hybrid Retrieval combining Lexical and Semantic ranking via Reciprocal Rank Fusion (RRF).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from aegis.intelligence.models import (
    RetrievalItem,
    RetrievalMode,
)
from aegis.intelligence.retrieval.base import BaseRetriever
from aegis.intelligence.retrieval.lexical import LexicalRetriever
from aegis.intelligence.retrieval.semantic import SemanticRetriever


class HybridRetriever(BaseRetriever):
    """Fuses Lexical and Semantic rankings via Reciprocal Rank Fusion (RRF)."""

    def __init__(self, rrf_k0: int = 60, lexical_weight: float = 1.0, semantic_weight: float = 1.0):
        super().__init__(mode=RetrievalMode.HYBRID)
        self.rrf_k0 = rrf_k0
        self.lexical_weight = lexical_weight
        self.semantic_weight = semantic_weight
        self.lexical = LexicalRetriever()
        self.semantic = SemanticRetriever()

    def index_document(
        self,
        document_id: str,
        chunk_id: str,
        text: str,
        page_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        self.lexical.index_document(
            document_id=document_id,
            chunk_id=chunk_id,
            text=text,
            page_number=page_number,
            metadata=metadata,
        )
        self.semantic.index_document(
            document_id=document_id,
            chunk_id=chunk_id,
            text=text,
            page_number=page_number,
            metadata=metadata,
            embedding=embedding,
        )

    def _execute_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalItem]:
        # Fetch candidate rankings from both modes
        fetch_k = max(top_k * 3, 20)
        lex_res = self.lexical._execute_search(query=query, top_k=fetch_k, filters=filters)
        sem_res = self.semantic._execute_search(query=query, top_k=fetch_k, filters=filters)

        # RRF dictionary: chunk_id -> (score, item)
        fused_scores: Dict[str, float] = {}
        items_by_chunk: Dict[str, RetrievalItem] = {}

        for rank, item in enumerate(lex_res, start=1):
            fused_scores[item.chunk_id] = fused_scores.get(item.chunk_id, 0.0) + (
                self.lexical_weight / (self.rrf_k0 + rank)
            )
            items_by_chunk[item.chunk_id] = item

        for rank, item in enumerate(sem_res, start=1):
            fused_scores[item.chunk_id] = fused_scores.get(item.chunk_id, 0.0) + (
                self.semantic_weight / (self.rrf_k0 + rank)
            )
            if item.chunk_id not in items_by_chunk:
                items_by_chunk[item.chunk_id] = item

        sorted_chunks = sorted(fused_scores.items(), key=lambda x: x[1], reverse=True)

        items: List[RetrievalItem] = []
        for rank, (chunk_id, rrf_score) in enumerate(sorted_chunks[:top_k], start=1):
            base_item = items_by_chunk[chunk_id]
            items.append(
                RetrievalItem(
                    document_id=base_item.document_id,
                    chunk_id=base_item.chunk_id,
                    page_number=base_item.page_number,
                    text=base_item.text,
                    rank=rank,
                    score=round(rrf_score, 5),
                    retrieval_method=f"rrf_fusion(k0={self.rrf_k0})",
                    source_reference=base_item.source_reference,
                    metadata=base_item.metadata,
                )
            )
        return items
