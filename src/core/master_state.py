"""
AEGIS-DocIntel — Master Document State
========================================
Implements the 10-tuple Master State D = (P, S, G, R, F, M, T, X, H, E)
as specified in Section 5.1 of the AMDI-OS Extended Monograph.

Each field below corresponds directly to one layer of the formal tuple.
Fields whose backing engine is not yet "Hardened" per Appendix E of the
monograph are explicitly nullable and carry an `is_mock` / `is_proposed`
flag rather than silently returning placeholder data as if it were real —
this makes an incomplete layer visible to callers instead of hidden.
"""
from __future__ import annotations

import math
import uuid
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Element(BaseModel):
    """Section 5.2 — 8-tuple element representation: E_i = (x, y, w, h, p, θ, t, c)."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    x: float = Field(..., ge=0.0, le=1.0, description="Normalized top-left x")
    y: float = Field(..., ge=0.0, le=1.0, description="Normalized top-left y")
    w: float = Field(..., ge=0.0, le=1.0, description="Normalized width")
    h: float = Field(..., ge=0.0, le=1.0, description="Normalized height")
    page: int = Field(..., ge=1, description="1-indexed page number")
    theta: float = Field(0.0, ge=0.0, lt=2 * math.pi, description="Rotation angle, radians")
    element_type: str = Field(..., description="text | table | figure | heading | ...")
    content: str | bytes = Field(default="")
    element_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    tenant_id: str = Field(default="default")

    @field_validator("theta", mode="before")
    @classmethod
    def _wrap_angle(cls, v: float) -> float:
        wrapped = float(v) % (2.0 * math.pi)
        if wrapped >= 2.0 * math.pi or math.isclose(wrapped, 2.0 * math.pi, abs_tol=1e-12):
            wrapped = 0.0
        return wrapped


class PageRepresentation(BaseModel):
    """Section 5.2 — a page P_i is an ordered set of elements."""

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    page_number: int = Field(..., ge=1)
    elements: list[Element] = Field(default_factory=list)
    physical_width: float = Field(..., gt=0, description="W_p — physical page width")
    physical_height: float = Field(..., gt=0, description="H_p — physical page height")


class LayerStatus(BaseModel):
    """
    Honesty flag for a layer, cross-referencing Appendix E of the monograph.
    Every non-'hardened' layer must set this explicitly rather than silently
    returning mock or partial data indistinguishable from the real thing.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    is_hardened: bool = False
    is_mock: bool = False
    is_proposed: bool = False
    note: str = ""


class MasterState(BaseModel):
    """
    D = (P, S, G, R, F, M, T, X, H, E) — Section 5.1 of the Extended Monograph.
    One instance per ingested document. This is the single object every
    engine reads from and writes to — no engine should invent its own
    parallel representation of document structure going forward.
    """

    model_config = ConfigDict(arbitrary_types_allowed=True, extra="allow")

    doc_id: str

    # P — ordered set of page representations
    pages: list[PageRepresentation] = Field(default_factory=list)
    pages_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # S — semantic embedding layer
    semantic_embeddings: Optional[list[list[float]]] = None
    semantic_status: LayerStatus = Field(
        default_factory=lambda: LayerStatus(
            is_mock=True,
            note="Real encoder proposed per monograph Appendix E; "
            "mock vectors used unless sentence-transformers is installed.",
        )
    )

    # G — geometric coordinate layer (derived from pages; kept separate per
    # the monograph's own layer separation, since G captures pairwise
    # relations, not raw element coordinates)
    geometric_adjacency: Optional[dict] = None
    geometric_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # R — structural recurrence layer
    recurrence_patterns: Optional[list[dict]] = None
    recurrence_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # F — token frequency/weight layer
    frequency_weights: Optional[dict[str, float]] = None
    frequency_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # M — table-matrix relational layer
    tables: Optional[list[dict]] = None
    matrix_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # T — clustered template-fingerprint layer
    template_fingerprint: Optional[str] = None
    template_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # X — structural linkage graph layer
    linkage_graph: Optional[dict] = None
    linkage_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    # H — hierarchical coordinate layer
    hierarchy: Optional[dict] = None
    hierarchy_status: LayerStatus = Field(
        default_factory=lambda: LayerStatus(
            is_proposed=True,
            note="Persistent-homology-based hierarchy proposed, "
            "not yet evaluated per monograph Appendix E.",
        )
    )

    # E — Shannon-entropy layer
    entropy_profile: Optional[dict[str, float]] = None
    entropy_status: LayerStatus = Field(default_factory=lambda: LayerStatus(is_hardened=True))

    schema_version: str = "1.0.0"

    # Internal reference to GeometricElements if set by pipeline
    _raw_elements: Optional[list[Any]] = None

    def set_geometric_elements(self, elements: list[Any]) -> None:
        """Store underlying GeometricElement objects for high-performance extraction."""
        self._raw_elements = list(elements)

    def get_geometric_elements(self) -> list[Any]:
        """Return the GeometricElement list for this document, synthesizing if needed."""
        if self._raw_elements is not None:
            return list(self._raw_elements)

        from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement

        synthesized: list[GeometricElement] = []
        for page in self.pages:
            for el in page.elements:
                etype = ElementType.PARAGRAPH
                try:
                    etype = ElementType(el.element_type)
                except ValueError:
                    pass
                bbox = BoundingBox(
                    x0=el.x,
                    y0=el.y,
                    x1=min(1.0, el.x + el.w),
                    y1=min(1.0, el.y + el.h),
                )
                content_str = (
                    el.content
                    if isinstance(el.content, str)
                    else el.content.decode("utf-8", errors="replace")
                )
                synthesized.append(
                    GeometricElement(
                        element_id=getattr(el, "element_id", None)
                        or f"{self.doc_id}_p{el.page}_{len(synthesized)}",
                        doc_id=self.doc_id,
                        tenant_id=getattr(el, "tenant_id", "default"),
                        page=el.page,
                        type=etype,
                        content=content_str,
                        bbox=bbox,
                    )
                )
        return synthesized

    def get_geometric_tables(self) -> list[Any]:
        """Return all table elements belonging to this MasterState."""
        from src.engines.geometry.element import ElementType

        return [
            e
            for e in self.get_geometric_elements()
            if getattr(e, "type", None) == ElementType.TABLE
        ]
