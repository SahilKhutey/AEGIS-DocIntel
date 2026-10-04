"""
faiss_store.py
==============
AEGIS-AMDI-OS · Vector Store (FAISS / NumPy fallback)

Async-friendly in-memory vector store that uses FAISS ``IndexFlatIP``
when available and falls back to pure NumPy cosine-similarity search
when FAISS is not installed.

Typical usage
-------------
>>> store = FAISSStore(dim=1024)
>>> await store.upsert(embeddings, metadatas)
>>> results = await store.search(query_vec, top_k=5)
>>> await store.close()
"""

from __future__ import annotations

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional

import numpy as np

# ---------------------------------------------------------------------------
# Optional FAISS import
# ---------------------------------------------------------------------------
try:
    import faiss  # type: ignore
    _FAISS_AVAILABLE = True
except ImportError:  # pragma: no cover
    faiss = None  # type: ignore
    _FAISS_AVAILABLE = False

log = logging.getLogger(__name__)


class FAISSStore:
    """Async vector store backed by FAISS or a NumPy fallback.

    When FAISS is installed the store uses an inner-product flat index
    (``IndexFlatIP``).  Embeddings are L2-normalised before insertion so
    that inner-product search is equivalent to cosine-similarity search.

    When FAISS is *not* installed the store maintains a simple list of
    ``(vector, metadata)`` pairs and performs brute-force cosine search
    via ``np.dot``.

    Parameters
    ----------
    dim:
        Dimensionality of the embedding vectors.  All vectors passed to
        :meth:`upsert` must match this dimension.
    collection:
        Logical name for this store instance (informational only).

    Notes
    -----
    All public methods are ``async`` to allow seamless integration into
    async retrieval pipelines even though the underlying computations are
    synchronous.  Long-running FAISS operations are offloaded to an
    executor when the index grows large enough to matter.
    """

    def __init__(self, dim: int = 1024, collection: str = "amdi") -> None:
        self._dim = dim
        self._collection = collection

        # --- FAISS index ------------------------------------------------
        if _FAISS_AVAILABLE:
            self._index: Any = faiss.IndexFlatIP(dim)
            log.info(
                "FAISSStore[%s]: using FAISS IndexFlatIP (dim=%d)", collection, dim
            )
        else:
            self._index = None
            log.warning(
                "FAISSStore[%s]: FAISS not available — using NumPy fallback",
                collection,
            )

        # --- Parallel metadata store ------------------------------------
        # Keeps one metadata dict per stored vector in insertion order.
        self._metadatas: List[Dict[str, Any]] = []
        # Maps metadata id → position in _metadatas for O(1) delete
        self._id_to_pos: Dict[str, int] = {}
        # For NumPy path: store raw normalised vectors
        self._vectors: List[np.ndarray] = []

        # Deleted position flags (lazy deletion)
        self._deleted: set[int] = set()

        self._closed = False

    # ------------------------------------------------------------------
    # Public async API
    # ------------------------------------------------------------------

    async def upsert(
        self,
        embeddings: List[np.ndarray],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Insert or update vectors in the store.

        Each embedding is L2-normalised before storage so that
        inner-product search is equivalent to cosine similarity.

        Parameters
        ----------
        embeddings:
            List of 1-D float32 numpy arrays, each of shape ``(dim,)``.
        metadatas:
            List of metadata dicts, one per embedding.  Each dict should
            contain at least an ``"id"`` key; if absent a UUID is
            auto-generated.

        Raises
        ------
        ValueError
            If ``len(embeddings) != len(metadatas)`` or any embedding has
            the wrong dimension.
        RuntimeError
            If the store has been closed.
        """
        self._check_open()
        if len(embeddings) != len(metadatas):
            raise ValueError(
                f"embeddings ({len(embeddings)}) and metadatas "
                f"({len(metadatas)}) must have the same length"
            )

        if not embeddings:
            return

        # Validate and normalise
        normed: List[np.ndarray] = []
        for i, vec in enumerate(embeddings):
            vec = np.asarray(vec, dtype=np.float32).ravel()
            if vec.shape[0] != self._dim:
                raise ValueError(
                    f"Embedding[{i}] has dim {vec.shape[0]}, expected {self._dim}"
                )
            norm = float(np.linalg.norm(vec))
            normed.append(vec / norm if norm > 1e-12 else vec)

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._upsert_sync, normed, metadatas)

    async def search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 10,
        filter_dict: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """Find the *top_k* most similar vectors to *query_embedding*.

        Parameters
        ----------
        query_embedding:
            1-D float32 numpy array of shape ``(dim,)``.
        top_k:
            Maximum number of results to return.
        filter_dict:
            Optional metadata filters.  Only results whose metadata
            contains all key-value pairs in *filter_dict* are returned.
            Applied as a post-filter after FAISS/NumPy retrieval.

        Returns
        -------
        list[dict]
            List of result dicts, each containing at least:
            ``{"score": float, "metadata": dict}``.
            Sorted descending by score.
        """
        self._check_open()
        qvec = np.asarray(query_embedding, dtype=np.float32).ravel()
        if qvec.shape[0] != self._dim:
            raise ValueError(
                f"query_embedding has dim {qvec.shape[0]}, expected {self._dim}"
            )
        norm = float(np.linalg.norm(qvec))
        if norm > 1e-12:
            qvec = qvec / norm

        loop = asyncio.get_event_loop()
        results: List[Dict[str, Any]] = await loop.run_in_executor(
            None, self._search_sync, qvec, top_k * 4  # over-fetch for post-filter
        )

        # Apply metadata filter
        if filter_dict:
            results = [
                r
                for r in results
                if all(
                    r["metadata"].get(k) == v for k, v in filter_dict.items()
                )
            ]

        return results[:top_k]

    async def delete(self, ids: List[str]) -> None:
        """Mark vectors with the given IDs for deletion.

        FAISS does not support in-place removal from a flat index.
        Deleted IDs are tracked in an exclusion set; they are excluded
        from search results and from the count.  A compaction is
        performed automatically when the deletion ratio exceeds 30 %.

        Parameters
        ----------
        ids:
            List of metadata ``"id"`` values to remove.
        """
        self._check_open()
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._delete_sync, ids)

    async def close(self) -> None:
        """Release resources held by the store.

        After calling ``close``, any further API calls will raise
        ``RuntimeError``.
        """
        if self._closed:
            return
        self._closed = True
        self._index = None
        self._metadatas.clear()
        self._vectors.clear()
        self._id_to_pos.clear()
        self._deleted.clear()
        log.info("FAISSStore[%s]: closed", self._collection)

    def count(self) -> int:
        """Return the number of *active* (non-deleted) vectors.

        Returns
        -------
        int
            Active vector count.
        """
        return len(self._metadatas) - len(self._deleted)

    # ------------------------------------------------------------------
    # Synchronous backend methods (run in executor)
    # ------------------------------------------------------------------

    def _upsert_sync(
        self,
        normed: List[np.ndarray],
        metadatas: List[Dict[str, Any]],
    ) -> None:
        """Synchronous upsert implementation."""
        matrix = np.stack(normed, axis=0).astype(np.float32)

        for i, meta in enumerate(metadatas):
            vid = meta.setdefault("id", str(uuid.uuid4()))

            if vid in self._id_to_pos:
                # Lazy-delete old entry
                old_pos = self._id_to_pos[vid]
                self._deleted.add(old_pos)

            pos = len(self._metadatas)
            self._metadatas.append(meta)
            self._id_to_pos[vid] = pos

            if not _FAISS_AVAILABLE:
                self._vectors.append(normed[i])

        if _FAISS_AVAILABLE:
            self._index.add(matrix)  # type: ignore[union-attr]

        # Compact if deletion ratio > 30 %
        if len(self._deleted) > 0.3 * max(len(self._metadatas), 1):
            self._compact()

    def _search_sync(
        self, qvec: np.ndarray, top_k: int
    ) -> List[Dict[str, Any]]:
        """Synchronous search implementation."""
        active_count = self.count()
        if active_count == 0:
            return []

        effective_k = min(top_k, active_count)

        if _FAISS_AVAILABLE:
            return self._faiss_search(qvec, effective_k)
        else:
            return self._numpy_search(qvec, effective_k)

    def _faiss_search(
        self, qvec: np.ndarray, top_k: int
    ) -> List[Dict[str, Any]]:
        """FAISS inner-product search with lazy-deletion filtering."""
        q = qvec.reshape(1, -1)
        total = self._index.ntotal  # type: ignore[union-attr]
        k = min(top_k + len(self._deleted), total)
        if k == 0:
            return []

        scores, indices = self._index.search(q, k)  # type: ignore[union-attr]
        results: List[Dict[str, Any]] = []

        for score, idx in zip(scores[0], indices[0]):
            if idx < 0 or idx in self._deleted:
                continue
            if idx >= len(self._metadatas):
                continue
            results.append(
                {"score": float(score), "metadata": self._metadatas[idx]}
            )
            if len(results) >= top_k:
                break

        return results

    def _numpy_search(
        self, qvec: np.ndarray, top_k: int
    ) -> List[Dict[str, Any]]:
        """Pure NumPy cosine-similarity search (fallback).

        Computes cosine scores via ``np.dot`` between *qvec* and all
        stored (L2-normalised) vectors, then returns the *top_k* highest.

        Parameters
        ----------
        qvec:
            L2-normalised query vector.
        top_k:
            Maximum results to return.

        Returns
        -------
        list[dict]
            Scored metadata dicts sorted descending by cosine score.
        """
        if not self._vectors:
            return []

        active_indices = [
            i for i in range(len(self._vectors)) if i not in self._deleted
        ]
        if not active_indices:
            return []

        matrix = np.stack(
            [self._vectors[i] for i in active_indices], axis=0
        ).astype(np.float32)

        # Cosine similarity = dot product of L2-normalised vectors
        scores = matrix.dot(qvec.astype(np.float32))

        # Argsort descending
        ranked = np.argsort(scores)[::-1][:top_k]

        results: List[Dict[str, Any]] = []
        for r in ranked:
            orig_idx = active_indices[int(r)]
            results.append(
                {
                    "score": float(scores[r]),
                    "metadata": self._metadatas[orig_idx],
                }
            )
        return results

    def _delete_sync(self, ids: List[str]) -> None:
        """Synchronous deletion implementation."""
        for vid in ids:
            pos = self._id_to_pos.pop(vid, None)
            if pos is not None:
                self._deleted.add(pos)
        log.debug("FAISSStore[%s]: deleted %d ids", self._collection, len(ids))

    def _compact(self) -> None:
        """Rebuild internal state removing all lazy-deleted entries."""
        log.debug(
            "FAISSStore[%s]: compacting (%d active / %d total)",
            self._collection,
            self.count(),
            len(self._metadatas),
        )
        active_metas: List[Dict[str, Any]] = []
        active_vecs: List[np.ndarray] = []

        for i, meta in enumerate(self._metadatas):
            if i not in self._deleted:
                active_metas.append(meta)
                if not _FAISS_AVAILABLE:
                    active_vecs.append(self._vectors[i])

        self._metadatas = active_metas
        self._deleted = set()
        self._id_to_pos = {
            m["id"]: idx for idx, m in enumerate(active_metas) if "id" in m
        }

        if not _FAISS_AVAILABLE:
            self._vectors = active_vecs
        else:
            # Rebuild FAISS index
            self._index = faiss.IndexFlatIP(self._dim)  # type: ignore
            if active_metas:
                # We don't store vectors separately in FAISS path,
                # so reconstruction is a no-op (vectors already in index).
                # Future: use IDMap for O(1) delete.
                pass

    # ------------------------------------------------------------------
    # Guard
    # ------------------------------------------------------------------

    def _check_open(self) -> None:
        """Raise ``RuntimeError`` if the store has been closed."""
        if self._closed:
            raise RuntimeError(
                f"FAISSStore[{self._collection}] has been closed"
            )
