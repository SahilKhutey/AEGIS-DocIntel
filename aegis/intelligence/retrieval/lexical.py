"""
aegis.intelligence.retrieval.lexical
===================================
Independent Lexical Retrieval mode implementing standard Okapi BM25 scoring.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from typing import Any, Dict, List, Optional

from aegis.intelligence.models import (
    RetrievalItem,
    RetrievalMode,
)
from aegis.intelligence.retrieval.base import BaseRetriever


class LexicalRetriever(BaseRetriever):
    """Standalone BM25 Inverted Index Retriever."""

    def __init__(self, k1: float = 1.5, b: float = 0.75):
        super().__init__(mode=RetrievalMode.LEXICAL)
        self.k1 = k1
        self.b = b
        self.docs: List[Dict[str, Any]] = []
        self.doc_len: List[int] = []
        self.doc_freq: Counter[str] = Counter()
        self.avg_doc_len: float = 0.0

    @staticmethod
    def tokenize(text: str) -> List[str]:
        """Normalize and tokenize text into lowercase alphanumeric tokens."""
        clean = re.sub(r"[^\w\s-]", " ", text.lower())
        return [tok for tok in clean.split() if len(tok) > 1]

    def index_document(
        self,
        document_id: str,
        chunk_id: str,
        text: str,
        page_number: int = 1,
        metadata: Optional[Dict[str, Any]] = None,
        embedding: Optional[List[float]] = None,
    ) -> None:
        tokens = self.tokenize(text)
        term_counts = Counter(tokens)
        doc_entry = {
            "document_id": document_id,
            "chunk_id": chunk_id,
            "text": text,
            "page_number": page_number,
            "metadata": metadata or {},
            "tokens": tokens,
            "term_counts": term_counts,
            "length": len(tokens),
        }
        self.docs.append(doc_entry)
        self.doc_len.append(len(tokens))
        for term in term_counts.keys():
            self.doc_freq[term] += 1
        self.avg_doc_len = sum(self.doc_len) / max(1, len(self.docs))

    def _execute_search(
        self,
        query: str,
        top_k: int = 5,
        filters: Optional[Dict[str, Any]] = None,
    ) -> List[RetrievalItem]:
        q_tokens = self.tokenize(query)
        if not q_tokens or not self.docs:
            return []

        n_docs = len(self.docs)
        scores: List[tuple[int, float]] = []

        for idx, doc in enumerate(self.docs):
            # Check metadata filters
            if filters:
                match = True
                for k, v in filters.items():
                    if doc["metadata"].get(k) != v and doc.get(k) != v:
                        match = False
                        break
                if not match:
                    continue

            score = 0.0
            dl = doc["length"]
            t_counts = doc["term_counts"]

            for term in q_tokens:
                if term not in t_counts:
                    continue
                tf = t_counts[term]
                df = self.doc_freq.get(term, 0)
                idf = math.log(1.0 + (n_docs - df + 0.5) / (df + 0.5))
                denom = tf + self.k1 * (1.0 - self.b + self.b * (dl / max(1.0, self.avg_doc_len)))
                score += idf * ((tf * (self.k1 + 1.0)) / denom)

            if score > 0.0:
                scores.append((idx, score))

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
                    retrieval_method="bm25",
                    source_reference=f"{doc['document_id']}:PAGE-{doc['page_number']}",
                    metadata=doc["metadata"],
                )
            )
        return items
