"""
AEGIS-AMDI — Semantic Engine (Layer 1)
========================================
Embeddings · NER · Keyphrase extraction · Extractive summarization
S = { (e_i, v_i) : e_i ∈ text, v_i ∈ R^d }
"""
from __future__ import annotations

import logging
import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Optional, Sequence

import numpy as np

from AMDI.engines.geometry.element import Element, ElementType

log = logging.getLogger("amdi.semantic")

# ─────────────────────────────────────────────────────────────────
# Result model
# ─────────────────────────────────────────────────────────────────

@dataclass
class SemanticResult:
    element_id: str
    embedding:  Optional[np.ndarray]
    entities:   list[tuple[str, str]]    # (span, label)
    keyphrases: list[str]
    summary:    str
    token_count: int
    sentiment:   float                   # [-1, 1] polarity heuristic


# ─────────────────────────────────────────────────────────────────
# Semantic Engine
# ─────────────────────────────────────────────────────────────────

class SemanticEngine:
    """
    Layer 1 — Semantic understanding.

    Operations:
        • Dense embedding (via injected embedder or mock)
        • Lightweight rule-based NER (no external deps)
        • TF-IDF keyphrase extraction
        • Greedy extractive summarization (sentence ranking)
        • Simple sentiment polarity

    Used in fusion weight: w_s
    Query score: S(q, e) = cosine(embed(q), embed(e))
    """

    STOP = frozenset(
        "a an the is are was were be been being have has had do does did "
        "will would could should may might shall of in on at to for with "
        "by from up down and or but not so yet both either neither as if "
        "when while after before this that these those it its we our they "
        "their i my you your he she him her".split()
    )

    POS_WORDS = {"good", "great", "excellent", "increase", "improve", "profit", "success", "efficient"}
    NEG_WORDS = {"bad", "poor", "decrease", "loss", "fail", "failure", "risk", "defect", "error"}

    def __init__(self, embedder=None):
        self.embedder   = embedder
        self._idf:       dict[str, float] = {}
        self._n_docs:    int = 0

    # ──────────────────────────────────────────────────────────────
    # Collection fitting (IDF)
    # ──────────────────────────────────────────────────────────────

    def fit(self, elements: Sequence[Element]) -> "SemanticEngine":
        df: Counter = Counter()
        n = len(elements)
        for e in elements:
            tokens = set(self._tokenize(e.content))
            df.update(tokens)
        self._idf = {
            t: math.log((1 + n) / (1 + c)) + 1.0
            for t, c in df.items()
        }
        self._n_docs = n
        log.info("SemanticEngine fitted on %d elements, %d unique terms", n, len(self._idf))
        return self

    # ──────────────────────────────────────────────────────────────
    # Process batch
    # ──────────────────────────────────────────────────────────────

    def process(self, elements: Sequence[Element]) -> list[SemanticResult]:
        """Process all elements and annotate in-place."""
        results: list[SemanticResult] = []
        texts = [e.content for e in elements]

        # Batch embedding
        embeddings = self._embed_batch(texts)

        for i, e in enumerate(elements):
            emb = embeddings[i] if embeddings else None
            ents = self._extract_entities(e.content)
            kps  = self._keyphrases(e.content, top_k=5)
            summ = self._summarize(e.content, n=2)
            sent = self._sentiment(e.content)
            tok  = max(1, int(len(e.content.split()) * 1.33))

            # Write back to element
            e.embedding  = emb.tolist() if emb is not None else None
            e.entities   = ents
            e.keyphrases = kps
            e.summary    = summ

            results.append(SemanticResult(
                element_id  = e.element_id,
                embedding   = emb,
                entities    = ents,
                keyphrases  = kps,
                summary     = summ,
                token_count = tok,
                sentiment   = sent,
            ))
        log.info("Semantic processing complete: %d elements", len(elements))
        return results

    # ──────────────────────────────────────────────────────────────
    # NER (zero-dependency rule-based)
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _extract_entities(text: str) -> list[tuple[str, str]]:
        ents: list[tuple[str, str]] = []
        for m in re.finditer(r"[$€£]\s*[\d,]+(?:\.\d+)?[MBKmk]?", text):
            ents.append((m.group().strip(), "MONEY"))
        for m in re.finditer(r"\d+(?:\.\d+)?\s*%", text):
            ents.append((m.group(), "PERCENT"))
        for m in re.finditer(
            r"\b\d{4}-\d{2}-\d{2}\b|\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s+\d{1,2},?\s+\d{4}\b",
            text, re.IGNORECASE
        ):
            ents.append((m.group(), "DATE"))
        for m in re.finditer(
            r"\b\d+(?:\.\d+)?\s*(?:km|m|cm|mm|kg|g|lb|ft|in|GB|MB|KB|Hz|kHz|MHz|GHz|MW|kW|kN)\b",
            text, re.IGNORECASE
        ):
            ents.append((m.group(), "QUANTITY"))
        for m in re.finditer(r"\b[A-Z][a-z]+(?: [A-Z][a-z]+)+\b", text):
            if len(m.group()) > 5:
                ents.append((m.group(), "ENTITY"))
        for m in re.finditer(r"[\w.+-]+@[\w-]+\.\w+", text):
            ents.append((m.group(), "EMAIL"))
        for m in re.finditer(r"https?://\S+", text):
            ents.append((m.group(), "URL"))
        return ents

    # ──────────────────────────────────────────────────────────────
    # Keyphrase extraction
    # ──────────────────────────────────────────────────────────────

    def _keyphrases(self, text: str, top_k: int = 5) -> list[str]:
        tokens = self._tokenize(text)
        if not tokens:
            return []
        tf  = Counter(tokens)
        uni = {t: tf[t] * self._idf.get(t, 1.0) for t in tf if t not in self.STOP and len(t) > 2}
        bi  = {}
        for a, b in zip(tokens, tokens[1:]):
            if a not in self.STOP and b not in self.STOP:
                ph = f"{a} {b}"
                bi[ph] = bi.get(ph, 0) + 1.5 * (self._idf.get(a, 1.0) + self._idf.get(b, 1.0))
        combined = {**uni, **bi}
        ranked = sorted(combined, key=combined.get, reverse=True)
        return ranked[:top_k]

    # ──────────────────────────────────────────────────────────────
    # Summarization (extractive)
    # ──────────────────────────────────────────────────────────────

    def _summarize(self, text: str, n: int = 2) -> str:
        sents = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        if len(sents) <= n:
            return text
        tf = Counter(self._tokenize(text))
        scored = sorted(sents, key=lambda s: sum(tf[w] for w in self._tokenize(s)), reverse=True)
        top = set(scored[:n])
        return " ".join(s for s in sents if s in top)

    # ──────────────────────────────────────────────────────────────
    # Sentiment (heuristic)
    # ──────────────────────────────────────────────────────────────

    def _sentiment(self, text: str) -> float:
        tokens = set(self._tokenize(text))
        pos = len(tokens & self.POS_WORDS)
        neg = len(tokens & self.NEG_WORDS)
        total = pos + neg
        if total == 0:
            return 0.0
        return (pos - neg) / total

    # ──────────────────────────────────────────────────────────────
    # Query scoring  S(q, e)
    # ──────────────────────────────────────────────────────────────

    def score(self, query_emb: Optional[np.ndarray], elem: Element) -> float:
        """S(q, e) = cosine(embed(q), embed(e))."""
        if query_emb is None or elem.embedding is None:
            return self._lexical_score(query_emb, elem)
        q = np.asarray(query_emb, dtype=np.float32)
        e = np.asarray(elem.embedding, dtype=np.float32)
        denom = (np.linalg.norm(q) * np.linalg.norm(e)) + 1e-9
        return float(np.dot(q, e) / denom)

    def _lexical_score(self, q_emb, elem: Element) -> float:
        """BM25-lite fallback when embeddings unavailable."""
        if not hasattr(self, "_query_text"):
            return 0.5 * elem.importance_weight
        q_tokens = set(self._tokenize(getattr(self, "_query_text", "")))
        e_tokens  = set(self._tokenize(elem.content))
        if not q_tokens or not e_tokens:
            return 0.0
        return len(q_tokens & e_tokens) / len(q_tokens)

    def embed_query(self, query: str) -> Optional[np.ndarray]:
        self._query_text = query
        embs = self._embed_batch([query])
        return embs[0] if embs else None

    # ──────────────────────────────────────────────────────────────
    # Embedding (pluggable)
    # ──────────────────────────────────────────────────────────────

    def _embed_batch(self, texts: list[str]) -> list[Optional[np.ndarray]]:
        if self.embedder is None:
            return [None] * len(texts)
        try:
            embs = self.embedder.encode(texts, batch_size=64, show_progress_bar=False)
            return [np.asarray(e, dtype=np.float32) for e in embs]
        except Exception as ex:
            log.warning("Embedding failed: %s", ex)
            return [None] * len(texts)

    # ──────────────────────────────────────────────────────────────
    # Helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"\b\w+\b", text)]
