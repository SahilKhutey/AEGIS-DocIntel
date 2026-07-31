"""Reranker reduces to identity when disabled, normalizes when enabled."""

from __future__ import annotations

import pytest

from amdi.retrieval.reranker import (
    CrossEncoderReranker,
    NoOpReranker,
    make_reranker,
)
from amdi.retrieval.schemas import RetrievalConfig


@pytest.mark.asyncio
async def test_noop_returns_ones() -> None:
    rr = NoOpReranker()
    scores = await rr.score("anything", ["a", "b", "c"])
    assert scores == [1.0, 1.0, 1.0]


@pytest.mark.asyncio
async def test_reranker_factory_respects_flag() -> None:
    assert isinstance(make_reranker(RetrievalConfig(enable_reranker=False)), NoOpReranker)
    assert isinstance(make_reranker(RetrievalConfig(enable_reranker=True)), CrossEncoderReranker)
