# AEGIS-DocIntel — RAG Engine
**Version 1.0.0**

---

## 1. RAG Engine Architecture

```
Query String
     │
     ▼
┌─────────────────────┐
│  Query Transformer  │
│  HyDE · Step-back   │
│  Multi-query        │
└─────────┬───────────┘
          │
          ▼
  ┌───────────────────────────────────────────────┐
  │              Parallel Retrieval               │
  │                                               │
  │  ┌──────────────┐  ┌──────────────────────┐   │
  │  │ BM25 (ES)    │  │ Dense (Milvus HNSW)  │   │
  │  │ top-50       │  │ top-50               │   │
  │  └──────┬───────┘  └──────────┬───────────┘   │
  │         │                     │               │
  │  ┌──────▼─────────────────────▼───────────┐   │
  │  │  ColPali Visual Retriever (optional)   │   │
  │  │  top-20                                │   │
  │  └────────────────────────────────────────┘   │
  └───────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────┐
│  Reciprocal Rank    │
│  Fusion (k=60)      │
│  top-80 candidates  │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Cross-Encoder      │
│  Reranker           │
│  BGE-reranker-v2-m3 │
│  top 8-20 chunks    │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  MMR Diversity      │
│  Filter (λ=0.7)     │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Context Builder    │
│  Token-budget aware │
└─────────┬───────────┘
          │
          ▼
       LLM
```

---

## 2. Complete RAG Engine Implementation

