"""

Frequency Search

================



TF-IDF and BM25-based search over term frequency vectors.



Mathematical Foundation:

    TF-IDF:

        tfidf(t, d) = tf(t, d) · log(N / df(t))



    BM25:

        score(q, d) = Σ_{t ∈ q} IDF(t) · (tf(t,d) · (k₁+1)) /

                       (tf(t,d) + k₁ · (1 - b + b · |d|/avgdl))

"""



from __future__ import annotations



import math

from collections import Counter

from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .exceptions import EmptyIndexError, InvalidQueryError





@dataclass

class FrequencyResult:

    """A single frequency search result."""



    doc_id: Any

    score: float

    rank: int

    matched_terms: List[str] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)





class FrequencySearch:

    """

    TF-IDF / BM25 frequency-based retrieval.

    """



    def __init__(
        self,
        method: str = "bm25",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        if method not in {"tfidf", "bm25"}:
            raise ValueError(f"Unknown method: {method}")
        self.method = method
        self.k1 = k1
        self.b = b
        # inverted index: term → {doc_id: tf}
        self.inverted_index: Dict[str, Dict[Any, int]] = {}
        # document statistics
        self.doc_lens: Dict[Any, int] = {}
        self.doc_count: int = 0
        self.avg_dl: float = 0.0
        self.metadata: Dict[Any, Dict[str, Any]] = {}
        self.item_tenants: Dict[Any, Optional[str]] = {}

    def add(
        self,
        doc_id: Any,
        tokens: List[str],
        metadata: Optional[Dict[str, Any]] = None,
        tenant_id: Optional[str] = None,
    ) -> None:
        """Add a tokenized document."""
        tf = Counter(tokens)
        self.doc_lens[doc_id] = len(tokens)
        for term, count in tf.items():
            if term not in self.inverted_index:
                self.inverted_index[term] = {}
            self.inverted_index[term][doc_id] = count
        if metadata is not None:
            self.metadata[doc_id] = metadata
            if tenant_id is None:
                tenant_id = metadata.get("tenant_id")
        self.item_tenants[doc_id] = tenant_id
        self._recompute_stats()

    def add_batch(
        self,
        docs: List[Tuple[Any, List[str]]],
        tenant_ids: Optional[List[Optional[str]]] = None,
    ) -> None:
        for i, (did, toks) in enumerate(docs):
            tid = tenant_ids[i] if tenant_ids else None
            self.add(did, toks, tenant_id=tid)

    def _recompute_stats(self) -> None:
        self.doc_count = len(self.doc_lens)
        if self.doc_count > 0:
            self.avg_dl = sum(self.doc_lens.values()) / self.doc_count
        else:
            self.avg_dl = 0.0

    def search(
        self,
        query_tokens: List[str],
        top_k: int = 10,
        tenant_id: Optional[str] = None,
    ) -> List[FrequencyResult]:
        """Search documents matching query tokens with optional tenant filtering."""
        if self.doc_count == 0:
            raise EmptyIndexError("Frequency index is empty.")
        if not query_tokens:
            raise InvalidQueryError("query_tokens is empty.")

        # candidate docs (any that contain at least one query term)
        candidates: Dict[Any, List[str]] = {}
        for term in set(query_tokens):
            if term in self.inverted_index:
                for did in self.inverted_index[term]:
                    if tenant_id is not None:
                        item_tenant = self.item_tenants.get(did)
                        if item_tenant is not None and item_tenant != tenant_id:
                            continue
                    if did not in candidates:
                        candidates[did] = []
                    candidates[did].append(term)

        if not candidates:

            return []

        # compute scores

        scored: List[Tuple[Any, float, List[str]]] = []

        for did, matched in candidates.items():

            if self.method == "bm25":

                score = self._bm25_score(did, query_tokens)

            else:

                score = self._tfidf_score(did, query_tokens)

            scored.append((did, score, matched))

        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:top_k]

        results: List[FrequencyResult] = []

        for rank, (did, score, matched) in enumerate(top, start=1):

            results.append(

                FrequencyResult(

                    doc_id=did,

                    score=float(score),

                    rank=rank,

                    matched_terms=matched,

                    metadata=self.metadata.get(did, {}),

                )

            )

        return results



    def _idf(self, term: str) -> float:

        df = len(self.inverted_index.get(term, {}))

        if df == 0:

            return 0.0

        return math.log((self.doc_count - df + 0.5) / (df + 0.5) + 1.0)



    def _tfidf_score(self, doc_id: Any, query_tokens: List[str]) -> float:
        score = 0.0
        for term in query_tokens:
            tf = self.inverted_index.get(term, {}).get(doc_id, 0)
            if tf == 0:
                continue
            df = len(self.inverted_index.get(term, {}))
            idf = math.log((self.doc_count + 1.0) / (df + 1.0)) + 1.0
            score += tf * idf
        return score



    def _bm25_score(self, doc_id: Any, query_tokens: List[str]) -> float:

        score = 0.0

        dl = self.doc_lens.get(doc_id, 0)

        for term in query_tokens:

            tf = self.inverted_index.get(term, {}).get(doc_id, 0)

            if tf == 0:

                continue

            idf = self._idf(term)

            norm = 1 - self.b + self.b * (dl / max(self.avg_dl, 1e-9))

            score += idf * (tf * (self.k1 + 1)) / (tf + self.k1 * norm)

        return score



    def __len__(self) -> int:

        return self.doc_count
