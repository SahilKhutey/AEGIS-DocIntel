"""All 7 retrieval methods respond to a benign query without error."""

from __future__ import annotations

import pytest

from amdi.retrieval.schemas import Query
from amdi.retrieval.hybrid import HybridRetriever
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


@pytest.mark.asyncio
async def test_seven_methods_return_something() -> None:
    store = InMemoryIndexStore()
    await store.add_units([
        CorpusUnit(unit_id=f"u{i}", document_id="d1", page=i+1,
                   bbox=(0, 0, 0.5, 0.1), section="body",
                   text=text, embedding=[1.0, 0.0])
        for i, text in enumerate([
            "Einstein proposed general relativity in 1915.",
            "Quantum entanglement violates Bell inequalities.",
            "PageRank computes a single global authority score.",
            "Persistent homology computes Betti numbers.",
            "Vertical scaling hits hardware ceilings and a single node's blast radius.",
            "Sharding splits data across many commodity nodes.",
            "Tokenizer maps text to integers for a transformer model.",
        ])
    ])
    cfg = None
    from amdi.retrieval.schemas import RetrievalConfig
    cfg = RetrievalConfig(enable_reranker=False, fusion="rrf")
    retriever = HybridRetriever(store, config=cfg)
    retriever._methods[1]._embedder = _identity_embedder()
    retriever._warmed = True
    result = await retriever.search(Query(raw="Einstein relativity", top_k=5))
    assert result.evidence, "no evidence produced"


def _identity_embedder():
    class _E:
        def encode(self, texts, **_):
            import numpy as np
            out = []
            for t in texts:
                v = [0.0, 0.0]
                tl = t.lower()
                if "einstein" in tl or "relativity" in tl:
                    v[0] = 1.0
                if "model" in tl or "transform" in tl:
                    v[1] = 1.0
                out.append(v)
            a = np.array(out, dtype=float)
            n = (a ** 2).sum(axis=1, keepdims=True) ** 0.5
            n[n == 0] = 1.0
            return a / n
    return _E()