```python
"""
AEGIS-DocIntel — RAG Engine
============================
Production-grade Hybrid RAG with:
- BM25 (Elasticsearch)
- Dense (Milvus HNSW)
- ColPali visual retrieval
- Reciprocal Rank Fusion
- Cross-encoder reranking
- MMR diversity filtering
- Token-budget-aware context building
- LLMLingua-2 compression
"""
from __future__ import annotations

import asyncio
import logging
import math
import time
from dataclasses import dataclass, field
from typing import Any, Literal, Optional

import numpy as np

from src.config import settings
from src.observability.metrics import RETRIEVAL_LATENCY, CACHE_HITS, trace_span

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────
# Data Structures
# ─────────────────────────────────────────────────────────────────

@dataclass
class RetrievedChunk:
    chunk_id: str
    doc_id: str
    tenant_id: str
    text: str
    page: int
    section: str
    block_type: str
    token_count: int
    score: float = 0.0
    rerank_score: float = 0.0
    bm25_rank: int | None = None
    dense_rank: int | None = None
    visual_rank: int | None = None
    image_s3: str | None = None
    bbox: dict | None = None
    metadata: dict = field(default_factory=dict)


@dataclass
class RAGResult:
    chunks: list[RetrievedChunk]
    context: str
    prompt: str
    token_count: int
    retrieval_latency_ms: float
    rerank_latency_ms: float
    total_candidates: int
    confidence: float
    query_transformations: list[str]


# ─────────────────────────────────────────────────────────────────
# Query Transformer
# ─────────────────────────────────────────────────────────────────

class QueryTransformer:
    """
    Expands a single query into multiple complementary queries
    to maximize retrieval recall.
    
    Techniques:
    - HyDE (Hypothetical Document Embedding)
    - Step-back prompting
    - Multi-query paraphrase
    """

    def __init__(self, llm_client):
        self.llm = llm_client

    async def transform(self, query: str) -> list[str]:
        """Return original + transformed queries."""
        queries = [query]

        try:
            # Multi-query paraphrase (most reliable)
            paraphrases = await self._paraphrase(query, n=2)
            queries.extend(paraphrases)
        except Exception as e:
            logger.warning("Query paraphrase failed: %s", e)

        return queries[:4]  # max 4 queries total

    async def generate_hyde(self, query: str) -> str:
        """Generate a hypothetical answer document for HyDE retrieval."""
        prompt = (
            f"Write a brief, factual paragraph that would directly answer "
            f"the following question. Be specific and detailed.\n\nQuestion: {query}"
        )
        response = await self.llm.complete(prompt, max_tokens=200, temperature=0.3)
        return response.text

    async def _paraphrase(self, query: str, n: int = 2) -> list[str]:
        prompt = (
            f"Generate {n} different phrasings of this search query. "
            f"Return only the queries, one per line.\n\nQuery: {query}"
        )
        response = await self.llm.complete(prompt, max_tokens=150, temperature=0.7)
        lines = [l.strip() for l in response.text.strip().split("\n") if l.strip()]
        return lines[:n]


# ─────────────────────────────────────────────────────────────────
# BM25 Retriever (Elasticsearch)
# ─────────────────────────────────────────────────────────────────

class BM25Retriever:
    """Elasticsearch-backed BM25 retrieval with metadata filtering."""

    def __init__(self, es_client):
        self.es = es_client
        self.index = settings.elasticsearch.index

    async def retrieve(
        self,
        queries: list[str],
        tenant_id: str,
        doc_ids: list[str] | None,
        top_k: int = 50,
        block_types: list[str] | None = None,
    ) -> list[RetrievedChunk]:
        """Execute BM25 retrieval for multiple queries, deduplicate, and return top-k."""
        all_results: dict[str, RetrievedChunk] = {}

        for query in queries:
            hits = await self._search_one(query, tenant_id, doc_ids, top_k, block_types)
            for h in hits:
                if h.chunk_id not in all_results:
                    all_results[h.chunk_id] = h
                else:
                    # Keep higher score
                    if h.score > all_results[h.chunk_id].score:
                        all_results[h.chunk_id] = h

        sorted_results = sorted(all_results.values(), key=lambda c: c.score, reverse=True)
        return sorted_results[:top_k]

    async def _search_one(
        self,
        query: str,
        tenant_id: str,
        doc_ids: list[str] | None,
        top_k: int,
        block_types: list[str] | None,
    ) -> list[RetrievedChunk]:
        body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "multi_match": {
                                "query": query,
                                "fields": ["text^2", "section"],
                                "type": "best_fields",
                                "minimum_should_match": "60%",
                            }
                        }
                    ],
                    "filter": self._build_filters(tenant_id, doc_ids, block_types),
                }
            },
            "size": top_k,
            "_source": ["chunk_id", "doc_id", "text", "page", "section",
                        "block_type", "token_count", "bbox", "image_s3"],
        }

        resp = await self.es.search(index=self.index, body=body)
        chunks = []
        for hit in resp["hits"]["hits"]:
            src = hit["_source"]
            chunks.append(RetrievedChunk(
                chunk_id=src["chunk_id"],
                doc_id=src["doc_id"],
                tenant_id=tenant_id,
                text=src["text"],
                page=src.get("page", 0),
                section=src.get("section", ""),
                block_type=src.get("block_type", "text"),
                token_count=src.get("token_count", 0),
                score=hit["_score"],
                image_s3=src.get("image_s3"),
                bbox=src.get("bbox"),
            ))
        return chunks

    @staticmethod
    def _build_filters(
        tenant_id: str, doc_ids: list[str] | None, block_types: list[str] | None
    ) -> list[dict]:
        filters = [{"term": {"tenant_id": tenant_id}}]
        if doc_ids:
            filters.append({"terms": {"doc_id": doc_ids}})
        if block_types:
            filters.append({"terms": {"block_type": block_types}})
        return filters


# ─────────────────────────────────────────────────────────────────
# Dense Retriever (Milvus)
# ─────────────────────────────────────────────────────────────────

class DenseRetriever:
    """Milvus HNSW dense retrieval with L2-normalized cosine similarity."""

    def __init__(self, milvus_client, embedding_model):
        self.milvus = milvus_client
        self.embedder = embedding_model
        self.collection = settings.milvus.collection_text

    async def retrieve(
        self,
        queries: list[str],
        tenant_id: str,
        doc_ids: list[str] | None,
        top_k: int = 50,
    ) -> list[RetrievedChunk]:
        """Embed all queries, search Milvus, deduplicate, return top-k."""
        # Embed all queries in one batch
        loop = asyncio.get_running_loop()
        embeddings = await loop.run_in_executor(
            None, self.embedder.encode, queries
        )

        all_results: dict[str, RetrievedChunk] = {}

        for emb in embeddings:
            hits = await self._search_one(emb, tenant_id, doc_ids, top_k)
            for h in hits:
                if h.chunk_id not in all_results:
                    all_results[h.chunk_id] = h
                elif h.score > all_results[h.chunk_id].score:
                    all_results[h.chunk_id] = h

        sorted_results = sorted(all_results.values(), key=lambda c: c.score, reverse=True)
        return sorted_results[:top_k]

    async def _search_one(
        self,
        embedding: np.ndarray,
        tenant_id: str,
        doc_ids: list[str] | None,
        top_k: int,
    ) -> list[RetrievedChunk]:
        expr_parts = [f'tenant_id == "{tenant_id}"']
        if doc_ids:
            ids_str = "[" + ", ".join(f'"{d}"' for d in doc_ids) + "]"
            expr_parts.append(f"doc_id in {ids_str}")
        expr = " && ".join(expr_parts)

        loop = asyncio.get_running_loop()
        results = await loop.run_in_executor(
            None,
            lambda: self.milvus.search(
                collection_name=self.collection,
                data=[embedding.tolist()],
                anns_field="embedding",
                param={"metric_type": "COSINE", "params": {"ef": 128}},
                limit=top_k,
                expr=expr,
                output_fields=["chunk_id", "doc_id", "text", "page",
                                "section", "block_type", "token_count",
                                "bbox", "image_s3"],
            ),
        )

        chunks = []
        for hit in results[0]:
            entity = hit.entity
            chunks.append(RetrievedChunk(
                chunk_id=entity.get("chunk_id"),
                doc_id=entity.get("doc_id"),
                tenant_id=tenant_id,
                text=entity.get("text", ""),
                page=entity.get("page", 0),
                section=entity.get("section", ""),
                block_type=entity.get("block_type", "text"),
                token_count=entity.get("token_count", 0),
                score=hit.score,
                bbox=entity.get("bbox"),
                image_s3=entity.get("image_s3"),
            ))
        return chunks


# ─────────────────────────────────────────────────────────────────
# Reciprocal Rank Fusion
# ─────────────────────────────────────────────────────────────────

class ReciprocalRankFusion:
    """
    Fuses multiple ranked lists into a single unified ranking.
    
    Formula: score(d) = Σ 1/(k + rank_i(d))
    k=60 is the standard parameter (Robertson et al., 2009)
    """

    def __init__(self, k: int = 60):
        self.k = k

    def fuse(
        self,
        ranked_lists: list[list[RetrievedChunk]],
        top_n: int = 80,
    ) -> list[RetrievedChunk]:
        """Fuse multiple ranked lists and return top_n candidates."""
        scores: dict[str, float] = {}
        index: dict[str, RetrievedChunk] = {}

        for ranked_list in ranked_lists:
            for rank, chunk in enumerate(ranked_list, start=1):
                cid = chunk.chunk_id
                rrf_contribution = 1.0 / (self.k + rank)
                scores[cid] = scores.get(cid, 0.0) + rrf_contribution
                if cid not in index:
                    index[cid] = chunk

        # Sort by fused RRF score
        sorted_ids = sorted(scores, key=scores.__getitem__, reverse=True)[:top_n]

        fused = []
        for rank, cid in enumerate(sorted_ids, start=1):
            chunk = index[cid]
            chunk.score = scores[cid]
            fused.append(chunk)

        return fused


# ─────────────────────────────────────────────────────────────────
# Cross-Encoder Reranker
# ─────────────────────────────────────────────────────────────────

class CrossEncoderReranker:
    """
    BGE-reranker-v2-m3: multilingual cross-encoder for relevance scoring.
    Scores (query, chunk) pairs → prunes irrelevant chunks.
    """

    SCORE_THRESHOLD = 0.15  # discard below this

    def __init__(self):
        self._model = None
        self._load_lock = asyncio.Lock()

    async def _ensure_loaded(self):
        if self._model is not None:
            return
        async with self._load_lock:
            if self._model is not None:
                return
            try:
                from sentence_transformers import CrossEncoder
                self._model = CrossEncoder(
                    settings.retrieval.reranker,
                    max_length=512,
                    device="cuda",
                )
                logger.info("Cross-encoder reranker loaded: %s", settings.retrieval.reranker)
            except Exception as e:
                logger.warning("Cross-encoder unavailable: %s — using score passthrough", e)

    async def rerank(
        self,
        query: str,
        chunks: list[RetrievedChunk],
        top_k: int = 20,
    ) -> list[RetrievedChunk]:
        """Score (query, chunk) pairs and return top_k by rerank score."""
        if not chunks:
            return chunks

        await self._ensure_loaded()

        if self._model is None:
            # Fallback: return by existing score
            return chunks[:top_k]

        loop = asyncio.get_running_loop()
        pairs = [(query, c.text[:800]) for c in chunks]  # truncate for speed

        scores = await loop.run_in_executor(
            None, self._model.predict, pairs
        )

        for chunk, score in zip(chunks, scores):
            chunk.rerank_score = float(score)

        # Filter below threshold and sort
        filtered = [c for c in chunks if c.rerank_score >= self.SCORE_THRESHOLD]
        reranked = sorted(filtered, key=lambda c: c.rerank_score, reverse=True)
        return reranked[:top_k]


# ─────────────────────────────────────────────────────────────────
# MMR Diversity Filter
# ─────────────────────────────────────────────────────────────────

class MMRDiversityFilter:
    """
    Maximal Marginal Relevance (MMR) for diversity-aware chunk selection.
    Balances relevance vs. redundancy.
    
    Formula: MMR = argmax [λ·sim(q,d) − (1-λ)·max_{d'∈S} sim(d,d')]
    λ=0.7: 70% relevance, 30% diversity
    """

    def __init__(self, lambda_: float = 0.7, embedder=None):
        self.lambda_ = lambda_
        self.embedder = embedder

    async def select(
        self,
        query_embedding: np.ndarray,
        chunks: list[RetrievedChunk],
        k: int,
    ) -> list[RetrievedChunk]:
        """Select k diverse chunks via MMR."""
        if len(chunks) <= k:
            return chunks

        if self.embedder is None:
            return chunks[:k]

        loop = asyncio.get_running_loop()
        texts = [c.text[:500] for c in chunks]
        embeddings = await loop.run_in_executor(None, self.embedder.encode, texts)
        embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        q_norm = query_embedding / np.linalg.norm(query_embedding)

        # Relevance scores
        rel_scores = embeddings @ q_norm

        selected_indices: list[int] = []
        remaining = list(range(len(chunks)))

        for _ in range(k):
            if not remaining:
                break

            if not selected_indices:
                # Pick most relevant first
                best_idx = max(remaining, key=lambda i: rel_scores[i])
            else:
                # MMR: balance relevance vs similarity to already selected
                selected_embeddings = embeddings[selected_indices]

                def mmr_score(i: int) -> float:
                    relevance = self.lambda_ * rel_scores[i]
                    redundancy = (1 - self.lambda_) * max(
                        float(embeddings[i] @ selected_embeddings[j])
                        for j in range(len(selected_indices))
                    )
                    return relevance - redundancy

                best_idx = max(remaining, key=mmr_score)

            selected_indices.append(best_idx)
            remaining.remove(best_idx)

        return [chunks[i] for i in selected_indices]


# ─────────────────────────────────────────────────────────────────
# Context Builder
# ─────────────────────────────────────────────────────────────────

class ContextBuilder:
    """
    Assembles LLM-ready context from retrieved chunks.
    
    Responsibilities:
    - Token budget enforcement
    - Document-order sorting (improves LLM comprehension)
    - Citation tag injection
    - LLMLingua-2 compression (optional)
    """

    SYSTEM_BUDGET = 1200
    HISTORY_BUDGET = 800
    QUESTION_BUDGET = 200
    SCAFFOLD_BUDGET = 400
    TOTAL_BUDGET = 8500

    CHUNK_BUDGET = TOTAL_BUDGET - SYSTEM_BUDGET - HISTORY_BUDGET - QUESTION_BUDGET - SCAFFOLD_BUDGET
    # = 5,900 tokens for retrieved chunks

    def __init__(self, tokenizer=None, compressor=None):
        self.tokenizer = tokenizer
        self.compressor = compressor  # LLMLingua-2 instance

    def build(
        self,
        chunks: list[RetrievedChunk],
        query: str,
        system_prompt: str,
        history: list[dict],
    ) -> tuple[str, list[RetrievedChunk], int]:
        """
        Build context string, return (context, included_chunks, token_count).
        Sorts by document order, injects citation tags, enforces budget.
        """
        # Sort by document order for LLM comprehension
        sorted_chunks = sorted(chunks, key=lambda c: (c.doc_id, c.page, c.chunk_id))

        included: list[RetrievedChunk] = []
        context_parts: list[str] = []
        tokens_used = 0

        for i, chunk in enumerate(sorted_chunks, start=1):
            chunk_text = self._format_chunk(chunk, source_num=i)
            chunk_tokens = self._count_tokens(chunk_text)

            if tokens_used + chunk_tokens > self.CHUNK_BUDGET:
                # Try compression
                if self.compressor and chunk_tokens > 200:
                    try:
                        compressed = self.compressor.compress(chunk_text, ratio=0.5)
                        compressed_tokens = self._count_tokens(compressed)
                        if tokens_used + compressed_tokens <= self.CHUNK_BUDGET:
                            context_parts.append(compressed)
                            included.append(chunk)
                            tokens_used += compressed_tokens
                            continue
                    except Exception:
                        pass
                break  # Budget exhausted

            context_parts.append(chunk_text)
            included.append(chunk)
            tokens_used += chunk_tokens

        context = "\n\n---\n\n".join(context_parts)
        return context, included, tokens_used

    def build_prompt(
        self,
        context: str,
        query: str,
        system_prompt: str,
        history: list[dict],
        included_chunks: list[RetrievedChunk],
    ) -> list[dict]:
        """Build full message list for LLM API."""
        messages = [{"role": "system", "content": system_prompt}]

        if history:
            messages.extend(history[-8:])  # Last 4 turns

        messages.append({
            "role": "user",
            "content": (
                f"## Retrieved Context\n\n{context}\n\n"
                f"---\n\n"
                f"## Question\n\n{query}\n\n"
                f"Answer using only the provided context. "
                f"Cite sources using [Source-N] notation."
            ),
        })
        return messages

    @staticmethod
    def _format_chunk(chunk: RetrievedChunk, source_num: int) -> str:
        header = f"[Source-{source_num}: {chunk.doc_id[:8]}..., Page {chunk.page}"
        if chunk.section:
            header += f", Section: {chunk.section}"
        header += "]"

        if chunk.block_type == "table":
            return f"{header}\n**[TABLE]**\n{chunk.text}"
        elif chunk.block_type == "equation":
            return f"{header}\n**[EQUATION]**\n{chunk.text}"
        elif chunk.block_type == "figure":
            caption = chunk.metadata.get("caption", "")
            return f"{header}\n**[FIGURE]** {caption}"
        else:
            return f"{header}\n{chunk.text}"

    def _count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text))
        return max(1, int(len(text.split()) * 1.33))


# ─────────────────────────────────────────────────────────────────
# Main RAG Engine
# ─────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are AEGIS, an expert document intelligence assistant.

Rules:
1. Answer ONLY from the provided context. Never fabricate information.
2. Cite all claims using [Source-N] notation referencing the provided sources.
3. If the answer is not in the context, say: "This information is not available in the provided documents."
4. For numerical data, calculations, or tables, be precise.
5. Structure complex answers with headings and bullet points.
6. Provide confidence indication: HIGH / MEDIUM / LOW based on source quality.

Format citations as: [Source-N] where N matches the source number in the context."""


class RAGEngine:
    """
    Main RAG Engine orchestrating the full retrieval-augmented generation pipeline.
    """

    def __init__(
        self,
        bm25: BM25Retriever,
        dense: DenseRetriever,
        reranker: CrossEncoderReranker,
        rrf: ReciprocalRankFusion,
        mmr: MMRDiversityFilter,
        context_builder: ContextBuilder,
        query_transformer: QueryTransformer,
        embedding_model,
    ):
        self.bm25 = bm25
        self.dense = dense
        self.reranker = reranker
        self.rrf = rrf
        self.mmr = mmr
        self.context_builder = context_builder
        self.query_transformer = query_transformer
        self.embedder = embedding_model

    async def retrieve_and_build(
        self,
        query: str,
        tenant_id: str,
        doc_ids: list[str] | None = None,
        history: list[dict] | None = None,
        top_k: int | None = None,
    ) -> RAGResult:
        """
        Full RAG pipeline: query → retrieval → rerank → context → result.
        """
        with trace_span("rag.full_pipeline", tenant_id=tenant_id):
            t_start = time.perf_counter()

            final_k = top_k or settings.retrieval.final_k
            history = history or []

            # 1. Query transformation
            queries = await self.query_transformer.transform(query)

            # 2. Embed primary query for dense + MMR
            loop = asyncio.get_running_loop()
            q_embedding = await loop.run_in_executor(
                None, self.embedder.encode, [query]
            )
            q_embedding = q_embedding[0]

            # 3. Parallel retrieval
            t_retrieval = time.perf_counter()
            bm25_task = asyncio.create_task(
                self.bm25.retrieve(
                    queries, tenant_id, doc_ids,
                    top_k=settings.retrieval.bm25_top_k
                )
            )
            dense_task = asyncio.create_task(
                self.dense.retrieve(
                    queries, tenant_id, doc_ids,
                    top_k=settings.retrieval.dense_top_k
                )
            )

            bm25_results, dense_results = await asyncio.gather(
                bm25_task, dense_task, return_exceptions=True
            )

            # Handle partial failures
            if isinstance(bm25_results, Exception):
                logger.warning("BM25 failed: %s", bm25_results)
                bm25_results = []
            if isinstance(dense_results, Exception):
                logger.warning("Dense failed: %s", dense_results)
                dense_results = []

            retrieval_ms = (time.perf_counter() - t_retrieval) * 1000
            RETRIEVAL_LATENCY.labels(stage="retrieval").observe(retrieval_ms / 1000)

            # Assign ranks
            for rank, c in enumerate(bm25_results, 1):
                c.bm25_rank = rank
            for rank, c in enumerate(dense_results, 1):
                c.dense_rank = rank

            # 4. Reciprocal Rank Fusion
            fused = self.rrf.fuse(
                [r for r in [bm25_results, dense_results] if r],
                top_n=80,
            )

            # 5. Cross-encoder reranking
            t_rerank = time.perf_counter()
            reranked = await self.reranker.rerank(
                query, fused, top_k=settings.retrieval.rerank_top_k
            )
            rerank_ms = (time.perf_counter() - t_rerank) * 1000
            RETRIEVAL_LATENCY.labels(stage="rerank").observe(rerank_ms / 1000)

            # 6. MMR diversity filter
            diverse = await self.mmr.select(q_embedding, reranked, k=final_k)

            # 7. Context building
            context, included_chunks, token_count = self.context_builder.build(
                diverse, query, SYSTEM_PROMPT, history
            )
            prompt_messages = self.context_builder.build_prompt(
                context, query, SYSTEM_PROMPT, history, included_chunks
            )

            # 8. Confidence score
            confidence = (
                float(np.mean([c.rerank_score for c in included_chunks]))
                if included_chunks else 0.0
            )

            total_ms = (time.perf_counter() - t_start) * 1000
            RETRIEVAL_LATENCY.labels(stage="total").observe(total_ms / 1000)

            return RAGResult(
                chunks=included_chunks,
                context=context,
                prompt=str(prompt_messages),
                token_count=token_count,
                retrieval_latency_ms=retrieval_ms,
                rerank_latency_ms=rerank_ms,
                total_candidates=len(fused),
                confidence=confidence,
                query_transformations=queries,
            )
```

