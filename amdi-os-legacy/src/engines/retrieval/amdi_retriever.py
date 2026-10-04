"""
amdi_retriever.py
=================
AEGIS-AMDI-OS — Multi-Engine Retrieval Orchestrator

Coordinates seven specialised scoring engines
(semantic, geometry, recurrence, frequency, matrix, template, extra)
through an :class:`AdaptiveFusionEngine` to produce ranked retrieval
results for a given natural-language query.

Engine roles
------------
  s — semantic    : embedding cosine similarity
  g — geometry    : spatial / layout similarity
  r — recurrence  : cross-document pattern recurrence
  f — frequency   : term frequency / BM25-style
  m — matrix      : structured table / matrix matching
  t — template    : template-pattern matching
  x — extra       : plug-in / graph / hypergraph scoring

Typical usage
-------------
>>> retriever = AMDIRetriever(
...     embedder=my_embedder,
...     geometry_engine=geo_eng,
...     recurrence_engine=rec_eng,
...     frequency_engine=freq_eng,
...     matrix_engine=mat_eng,
...     template_engine=tmpl_eng,
...     semantic_engine=sem_eng,
...     graph_engine=graph_eng,
... )
>>> ctx = await retriever.retrieve(query, elements, tables, top_k=12)
>>> for result in ctx.results:
...     print(result.rank, result.score, result.element.element_id)
"""

from __future__ import annotations

import asyncio
import logging
import re
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from src.engines.fusion.adaptive_fusion import AdaptiveFusionEngine, FusionContext
from src.engines.geometry.element import GeometricElement

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Dataclasses
# ---------------------------------------------------------------------------


@dataclass
class RetrievalResult:
    """
    A single ranked retrieval result.

    Attributes
    ----------
    element:
        The :class:`~src.engines.geometry.element.GeometricElement` that
        was retrieved.
    score:
        Final fused relevance score in the range [0, 1].
    layer_scores:
        Per-engine scores keyed by single-letter engine identifier
        (``'s'``, ``'g'``, ``'r'``, ``'f'``, ``'m'``, ``'t'``, ``'x'``).
    rank:
        1-based rank of this result in the retrieval context.
    """

    element: GeometricElement
    score: float
    layer_scores: Dict[str, float] = field(default_factory=dict)
    rank: int = 0


@dataclass
class RetrievalContext:
    """
    The complete output of a single retrieval call.

    Attributes
    ----------
    query:
        The original natural-language query string.
    query_type:
        Query classification label produced by
        :class:`~src.engines.fusion.adaptive_fusion.AdaptiveFusionEngine`
        (e.g. ``'tabular'``, ``'semantic'``, ``'structural'``).
    weights:
        Per-engine fusion weights used for this query.
    results:
        Ranked list of :class:`RetrievalResult` objects.
    table_answers:
        Direct answers extracted from structured tables by the matrix
        engine.
    latency_ms:
        Wall-clock retrieval latency in milliseconds.
    """

    query: str
    query_type: str
    weights: Dict[str, float]
    results: List[RetrievalResult] = field(default_factory=list)
    table_answers: List[str] = field(default_factory=list)
    latency_ms: float = 0.0


# ---------------------------------------------------------------------------
# Main retriever
# ---------------------------------------------------------------------------


