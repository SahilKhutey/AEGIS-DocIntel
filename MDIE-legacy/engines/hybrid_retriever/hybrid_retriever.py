"""
AEGIS-MDIE — Hybrid Retriever
================================
R(q, D) = α·S(q,D) + β·G(q,D) + γ·F(q,D) + δ·M(q,D)

Multi-signal mathematical retrieval:
    S = Semantic  (dense embedding cosine)
    G = Geometric (spatial proximity, section match)
    F = Frequency (importance-weighted token overlap)
    M = Matrix    (table-based algebraic match)

Weights α, β, γ, δ are learnable; defaults are empirically tuned.
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass, field
from typing import Optional

import numpy as np

from MDIE.engines.frequency.frequency_engine import FrequencyEngine
from MDIE.engines.geometry.element import ElementType, GeometricElement
from MDIE.engines.geometry.geometry_engine import GeometryEngine
from MDIE.engines.graph.graph_engine import DocumentGraph, GraphEngine
from MDIE.engines.matrix.matrix_engine import MatrixEngine

log = logging.getLogger("mdie.retriever")


# ─────────────────────────────────────────────────────────────────
# Retrieval Result
# ─────────────────────────────────────────────────────────────────

@dataclass
class RetrievalResult:
    element:      GeometricElement
    score:        float     # R(q, e) — composite
    score_s:      float     # semantic
    score_g:      float     # geometric
    score_f:      float     # frequency
    score_m:      float     # matrix
    rank:         int       = 0

    def explain(self) -> str:
        return (
            f"[{self.rank}] R={self.score:.3f} "
            f"(S={self.score_s:.3f} G={self.score_g:.3f} "
            f"F={self.score_f:.3f} M={self.score_m:.3f}) "
            f"type={self.element.type.value} page={self.element.page} "
            f"'{self.element.content[:60]}'"
        )


@dataclass
class RetrievalContext:
    """Output of the hybrid retriever — ready for context building."""
    query:          str
    results:        list[RetrievalResult]
    table_answers:  list[str]           = field(default_factory=list)
    weights_used:   dict[str, float]    = field(default_factory=dict)
    latency_ms:     float               = 0.0
    token_count:    int                 = 0

    @property
    def top_elements(self) -> list[GeometricElement]:
        return [r.element for r in self.results]


# ─────────────────────────────────────────────────────────────────
# Hybrid Retriever
# ─────────────────────────────────────────────────────────────────

class HybridRetriever:
    """
    Hybrid mathematical retrieval:
        R(q, e) = α·S(q,e) + β·G(q,e) + γ·F(q,e) + δ·M(q,e)

    Weight adaptation:
        - If query contains numeric terms → boost δ (matrix)
        - If query contains location terms → boost β (geometry)
        - If query is general → default weights
    """

    DEFAULT_WEIGHTS = {"alpha": 0.50, "beta": 0.20, "gamma": 0.20, "delta": 0.10}

    def __init__(
        self,
        geometry_engine:   Optional[GeometryEngine]   = None,
        frequency_engine:  Optional[FrequencyEngine]  = None,
        matrix_engine:     Optional[MatrixEngine]     = None,
        graph:             Optional[DocumentGraph]    = None,
        embedding_model    = None,
        weights:           Optional[dict[str, float]] = None,
    ):
        self.geo     = geometry_engine  or GeometryEngine()
        self.freq    = frequency_engine or FrequencyEngine()
        self.matrix  = matrix_engine   or MatrixEngine()
        self.graph   = graph
        self.embedder = embedding_model
        self.weights  = weights or dict(self.DEFAULT_WEIGHTS)

    # ──────────────────────────────────────────────────────────────
    # Main retrieval
    # ──────────────────────────────────────────────────────────────

    def retrieve(
        self,
        query: str,
        elements: list[GeometricElement],
        top_k: int = 12,
        query_pages: Optional[list[int]] = None,
        section_hint: Optional[str] = None,
    ) -> RetrievalContext:
        """
        Score all elements using R(q,e) and return top_k.
        """
        import time
        t0 = time.perf_counter()

        # Adapt weights to query type
        alpha, beta, gamma, delta = self._adapt_weights(query)

        # Embed query
        q_emb = self._embed(query)

        # Score every element
        scored: list[RetrievalResult] = []
        for e in elements:
            s_s = self._semantic_score(q_emb, e)
            s_g = self.geo.geometry_relevance(query_pages, e, section_hint)
            s_f = self.freq.query_frequency_score(query, e)
            s_m = self._matrix_score(query, e)

            composite = alpha * s_s + beta * s_g + gamma * s_f + delta * s_m

            scored.append(RetrievalResult(
                element=e,
                score=composite,
                score_s=s_s,
                score_g=s_g,
                score_f=s_f,
                score_m=s_m,
            ))

        # Sort and rank
        scored.sort(key=lambda r: r.score, reverse=True)
        top = scored[:top_k]
        for i, r in enumerate(top):
            r.rank = i + 1

        # Graph expansion: add structurally adjacent nodes
        if self.graph:
            top = self._graph_expand(top, scored, max_expand=3)

        # Direct matrix QA
        table_answers = self.matrix.query(query)

        latency = (time.perf_counter() - t0) * 1000
        total_tokens = sum(r.element.token_count for r in top)

        log.info(
            "Retrieved %d elements | R_max=%.3f | latency=%.1fms | tokens=%d",
            len(top), top[0].score if top else 0, latency, total_tokens,
        )

        return RetrievalContext(
            query=query,
            results=top,
            table_answers=table_answers,
            weights_used={"alpha": alpha, "beta": beta, "gamma": gamma, "delta": delta},
            latency_ms=latency,
            token_count=total_tokens,
        )

    # ──────────────────────────────────────────────────────────────
    # Score components
    # ──────────────────────────────────────────────────────────────

    def _semantic_score(
        self,
        q_emb: Optional[np.ndarray],
        e: GeometricElement,
    ) -> float:
        """S(q, e) = cosine(embed(q), embed(e))."""
        if q_emb is None or e.embedding is None:
            return self._lexical_fallback(q_emb, e)
        a = np.array(q_emb,   dtype=np.float32)
        b = np.array(e.embedding, dtype=np.float32)
        na = np.linalg.norm(a); nb = np.linalg.norm(b)
        if na == 0 or nb == 0:
            return 0.0
        return float(np.dot(a, b) / (na * nb))

    def _lexical_fallback(self, q_emb, e: GeometricElement) -> float:
        """BM25-inspired lexical overlap when embeddings unavailable."""
        # Use frequency engine for token overlap scoring
        return self.freq.query_frequency_score("" if q_emb is None else str(q_emb), e)

    def _matrix_score(self, query: str, e: GeometricElement) -> float:
        """M(q, e) — is this element a table relevant to a numeric query?"""
        if e.type != ElementType.TABLE:
            return 0.0
        # Check if any table header appears in query
        table = self.matrix.get(e.element_id)
        if not table:
            return 0.1   # generic table bonus
        q_lower = query.lower()
        for h in table.headers:
            if h.lower() in q_lower:
                return 0.9
        # Keyword match on table content
        return 0.3 if any(w in query.lower() for w in ["total","sum","average","max","min","growth"]) else 0.1

    # ──────────────────────────────────────────────────────────────
    # Graph expansion
    # ──────────────────────────────────────────────────────────────

    def _graph_expand(
        self,
        top: list[RetrievalResult],
        all_scored: list[RetrievalResult],
        max_expand: int = 3,
    ) -> list[RetrievalResult]:
        """
        Expand top results with structurally adjacent nodes from the graph.
        Prevents fragmented context when answer spans multiple elements.
        """
        seed_ids = {r.element.element_id for r in top}
        score_map = {r.element.element_id: r.score for r in all_scored}
        expansion: list[RetrievalResult] = []

        for r in top[:5]:   # only expand from top-5
            neighbors = self.graph.bfs(r.element.element_id, max_depth=2)
            for nb in neighbors:
                if nb.element_id in seed_ids:
                    continue
                seed_ids.add(nb.element_id)
                # Use structural proximity as score modifier
                struct_score = self.graph.structural_score(nb.element_id, [r.element.element_id])
                orig_score   = score_map.get(nb.element_id, 0.0)
                combined     = 0.7 * orig_score + 0.3 * struct_score * r.score

                # Find the element object
                e_obj = self.geo.elements.get(nb.element_id)
                if e_obj:
                    expansion.append(RetrievalResult(
                        element=e_obj,
                        score=combined,
                        score_s=0.0, score_g=struct_score, score_f=0.0, score_m=0.0,
                    ))
                if len(expansion) >= max_expand:
                    break

        merged = top + expansion
        merged.sort(key=lambda r: r.score, reverse=True)
        for i, r in enumerate(merged):
            r.rank = i + 1
        return merged

    # ──────────────────────────────────────────────────────────────
    # Weight adaptation
    # ──────────────────────────────────────────────────────────────

    def _adapt_weights(self, query: str) -> tuple[float, float, float, float]:
        """
        Dynamically adjust α, β, γ, δ based on query intent.
        """
        q = query.lower()
        alpha = self.weights["alpha"]
        beta  = self.weights["beta"]
        gamma = self.weights["gamma"]
        delta = self.weights["delta"]

        # Numeric / calculation queries → boost matrix weight
        numeric_terms = ["total","sum","average","growth","percentage","revenue","cost","count","how many","calculate"]
        if any(t in q for t in numeric_terms):
            delta = min(0.35, delta + 0.15)
            alpha = max(0.30, alpha - 0.10)

        # Spatial queries → boost geometry
        spatial_terms = ["page","section","chapter","figure","table","diagram","appendix","where is","location"]
        if any(t in q for t in spatial_terms):
            beta  = min(0.40, beta + 0.15)
            alpha = max(0.30, alpha - 0.10)

        # Rare / important terms → boost frequency
        unique_terms = ["conclusion","finding","result","summary","recommendation","critical","important"]
        if any(t in q for t in unique_terms):
            gamma = min(0.35, gamma + 0.10)

        # Normalize weights to sum to 1
        total = alpha + beta + gamma + delta
        return alpha/total, beta/total, gamma/total, delta/total

    # ──────────────────────────────────────────────────────────────
    # Embedding
    # ──────────────────────────────────────────────────────────────

    def _embed(self, text: str) -> Optional[np.ndarray]:
        if self.embedder is None:
            return None
        try:
            return np.array(self.embedder.encode([text])[0], dtype=np.float32)
        except Exception as ex:
            log.warning("Embedding failed: %s", ex)
            return None

    def embed_elements(self, elements: list[GeometricElement]) -> None:
        """Compute and store embeddings for all elements in-place."""
        if self.embedder is None:
            return
        texts = [e.content for e in elements]
        try:
            embs = self.embedder.encode(texts, batch_size=64, show_progress_bar=False)
            for e, emb in zip(elements, embs):
                e.embedding = emb.tolist()
            log.info("Embedded %d elements", len(elements))
        except Exception as ex:
            log.warning("Batch embedding failed: %s", ex)

    # ──────────────────────────────────────────────────────────────
    # MMR (Maximal Marginal Relevance) for diversity
    # ──────────────────────────────────────────────────────────────

    def mmr(
        self,
        results: list[RetrievalResult],
        lambda_: float = 0.7,
        top_k: int = 8,
    ) -> list[RetrievalResult]:
        """
        Maximal Marginal Relevance:
            MMR = argmax [λ·R(q,e) - (1-λ)·max_sim(e, selected)]
        Avoids redundant context.
        """
        if not results:
            return []
        selected:    list[RetrievalResult] = []
        remaining:   list[RetrievalResult] = list(results)
        selected_emb: list[np.ndarray]    = []

        while remaining and len(selected) < top_k:
            if not selected:
                best = max(remaining, key=lambda r: r.score)
                selected.append(best)
                remaining.remove(best)
                if best.element.embedding:
                    selected_emb.append(np.array(best.element.embedding, dtype=np.float32))
                continue

            best_mmr = -float("inf")
            best_r   = None
            for r in remaining:
                rel = r.score
                if selected_emb and r.element.embedding:
                    emb = np.array(r.element.embedding, dtype=np.float32)
                    sims = [
                        float(np.dot(emb, s) / (np.linalg.norm(emb) * np.linalg.norm(s) + 1e-8))
                        for s in selected_emb
                    ]
                    max_sim = max(sims)
                else:
                    max_sim = 0.0
                score = lambda_ * rel - (1 - lambda_) * max_sim
                if score > best_mmr:
                    best_mmr = score
                    best_r   = r
            if best_r:
                selected.append(best_r)
                remaining.remove(best_r)
                if best_r.element.embedding:
                    selected_emb.append(np.array(best_r.element.embedding, dtype=np.float32))

        for i, r in enumerate(selected):
            r.rank = i + 1
        return selected
