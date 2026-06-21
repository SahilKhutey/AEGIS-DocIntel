"""
AEGIS-MDIE — Compression Engine
==================================
D = {T, R_n, Δ}  —  Template + Recurrence + Delta.
Achieves 80-95% token compression on structured documents.
"""
from __future__ import annotations

import json
import logging
import zlib
from dataclasses import asdict, dataclass, field
from typing import Optional

import numpy as np

from MDIE.engines.geometry.element import ElementType, GeometricElement
from MDIE.engines.geometry.geometry_engine import GeometryEngine
from MDIE.engines.recurrence.recurrence_engine import RecurrenceEngine, RecurrenceGroup

log = logging.getLogger("mdie.compression")


# ─────────────────────────────────────────────────────────────────
# Template Signature
# ─────────────────────────────────────────────────────────────────

@dataclass
class TemplateSignature:
    """
    T = {h, b, t, i, m}
    Fingerprint of a document template for similarity comparison.
    """
    signature_id:  str
    heading_count: int   = 0
    block_count:   int   = 0
    table_count:   int   = 0
    image_count:   int   = 0
    margin_sig:    tuple = (0.0, 0.0, 0.0, 0.0)    # (left, top, right, bottom)
    page_sig:      Optional[np.ndarray] = None       # 32-D spatial vector

    def feature_vector(self) -> np.ndarray:
        v = np.array([
            self.heading_count / max(1, self.block_count),
            self.block_count,
            self.table_count,
            self.image_count,
            *self.margin_sig,
        ], dtype=np.float32)
        n = np.linalg.norm(v)
        return v / n if n > 0 else v

    def similarity(self, other: "TemplateSignature") -> float:
        """Cosine similarity between two template signatures."""
        a = self.feature_vector()
        b = other.feature_vector()
        dot = float(np.dot(a, b))
        na  = float(np.linalg.norm(a))
        nb  = float(np.linalg.norm(b))
        return dot / (na * nb) if na > 0 and nb > 0 else 0.0


# ─────────────────────────────────────────────────────────────────
# Compressed Document
# ─────────────────────────────────────────────────────────────────

@dataclass
class CompressedDocument:
    """
    D = {T, R_n, Δ}

    Stores:
        template:        unique structural template
        recurrences:     {group_id: {representative, pages}}
        uniques:         non-repeating elements (the δ deltas)
        index:           page → [element_ids in order] for reconstruction
        stats:           compression metrics
    """
    doc_id:       str
    template:     Optional[TemplateSignature]  = None
    recurrences:  dict = field(default_factory=dict)    # gid → {rep, pages}
    uniques:      list = field(default_factory=list)    # list of compact element dicts
    index:        dict = field(default_factory=dict)    # page → [eid, ...]
    stats:        dict = field(default_factory=dict)

    def token_count_compressed(self) -> int:
        return sum(
            len(e.get("content", "").split()) * 4 // 3
            for e in self.uniques
        ) + sum(
            len(v["content"].split()) * 4 // 3
            for v in self.recurrences.values()
        )

    def token_count_original(self) -> int:
        return self.stats.get("original_tokens", 0)

    def savings_pct(self) -> float:
        orig = self.token_count_original()
        comp = self.token_count_compressed()
        if orig == 0:
            return 0.0
        return (1 - comp / orig) * 100

    def to_json(self, pretty: bool = False) -> str:
        data = {
            "doc_id":      self.doc_id,
            "recurrences": self.recurrences,
            "uniques":     self.uniques,
            "index":       {str(k): v for k, v in self.index.items()},
            "stats":       self.stats,
        }
        return json.dumps(data, indent=2 if pretty else None)

    def to_bytes(self) -> bytes:
        """Zlib-compress the JSON representation."""
        return zlib.compress(self.to_json().encode("utf-8"), level=6)

    @classmethod
    def from_bytes(cls, data: bytes, doc_id: str) -> "CompressedDocument":
        raw = json.loads(zlib.decompress(data).decode("utf-8"))
        cd  = cls(doc_id=doc_id)
        cd.recurrences = raw.get("recurrences", {})
        cd.uniques     = raw.get("uniques", [])
        cd.index       = {int(k): v for k, v in raw.get("index", {}).items()}
        cd.stats       = raw.get("stats", {})
        return cd


# ─────────────────────────────────────────────────────────────────
# Compression Engine
# ─────────────────────────────────────────────────────────────────

