"""
Document Manifold Representation
================================

Models a document as a topological manifold represented by a point cloud
of geometric elements (using spatial coordinates or text embeddings).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional

import numpy as np

from src.engines.geometry.element import GeometricElement
from .distance_matrix import DistanceMatrix


@dataclass
class DocumentManifold:
    """
    Topological manifold representing a document.

    Attributes
    ----------
    elements : List[GeometricElement]
        List of geometric document elements.
    coordinates : np.ndarray
        (n, d) array of coordinates or embedding vectors representing each element.
    labels : List[str]
        Optional list of element identifiers.
    """

    elements: List[GeometricElement]
    coordinates: np.ndarray
    labels: List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if len(self.elements) != self.coordinates.shape[0]:
            raise ValueError("Number of elements must match coordinate dimensions.")
        if not self.labels:
            self.labels = [e.element_id for e in self.elements]

    @classmethod
    def from_elements(
        cls,
        elements: List[GeometricElement],
        use_spatial: bool = True,
        use_semantic: bool = False,
        embedding_service: Optional[any] = None,
    ) -> DocumentManifold:
        """
        Build a DocumentManifold from elements.

        Parameters
        ----------
        elements : List[GeometricElement]
            Geometric elements to represent.
        use_spatial : bool
            Use 2D bounding box center as coordinates (default: True).
        use_semantic : bool
            Use semantic text embeddings as coordinates (default: False).
        embedding_service : Optional[any]
            Service with an `embed_documents` method to compute embeddings.
        """
        n = len(elements)
        if n == 0:
            raise ValueError("Cannot construct manifold from empty elements.")

        if use_semantic and embedding_service is not None:
            texts = [e.content for e in elements]
            embeddings = embedding_service.embed_documents(texts)
            coords = np.asarray(embeddings, dtype=np.float64)
        else:
            coords_list = []
            for e in elements:
                if e.bbox:
                    coords_list.append(list(e.bbox.center))
                else:
                    coords_list.append([0.0, 0.0])
            coords = np.asarray(coords_list, dtype=np.float64)

        labels = [e.element_id for e in elements]
        return cls(elements=elements, coordinates=coords, labels=labels)

    def compute_distance_matrix(self, metric: str = "euclidean") -> DistanceMatrix:
        """Compute the pairwise distance matrix between elements."""
        return DistanceMatrix.from_coordinates(self.coordinates, self.labels, metric=metric)
