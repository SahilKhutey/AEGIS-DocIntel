"""
AEGIS-AMDI-OS — Coordinate Engine
====================================
E_i = (x_i, y_i, w_i, h_i, p_i, θ_i, t_i, c_i)
Implements formulas §3-§8 from MathematicalFoundations.md
"""
from __future__ import annotations

import math
import logging
from dataclasses import dataclass
from typing import Optional, Tuple, List, Dict, Any
import numpy as np

from src.engines.geometry.element import BoundingBox, ElementType, GeometricElement

logger = logging.getLogger("amdi.math.coordinate")


@dataclass
class NormalizedCoordinate:
    """E_i in normalized form (Theorem 4.1: scale invariant)."""
    x: float          # ∈ [0, 1]
    y: float          # ∈ [0, 1]
    w: float          # ∈ [0, 1]
    h: float          # ∈ [0, 1]
    p: int            # page
    theta: float      # rotation in radians
    type: ElementType
    content: str = ""
    element_id: str = ""

    def vector(self) -> np.ndarray:
        return np.array([self.x, self.y, self.w, self.h, self.p, self.theta], dtype=np.float32)

    def area_ratio(self) -> float:
        """AR_i = w_i · h_i  (Theorem §7)"""
        return self.w * self.h

    def reading_order_key(self) -> Tuple[float, float]:
        """RO(E_i) = (y, x)  (Theorem §8)"""
        return (self.y, self.x)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "x": round(self.x, 4), 
            "y": round(self.y, 4),
            "w": round(self.w, 4), 
            "h": round(self.h, 4),
            "p": self.p, 
            "theta": round(self.theta, 4),
            "type": self.type.value, 
            "element_id": self.element_id,
        }


class CoordinateEngine:
    """
    Implements the Coordinate formulation (Formulas §3-§8).
    Provides distance, alignment, and reading-order operations.
    """

    @staticmethod
    def normalize(
        bbox: BoundingBox,
        page_width: float,
        page_height: float,
        page: int,
        theta: float = 0.0,
        etype: ElementType = ElementType.TEXT,
        content: str = "",
        element_id: str = "",
    ) -> NormalizedCoordinate:
        """Apply formulas §4: x̃ = x/W, ỹ = y/H, etc."""
        if page_width <= 0 or page_height <= 0:
            return NormalizedCoordinate(0.0, 0.0, 0.0, 0.0, page, theta, etype, content, element_id)
        return NormalizedCoordinate(
            x=bbox.x0 / page_width,
            y=bbox.y0 / page_height,
            w=bbox.width / page_width,
            h=bbox.height / page_height,
            p=page,
            theta=theta,
            type=etype,
            content=content,
            element_id=element_id,
        )

    # ------------------------------------------------------------------ #
    # Formula §5: Geometric distance                                      #
    # ------------------------------------------------------------------ #

    @staticmethod
    def distance(a: NormalizedCoordinate, b: NormalizedCoordinate) -> float:
        """d_ij = √[(x_i - x_j)² + (y_i - y_j)²]"""
        if a.p != b.p:
            # Cross-page: add page distance penalty
            page_penalty = abs(a.p - b.p) * 1.5
            return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2) + page_penalty
        return math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)

    # ------------------------------------------------------------------ #
    # Formula §6: Alignment score                                          #
    # ------------------------------------------------------------------ #

    @staticmethod
    def alignment_horizontal(a: NormalizedCoordinate, b: NormalizedCoordinate, W: float = 1.0) -> float:
        """A_x = 1 - |x_i - x_j| / W"""
        return max(0.0, 1.0 - abs(a.x - b.x) / W)

    @staticmethod
    def alignment_vertical(a: NormalizedCoordinate, b: NormalizedCoordinate, H: float = 1.0) -> float:
        """A_y = 1 - |y_i - y_j| / H"""
        return max(0.0, 1.0 - abs(a.y - b.y) / H)

    @staticmethod
    def alignment(a: NormalizedCoordinate, b: NormalizedCoordinate) -> float:
        """A = (A_x + A_y) / 2"""
        return (CoordinateEngine.alignment_horizontal(a, b)
                + CoordinateEngine.alignment_vertical(a, b)) / 2.0

    # ------------------------------------------------------------------ #
    # Formula §7: Area ratio                                              #
    # ------------------------------------------------------------------ #

    @staticmethod
    def area_importance(coord: NormalizedCoordinate) -> float:
        """I_A = AR = w·h"""
        return coord.area_ratio()

    # ------------------------------------------------------------------ #
    # Formula §8: Reading order                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def reading_order(coords: List[NormalizedCoordinate]) -> List[NormalizedCoordinate]:
        """Sort by RO(E_i) = (y, x)"""
        return sorted(coords, key=lambda c: c.reading_order_key())

    # ------------------------------------------------------------------ #
    # Batch operations                                                     #
    # ------------------------------------------------------------------ #

    @staticmethod
    def pairwise_distances(coords: List[NormalizedCoordinate]) -> np.ndarray:
        """Compute full NxN distance matrix."""
        n = len(coords)
        D = np.zeros((n, n), dtype=np.float32)
        for i in range(n):
            for j in range(i + 1, n):
                d = CoordinateEngine.distance(coords[i], coords[j])
                D[i, j] = d
                D[j, i] = d
        return D

    @staticmethod
    def pairwise_alignment(coords: List[NormalizedCoordinate]) -> np.ndarray:
        """Compute full NxN alignment matrix."""
        n = len(coords)
        A = np.zeros((n, n), dtype=np.float32)
        for i in range(n):
            for j in range(n):
                if i != j:
                    A[i, j] = CoordinateEngine.alignment(coords[i], coords[j])
        return A
