"""Dense semantic retrieval via sentence-transformers (or HF AutoModel)."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING

import numpy as np

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from sentence_transformers import SentenceTransformer  # type: ignore
    from amdi.retrieval.index_store import IndexStore


class DenseMethod(BaseRetrievalMethod):
    name = "dense"

    def __init__(
        self,
        store: "IndexStore",
        embedder: "SentenceTransformer | None" = None,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
    ) -> None:
        super().__init__()
        self._store = store
        self._embedder = embedder
        self._model_name = model_name

    async def warmup(self) -> None:
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer  # local import
                self._embedder = SentenceTransformer(self._model_name)
                self._embedder.encode(["warmup"], normalize_embeddings=True)
            except Exception:
                pass

    def _encode(self, texts: list[str]) -> np.ndarray:
        if self._embedder is None:
            # Fallback deterministic zero/mock vector if embedder unavailable
            return np.zeros((len(texts), 384), dtype=np.float32)
        return self._embedder.encode(texts, normalize_embeddings=True, convert_to_numpy=True)

    async def search(self, query: Query, k: int) -> list[Evidence]:
        if self._embedder is None:
            await self.warmup()

        qvec = self._encode([query.raw])[0]
        scores, unit_ids = await self._dense_search(qvec, k)

        out: list[Evidence] = []
        for s, uid in zip(scores, unit_ids, strict=False):
            unit = await self._store.get_unit(uid)
            if unit is None:
                continue
            out.append(Evidence(
                text=unit.text,
                score_dense=float(s),
                citations=[Citation(
                    document_id=unit.document_id,
                    page=unit.page,
                    bbox=unit.bbox,
                    section=unit.section,
                    method_votes=[self.name],
                )],
                metadata={"unit_id": unit.unit_id},
            ))
        return out

    async def _dense_search(self, qvec: np.ndarray, k: int) -> tuple[list[float], list[str]]:
        if hasattr(self._store, "search_dense"):
            return await self._store.search_dense(qvec, k)  # type: ignore[attr-defined]
        units = await self._store.all_units()
        if not units:
            return [], []
        emb = [(np.asarray(u.embedding, dtype=np.float32) if u.embedding is not None else None) for u in units]
        valid = [i for i, v in enumerate(emb) if v is not None]
        if not valid:
            return [], []
        M = np.vstack([emb[i] for i in valid])
        qn = np.linalg.norm(qvec)
        q = qvec / (qn if qn else 1.0)
        sim = M @ q
        top = sorted(zip(sim.tolist(), valid, strict=False), key=lambda x: -x[0])[:k]
        return [s for s, _ in top], [units[i].unit_id for _, i in top]


__all__ = ["DenseMethod"]
