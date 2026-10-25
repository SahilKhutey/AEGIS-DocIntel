"""
Geometry Dashboard
===================

Visualizes document spatial coordinates, bounding boxes,
and geometric relationships.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class BoundingBox:
    """A bounding box element."""

    element_id: str
    x: float
    y: float
    width: float
    height: float
    page: int = 1
    element_type: str = "unknown"
    confidence: float = 1.0
    label: str = ""

    def to_dict(self) -> dict:
        return {
            "element_id": self.element_id,
            "x": round(self.x, 2),
            "y": round(self.y, 2),
            "width": round(self.width, 2),
            "height": round(self.height, 2),
            "page": self.page,
            "element_type": self.element_type,
            "confidence": round(self.confidence, 4),
            "label": self.label,
        }


@dataclass
class GeometryViewData:
    """Data for geometry dashboard."""

    document_id: str
    page_count: int
    bounding_boxes: List[BoundingBox] = field(default_factory=list)
    coordinate_system: str = "pixel"
    canvas_size: Dict[str, float] = field(default_factory=lambda: {"width": 800, "height": 1000})
    element_type_counts: Dict[str, int] = field(default_factory=dict)
    average_confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "page_count": self.page_count,
            "bounding_boxes": [b.to_dict() for b in self.bounding_boxes],
            "coordinate_system": self.coordinate_system,
            "canvas_size": self.canvas_size,
            "element_type_counts": self.element_type_counts,
            "average_confidence": round(self.average_confidence, 4),
        }


class GeometryDashboard:
    """Geometry dashboard backend API."""

    def __init__(self) -> None:
        self.documents: Dict[str, GeometryViewData] = {}

    def add_bounding_box(
        self,
        document_id: str,
        bbox: BoundingBox,
    ) -> None:
        if document_id not in self.documents:
            self.documents[document_id] = GeometryViewData(
                document_id=document_id, page_count=1
            )
        view = self.documents[document_id]
        view.bounding_boxes.append(bbox)
        # update stats
        view.element_type_counts[bbox.element_type] = (
            view.element_type_counts.get(bbox.element_type, 0) + 1
        )

    def set_page_count(self, document_id: str, page_count: int) -> None:
        if document_id not in self.documents:
            self.documents[document_id] = GeometryViewData(
                document_id=document_id, page_count=page_count
            )
        self.documents[document_id].page_count = page_count

    def get_view(self, document_id: str, page: Optional[int] = None) -> GeometryViewData:
        if document_id not in self.documents:
            return GeometryViewData(document_id=document_id, page_count=0)
        view = self.documents[document_id]
        if page is not None:
            # filter by page
            page_boxes = [b for b in view.bounding_boxes if b.page == page]
            return GeometryViewData(
                document_id=document_id,
                page_count=view.page_count,
                bounding_boxes=page_boxes,
                coordinate_system=view.coordinate_system,
                canvas_size=view.canvas_size,
                element_type_counts=view.element_type_counts,
                average_confidence=self._mean_confidence(page_boxes),
            )
        view.average_confidence = self._mean_confidence(view.bounding_boxes)
        return view

    @staticmethod
    def _mean_confidence(boxes: List[BoundingBox]) -> float:
        if not boxes:
            return 0.0
        return float(sum(b.confidence for b in boxes) / len(boxes))
