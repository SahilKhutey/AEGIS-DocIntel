"""
AMDI-OS — Adaptive Fusion Engine
================================
Classifies queries and dynamically fuses multiple representation layer scores.
Includes MMR (Maximal Marginal Relevance) deduplication and ASCII explanation.
"""
from __future__ import annotations
import time
import re
import logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from src.engines.geometry.element import GeometricElement

log = logging.getLogger("amdi.fusion")


class QueryType(str, Enum):
    NUMERICAL    = "numerical"
    AGGREGATION  = "aggregation"
    STRUCTURAL   = "structural"
    LAYOUT       = "layout"
    SEMANTIC     = "semantic"
    TEMPLATE     = "template"
    RECURRENCE   = "recurrence"
    ENTITY       = "entity"
    GRAPH        = "graph"
    TEMPORAL     = "temporal"
    UNKNOWN      = "unknown"


@dataclass
class FusionWeights:
    w_s: float  # semantic
    w_g: float  # geometry
    w_r: float  # recurrence
    w_f: float  # frequency
    w_m: float  # matrix
    w_t: float  # template
    w_x: float  # graph

    def normalized(self) -> FusionWeights:
        total = self.w_s + self.w_g + self.w_r + self.w_f + self.w_m + self.w_t + self.w_x
        if total == 0:
            return FusionWeights(1/7, 1/7, 1/7, 1/7, 1/7, 1/7, 1/7)
        return FusionWeights(
            self.w_s / total,
            self.w_g / total,
            self.w_r / total,
            self.w_f / total,
            self.w_m / total,
            self.w_t / total,
            self.w_x / total
        )

    def dominant(self) -> str:
        weights = {
            "semantic": self.w_s,
            "geometry": self.w_g,
            "recurrence": self.w_r,
            "frequency": self.w_f,
            "matrix": self.w_m,
            "template": self.w_t,
            "graph": self.w_x
        }
        return max(weights, key=weights.get) # type: ignore

    def to_dict(self) -> dict[str, float]:
        return {
            "w_s": self.w_s,
            "w_g": self.w_g,
            "w_r": self.w_r,
            "w_f": self.w_f,
            "w_m": self.w_m,
            "w_t": self.w_t,
            "w_x": self.w_x
        }

    def _arr(self) -> np.ndarray:
        return np.array([self.w_s, self.w_g, self.w_r, self.w_f, self.w_m, self.w_t, self.w_x], dtype=np.float32)


# Default weight configurations that normalize to exactly 1.0
DEFAULT_WEIGHTS: Dict[QueryType, FusionWeights] = {
    QueryType.AGGREGATION: FusionWeights(0.15, 0.04, 0.04, 0.04, 0.65, 0.04, 0.04),
    QueryType.NUMERICAL:   FusionWeights(0.20, 0.05, 0.05, 0.05, 0.55, 0.05, 0.05),
    QueryType.STRUCTURAL:  FusionWeights(0.15, 0.50, 0.07, 0.07, 0.07, 0.07, 0.07),
    QueryType.LAYOUT:      FusionWeights(0.07, 0.55, 0.07, 0.07, 0.06, 0.12, 0.06),
    QueryType.SEMANTIC:    FusionWeights(0.75, 0.04, 0.04, 0.04, 0.03, 0.03, 0.07),
    QueryType.TEMPLATE:    FusionWeights(0.09, 0.18, 0.09, 0.09, 0.09, 0.38, 0.08),
    QueryType.RECURRENCE:  FusionWeights(0.06, 0.12, 0.58, 0.06, 0.06, 0.06, 0.06),
    QueryType.ENTITY:      FusionWeights(0.68, 0.05, 0.04, 0.04, 0.04, 0.04, 0.11),
    QueryType.GRAPH:       FusionWeights(0.18, 0.07, 0.07, 0.06, 0.06, 0.06, 0.50),
    QueryType.TEMPORAL:    FusionWeights(0.25, 0.11, 0.22, 0.11, 0.11, 0.10, 0.10),
    QueryType.UNKNOWN:     FusionWeights(0.50, 0.15, 0.07, 0.07, 0.07, 0.07, 0.07),
}


@dataclass
class FusionResult:
    element: GeometricElement
    final_score: float
    layer_scores: dict[str, float]
    rank: int = 0


@dataclass
class FusionContext:
    query: str
    query_type: QueryType
    confidence: float
    weights: FusionWeights
    results: List[FusionResult] = field(default_factory=list)
    table_answers: List[str] = field(default_factory=list)
    latency_ms: float = 0.0

    @property
    def ranked_items(self) -> List[Tuple[GeometricElement, float]]:
        return [(r.element, r.final_score) for r in self.results]



