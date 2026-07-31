"""Graph method surfaces units sharing capitalized entities."""

from __future__ import annotations

import pytest

from amdi.retrieval.methods.graph_method import GraphMethod
from amdi.retrieval.schemas import Query
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_graph_method_finds_entity_overlap() -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(unit_id=f"u{i+1}", document_id="d1", page=1,
                   bbox=(0, 0, 0.5, 0.1), section="body", text=text)
        for i, text in enumerate([
            "Quantum entanglement links Schrödinger and Einstein.",
            "Einstein disagreed with Bohr about quantum interpretations.",
            "Cooking pasta requires boiling water and patience.",
        ])
    ])
    method = GraphMethod(store)
    out = await method.search(Query(raw="Einstein", top_k=3), k=3)
    ids = [e.metadata["unit_id"] for e in out]
    assert "u1" in ids
    assert "u2" in ids


@pytest.mark.asyncio
async def test_graph_method_handles_no_entities() -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(unit_id="u1", document_id="d1", page=1,
                   bbox=(0, 0, 0.5, 0.1), section="body", text="hello world there"),
    ])
    method = GraphMethod(store)
    out = await method.search(Query(raw="hello", top_k=1), k=1)
    assert out == []
