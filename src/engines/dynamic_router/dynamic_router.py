"""
AEGIS-AMDI-OS — Dynamic Router
================================
Predicts optimal layer weights W = (w_S, w_G, w_R, w_F, w_M, w_T, w_X, w_H, w_E)
Implements Formulas §24-§27.

Two modes:
1. Rule-based (default, no training needed)
2. MLP-based (trained on query logs)
"""
from __future__ import annotations

import logging
import math
import re
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any

import numpy as np

logger = logging.getLogger("amdi.math.router")


LAYER_NAMES = ["S", "G", "R", "F", "M", "T", "X", "H", "E"]


@dataclass
class QueryFeatures:
    """
    φ(Q) - features extracted from a query.
    """
    length: int
    n_words: int
    has_table_keyword: float
    has_geometry_keyword: float
    has_graph_keyword: float
    has_aggregate_keyword: float
    has_template_keyword: float
    has_recurrence_keyword: float
    has_page_ref: float
    has_section_ref: float
    has_numeric: float
    has_comparison: float
    has_temporal: float
    is_question: float

    def to_vector(self) -> np.ndarray:
        return np.array([
            float(self.length), float(self.n_words),
            self.has_table_keyword, self.has_geometry_keyword,
            self.has_graph_keyword, self.has_aggregate_keyword,
            self.has_template_keyword, self.has_recurrence_keyword,
            self.has_page_ref, self.has_section_ref,
            self.has_numeric, self.has_comparison, self.has_temporal,
            self.is_question,
        ], dtype=np.float32)


