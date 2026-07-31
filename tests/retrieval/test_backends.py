"""Tests for IndexStore backends, budget trimming, telemetry, and rerankers."""

from __future__ import annotations

import pytest
import numpy as np

from amdi.retrieval.index_store import CorpusUnit
from amdi.retrieval.backends.inmemory import InMemoryIndexStore
from amdi.retrieval.backends.filesystem import FilesystemIndexStore
from amdi.retrieval.backends.faiss_store import FaissIndexStore
from amdi.retrieval.budget import trim_to_budget, estimate_tokens
from amdi.retrieval.telemetry import Telemetry, _pct
from amdi.retrieval.methods.frequency_method import FrequencyMethod
from amdi.retrieval.methods.matrix_method import MatrixMethod
from amdi.retrieval.methods.template_method import TemplateMethod
from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.schemas import Query, Evidence, Citation, RetrievalConfig, RetrievalResult
from amdi.retrieval.reranker import CrossEncoderReranker


@pytest.mark.asyncio
async def test_inmemory_index_store(tmp_path) -> None:
    store = InMemoryIndexStore()
    u1 = CorpusUnit("u1", "doc1", 1, (0, 0, 1, 1), "header", "hello world", [0.1]*384)
    u2 = CorpusUnit("u2", "doc1", 2, (0, 0, 1, 1), "body", "foo bar", [0.2]*384)
    await store.add_units([u1, u2])

    assert await store.size() == 2
    assert len(await store.all_units()) == 2
    assert (await store.get_unit("u1")).text == "hello world"
    assert len(await store.by_document("doc1")) == 2
    await store.commit()


@pytest.mark.asyncio
async def test_filesystem_index_store(tmp_path) -> None:
    store = FilesystemIndexStore(tmp_path)
    u1 = CorpusUnit("u1", "doc1", 1, (0.0, 0.0, 1.0, 1.0), "header", "hello filesystem", [0.1]*10)
    await store.add_units([u1])
    await store.commit()

    assert await store.size() == 1
    assert len(await store.all_units()) == 1
    fetched = await store.get_unit("u1")
    assert fetched is not None
    assert fetched.text == "hello filesystem"
    embs = await store.load_embeddings("doc1")
    assert embs is not None


try:
    import faiss
except ImportError:
    faiss = None


@pytest.mark.skipif(faiss is None, reason="faiss not installed")
@pytest.mark.asyncio
async def test_faiss_index_store(tmp_path) -> None:

    store = FaissIndexStore(tmp_path, dim=4)
    u1 = CorpusUnit("u1", "doc1", 1, (0, 0, 1, 1), "h1", "quantum physics", [1.0, 0.0, 0.0, 0.0])
    await store.add_units([u1])
    assert await store.size() == 1
    assert await store.get_unit("u1") is not None

    scores, ids = await store.search_dense(np.array([1.0, 0.0, 0.0, 0.0]), k=1)
    assert ids == ["u1"]

    scores_b, ids_b = await store.search_bm25("quantum", k=1)
    assert ids_b == ["u1"]


def test_budget_trimming() -> None:
    assert estimate_tokens("12345678") == 2
    ev1 = Evidence(text="Short text", citations=[Citation(document_id="doc1", page=1)])
    ev2 = Evidence(text="Another longer text for budgeting", citations=[Citation(document_id="doc2")])

    res = trim_to_budget([ev1, ev2], budget=100)
    assert "Short text" in res


@pytest.mark.asyncio
async def test_telemetry() -> None:
    tel = Telemetry()
    async with tel.time("test.stage"):
        pass
    tel.incr("my_counter", 5)
    snap = tel.snapshot()
    assert "test.stage.count" in snap
    assert snap["counter.my_counter"] == 5
    assert _pct([], 50) == 0.0


@pytest.mark.asyncio
async def test_frequency_matrix_template_methods() -> None:
    store = InMemoryIndexStore()
    u1 = CorpusUnit("u1", "d1", 1, (0, 0, 1, 1), "header", "Table of contents:\n1. Introduction\n2. Methods\n- Item A\n- Item B\n- Item C")
    u2 = CorpusUnit("u2", "d1", 2, (0, 0, 1, 1), "financials", "Q1 2024 Revenue was $5,000,000 USD on 2024-03-31.")
    await store.add_units([u1, u2])

    freq = FrequencyMethod(store)
    await freq.warmup()
    res_freq = await freq.search(Query(raw="revenue methods"), k=2)
    assert isinstance(res_freq, list)

    mat = MatrixMethod(store)
    res_mat = await mat.search(Query(raw="Revenue 2024 $5,000,000 USD"), k=2)
    assert len(res_mat) >= 1
    assert res_mat[0].score_matrix > 0

    tmpl = TemplateMethod(store)
    res_tmpl = await tmpl.search(Query(raw="table of contents outline"), k=2)
    assert len(res_tmpl) >= 1
    assert res_tmpl[0].score_template > 0


@pytest.mark.asyncio
async def test_fusion_strategies_and_dedup_helpers() -> None:
    from amdi.retrieval.fusion import fuse, weighted_sum_fuse
    from amdi.retrieval.deduplication import normalize, content_hash
    from amdi.retrieval.schemas import RetrievalConfig, Evidence, Citation

    assert normalize("  Hello   World  ") == "hello world"
    assert len(content_hash("hello world")) == 64

    e1 = Evidence(text="text 1", score_bm25=0.8, citations=[Citation(document_id="d1")])
    e1.metadata["unit_id"] = "u1"
    e2 = Evidence(text="text 2", score_bm25=0.4, citations=[Citation(document_id="d2")])
    e2.metadata["unit_id"] = "u2"

    method_res = {"bm25": [e1, e2]}
    w_fused = weighted_sum_fuse(method_res)
    assert len(w_fused) == 2

    cfg_rrf = RetrievalConfig(fusion="rrf")
    assert len(fuse(method_res, cfg_rrf)) == 2

    cfg_w = RetrievalConfig(fusion="weighted")
    assert len(fuse(method_res, cfg_w)) == 2

    cfg_cal = RetrievalConfig(fusion="calibrated")
    assert len(fuse(method_res, cfg_cal)) == 2

    with pytest.raises(ValueError):
        fuse(method_res, RetrievalConfig(fusion="invalid"))  # type: ignore[arg-type]


@pytest.mark.asyncio
async def test_hybrid_retriever_with_different_fusion() -> None:
    from amdi.retrieval.hybrid import HybridRetriever, _aggregate_score
    from amdi.retrieval.schemas import Query, RetrievalConfig
    store = InMemoryIndexStore()
    u1 = CorpusUnit("u1", "doc1", 1, (0, 0, 1, 1), "Abstract", "quantum physics and einstein relativity", [1.0]*384)
    await store.add_units([u1])

    cfg = RetrievalConfig(enable_reranker=False, fusion="calibrated")
    retriever = HybridRetriever(store, config=cfg)
    await retriever.warmup()

    res = await retriever.search(Query(raw="quantum einstein", top_k=1))
    assert res.evidence
    await retriever.aclose()

    score = _aggregate_score(res.evidence[0])
    assert score >= 0.0

