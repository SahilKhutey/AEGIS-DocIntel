"""Hybrid 7-Method Retrieval — top-level orchestrator."""

from __future__ import annotations

import asyncio
import logging
import time
from typing import Any

from amdi.config import get_settings
from amdi.retrieval import fusion
from amdi.retrieval.deduplication import deduplicate
from amdi.retrieval.methods.base import BaseRetrievalMethod
from amdi.retrieval.methods.bm25_method import BM25Method
from amdi.retrieval.methods.dense_method import DenseMethod
from amdi.retrieval.methods.frequency_method import FrequencyMethod
from amdi.retrieval.methods.geometry_method import GeometryMethod
from amdi.retrieval.methods.graph_method import GraphMethod
from amdi.retrieval.methods.matrix_method import MatrixMethod
from amdi.retrieval.methods.template_method import TemplateMethod
from amdi.retrieval.reranker import make_reranker
from amdi.retrieval.schemas import (
    Evidence,
    Query,
    RetrievalConfig,
    RetrievalResult,
)
from amdi.retrieval.telemetry import Telemetry

logger = logging.getLogger("amdi.retrieval")


class HybridRetriever:
    def __init__(
        self,
        store: Any,
        *,
        config: RetrievalConfig | None = None,
    ) -> None:
        self._store = store
        self._settings = get_settings()
        self._config = config or RetrievalConfig(
            enable_reranker=self._settings.enable_reranker,
            reranker_model=self._settings.reranker_model,
        )
        self._reranker = make_reranker(self._config)
        self._methods: list[BaseRetrievalMethod] = self._build_methods()
        self._warmed = False
        self._tel = Telemetry()

    def _build_methods(self) -> list[BaseRetrievalMethod]:
        bm25_getter = (
            self._store.bm25_or_none
            if hasattr(self._store, "bm25_or_none") else (lambda: None)
        )
        methods: list[BaseRetrievalMethod] = [
            BM25Method(self._store, bm25_getter),
            DenseMethod(self._store, model_name=self._settings.embedding_model),
            FrequencyMethod(self._store),
            GeometryMethod(self._store),
            GraphMethod(self._store),
            MatrixMethod(self._store),
            TemplateMethod(self._store),
        ]
        return methods

    async def warmup(self) -> None:
        if self._warmed:
            return
        await asyncio.gather(*(m.warmup() for m in self._methods))
        self._warmed = True
        logger.info("retriever.warmup.done methods=%s", [m.name for m in self._methods])

    async def search(self, query: Query) -> RetrievalResult:
        if not self._warmed:
            await self.warmup()

        t0 = time.perf_counter()
        method_results: dict[str, list[Evidence]] = {}

        async def _safe(name: str, m: BaseRetrievalMethod) -> tuple[str, list[Evidence]]:
            try:
                async with self._tel.time(f"method.{name}"):
                    res = await m.timed_search(query, self._config.candidate_pool_size)
                return name, res
            except Exception as exc:  # noqa: BLE001
                logger.warning("method.failed method=%s error=%s", name, str(exc))
                return name, []

        async with self._tel.time("stage.fanout"):
            outcomes = await asyncio.gather(
                *(_safe(m.name, m) for m in self._methods),
                return_exceptions=False,
            )
        for name, items in outcomes:
            method_results[name] = items
            self._tel.incr(f"results.{name}", len(items))

        # Fusion
        t_fuse0 = time.perf_counter()
        fused = fusion.fuse(method_results, self._config)
        self._tel.latencies_ms["stage.fusion"].append(
            (time.perf_counter() - t_fuse0) * 1000.0
        )
        self._tel.incr("results.fused", len(fused))

        # Dedup
        t_dd0 = time.perf_counter()
        if self._config.enable_dedup:
            fused = deduplicate(
                fused,
                simhash_threshold=self._config.dedup_simhash_threshold,
                keep="highest_fused",
            )
        self._tel.latencies_ms["stage.dedup"].append(
            (time.perf_counter() - t_dd0) * 1000.0
        )

        # Rerank top-N
        t_rr0 = time.perf_counter()
        if self._config.enable_reranker and self._config.reranker_top_n:
            head = fused[: self._config.reranker_top_n]
            tail = fused[self._config.reranker_top_n :]
            scores = await self._reranker.score(
                query.raw, [e.text for e in head]
            )
            if scores:
                lo, hi = min(scores), max(scores)
                span = (hi - lo) or 1.0
                for e, s in zip(head, scores, strict=False):
                    e.score_rerank = (s - lo) / span
            head.sort(
                key=lambda e: (e.score_rerank if e.score_rerank is not None
                               else e.score_fused),
                reverse=True,
            )
            fused = head + tail
        self._tel.latencies_ms["stage.rerank"].append(
            (time.perf_counter() - t_rr0) * 1000.0
        )

        # Trim to top_k
        fused = fused[: query.top_k]

        for ev in fused:
            ev.score_fused = _aggregate_score(ev)

        result = RetrievalResult(
            query=query,
            evidence=fused,
            timings_ms={k: round(v[0] if isinstance(v, list) and v else float(v or 0.0), 3)
                        for k, v in self._tel.latencies_ms.items()},
            counters=dict(self._tel.counters),
        )
        result.timings_ms["total_ms"] = round((time.perf_counter() - t0) * 1000.0, 3)
        return result

    async def aclose(self) -> None:
        for m in self._methods:
            await m.aclose()
        await self._reranker.aclose()


def _aggregate_score(ev: Evidence) -> float:
    components = [
        ev.score_fused,
        ev.score_rerank if ev.score_rerank is not None else ev.score_fused,
    ]
    votes = sum(len(c.method_votes) for c in ev.citations)
    return max(components) + 0.02 * min(votes, 10)


__all__ = ["HybridRetriever"]