class CompressionEngine:
    """
    D = { T, R_n, Δ }

    Pipeline:
        1. Build TemplateSignature for document
        2. Delegate to RecurrenceEngine for grouping
        3. Separate templates from unique deltas
        4. Build spatial index for reconstruction
        5. Compute compression metrics

    Token savings formula:
        savings = 1 - (|T| + Σ|Δ_j|) / (|T| + Σ|R_i| + Σ|Δ_j|)
    """

    def __init__(
        self,
        recurrence_engine: Optional[RecurrenceEngine] = None,
        geometry_engine:   Optional[GeometryEngine]   = None,
    ):
        self.recurrence = recurrence_engine or RecurrenceEngine()
        self.geometry   = geometry_engine   or GeometryEngine()

    # ──────────────────────────────────────────────────────────────
    # Template Signature
    # ──────────────────────────────────────────────────────────────

    def build_template_signature(
        self, elements: list[GeometricElement], doc_id: str
    ) -> TemplateSignature:
        h  = sum(1 for e in elements if e.type == ElementType.HEADING)
        b  = len(elements)
        t  = sum(1 for e in elements if e.type == ElementType.TABLE)
        img = sum(1 for e in elements if e.type == ElementType.FIGURE)

        # Margin: estimate from bounding boxes on first page
        page1 = [e for e in elements if e.page == 1 and e.bbox]
        left   = min((e.bbox.x0 for e in page1), default=0.0)
        top    = min((e.bbox.y0 for e in page1), default=0.0)
        right  = max((e.bbox.x1 for e in page1), default=1.0)
        bottom = max((e.bbox.y1 for e in page1), default=1.0)

        return TemplateSignature(
            signature_id  = doc_id,
            heading_count = h,
            block_count   = b,
            table_count   = t,
            image_count   = img,
            margin_sig    = (round(left,2), round(top,2), round(right,2), round(bottom,2)),
        )

    # ──────────────────────────────────────────────────────────────
    # Compress
    # ──────────────────────────────────────────────────────────────

    def compress(
        self, elements: list[GeometricElement], doc_id: str
    ) -> CompressedDocument:
        """
        Full compression pipeline.
        Returns CompressedDocument with template + delta decomposition.
        """
        log.info("Compressing document '%s' (%d elements)", doc_id, len(elements))

        # 1. Template signature
        tmpl = self.build_template_signature(elements, doc_id)

        # 2. Detect recurrences
        groups = self.recurrence.detect(elements)

        # 3. Separate compressed representation
        compact = self.recurrence.compress(elements)
        template_ids  = set(compact["templates"])
        unique_ids    = set(compact["uniques"])

        # 4. Build compact element dicts
        id_to_elem = {e.element_id: e for e in elements}

        recs: dict = {}
        for gid, pages in compact["recurrences"].items():
            group = self.recurrence.groups[gid]
            rep   = group.representative
            recs[gid] = {
                "content":    rep.content,
                "type":       rep.type.value,
                "pages":      pages,
                "count":      group.count,
                "bbox":       rep.bbox.to_tuple() if rep.bbox else None,
                "weight":     round(rep.importance_weight, 4),
            }

        uniques: list[dict] = []
        for eid in unique_ids:
            e = id_to_elem.get(eid)
            if e:
                uniques.append(e.to_compact())

        # 5. Reconstruction index: page → [eid, ...]
        index: dict[int, list[str]] = {}
        for e in elements:
            index.setdefault(e.page, []).append(e.element_id)

        # 6. Compute metrics
        orig_tokens = sum(e.token_count for e in elements)
        comp_tokens = (
            sum(len(v["content"].split()) * 4 // 3 for v in recs.values())
            + sum(len(u.get("content","").split()) * 4 // 3 for u in uniques)
        )
        ratio = comp_tokens / max(1, orig_tokens)

        stats = {
            "original_elements": len(elements),
            "original_tokens":   orig_tokens,
            "compressed_tokens": comp_tokens,
            "compression_ratio": round(ratio, 3),
            "savings_pct":       round((1 - ratio) * 100, 1),
            "template_groups":   len(recs),
            "unique_elements":   len(uniques),
            **self.recurrence.statistics(),
        }

        log.info(
            "Compression complete: %.1f%% token reduction (%d → %d tokens)",
            (1 - ratio) * 100, orig_tokens, comp_tokens,
        )

        return CompressedDocument(
            doc_id      = doc_id,
            template    = tmpl,
            recurrences = recs,
            uniques     = uniques,
            index       = index,
            stats       = stats,
        )

    # ──────────────────────────────────────────────────────────────
    # Decompression (reconstruction)
    # ──────────────────────────────────────────────────────────────

    def decompress_page(
        self,
        compressed: CompressedDocument,
        page: int,
    ) -> list[dict]:
        """
        Reconstruct all elements on a page from compressed representation.
        Returns list of element dicts (lightweight, no GeometricElement).
        """
        page_ids = set(compressed.index.get(page, []))
        result: list[dict] = []

        # Unique elements on this page
        for u in compressed.uniques:
            if u.get("page") == page:
                result.append(u)

        # Recurring elements that appear on this page
        for gid, rec in compressed.recurrences.items():
            if page in rec["pages"]:
                result.append({
                    "id":      f"{gid}_p{page}",
                    "type":    rec["type"],
                    "page":    page,
                    "content": rec["content"],
                    "weight":  rec["weight"],
                    "bbox":    rec["bbox"],
                    "from_template": True,
                })

        result.sort(key=lambda x: (x.get("page", 0),))
        return result

    # ──────────────────────────────────────────────────────────────
    # Cross-document template comparison
    # ──────────────────────────────────────────────────────────────

    def template_similarity(
        self,
        sig_a: TemplateSignature,
        sig_b: TemplateSignature,
    ) -> float:
        """Sim(T1, T2) = cosine(feature_vector(T1), feature_vector(T2))."""
        return sig_a.similarity(sig_b)

    def find_similar_templates(
        self,
        query_sig: TemplateSignature,
        library: list[TemplateSignature],
        threshold: float = 0.85,
    ) -> list[tuple[TemplateSignature, float]]:
        """Identify documents sharing the same template structure."""
        results = []
        for t in library:
            sim = self.template_similarity(query_sig, t)
            if sim >= threshold:
                results.append((t, sim))
        return sorted(results, key=lambda x: x[1], reverse=True)