class QueryClassifier:
    """
    Classifies natural language queries to route weight configurations.
    """
    def classify(self, query: str) -> Tuple[QueryType, float]:
        q = query.lower().strip()
        
        # Temporal
        if re.search(r"\b(year|month|quarter|q[1-4]|fiscal|fy\d{2}|fy\d{4}|timeline|date|schedule|timeline)\b", q):
            return QueryType.TEMPORAL, 0.85
            
        # Aggregation
        if re.search(r"\b(sum|average|mean|total|aggregate|stats|statistics|count|min|max|highest|lowest|summing|avg)\b", q):
            return QueryType.AGGREGATION, 0.90
            
        # Numerical
        if re.search(r"\b(how (many|much)|percent|percentage|rate|cost|price|revenue|sales|profit|amount|\d+(\.\d+)?)\b", q):
            return QueryType.NUMERICAL, 0.80
            
        # Structural
        if re.search(r"\b(below|above|next to|right of|left of|column|row|coordinates|visual|layout)\b", q):
            return QueryType.STRUCTURAL, 0.85
            
        # Layout
        if re.search(r"\b(header|footer|page number|margin|sidebar|title|subtitle|caption)\b", q):
            return QueryType.LAYOUT, 0.80
            
        # Template
        if re.search(r"\b(template|form|invoice|statement|receipt|po|purchase order|contract|format)\b", q):
            return QueryType.TEMPLATE, 0.85
            
        # Recurrence
        if re.search(r"\b(duplicate|repeat|recurring|redundant|pattern|overlap|identical)\b", q):
            return QueryType.RECURRENCE, 0.80
            
        # Graph
        if re.search(r"\b(connect|relates|link|reference|relationship|dependency|centrality|neighbor|path)\b", q):
            return QueryType.GRAPH, 0.85
            
        # Entity
        if re.search(r"\b(who|when|where|which|person|organization|company|location|date|dollar)\b", q):
            return QueryType.ENTITY, 0.75
            
        # Semantic (summarize, explain, what, why)
        if re.search(r"\b(summarize|explain|what is|why|how does|context|meaning|concept)\b", q):
            return QueryType.SEMANTIC, 0.90
            
        return QueryType.UNKNOWN, 0.50

    def route(self, query: str) -> Tuple[FusionWeights, QueryType, float]:
        q_type, conf = self.classify(query)
        weights = DEFAULT_WEIGHTS.get(q_type, DEFAULT_WEIGHTS[QueryType.UNKNOWN])
        return weights, q_type, conf


