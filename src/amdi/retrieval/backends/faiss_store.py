"""FAISS dense index + persistent BM25.

Why FAISS here and not Qdrant/Milvus?
- Zero external services for single-node
- Strong batch IVF/HNSW performance
- Easily swappable behind IndexStore interface
"""

from __future__ import annotations

import asyncio
import pickle
from pathlib import Path
from typing import Sequence

import numpy as np

from amdi.retrieval.index_store import CorpusUnit, IndexStore

try:
    import faiss  # type: ignore
except ImportError:  # pragma: no cover
    faiss = None

try:
    from rank_bm25 import BM25Okapi  # type: ignore
except ImportError:  # pragma: no cover
    BM25Okapi = None


class FaissIndexStore(IndexStore):
    def __init__(self, root: Path, dim: int = 384) -> None:
        if faiss is None:
            raise RuntimeError(
                "faiss not installed. Install with: pip install faiss-cpu"
            )
        self._root = Path(root)
        (self._root / "faiss").mkdir(parents=True, exist_ok=True)
        (self._root / "bm25").mkdir(parents=True, exist_ok=True)

        self._dim = dim
        self._index = faiss.IndexFlatIP(dim)   # cosine via normalized vectors
        self._unit_ids: list[str] = []
        self._bm25_corpus: list[list[str]] = []
        self._bm25_unit_ids: list[str] = []
        self._bm25: "BM25Okapi | None" = None
        self._units: dict[str, CorpusUnit] = {}
        self._lock = asyncio.Lock()

        self._load()

    def _load(self) -> None:
        idx_path = self._root / "faiss" / "index.bin"
        ids_path = self._root / "faiss" / "ids.pkl"
        bm25_path = self._root / "bm25" / "bm25.pkl"
        if idx_path.exists() and ids_path.exists():
            self._index = faiss.read_index(str(idx_path))
            self._unit_ids = pickle.loads(ids_path.read_bytes())
        if bm25_path.exists() and BM25Okapi is not None:
            blob = pickle.loads(bm25_path.read_bytes())
            self._bm25 = blob["bm25"]
            self._bm25_corpus = blob["corpus"]
            self._bm25_unit_ids = blob["ids"]

    async def add_units(self, units: Sequence[CorpusUnit]) -> None:
        async with self._lock:
            emb_batch = []
            for u in units:
                self._units[u.unit_id] = u
                if u.embedding is None:
                    continue
                vec = np.asarray(u.embedding, dtype=np.float32)
                n = np.linalg.norm(vec)
                if n:
                    vec = vec / n
                emb_batch.append((u.unit_id, vec))
                self._bm25_corpus.append(u.text.lower().split())
                self._bm25_unit_ids.append(u.unit_id)
            if emb_batch:
                mat = np.vstack([v for _, v in emb_batch])
                self._index.add(mat)
                self._unit_ids.extend([i for i, _ in emb_batch])
                faiss.write_index(self._index, str(self._root / "faiss" / "index.bin"))
                (self._root / "faiss" / "ids.pkl").write_bytes(pickle.dumps(self._unit_ids))
            if BM25Okapi is not None and self._bm25_corpus:
                self._bm25 = BM25Okapi(self._bm25_corpus)
                (self._root / "bm25" / "bm25.pkl").write_bytes(pickle.dumps({
                    "bm25": self._bm25,
                    "corpus": self._bm25_corpus,
                    "ids": self._bm25_unit_ids,
                }))

    async def search_dense(self, query_vec: np.ndarray, k: int) -> tuple[list[float], list[str]]:
        async with self._lock:
            if self._index.ntotal == 0:
                return [], []
            q = query_vec.astype(np.float32).reshape(1, -1)
            n = np.linalg.norm(q)
            if n:
                q = q / n
            scores, idxs = self._index.search(q, min(k, self._index.ntotal))
            scores_list = scores[0].tolist()
            ids = [self._unit_ids[i] for i in idxs[0] if 0 <= i < len(self._unit_ids)]
            return scores_list, ids

    async def search_bm25(self, text: str, k: int) -> tuple[list[float], list[str]]:
        async with self._lock:
            if self._bm25 is None:
                return [], []
            tokens = text.lower().split()
            scores = self._bm25.get_scores(tokens)
            top = sorted(enumerate(scores), key=lambda x: -x[1])[:k]
            return [float(s) for _, s in top], [self._bm25_unit_ids[i] for i, _ in top]

    async def all_units(self) -> Sequence[CorpusUnit]:
        async with self._lock:
            return list(self._units.values())

    async def get_unit(self, unit_id: str) -> CorpusUnit | None:
        async with self._lock:
            return self._units.get(unit_id)

    async def commit(self) -> None:
        return None

    async def size(self) -> int:
        async with self._lock:
            return self._index.ntotal


__all__ = ["FaissIndexStore"]
