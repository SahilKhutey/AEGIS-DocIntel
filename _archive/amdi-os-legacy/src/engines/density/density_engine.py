"""
AEGIS-AMDI-OS — Information Density Engine
===========================================
Implements Formula §14: D = N / A
"""
from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import Iterable, List, Dict, Set, Tuple, Any

import numpy as np

from src.engines.coordinate.coordinate_engine import NormalizedCoordinate
from src.engines.entropy.entropy_engine import EntropyEngine

logger = logging.getLogger("amdi.math.density")


@dataclass
class DensityMetric:
    element_id: str
    page: int
    area_ratio: float        # AR = w·h
    token_density: float     # tokens / area
    entropy_density: float   # H / area
    information_density: float # composite
    quadrant: str            # "TL", "TR", "BL", "BR"


class DensityEngine:
    """
    Compute information density per element and per page.
    D = N / A
    """

    def __init__(self, entropy: EntropyEngine | None = None) -> None:
        self.entropy = entropy or EntropyEngine()

    # ------------------------------------------------------------------ #
    # Formula §14                                                         #
    # ------------------------------------------------------------------ #

    @staticmethod
    def token_density(text: str, area: float) -> float:
        """D = N / A"""
        if area <= 0:
            return 0.0
        return len(text.split()) / area

    def entropy_density(self, text: str, area: float) -> float:
        """H / A"""
        if area <= 0:
            return 0.0
        return self.entropy.shannon_entropy(text) / area

    def composite_density(self, text: str, area: float) -> float:
        """
        Composite density:
            D_composite = (N · H) / A²
        """
        if area <= 0:
            return 0.0
        n = len(text.split())
        h = self.entropy.shannon_entropy(text)
        return (n * h) / (area ** 2 + 1e-9)

    # ------------------------------------------------------------------ #
    # Per-element and per-page                                             #
    # ------------------------------------------------------------------ #

    def profile_elements(self, coords: List[NormalizedCoordinate]) -> List[DensityMetric]:
        """Compute density for all elements."""
        out: List[DensityMetric] = []
        for c in coords:
            area = c.area_ratio()
            out.append(DensityMetric(
                element_id=c.element_id,
                page=c.p,
                area_ratio=area,
                token_density=self.token_density(c.content, area),
                entropy_density=self.entropy_density(c.content, area),
                information_density=self.composite_density(c.content, area),
                quadrant=self._quadrant(c),
            ))
        return out

    def page_density(self, page: int, coords: List[NormalizedCoordinate]) -> Dict[str, Any]:
        """Aggregate density for a specific page."""
        page_coords = [c for c in coords if c.p == page]
        if not page_coords:
            return {"page": page, "density": 0.0, "n_elements": 0}
        total_area = sum(c.area_ratio() for c in page_coords)
        total_tokens = sum(len(c.content.split()) for c in page_coords if c.content)
        return {
            "page": page,
            "n_elements": len(page_coords),
            "total_area": total_area,
            "total_tokens": total_tokens,
            "tokens_per_area": total_tokens / total_area if total_area > 0 else 0.0,
        }

    @staticmethod
    def _quadrant(coord: NormalizedCoordinate) -> str:
        x, y = coord.x, coord.y
        if x < 0.5 and y < 0.5: return "TL"
        if x >= 0.5 and y < 0.5: return "TR"
        if x < 0.5 and y >= 0.5: return "BL"
        return "BR"

    def find_dense_regions(
        self,
        coords: List[NormalizedCoordinate],
        top_k: int = 5,
    ) -> List[NormalizedCoordinate]:
        """Find top-K most information-dense elements."""
        metrics = self.profile_elements(coords)
        metrics.sort(key=lambda m: m.information_density, reverse=True)
        top_ids = {m.element_id for m in metrics[:top_k]}
        return [c for c in coords if c.element_id in top_ids]
