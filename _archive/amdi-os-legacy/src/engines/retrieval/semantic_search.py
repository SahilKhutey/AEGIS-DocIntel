"""

Semantic Search

===============



Embedding-based similarity search.

Supports:

- Cosine similarity

- Dot product

- Euclidean (negative distance)

- Approximate NN via vector index (FAISS-like interface)

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .exceptions import EmptyIndexError, IndexDimensionError, InvalidQueryError





@dataclass

class SemanticResult:

    """A single semantic search result."""



    doc_id: Any

    score: float

    rank: int

    metadata: Dict[str, Any] = field(default_factory=dict)





class SemanticSearch:

    """

    Embedding-based semantic search.



    Mathematical Foundation:

        Cosine similarity:

            cos(u, v) = (u · v) / (||u|| · ||v||)



        Dot product (when vectors are normalized):

            dot(u, v) = u · v



        Negative Euclidean:

            sim(u, v) = -||u - v||₂

    """



    METRICS = ("cosine", "dot", "euclidean")



    def __init__(self, metric: str = "cosine") -> None:

        if metric not in self.METRICS:

            raise ValueError(f"Unknown metric: {metric}")

        self.metric = metric

        self.embeddings: Dict[Any, np.ndarray] = {}

        self.metadata: Dict[Any, Dict[str, Any]] = {}



    def add(

        self,

        doc_id: Any,

        embedding: np.ndarray,

        metadata: Optional[Dict[str, Any]] = None,

    ) -> None:

        """Add a document embedding to the index."""

        emb = np.asarray(embedding, dtype=np.float64)

        if emb.ndim != 1:

            raise ValueError("embedding must be 1-D.")

        self.embeddings[doc_id] = emb

        if metadata is not None:

            self.metadata[doc_id] = metadata



    def add_batch(

        self,

        doc_ids: List[Any],

        embeddings: np.ndarray,

        metadata_list: Optional[List[Dict[str, Any]]] = None,

    ) -> None:

        """Add multiple embeddings at once."""

        if len(doc_ids) != embeddings.shape[0]:

            raise ValueError("doc_ids and embeddings length mismatch.")

        for i, did in enumerate(doc_ids):

            meta = metadata_list[i] if metadata_list else None

            self.add(did, embeddings[i], metadata=meta)



    def search(

        self,

        query_embedding: np.ndarray,

        top_k: int = 10,

    ) -> List[SemanticResult]:

        """

        Search by query embedding.



        Returns top-k results sorted by similarity descending.

        """

        if not self.embeddings:

            raise EmptyIndexError("Semantic index is empty.")

        q = np.asarray(query_embedding, dtype=np.float64)

        if q.ndim != 1:

            raise InvalidQueryError("query_embedding must be 1-D.")

        # dimension check

        first_emb = next(iter(self.embeddings.values()))

        if q.shape[0] != first_emb.shape[0]:

            raise IndexDimensionError(

                f"Query dim {q.shape[0]} ≠ index dim {first_emb.shape[0]}."

            )



        scores: List[Tuple[Any, float]] = []

        for doc_id, emb in self.embeddings.items():

            score = self._similarity(q, emb)

            scores.append((doc_id, score))

        scores.sort(key=lambda x: x[1], reverse=True)

        top = scores[:top_k]

        return [

            SemanticResult(

                doc_id=did,

                score=float(s),

                rank=i + 1,

                metadata=self.metadata.get(did, {}),

            )

            for i, (did, s) in enumerate(top)

        ]



    def _similarity(self, u: np.ndarray, v: np.ndarray) -> float:

        if self.metric == "cosine":

            nu = np.linalg.norm(u)

            nv = np.linalg.norm(v)

            if nu < 1e-12 or nv < 1e-12:

                return 0.0

            return float(np.dot(u, v) / (nu * nv))

        if self.metric == "dot":

            return float(np.dot(u, v))

        if self.metric == "euclidean":

            return float(-np.linalg.norm(u - v))

        return 0.0



    def __len__(self) -> int:

        return len(self.embeddings)
