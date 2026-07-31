"""Thread/async-safe in-memory index. Lossless, ideal for tests."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from typing import Sequence

from amdi.retrieval.index_store import CorpusUnit, IndexStore


class InMemoryIndexStore(IndexStore):
    def __init__(self) -> None:
        self._units: dict[str, CorpusUnit] = {}
        self._doc_index: dict[str, list[str]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def all_units(self) -> Sequence[CorpusUnit]:
        async with self._lock:
            return list(self._units.values())

    async def get_unit(self, unit_id: str) -> CorpusUnit | None:
        async with self._lock:
            return self._units.get(unit_id)

    async def add_units(self, units: Sequence[CorpusUnit]) -> None:
        async with self._lock:
            for u in units:
                self._units[u.unit_id] = u
                self._doc_index[u.document_id].append(u.unit_id)

    async def commit(self) -> None:
        return None

    async def size(self) -> int:
        async with self._lock:
            return len(self._units)

    async def by_document(self, document_id: str) -> list[CorpusUnit]:
        async with self._lock:
            ids = list(self._doc_index.get(document_id, ()))
            return [self._units[i] for i in ids if i in self._units]


__all__ = ["InMemoryIndexStore"]
