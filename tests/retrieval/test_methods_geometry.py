"""Geometry method favors upper-page locations with section-marker hits."""

from __future__ import annotations

import pytest

from amdi.retrieval.methods.geometry_method import GeometryMethod
from amdi.retrieval.schemas import Query
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_geometry_prefers_section_mentions() -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(unit_id="u1", document_id="d1", page=1,
                   bbox=(0.0, 0.0, 0.5, 0.05),
                   section="Abstract", text="This is the abstract."),
        CorpusUnit(unit_id="u2", document_id="d1", page=3,
                   bbox=(0.0, 0.5, 0.5, 0.05),
                   section="Misc",     text="This is unrelated prose."),
    ])

    method = GeometryMethod(store)
    out = await method.search(Query(raw="abstract", top_k=2), k=2)
    assert out[0].metadata["unit_id"] == "u1"
    assert out[0].score_geometry > 0
