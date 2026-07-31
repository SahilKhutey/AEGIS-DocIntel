"""Entity-graph retrieval."""

from __future__ import annotations

import re
from collections import defaultdict
from typing import TYPE_CHECKING

from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Citation, Evidence, Query

if TYPE_CHECKING:
    from amdi.retrieval.index_store import IndexStore


_ENTITY_RE = re.compile(
    r"\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b|([A-Z]{2,})\b"
)


class GraphMethod(BaseRetrievalMethod):
    name = "graph"

    def __init__(self, store: "IndexStore") -> None:
        super().__init__()
        self._store = store
        self._mention_index: dict[str, list[str]] = defaultdict(list)
        self._entity_index: dict[str, list[str]] = defaultdict(list)

    async def warmup(self) -> None:
        units = await self._store.all_units()
        for u in units:
            ents = set(self._entities_in(u.text))
            for e in ents:
                self._entity_index[e].append(u.unit_id)
                for tok in u.text.lower().split():
                    if len(tok) > 4:
                        self._mention_index[tok].append(u.unit_id)

    @staticmethod
    def _entities_in(text: str) -> list[str]:
        return [m[0] or m[1] for m in _ENTITY_RE.findall(text) if (m[0] or m[1])]

    async def search(self, query: Query, k: int) -> list[Evidence]:
        if not self._entity_index:
            await self.warmup()

        ents = self._entities_in(query.raw)
        qtokens = [t for t in query.raw.lower().split() if len(t) > 4]

        scores: dict[str, float] = defaultdict(float)
        for e in ents:
            for uid in self._entity_index.get(e, ()):
                scores[uid] += 1.0
        for tok in qtokens:
            for uid in self._mention_index.get(tok, ()):
                scores[uid] += 0.4

        ranked = sorted(scores.items(), key=lambda x: -x[1])[:k]
        out: list[Evidence] = []
        for uid, s in ranked:
            unit = await self._store.get_unit(uid)
            if unit is None:
                continue
            norm = min(s / 5.0, 1.0)
            out.append(Evidence(
                text=unit.text,
                score_graph=norm,
                citations=[Citation(
                    document_id=unit.document_id,
                    page=unit.page,
                    bbox=unit.bbox,
                    section=unit.section,
                    method_votes=[self.name, *("entity:" + e for e in ents[:3])],
                )],
                metadata={"unit_id": uid, "entities_hit": ents},
            ))
        return out


__all__ = ["GraphMethod"]