class DynamicRouter:
    """
    Predicts W = (w_1, ..., w_n) for a query.

    Rule-based mode uses keyword matching.
    MLP-based mode uses a learned network (optional).
    """

    KEYWORD_PATTERNS = {
        "table": [r"\btable\b", r"\bmatrix\b", r"\bgrid\b", r"\bspreadsheet\b", r"\bcell\b"],
        "geometry": [r"\blayout\b", r"\bposition\b", r"\bcoordinate\b", r"\bpage\s+\d+", r"\bsection\b"],
        "graph": [r"\brefer", r"\bcit", r"\blink", r"\brelate", r"\bconnect", r"\bneighbor\b", r"\bpath\b"],
        "aggregate": [r"\btotal\b", r"\bsum\b", r"\baverage\b", r"\bmean\b", r"\bgrowth\b",
                      r"\bmax\b", r"\bmin\b", r"\bhighest\b", r"\blowest\b", r"\bcount\b"],
        "template": [r"\btemplate\b", r"\bpattern\b", r"\bsimilar\b", r"\blayout\s+type\b", r"\bformat\b"],
        "recurrence": [r"\bheader\b", r"\bfooter\b", r"\brepeated\b", r"\bcommon\b", r"\bwatermark\b", r"\bduplicate\b"],
        "numeric": [r"\d+", r"\brevenue\b", r"\bprofit\b", r"\bcost\b", r"\bamount\b", r"\d+\s*%"],
        "comparison": [r"\bcompar", r"\bdiffer", r"\bversus\b", r"\bvs\b"],
        "temporal": [r"\bv\d+", r"\bversion\b", r"\bupdate", r"\bchange", r"\bevolve", r"\bhistory\b"],
    }

    DEFAULT_WEIGHTS = {
        "default": np.array([0.35, 0.15, 0.10, 0.10, 0.15, 0.05, 0.05, 0.03, 0.02], dtype=np.float32),
    }

    QUERY_TYPE_WEIGHTS = {
        "numerical":     np.array([0.20, 0.05, 0.05, 0.10, 0.45, 0.02, 0.03, 0.05, 0.05], dtype=np.float32),
        "aggregate":     np.array([0.15, 0.05, 0.05, 0.10, 0.50, 0.02, 0.03, 0.05, 0.05], dtype=np.float32),
        "structural":    np.array([0.15, 0.45, 0.10, 0.10, 0.05, 0.05, 0.05, 0.03, 0.02], dtype=np.float32),
        "layout":        np.array([0.10, 0.50, 0.10, 0.05, 0.05, 0.10, 0.05, 0.03, 0.02], dtype=np.float32),
        "semantic":      np.array([0.70, 0.05, 0.05, 0.05, 0.02, 0.02, 0.06, 0.03, 0.02], dtype=np.float32),
        "template":      np.array([0.15, 0.20, 0.15, 0.10, 0.05, 0.25, 0.05, 0.03, 0.02], dtype=np.float32),
        "recurrence":    np.array([0.10, 0.15, 0.50, 0.10, 0.02, 0.05, 0.03, 0.03, 0.02], dtype=np.float32),
        "graph":         np.array([0.20, 0.10, 0.10, 0.05, 0.10, 0.05, 0.35, 0.03, 0.02], dtype=np.float32),
        "entity":        np.array([0.65, 0.05, 0.05, 0.05, 0.05, 0.02, 0.08, 0.03, 0.02], dtype=np.float32),
        "temporal":      np.array([0.30, 0.10, 0.20, 0.10, 0.10, 0.10, 0.05, 0.03, 0.02], dtype=np.float32),
        "hierarchical":  np.array([0.20, 0.10, 0.10, 0.10, 0.10, 0.05, 0.10, 0.20, 0.05], dtype=np.float32),
        "entropy":       np.array([0.15, 0.10, 0.10, 0.15, 0.10, 0.05, 0.10, 0.05, 0.20], dtype=np.float32),
    }

    def __init__(self, mlp_weights: Optional[np.ndarray] = None, mlp_bias: Optional[np.ndarray] = None) -> None:
        self.mlp_weights = mlp_weights  # (n_layers, n_features)
        self.mlp_bias = mlp_bias        # (n_layers,)

    # ------------------------------------------------------------------ #
    # Feature extraction                                                  #
    # ------------------------------------------------------------------ #

    def extract_features(self, query: str) -> QueryFeatures:
        """φ(Q) - feature vector for query."""
        q_lower = query.lower()
        n_words = len(q_lower.split())
        return QueryFeatures(
            length=len(q_lower),
            n_words=n_words,
            has_table_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["table"]),
            has_geometry_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["geometry"]),
            has_graph_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["graph"]),
            has_aggregate_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["aggregate"]),
            has_template_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["template"]),
            has_recurrence_keyword=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["recurrence"]),
            has_page_ref=1.0 if re.search(r"page\s+\d+", q_lower) else 0.0,
            has_section_ref=1.0 if re.search(r"section|chapter", q_lower) else 0.0,
            has_numeric=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["numeric"]),
            has_comparison=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["comparison"]),
            has_temporal=self._has_pattern(q_lower, self.KEYWORD_PATTERNS["temporal"]),
            is_question=1.0 if q_lower.strip().endswith("?") else 0.0,
        )

    @staticmethod
    def _has_pattern(text: str, patterns: list[str]) -> float:
        return float(any(re.search(p, text) for p in patterns))

    # ------------------------------------------------------------------ #
    # Weight prediction                                                    #
    # ------------------------------------------------------------------ #

    def predict(self, query: str) -> Tuple[np.ndarray, str]:
        """
        Predict layer weights for a query.
        Returns (weights, query_type).
        """
        if self.mlp_weights is not None and self.mlp_bias is not None:
            return self._predict_mlp(query)
        return self._predict_rules(query)

    def _predict_rules(self, query: str) -> Tuple[np.ndarray, str]:
        """Rule-based prediction using keyword matching."""
        features = self.extract_features(query)
        # Find best matching query type
        scores = {
            "numerical":   features.has_numeric + features.has_aggregate_keyword,
            "aggregate":   features.has_aggregate_keyword * 2.0,
            "structural":  features.has_geometry_keyword + features.has_page_ref + features.has_section_ref,
            "layout":      features.has_geometry_keyword * 1.5,
            "semantic":    features.is_question + 0.5,
            "template":    features.has_template_keyword + features.has_comparison,
            "recurrence":  features.has_recurrence_keyword * 2.0,
            "graph":       features.has_graph_keyword * 2.0,
            "entity":      features.has_numeric * 0.5 + features.has_page_ref * 0.5,
            "temporal":    features.has_temporal * 2.0,
            "hierarchical": features.has_section_ref * 1.5 + features.has_page_ref * 0.5,
            "entropy":     (1.0 if features.n_words > 12 else 0.0) + (1.0 if features.is_question else 0.0),
        }
        
        best_type = max(scores, key=lambda k: scores[k])
        weights = self.QUERY_TYPE_WEIGHTS.get(best_type, self.DEFAULT_WEIGHTS["default"])
        return weights, best_type

    def _predict_mlp(self, query: str) -> Tuple[np.ndarray, str]:
        features = self.extract_features(query)
        x = features.to_vector()
        
        # Simple MLP forward pass: z = Wx + b
        z = np.dot(self.mlp_weights, x) + self.mlp_bias # type: ignore
        
        # Softmax to ensure weights sum to 1.0
        exp_z = np.exp(z - np.max(z))
        weights = exp_z / np.sum(exp_z)
        
        # Map output weights back to the most dominant class/type
        dominant_idx = int(np.argmax(weights))
        query_type = LAYER_NAMES[dominant_idx]
        
        return weights, query_type
