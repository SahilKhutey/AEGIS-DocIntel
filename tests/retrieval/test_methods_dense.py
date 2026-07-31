"""Dense method returns cosine-ranked evidence with mocked embedder."""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np
import pytest

from amdi.retrieval.methods.dense_method import DenseMethod
from amdi.retrieval.schemas import Query
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_dense_method_scores_by_cosine() -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(
            unit_id=f"u{i}", document_id="d1", page=i,
            bbox=(0, 0, 0.5, 0.1), section="body",
            text=text, embedding=emb,
        )
        for i, (text, emb) in enumerate([
            ("alpha", [1.0, 0.0]),
            ("beta",  [0.0, 1.0]),
            ("gamma", [0.7, 0.7]),
        ])
    ])

    embedder = MagicMock()
    embedder.encode = MagicMock(return_value=np.array([[1.0, 0.0]], dtype=np.float32))
    method = DenseMethod(store, embedder=embedder)  # type: ignore[arg-type]
    out = await method.search(Query(raw="alpha", top_k=3), k=3)
    assert len(out) == 3
    assert out[0].text == "alpha"
    assert out[0].score_dense >= 0.99
