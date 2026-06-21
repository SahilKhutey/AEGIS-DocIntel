"""
Simplicial Complex Construction
==============================

Mathematical Foundation:
-----------------------
A k-simplex is the convex hull of (k+1) affinely independent points.
σ = conv({v₀, v₁, ..., v_k})

A simplicial complex K is a collection of simplices closed under
taking faces: if σ ∈ K then all faces of σ are also in K.

Examples:
- 0-simplex: vertex
- 1-simplex: edge
- 2-simplex: triangle (filled)
- 3-simplex: tetrahedron

In AMDI-OS context:
- Vertices  = document elements (paragraphs, tables, figures)
- Edges     = structural relationships (containment, reference)
- Triangles = multi-element relationships (e.g., table+caption+section)
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

from .exceptions import TopologyEngineError


@dataclass(frozen=True)
class Simplex:
    """
    Represents a k-simplex.

    A Simplex is identified by its vertices. Two simplices with the same vertices
    are considered identical.

    Attributes
    ----------
    vertices : FrozenSet[int]
        The set of vertex IDs that define this simplex.
    weight : float
        Optional filtration weight (birth time) for persistent homology.
    """

    vertices: FrozenSet[int]
    weight: float = 0.0

    def __post_init__(self) -> None:
        if len(self.vertices) == 0:
            raise TopologyEngineError("Simplex must contain at least one vertex.")

    @property
    def dimension(self) -> int:
        """The dimension of the simplex: k = |vertices| - 1."""
        return len(self.vertices) - 1

    def faces(self) -> List["Simplex"]:
        """Return all proper faces of this simplex."""
        if len(self.vertices) <= 1:
            return []
        face_list: List[Simplex] = []
        vertices_list = list(self.vertices)
        for r in range(1, len(vertices_list)):
            for combo in itertools.combinations(vertices_list, r):
                face_list.append(Simplex(frozenset(combo), self.weight))
        return face_list

    def is_face_of(self, other: "Simplex") -> bool:
        """Return True if this simplex is a face of the other simplex."""
        return self.vertices.issubset(other.vertices) and self.vertices != other.vertices


@dataclass
class SimplicialComplex:
    """
    An abstract simplicial complex.

    Attributes
    ----------
    simplices : Dict[int, List[Simplex]]
        Dictionary mapping dimension → list of simplices of that dimension.
    """

    simplices: Dict[int, List[Simplex]] = field(default_factory=dict)
    _max_dimension: int = 0

    def add_simplex(self, simplex: Simplex) -> None:
        """Add a simplex and all its faces to the complex."""
        dim = simplex.dimension
        if dim not in self.simplices:
            self.simplices[dim] = []
        
        # Check if already exists to keep minimum weight
        found = False
        for i, s in enumerate(self.simplices[dim]):
            if s.vertices == simplex.vertices:
                found = True
                if simplex.weight < s.weight:
                    self.simplices[dim][i] = simplex
                    # Recursively update faces
                    for face in simplex.faces():
                        self.add_simplex(face)
                break
        
        if not found:
            self.simplices[dim].append(simplex)
            if dim > self._max_dimension:
                self._max_dimension = dim
            # add all faces
            for face in simplex.faces():
                self.add_simplex(face)

    def add_simplices(self, simplices: Iterable[Simplex]) -> None:
        """Add a collection of simplices."""
        for s in simplices:
            self.add_simplex(s)

    def n_simplices(self, dim: int) -> int:
        """Number of simplices of dimension dim."""
        return len(self.simplices.get(dim, []))

    @property
    def num_vertices(self) -> int:
        """Number of distinct vertices."""
        if 0 not in self.simplices:
            return 0
        return len(self.simplices[0])

    @property
    def num_edges(self) -> int:
        """Number of 1-simplices (edges)."""
        return self.n_simplices(1)

    @property
    def num_triangles(self) -> int:
        """Number of 2-simplices (filled triangles)."""
        return self.n_simplices(2)

    @property
    def max_dimension(self) -> int:
        """Maximum dimension present in the complex."""
        return self._max_dimension

    def vertices(self) -> Set[int]:
        """Return the set of all vertices in the complex."""
        if 0 not in self.simplices:
            return set()
        return {next(iter(s.vertices)) for s in self.simplices[0]}

    def __len__(self) -> int:
        return sum(len(simps) for simps in self.simplices.values())