class AMDIRetriever:
    """
    Multi-engine retrieval orchestrator for AMDI document intelligence.

    All scoring engines are injected at construction time, making the
    retriever fully testable without I/O dependencies.

    Parameters
    ----------
    embedder:
        Embedding model with an ``async encode(text) -> np.ndarray`` interface.
    geometry_engine:
        Scores elements by spatial/layout similarity to the query.
    recurrence_engine:
        Scores elements by cross-document recurrence patterns.
    frequency_engine:
        Scores elements by term-frequency / BM25 relevance.
    matrix_engine:
        Scores structured tables and extracts direct answers.
    template_engine:
        Scores elements against document template patterns.
    semantic_engine:
        Scores elements by deep semantic similarity.
    graph_engine:
        Optional graph / hypergraph-based scorer.
    """

    def __init__(
        self,
        embedder: Any,
        geometry_engine: Any,
        recurrence_engine: Any,
        frequency_engine: Any,
        matrix_engine: Any,
        template_engine: Any,
        semantic_engine: Any,
        graph_engine: Optional[Any] = None,
    ) -> None:
        self._embedder = embedder
        self._geometry = geometry_engine
        self._recurrence = recurrence_engine
        self._frequency = frequency_engine
        self._matrix = matrix_engine
        self._template = template_engine
        self._semantic = semantic_engine
        self._graph = graph_engine
        self._fusion = AdaptiveFusionEngine()
        logger.info(
            "AMDIRetriever initialised — graph_engine=%s",
            "present" if graph_engine else "absent",
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def retrieve(
        self,
        query: str,
        elements: List[GeometricElement],
        tables: List[Any],
        graph: Optional[Any] = None,
        hypergraph: Optional[Any] = None,
        top_k: int = 12,
    ) -> RetrievalContext:
        """
        Execute a full multi-engine retrieval pass and return ranked results.

        Steps
        -----
        1. Classify the query and determine fusion weights via
           :class:`AdaptiveFusionEngine`.
        2. Encode the query into an embedding vector.
        3. Compute per-engine element scores in parallel.
        4. Collect direct table answers from the matrix engine.
        5. Fuse scores and re-rank via :meth:`AdaptiveFusionEngine.fuse`.
        6. Wrap results into a :class:`RetrievalContext` and return.

        Parameters
        ----------
        query:
            Natural-language question or search query.
        elements:
            Candidate :class:`~src.engines.geometry.element.GeometricElement`
            objects to score.
        tables:
            Structured table objects available for direct answer extraction.
        graph:
            Optional document graph (ignored if *graph_engine* is absent).
        hypergraph:
            Optional document hypergraph for advanced graph scoring.
        top_k:
            Maximum number of results to return.

        Returns
        -------
        RetrievalContext
            Fully populated retrieval context with ranked results.
        """
        t_start = time.perf_counter()
        logger.info("retrieve() query=%r elements=%d top_k=%d", query, len(elements), top_k)

        if not elements:
            logger.warning("retrieve() called with empty elements list.")
            return RetrievalContext(
                query=query,
                query_type="unknown",
                weights={},
                results=[],
                table_answers=[],
                latency_ms=0.0,
            )

        # ------------------------------------------------------------------
        # Step 1 — classify query and obtain fusion weights
        # ------------------------------------------------------------------
        query_type, weights = await self._fusion.classify(query)
        logger.debug("query_type=%s weights=%s", query_type, weights)

        # ------------------------------------------------------------------
        # Step 2 — embed the query
        # ------------------------------------------------------------------
        try:
            q_emb = self._embedder.encode(query)
            if asyncio.iscoroutine(q_emb):
                q_emb = await q_emb
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("Embedder error: %s", exc)
            q_emb = None

        # ------------------------------------------------------------------
        # Step 3 — compute per-engine scores (concurrently where possible)
        # ------------------------------------------------------------------
        query_pages = self._extract_query_pages(query)

        (
            s_scores,
            g_scores,
            r_scores,
            f_scores,
            m_scores,
            t_scores,
            x_scores,
        ) = await self._compute_layer_scores(query, elements, q_emb, query_pages)

        # ------------------------------------------------------------------
        # Step 4 — direct table answers from matrix engine
        # ------------------------------------------------------------------
        table_answers: List[str] = []
        if tables:
            try:
                raw_answers = await self._matrix.query(query, tables)
                if isinstance(raw_answers, list):
                    table_answers = [str(a) for a in raw_answers if a]
                elif raw_answers:
                    table_answers = [str(raw_answers)]
            except Exception as exc:  # pylint: disable=broad-except
                logger.warning("matrix_engine.query() error: %s", exc)

        # ------------------------------------------------------------------
        # Step 5 — fuse and rank
        # ------------------------------------------------------------------
        all_scores: Dict[str, Dict[str, float]] = {
            "s": s_scores,
            "g": g_scores,
            "r": r_scores,
            "f": f_scores,
            "m": m_scores,
            "t": t_scores,
            "x": x_scores,
        }

        try:
            fusion_ctx: FusionContext = await self._fusion.fuse(
                query=query,
                elements=elements,
                layer_scores=all_scores,
                weights=weights,
                top_k=top_k,
            )
            fused_items = fusion_ctx.ranked_items
        except Exception as exc:  # pylint: disable=broad-except
            logger.error("AdaptiveFusionEngine.fuse() error: %s", exc)
            # Graceful degradation: fall back to semantic scores
            fused_items = sorted(
                elements,
                key=lambda e: s_scores.get(e.element_id, 0.0),
                reverse=True,
            )[:top_k]

        # ------------------------------------------------------------------
        # Step 6 — build RetrievalResult list
        # ------------------------------------------------------------------
        results: List[RetrievalResult] = []
        for rank, item in enumerate(fused_items[:top_k], start=1):
            if isinstance(item, tuple):
                element, fused_score = item
            else:
                element = item
                eid = getattr(element, "element_id", "")
                fused_score = s_scores.get(eid, 0.0)

            eid = getattr(element, "element_id", "")
            layer_scores = {
                "s": s_scores.get(eid, 0.0),
                "g": g_scores.get(eid, 0.0),
                "r": r_scores.get(eid, 0.0),
                "f": f_scores.get(eid, 0.0),
                "m": m_scores.get(eid, 0.0),
                "t": t_scores.get(eid, 0.0),
                "x": x_scores.get(eid, 0.0),
            }
            results.append(
                RetrievalResult(
                    element=element,
                    score=round(float(fused_score), 6),
                    layer_scores=layer_scores,
                    rank=rank,
                )
            )

        latency_ms = (time.perf_counter() - t_start) * 1_000
        logger.info(
            "retrieve() complete — results=%d table_answers=%d latency=%.1fms",
            len(results),
            len(table_answers),
            latency_ms,
        )

        return RetrievalContext(
            query=query,
            query_type=query_type,
            weights=weights,
            results=results,
            table_answers=table_answers,
            latency_ms=round(latency_ms, 2),
        )

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    async def _compute_layer_scores(
        self,
        query: str,
        elements: List[GeometricElement],
        q_emb: Optional[Any],
        query_pages: Optional[List[int]],
    ) -> Tuple[
        Dict[str, float],
        Dict[str, float],
        Dict[str, float],
        Dict[str, float],
        Dict[str, float],
        Dict[str, float],
        Dict[str, float],
    ]:
        """
        Compute per-engine relevance scores for every element concurrently.

        Each engine is called with a best-effort try/except so that a single
        failing engine cannot abort the entire retrieval pipeline.

        Parameters
        ----------
        query:
            The raw query string.
        elements:
            Candidate elements to score.
        q_emb:
            Pre-computed query embedding (may be ``None`` if encoding failed).
        query_pages:
            List of page numbers extracted from the query, or ``None``.

        Returns
        -------
        tuple
            Seven dicts (s, g, r, f, m, t, x), each mapping
            ``element_id → score``.
        """
        # Run all engines concurrently
        tasks = [
            self._run_engine("semantic",    self._semantic.score,    query, elements, q_emb),
            self._run_engine("geometry",    self._geometry.score,    query, elements, query_pages),
            self._run_engine("recurrence",  self._recurrence.score,  query, elements),
            self._run_engine("frequency",   self._frequency.score,   query, elements),
            self._run_engine("matrix",      self._matrix.score,      query, elements),
            self._run_engine("template",    self._template.score,    query, elements),
            self._run_engine("graph",       self._graph.score if self._graph else None,
                             query, elements),
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        scored: List[Dict[str, float]] = []
        engine_names = ["semantic", "geometry", "recurrence", "frequency", "matrix", "template", "graph"]
        for name, result in zip(engine_names, results):
            if isinstance(result, Exception):
                logger.warning("Engine %s raised: %s", name, result)
                scored.append({})
            else:
                scored.append(result or {})

        s_scores, g_scores, r_scores, f_scores, m_scores, t_scores, x_scores = scored
        return s_scores, g_scores, r_scores, f_scores, m_scores, t_scores, x_scores

    @staticmethod
    async def _run_engine(
        name: str,
        fn: Optional[Any],
        *args: Any,
    ) -> Dict[str, float]:
        """
        Call an engine scoring function, returning an empty dict on failure.

        Parameters
        ----------
        name:
            Human-readable engine name for logging.
        fn:
            Async callable (or ``None`` if engine not available).
        *args:
            Positional arguments forwarded to *fn*.

        Returns
        -------
        dict
            Mapping of element_id → float score.
        """
        if fn is None:
            return {}
        try:
            result = fn(*args)
            if asyncio.iscoroutine(result):
                return await result
            return result or {}
        except Exception as exc:  # pylint: disable=broad-except
            logger.warning("Engine '%s' error: %s", name, exc)
            return {}

    @staticmethod
    def _extract_query_pages(query: str) -> Optional[List[int]]:
        """
        Extract explicit page number references from a query string.

        Recognises patterns such as:
          - ``"page 3"``
          - ``"pages 1, 2 and 4"``
          - ``"p.5"``
          - ``"pg 7"``

        Parameters
        ----------
        query:
            The raw query string to scan.

        Returns
        -------
        list[int] or None
            A de-duplicated, sorted list of page numbers if any are found,
            otherwise ``None``.

        Examples
        --------
        >>> AMDIRetriever._extract_query_pages("see page 3 and page 7")
        [3, 7]
        >>> AMDIRetriever._extract_query_pages("what is the revenue?")
        None
        """
        patterns = [
            r"\bpages?\s+(\d+(?:\s*[,&and]+\s*\d+)*)",   # "page 3", "pages 1, 2 and 4"
            r"\bpg\.?\s*(\d+)",                            # "pg. 7"
            r"\bp\.(\d+)",                                 # "p.5"
        ]
        pages: List[int] = []
        for pattern in patterns:
            for match in re.finditer(pattern, query, re.IGNORECASE):
                # Extract all digits from the matched group
                digits = re.findall(r"\d+", match.group(0))
                pages.extend(int(d) for d in digits)

        if not pages:
            return None
        return sorted(set(pages))
