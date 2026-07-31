"""BM25 method scores non-zero on real corpus overlap."""

from __future__ import annotations

import pytest

from amdi.retrieval.methods.bm25_method import BM25Method
from amdi.retrieval.schemas import Query
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_bm25_finds_relevant_unit_with_monkeypatched_index(monkeypatch) -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(
            unit_id=f"u{i}", document_id="d1", page=i,
            bbox=(0.1, 0.2, 0.8, 0.05), section="body", text=text,
        )
        for i, text in enumerate([
            "the cat sat on the mat",
            "dogs love to run in the park",
            "a quick brown fox jumps high",
            "transformers are sequence models",
        ])
    ])

    from rank_bm25 import BM25Okapi

    units = await store.all_units()
    bm25 = BM25Okapi([u.text.split() for u in units])

    method = BM25Method(store, lambda: bm25)
    await method.warmup()

    out = await method.search(Query(raw="sequence models", top_k=2), k=2)
    assert out, "BM25 should surface at least one evidence item"
    texts = [e.text for e in out]
    assert any("transformers" in t for t in texts)