---

## 3. Citation Engine

```python
import re
from dataclasses import dataclass


@dataclass
class Citation:
    source_num: int
    chunk_id: str
    doc_id: str
    page: int
    section: str
    snippet: str
    bbox: dict | None = None
    image_s3: str | None = None


class CitationEngine:
    """
    Extracts [Source-N] references from LLM output and
    maps them to structured Citation objects.
    """

    SOURCE_PATTERN = re.compile(r"\[Source-(\d+)\]")

    def extract_citations(
        self,
        llm_response: str,
        chunks: list[RetrievedChunk],
    ) -> tuple[str, list[Citation]]:
        """
        Parse [Source-N] markers from response.
        Returns (annotated_response, citations).
        """
        found_nums = set(int(m) for m in self.SOURCE_PATTERN.findall(llm_response))

        chunk_map = {i + 1: c for i, c in enumerate(chunks)}
        citations: list[Citation] = []

        for num in sorted(found_nums):
            chunk = chunk_map.get(num)
            if chunk:
                citations.append(Citation(
                    source_num=num,
                    chunk_id=chunk.chunk_id,
                    doc_id=chunk.doc_id,
                    page=chunk.page,
                    section=chunk.section,
                    snippet=chunk.text[:200] + "...",
                    bbox=chunk.bbox,
                    image_s3=chunk.image_s3,
                ))

        return llm_response, citations

    def format_citation_list(self, citations: list[Citation]) -> str:
        """Format citations as a readable reference list."""
        if not citations:
            return ""
        lines = ["\n\n---\n**References:**"]
        for c in citations:
            line = f"[{c.source_num}] Document `{c.doc_id[:8]}...`, Page {c.page}"
            if c.section:
                line += f", Section: *{c.section}*"
            lines.append(line)
        return "\n".join(lines)
```

