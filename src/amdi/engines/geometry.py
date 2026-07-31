"""Computational geometry engine re-exports."""

from __future__ import annotations

from amdi.math_concepts.computational_geometry import KDTree, convex_hull, voronoi_areas

class GeometryEngine:
    """Backwards compatibility shim for GeometryEngine."""
    pass

SpatialStats = dict

__all__ = ["GeometryEngine", "SpatialStats", "convex_hull", "voronoi_areas", "KDTree"]