class AdaptiveFusionEngine:
    """
    Unified Fusion Engine combining representations and applying MMR.
    """
    def __init__(self) -> None:
        self.classifier = QueryClassifier()

    async def classify(self, query: str) -> Tuple[QueryType, FusionWeights]:
        """
        Classifies the query and returns (query_type, fusion_weights).
        """
        weights, q_type, conf = self.classifier.route(query)
        return q_type, weights

    async def fuse(
        self,
        query: str,
        elements: List[GeometricElement],
        *,
        s_scores: Optional[Dict[str, float]] = None,
        g_scores: Optional[Dict[str, float]] = None,
        r_scores: Optional[Dict[str, float]] = None,
        f_scores: Optional[Dict[str, float]] = None,
        m_scores: Optional[Dict[str, float]] = None,
        t_scores: Optional[Dict[str, float]] = None,
        x_scores: Optional[Dict[str, float]] = None,
        layer_scores: Optional[Dict[str, Dict[str, float]]] = None,
        weights: Optional[FusionWeights] = None,
        table_answers: Optional[List[str]] = None,
        top_k: int = 12,
        use_mmr: bool = True,
        mmr_lambda: float = 0.70,
        **kwargs: Any
    ) -> FusionContext:
        t0 = time.perf_counter()
        
        if layer_scores is not None:
            s_scores = layer_scores.get("s", s_scores)
            g_scores = layer_scores.get("g", g_scores)
            r_scores = layer_scores.get("r", r_scores)
            f_scores = layer_scores.get("f", f_scores)
            m_scores = layer_scores.get("m", m_scores)
            t_scores = layer_scores.get("t", t_scores)
            x_scores = layer_scores.get("x", x_scores)

        s_scores = s_scores or {}
        g_scores = g_scores or {}
        r_scores = r_scores or {}
        f_scores = f_scores or {}
        m_scores = m_scores or {}
        t_scores = t_scores or {}
        x_scores = x_scores or {}

        if weights is None:
            weights, q_type, conf = self.classifier.route(query)
        else:
            q_type, conf = self.classifier.classify(query)

        
        results: List[FusionResult] = []
        for el in elements:
            eid = el.element_id
            
            # Retrieve layer scores, defaulting to 0.0
            s = s_scores.get(eid, 0.0)
            g = g_scores.get(eid, 0.0)
            r = r_scores.get(eid, 0.0)
            f = f_scores.get(eid, 0.0)
            m = m_scores.get(eid, 0.0)
            t = t_scores.get(eid, 0.0)
            x = x_scores.get(eid, 0.0)
            
            # Combine linearly
            final_score = (
                weights.w_s * s +
                weights.w_g * g +
                weights.w_r * r +
                weights.w_f * f +
                weights.w_m * m +
                weights.w_t * t +
                weights.w_x * x
            )
            
            layer_scores = {"s": s, "g": g, "r": r, "f": f, "m": m, "t": t, "x": x}
            results.append(FusionResult(element=el, final_score=final_score, layer_scores=layer_scores))
            
        # Sort by final score descending
        results.sort(key=lambda x: x.final_score, reverse=True)
        
        # Apply MMR deduplication if requested
        if use_mmr and results:
            results = self._mmr(results, mmr_lambda, top_k)
        else:
            results = results[:top_k]
            
        # Assign ranks
        for i, res in enumerate(results):
            res.rank = i + 1
            
        elapsed_ms = (time.perf_counter() - t0) * 1000
        
        return FusionContext(
            query=query,
            query_type=q_type,
            confidence=conf,
            weights=weights,
            results=results,
            table_answers=table_answers or [],
            latency_ms=elapsed_ms
        )

    def _mmr(self, results: List[FusionResult], lambda_: float, top_k: int) -> List[FusionResult]:
        """
        Maximal Marginal Relevance (MMR) for diverse retrieval.
        """
        if not results:
            return []
            
        selected: List[FusionResult] = [results[0]]
        candidates = results[1:]
        
        def cosine_sim(a, b) -> float:
            if a is None or b is None:
                return 0.0
            arr_a = np.array(a)
            arr_b = np.array(b)
            norm_a = np.linalg.norm(arr_a)
            norm_b = np.linalg.norm(arr_b)
            if norm_a > 0 and norm_b > 0:
                return float(np.dot(arr_a, arr_b) / (norm_a * norm_b))
            return 0.0

        def jaccard_sim(str1: str, str2: str) -> float:
            s1 = set(str1.lower().split())
            s2 = set(str2.lower().split())
            if not s1 and not s2:
                return 0.0
            return len(s1.intersection(s2)) / len(s1.union(s2))

        def sim(r1: FusionResult, r2: FusionResult) -> float:
            e1, e2 = r1.element, r2.element
            if e1.embedding is not None and e2.embedding is not None:
                return cosine_sim(e1.embedding, e2.embedding)
            return jaccard_sim(e1.content, e2.content)

        while len(selected) < top_k and candidates:
            best_score = -float("inf")
            best_cand: Optional[FusionResult] = None
            
            for cand in candidates:
                # Compute maximum similarity to already selected elements
                max_sim = max(sim(cand, sel) for sel in selected)
                
                # MMR score formula
                mmr_score = lambda_ * cand.final_score - (1.0 - lambda_) * max_sim
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_cand = cand
                    
            if best_cand is not None:
                selected.append(best_cand)
                candidates.remove(best_cand)
            else:
                break
                
        return selected

    def explain_routing(self, query: str) -> str:
        """
        Returns an ASCII bar chart explaining the query classification routing.
        """
        weights, q_type, conf = self.classifier.route(query)
        w_dict = weights.to_dict()
        
        lines = [
            f"Query: \"{query}\"",
            f"Query Type: {q_type.upper()} (Confidence: {conf:.2f})",
            "Routing weights:"
        ]
        
        labels = {
            "w_s": "Semantic (w_s)",
            "w_g": "Geometry (w_g)",
            "w_r": "Recurrence (w_r)",
            "w_f": "Frequency (w_f)",
            "w_m": "Matrix (w_m)",
            "w_t": "Template (w_t)",
            "w_x": "Graph (w_x)"
        }
        
        for key, val in w_dict.items():
            pct = val * 100
            bar_len = int(round(val * 20))
            bar = "█" * bar_len + "░" * (20 - bar_len)
            lines.append(f"  {labels[key]:<16}: {bar} {pct:.0f}%")
            
        return "\n".join(lines)
