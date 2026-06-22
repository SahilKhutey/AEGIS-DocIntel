"""
AEGIS-AMDI-OS — 3D Geometry Engine
====================================
Extends 2D coordinates into full 3D spatial representation.

Coordinate System:
    x: horizontal (0-1 normalized)
    y: vertical (0-1 normalized)
    z = page index (0 to N)

Each element is positioned in 3D space:
    E_i = (x_i, y_i, z_i, w_i, h_i, d_i)

Where d_i is depth (e.g., for tables spanning pages).
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from typing import Iterable

import numpy as np

from src.core.geometric_element import GeometricElement, ElementType

logger = logging.getLogger(__name__)


@dataclass
class Point3D:
    """3D point with optional metadata."""
    x: float
    y: float
    z: float
    label: str = ""
    color: str = "#4fc3f7"
    size: float = 5.0
    metadata: dict = field(default_factory=dict)


@dataclass
class Element3D:
    """Element with full 3D extent."""
    element_id: str
    element_type: ElementType
    # 3D bounding box
    x: float
    y: float
    z: float      # page
    width: float
    height: float
    depth: float = 0.0  # cross-page depth (0 for single page)
    color: str = "#4fc3f7"
    importance: float = 1.0
    text: str = ""
    page: int = 0
    section: str | None = None

    def to_corners(self) -> np.ndarray:
        """
        Compute 8 corners of the 3D bounding box.
        Returns (8, 3) array.
        """
        hw = self.width / 2
        hh = self.height / 2
        hd = self.depth / 2
        cx, cy, cz = self.x, self.y, self.z
        return np.array([
            [cx - hw, cy - hh, cz - hd],
            [cx + hw, cy - hh, cz - hd],
            [cx + hw, cy + hh, cz - hd],
            [cx - hw, cy + hh, cz - hd],
            [cx - hw, cy - hh, cz + hd],
            [cx + hw, cy - hh, cz + hd],
            [cx + hw, cy + hh, cz + hd],
            [cx - hw, cy + hh, cz + hd],
        ])


@dataclass
class Connection3D:
    """Connection between two 3D points (for graph edges)."""
    src_id: str
    dst_id: str
    src_pos: tuple
    dst_pos: tuple
    edge_type: str = "follows"
    weight: float = 1.0


class Geometry3DEngine:
    """
    Build and query 3D representations of document geometry.

    Operations:
    - Lift 2D elements into 3D (x, y, z=page)
    - Compute 3D distances
    - Find neighboring elements in 3D space
    - Build connection graph
    """

    COLOR_PALETTE = {
        ElementType.TEXT: "#94a3b8",       # gray
        ElementType.HEADING: "#fbbf24",     # amber
        ElementType.TABLE: "#f97316",       # orange
        ElementType.FIGURE: "#a78bfa",      # purple
        ElementType.EQUATION: "#22d3ee",    # cyan
        ElementType.HEADER: "#64748b",      # dark gray
        ElementType.FOOTER: "#475569",      # darker gray
        ElementType.CAPTION: "#10b981",     # emerald
        ElementType.LIST_ITEM: "#60a5fa",   # blue
        ElementType.PARAGRAPH: "#94a3b8",   # gray
        ElementType.FORMULA: "#22d3ee",     # cyan
        ElementType.CODE: "#ec4899",        # pink
    }

    def lift_to_3d(
        self,
        elements: list[GeometricElement],
        total_pages: int,
    ) -> list[Element3D]:
        """
        Convert 2D elements to 3D by using page number as z-axis.

        Pages are stacked vertically with spacing = 1.0.
        Within each page, x, y ∈ [0, 1].
        """
        result = []
        max_pages = max(total_pages, 1)
        for e in elements:
            if e.bbox is None:
                continue
            color = self.COLOR_PALETTE.get(e.type, "#4fc3f7")
            # z value is normal page coordinate
            z = (e.page - 1) / max_pages  # normalize z to [0, 1]
            element_3d = Element3D(
                element_id=e.element_id,
                element_type=e.type,
                x=e.bbox.x0 + e.bbox.width / 2,
                y=1.0 - (e.bbox.y0 + e.bbox.height / 2),  # flip Y for display
                z=z,
                width=e.bbox.width,
                height=e.bbox.height,
                depth=1.0 / max_pages,
                color=color,
                importance=e.importance_weight,
                text=e.content[:200],
                page=e.page,
                section=e.section,
            )
            result.append(element_3d)
        return result

    def compute_distances_3d(
        self,
        elements: list[Element3D],
    ) -> np.ndarray:
        """
        Compute pairwise Euclidean distances in 3D.

        Returns NxN distance matrix.
        """
        n = len(elements)
        if n == 0:
            return np.zeros((0, 0))
        positions = np.array([(e.x, e.y, e.z) for e in elements])
        diffs = positions[:, None, :] - positions[None, :, :]
        return np.sqrt(np.sum(diffs ** 2, axis=-1))

    def find_neighbors_3d(
        self,
        target: Element3D,
        elements: list[Element3D],
        radius: float = 0.1,
        max_neighbors: int = 10,
    ) -> list[Element3D]:
        """Find k-nearest elements within radius."""
        neighbors = []
        for e in elements:
            if e.element_id == target.element_id:
                continue
            d = math.sqrt(
                (e.x - target.x) ** 2 +
                (e.y - target.y) ** 2 +
                (e.z - target.z) ** 2
            )
            if d <= radius:
                neighbors.append((d, e))
        neighbors.sort(key=lambda x: x[0])
        return [e for _, e in neighbors[:max_neighbors]]

    def build_connections(
        self,
        elements: list[Element3D],
        same_page: bool = True,
    ) -> list[Connection3D]:
        """
        Build connection graph in 3D space.

        For each element, connect to:
        - k nearest neighbors on same page
        - 1 nearest neighbor on next page (cross-page continuity)
        """
        connections = []
        for e in elements:
            # Same-page connections
            if same_page:
                page_elements = [x for x in elements if x.page == e.page]
                # Sort page elements by 2D proximity on the page
                page_elements_sorted = sorted(
                    page_elements,
                    key=lambda x: math.sqrt((x.x - e.x) ** 2 + (x.y - e.y) ** 2)
                )
                count = 0
                for other in page_elements_sorted:
                    if other.element_id == e.element_id:
                        continue
                    if count >= 3:
                        break
                    connections.append(Connection3D(
                        src_id=e.element_id,
                        dst_id=other.element_id,
                        src_pos=(e.x, e.y, e.z),
                        dst_pos=(other.x, other.y, other.z),
                        edge_type="spatial_proximity",
                        weight=e.importance * other.importance,
                    ))
                    count += 1
            # Cross-page connection (next page)
            next_page_elements = [x for x in elements if x.page == e.page + 1]
            if next_page_elements:
                nearest = min(
                    next_page_elements,
                    key=lambda x: math.sqrt(
                        (x.x - e.x) ** 2 + (x.y - e.y) ** 2 + (x.z - e.z) ** 2
                    ),
                )
                connections.append(Connection3D(
                    src_id=e.element_id,
                    dst_id=nearest.element_id,
                    src_pos=(e.x, e.y, e.z),
                    dst_pos=(nearest.x, nearest.y, nearest.z),
                    edge_type="next_page",
                    weight=0.5,
                ))
        return connections

    def compute_field_3d(
        self,
        query: tuple,
        elements: list[Element3D],
        epsilon: float = 1e-3,
    ) -> float:
        """
        Compute information field strength at query point.
        Φ(x, y, z) = Σ W_i / d_i²
        """
        total = 0.0
        for e in elements:
            d_sq = (
                (e.x - query[0]) ** 2 +
                (e.y - query[1]) ** 2 +
                (e.z - query[2]) ** 2
            ) + epsilon
            total += e.importance / d_sq
        return total

    def field_heatmap_3d(
        self,
        elements: list[Element3D],
        plane: str = "xy",
        page: int | None = None,
        resolution: int = 32,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Compute 3D field heatmap on a 2D slice.

        Args:
            elements: list of Element3D
            plane: 'xy', 'xz', or 'yz'
            page: restrict to specific page (xy plane only)
            resolution: grid resolution
        """
        coords = np.linspace(0, 1, resolution)
        if plane == "xy":
            grid_x, grid_y = np.meshgrid(coords, coords)
            max_pages = max([e.page for e in elements]) if elements else 1
            z_val = (page - 0.5) / max_pages if page else 0.5
            elements_filtered = [
                e for e in elements
                if not page or e.page == page
            ]
            heatmap = np.zeros_like(grid_x)
            for i in range(resolution):
                for j in range(resolution):
                    heatmap[i, j] = self.compute_field_3d(
                        (grid_x[i, j], grid_y[i, j], z_val),
                        elements_filtered,
                    )
            return grid_x, grid_y, heatmap
        elif plane == "xz":
            grid_x, grid_z = np.meshgrid(coords, coords)
            heatmap = np.zeros_like(grid_x)
            for i in range(resolution):
                for j in range(resolution):
                    heatmap[i, j] = self.compute_field_3d(
                        (grid_x[i, j], 0.5, grid_z[i, j]),
                        elements,
                    )
            return grid_x, grid_z, heatmap
        else:  # yz
            grid_y, grid_z = np.meshgrid(coords, coords)
            heatmap = np.zeros_like(grid_y)
            for i in range(resolution):
                for j in range(resolution):
                    heatmap[i, j] = self.compute_field_3d(
                        (0.5, grid_y[i, j], grid_z[i, j]),
                        elements,
                    )
            return grid_y, grid_z, heatmap

    def statistics(self, elements: list[Element3D]) -> dict:
        """Compute statistics about 3D representation."""
        if not elements:
            return {}
        x_coords = [e.x for e in elements]
        y_coords = [e.y for e in elements]
        z_coords = [e.z for e in elements]
        return {
            "n_elements": len(elements),
            "x_range": (min(x_coords), max(x_coords)),
            "y_range": (min(y_coords), max(y_coords)),
            "z_range": (min(z_coords), max(z_coords)),
            "mean_importance": float(np.mean([e.importance for e in elements])),
            "n_pages": len(set(e.page for e in elements)),
        }
