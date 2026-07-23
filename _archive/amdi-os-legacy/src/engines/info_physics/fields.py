"""
Information Field Theory
=========================

Mathematical Definition:
-----------------------
Every document generates a continuous scalar field Φ: R² → R defined by:

    Φ(x, y) = Σ_i W_i / (d((x, y), v_i)² + ε)

where:
    W_i    weight / mass of source element i
    v_i    position of element i
    d      Euclidean distance
    ε      smoothing constant

This produces a heatmap of information density useful for:
- Attention maps
- Priority maps
- Retrieval maps

Field derivatives:
- Gradient:  ∇Φ = (∂Φ/∂x, ∂Φ/∂y)        — direction of steepest ascent
- Laplacian: ∇²Φ                            — local concentration / divergence
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple

import numpy as np

from .exceptions import FieldComputationError, InvalidDocumentError


@dataclass
class FieldMap:
    """
    2D scalar field representation.

    Attributes
    ----------
    values : np.ndarray
        (H, W) field values.
    x_grid : np.ndarray
        (W,) x-coordinates.
    y_grid : np.ndarray
        (H,) y-coordinates.
    source_positions : np.ndarray
        (n, 2) source element positions.
    source_weights : np.ndarray
        (n,) source weights.
    """

    values: np.ndarray
    x_grid: np.ndarray
    y_grid: np.ndarray
    source_positions: np.ndarray
    source_weights: np.ndarray

    @property
    def shape(self) -> Tuple[int, int]:
        return self.values.shape

    @property
    def max_value(self) -> float:
        return float(self.values.max())

    @property
    def min_value(self) -> float:
        return float(self.values.min())

    @property
    def max_position(self) -> Tuple[int, int]:
        idx = np.unravel_index(int(np.argmax(self.values)), self.values.shape)
        return (int(idx[0]), int(idx[1]))

    def gradient(self) -> Tuple[np.ndarray, np.ndarray]:
        """Compute gradient (∂Φ/∂y, ∂Φ/∂x) via finite differences."""
        dy, dx = np.gradient(self.values)
        return dy, dx

    def laplacian(self) -> np.ndarray:
        """Compute Laplacian ∇²Φ via finite differences."""
        dy, dx = self.gradient()
        d2y = np.gradient(dy, axis=0)
        d2x = np.gradient(dx, axis=1)
        return d2y + d2x


@dataclass
class InformationField:
    """Container for information field result."""

    field_map: FieldMap
    max_density_location: Tuple[int, int]
    total_field_energy: float
    mean_field_strength: float


class FieldCalculator:
    """
    Builds continuous information fields from discrete sources.
    """

    def __init__(self, epsilon: float = 1e-3) -> None:
        self.epsilon = epsilon

    def compute(
        self,
        positions: np.ndarray,
        weights: np.ndarray,
        grid_size: Tuple[int, int] = (50, 50),
        bbox: Optional[Tuple[float, float, float, float]] = None,
    ) -> InformationField:
        """
        Compute the information field.

        Parameters
        ----------
        positions : np.ndarray
            (n, 2) source positions.
        weights : np.ndarray
            (n,) source weights.
        grid_size : Tuple[int, int]
            (H, W) output grid resolution.
        bbox : Optional[Tuple[float, float, float, float]]
            (x_min, y_min, x_max, y_max). If None, inferred.
        """
        pos = np.asarray(positions, dtype=np.float64)
        w = np.asarray(weights, dtype=np.float64)
        if pos.ndim != 2 or pos.shape[1] != 2:
            raise InvalidDocumentError("positions must be (n, 2).")
        if w.shape[0] != pos.shape[0]:
            raise InvalidDocumentError("weights length mismatch.")
        if pos.shape[0] == 0:
            raise InvalidDocumentError("Empty positions.")

        if bbox is None:
            x_min, y_min = pos.min(axis=0) - 1.0
            x_max, y_max = pos.max(axis=0) + 1.0
        else:
            x_min, y_min, x_max, y_max = bbox

        if x_max <= x_min or y_max <= y_min:
            raise FieldComputationError("Invalid bounding box.")

        H, W = grid_size
        x_grid = np.linspace(x_min, x_max, W)
        y_grid = np.linspace(y_min, y_max, H)
        X, Y = np.meshgrid(x_grid, y_grid)

        # build field
        values = np.zeros((H, W), dtype=np.float64)
        for i in range(pos.shape[0]):
            dx = X - pos[i, 0]
            dy = Y - pos[i, 1]
            d2 = dx ** 2 + dy ** 2 + self.epsilon
            values += w[i] / d2

        field_map = FieldMap(
            values=values,
            x_grid=x_grid,
            y_grid=y_grid,
            source_positions=pos,
            source_weights=w,
        )
        max_loc = field_map.max_position
        total_energy = float(values.sum())
        mean_strength = float(values.mean())

        return InformationField(
            field_map=field_map,
            max_density_location=max_loc,
            total_field_energy=total_energy,
            mean_field_strength=mean_strength,
        )

    def attention_map(
        self,
        positions: np.ndarray,
        weights: np.ndarray,
        grid_size: Tuple[int, int] = (64, 64),
        normalize: bool = True,
    ) -> np.ndarray:
        """
        Produce a 2D attention heatmap (optionally normalized to [0, 1]).
        """
        info = self.compute(positions, weights, grid_size)
        heatmap = info.field_map.values
        if normalize:
            h_min, h_max = heatmap.min(), heatmap.max()
            if h_max > h_min:
                heatmap = (heatmap - h_min) / (h_max - h_min)
            else:
                heatmap = np.zeros_like(heatmap)
        return heatmap

    def priority_map(
        self,
        positions: np.ndarray,
        weights: np.ndarray,
        threshold: float = 0.5,
        grid_size: Tuple[int, int] = (64, 64),
    ) -> np.ndarray:
        """
        Binary priority map: 1 where field ≥ threshold, else 0.
        """
        heatmap = self.attention_map(positions, weights, grid_size)
        return (heatmap >= threshold).astype(np.float64)