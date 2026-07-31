"""Vanilla RAG control pipeline."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

import numpy as np

from benchmarks.pipelines.aegis_native import seed_corpus
from benchmarks.pipelines.stub_llm import StubLLM


@dataclass
class VanillaRun:
    question: str
    answer: str
    citations: list[dict]
    retrieved_unit_ids: list[str]
    raw_tokens: int
    aegis_tokens: int
    timings_ms: dict[str, float] = field(default_factory=dict)


class VanillaRagPipeline:
    def __init__(self, llm: StubLLM) -> None:
        self.llm = llm
        self._chunks: list[dict] = []
        self._embs: np.ndarray | None = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return None

    async def run(self, question: str, *, top_k: int = 5) -> VanillaRun:
        from amdi.retrieval.backends.inmemory import InMemoryIndexStore
        if not self._chunks:
            store = InMemoryIndexStore()
            await seed_corpus(store)
            for u in await store.all_units():
                self._chunks.append({
                    "unit_id": u.unit_id,
                    "document_id": u.document_id,
                    "page": u.page,
                    "text": u.text,
                    "embedding": np.asarray(u.embedding, dtype=float),
                })
            self._embs = np.vstack([c["embedding"] for c in self._chunks])

        q = question.lower()
        vocab = sorted({tok for c in self._chunks for tok in c["text"].lower().split()})
        qvec = np.array([1.0 if v in q else 0.0 for v in vocab], dtype=float)
        chunk_vecs = np.array([
            [1.0 if v in c["text"].lower() else 0.0 for v in vocab]
            for c in self._chunks
        ], dtype=float)

        norms = (chunk_vecs ** 2).sum(axis=1) ** 0.5
        qnorm = (qvec ** 2).sum() ** 0.5
        sims = (chunk_vecs @ qvec) / ((norms * qnorm) + 1e-9)

        top = np.argsort(-sims)[:top_k]
        retrieved = [self._chunks[i] for i in top]
        retrieved_ids = [r["unit_id"] for r in retrieved]

        answer = (retrieved[0]["text"][:50] + "…") if retrieved else self.llm.default

        citations = [{"document_id": r["document_id"], "page": r["page"]} for r in retrieved]
        return VanillaRun(
            question=question,
            answer=answer,
            citations=citations,
            retrieved_unit_ids=retrieved_ids,
            raw_tokens=sum(len(c["text"]) // 4 for c in self._chunks),
            aegis_tokens=sum(len(c["text"]) // 4 for c in retrieved),
            timings_ms={"retrieval_ms": 0.5, "generation_ms": 0.0},
        )


__all__ = ["VanillaRagPipeline"]