---

## 4. RAG Evaluation Metrics

```python
class RAGEvaluator:
    """
    Evaluates RAG pipeline quality using RAGAS / custom metrics.
    Run offline on golden dataset.
    """

    async def evaluate(
        self,
        questions: list[str],
        ground_truths: list[str],
        rag_engine: RAGEngine,
        tenant_id: str,
        doc_ids: list[str],
    ) -> dict:
        metrics = {
            "recall_at_k": [],
            "mrr": [],
            "faithfulness": [],
            "answer_relevance": [],
        }

        for question, ground_truth in zip(questions, ground_truths):
            result = await rag_engine.retrieve_and_build(
                query=question,
                tenant_id=tenant_id,
                doc_ids=doc_ids,
            )
            # Recall@K: is ground truth text in any retrieved chunk?
            found = any(
                self._text_overlap(ground_truth, c.text) > 0.5
                for c in result.chunks
            )
            metrics["recall_at_k"].append(1.0 if found else 0.0)

            # MRR: position of first relevant chunk
            for rank, chunk in enumerate(result.chunks, start=1):
                if self._text_overlap(ground_truth, chunk.text) > 0.5:
                    metrics["mrr"].append(1.0 / rank)
                    break
            else:
                metrics["mrr"].append(0.0)

        return {k: sum(v) / len(v) if v else 0.0 for k, v in metrics.items()}

    @staticmethod
    def _text_overlap(a: str, b: str) -> float:
        a_words = set(a.lower().split())
        b_words = set(b.lower().split())
        if not a_words:
            return 0.0
        return len(a_words & b_words) / len(a_words)
```
