"""HybridRetriever orchestrates 7 methods, fuses, dedupes, and reranks."""

from __future__ import annotations

import asyncio
import numpy as np
import pytest

from amdi.retrieval import HybridRetriever
from amdi.retrieval.schemas import Query, RetrievalConfig, RetrievalResult
from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore


class _FakeEmbedder:
    """Constant embedder: returns a normalized vector for any text."""
    def encode(self, texts, **_):
        out = []
        for t in texts:
            v = [0.0, 0.0]
            tl = t.lower()
            if "einstein" in tl or "quantum" in tl:
                v[0] = 1.0
            if "model" in tl or "transform" in tl:
                v[1] = 1.0
            out.append(v)
        a = np.array(out, dtype=float)
        norms = (a ** 2).sum(axis=1, keepdims=True) ** 0.5
        norms[norms == 0] = 1.0
        return a / norms


@pytest.mark.asyncio
async def test_hybrid_returns_evidence_with_telemetry(monkeypatch, tmp_path) -> None:
    store = InMemoryIndexStore()
    units = []
    for i, text in enumerate([
        "Quantum entanglement links Schrödinger and Einstein in modern physics.",
        "Einstein disagreed with the Copenhagen interpretation of quantum mechanics.",
        "Italian cuisine features regional pasta and olive oil daily.",
        "Transformers are sequence models that use self-attention layers.",
        "The cat sat on the mat watching the rain pour.",
    ]):
        units.append(CorpusUnit(
            unit_id=f"u{i}", document_id="doc1", page=1,
            bbox=(0.0, float(i) * 0.1, 0.8, 0.08),
            section="body" if i < 4 else "misc",
            text=text,
            embedding=[1.0 if "quantum" in text or "einstein" in text else 0.0,
                       1.0 if "model" in text or "transform" in text else 0.0],
        ))
    await store.add_units(units)

    cfg = RetrievalConfig(enable_reranker=False, fusion="rrf")
    retriever = HybridRetriever(store, config=cfg)
    retriever._methods[1]._embedder = _FakeEmbedder()  # type: ignore[assignment]
    retriever._warmed = True

    result = await retriever.search(
        Query(raw="Einstein quantum", top_k=5)
    )
    assert isinstance(result, RetrievalResult)
    assert result.evidence, "fused evidence must not be empty"
    assert any("Einstein" in e.text for e in result.evidence)
    assert "stage.fanout" in result.timings_ms
    assert "stage.fusion" in result.timings_ms
    assert "stage.dedup"  in result.timings_ms
    assert "stage.rerank" in result.timings_ms
    assert result.timings_ms["total_ms"] > 0
