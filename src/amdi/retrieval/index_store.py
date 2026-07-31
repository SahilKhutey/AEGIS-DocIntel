"""Read API over a multi-method corpus.

A corpus is a collection of (document_id, unit_index, text, layout) records
already produced by the ingestion pipeline. The IndexStore exposes minimal
accessors used by each retrieval method.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass
from typing import Any, Sequence


@dataclass(slots=True)
class CorpusUnit:
    unit_id: str            # globally unique
    document_id: str
    page: int | None
    bbox: tuple[float, float, float, float] | None
    section: str | None
    text: str
    embedding: list[float] | None = None
    features: dict[str, float] | None = None      # TDM stats, layout features, etc.


class IndexStore(abc.ABC):
    @abc.abstractmethod
    async def all_units(self) -> Sequence[CorpusUnit]: ...
    @abc.abstractmethod
    async def get_unit(self, unit_id: str) -> CorpusUnit | None: ...
    @abc.abstractmethod
    async def add_units(self, units: Sequence[CorpusUnit]) -> None: ...
    @abc.abstractmethod
    async def commit(self) -> None: ...
    @abc.abstractmethod
    async def size(self) -> int: ...


__all__ = ["CorpusUnit", "IndexStore"]
