"""BM25 keyword retrieval using the `rank_bm25` package.

Each search() gets scores normalized to [0, 1] via min-max for fairness
across other methods before fusion.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from amdi.retrieval.index_store import IndexStore


class BM25Method(BaseRetrievalMethod):
    name = "bm25"

    def __init__(
        self,
        store: "IndexStore",
        bm25_index_getter: Callable[[], object | None] | None = None,
    ) -> None:
        super().__init__()
        self._store = store
        self._get_bm25 = bm25_index_getter or (lambda: None)
        self._units_cache: list[str] = []

    async def _unit_id_at(self, local_idx: int) -> str:
        if 0 <= local_idx < len(self._units_cache):
            return self._units_cache[local_idx]
        units = await self._store.all_units()
        if 0 <= local_idx < len(units):
            return units[local_idx].unit_id
        raise IndexError(f"local_idx {local_idx} out of range")

    async def search(self, query: Query, k: int) -> list[Evidence]:
        if hasattr(self._store, "search_bm25"):
            scores, unit_ids = await self._store.search_bm25(query.raw, k)  # type: ignore[attr-defined]
            if not unit_ids:
                return []
            max_s = max(scores) if scores else 1.0
            min_s = min(scores) if scores else 0.0
            span = (max_s - min_s) or 1.0

            out: list[Evidence] = []
            for s, uid in zip(scores, unit_ids, strict=False):
                unit = await self._store.get_unit(uid)
                if unit is None:
                    continue
                out.append(Evidence(
                    text=unit.text,
                    score_bm25=(s - min_s) / span,
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

        bm25 = self._get_bm25()
        units = await self._store.all_units()
        if not units:
            return []
        self._units_cache = [u.unit_id for u in units]

        if bm25 is None:
            from rank_bm25 import BM25Okapi  # local import
            bm25 = BM25Okapi([u.text.lower().split() for u in units])

        tokens = query.raw.lower().split()
        if not tokens:
            return []

        scores = bm25.get_scores(tokens)  # type: ignore[attr-defined]
        ranked = sorted(enumerate(scores), key=lambda x: -x[1])[:k]
        if not ranked or ranked[0][1] == 0:
            return []

        max_s = max(s for _, s in ranked)
        min_s = min(s for _, s in ranked)
        span = (max_s - min_s) or 1.0

        out: list[Evidence] = []
        for local_idx, raw in ranked:
            uid = await self._unit_id_at(local_idx)
            unit = await self._store.get_unit(uid)
            if unit is None:
                continue
            out.append(Evidence(
                text=unit.text,
                score_bm25=(raw - min_s) / span,
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


__all__ = ["BM25Method"]
