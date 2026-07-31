"""Layout-aware retrieval."""

from __future__ import annotations

import math
from collections import Counter
from typing import TYPE_CHECKING

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from amdi.retrieval.index_store import IndexStore


class GeometryMethod(BaseRetrievalMethod):
    name = "geometry"

    def __init__(self, store: "IndexStore") -> None:
        super().__init__()
        self._store = store

    async def search(self, query: Query, k: int) -> list[Evidence]:
        units = await self._store.all_units()
        if not units:
            return []

        Q = query.raw.lower().split()
        if not Q:
            return []

        grams = Counter(Q)
        candidates: list[tuple[float, float, str]] = []

        for u in units:
            text = (u.text or "").lower()
            lexical = sum(text.count(tok) for tok in grams)

            page = u.page or 0
            bbox_y = u.bbox[1] if u.bbox else 0.0
            bbox_w = u.bbox[2] if u.bbox else 0.5
            reading_order = page * 1000 + bbox_y
            width_norm = 1.0 - bbox_w

            section_bias = 0.0
            if u.section and any(sec in u.section.lower() for sec in ("abstract", "summary", "intro", "conclusion")):
                section_bias = 0.3

            score = (
                lexical * 1.0
                + section_bias
                + 0.4 * math.tanh(1.0 - width_norm)
            )
            raw_score = score - reading_order * 1e-6
            candidates.append((raw_score, reading_order, u.unit_id))

        candidates.sort(key=lambda x: -x[0])
        top = candidates[:k]

        out: list[Evidence] = []
        for raw_score, reading_order, uid in top:
            unit = await self._store.get_unit(uid)
            if unit is None:
                continue
            norm = math.tanh(max(raw_score, 0.0))
            out.append(Evidence(
                text=unit.text,
                score_geometry=norm,
                citations=[Citation(
                    document_id=unit.document_id,
                    page=unit.page,
                    bbox=unit.bbox,
                    section=unit.section,
                    method_votes=[self.name],
                )],
                metadata={"unit_id": uid, "reading_order": reading_order},
            ))
        return out


__all__ = ["GeometryMethod"]
