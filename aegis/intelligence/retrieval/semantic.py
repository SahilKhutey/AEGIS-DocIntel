"""
aegis.intelligence.retrieval.semantic
====================================
Independent Semantic Retrieval mode computing Cosine Similarity over dense vectors.
"""

from __future__ import annotations

import hashlib
import math
from typing import Any, Dict, List, Optional
import numpy as np

from aegis.intelligence.models import (
    RetrievalItem,
    RetrievalMode,
)
from aegis.intelligence.retrieval.base import BaseRetriever


class SemanticRetriever(BaseRetriever):
    """Dense Vector Embedding Similarity Retriever."""

    def __init__(self, embedding_dim: int = 128):
        super().__init__(mode=RetrievalMode.SEMANTIC)
        self.embedding_dim = embedding_dim
        self.docs: List[Dict[str, Any]] = []
        self.embeddings: List[np.ndarray] = []

    def _generate_deterministic_embedding(self, text: str) -> np.ndarray:
        """Deterministic character and word feature hash embedding with L2 normalization."""
        vec = np.zeros(self.embedding_dim, dtype=np.float32)
        words = text.lower().split()
        if not words:
            return vec

        for word in words:
            # Hash word to embedding dimensions
            h = int(hashlib.md5(word.encode("utf-8")).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if ((h >> 8) & 1) else -1.0
            vec[idx] += sign

        # Subword 3-grams
        for i in range(len(text) - 2):
            trigram = text[i:i+3].lower()
            h = int(hashlib.sha256(trigram.encode("utf-8")).hexdigest(), 16)
            idx = h % self.embedding_dim
            sign = 1.0 if ((h >> 4) & 1) else -1.0
            vec[idx] += 0.5 * sign

        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def index_document(
        self,
        document_id: str,
        chunk_id: str,
        text: str,
        page_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        if embedding is not None:
            arr = np.array(embedding, dtype=np.float32)
            norm = np.linalg.norm(arr)
            vec = arr / norm if norm > 0 else arr
        else:
            vec = self._generate_deterministic_embedding(text)

        doc_entry = {
            "document_id": document_id,
            "chunk_id": chunk_id,
            "text": text,
            "page_number": page_number,
            "metadata": metadata or {},
        }
        self.docs.append(doc_entry)
        self.embeddings.append(vec)

    def _execute_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalItem]:
        if not self.docs:
            return []

        q_vec = self._generate_deterministic_embedding(query)
        q_norm = np.linalg.norm(q_vec)
        if q_norm == 0:
            return []

        emb_matrix = np.vstack(self.embeddings)  # (N, D)
        # Cosine similarities = dot product of L2-normalized vectors
        sims = np.dot(emb_matrix, q_vec)

        scores: List[tuple[int, float]] = []
        for idx, sim in enumerate(sims):
            doc = self.docs[idx]
            if filters:
                match = True
                for k, v in filters.items():
                    if doc["metadata"].get(k) != v and doc.get(k) != v:
                        match = False
                        break
                if not match:
                    continue
            scores.append((idx, float(sim)))

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
                    retrieval_method="cosine_similarity",
                    source_reference=f"{doc['document_id']}:PAGE-{doc['page_number']}",
                    metadata=doc["metadata"],
                )
            )
        return items
