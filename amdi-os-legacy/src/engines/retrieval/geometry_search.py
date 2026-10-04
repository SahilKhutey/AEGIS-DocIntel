"""

Geometry Search

===============



Spatial proximity search over document element coordinates.

Uses:

- k-NN by Euclidean distance

- Range queries (radius search)

- R-tree-like spatial filtering

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .exceptions import EmptyIndexError





@dataclass

class GeometryResult:

    """A single geometry search result."""



    item_id: Any

    distance: float

    similarity: float

    rank: int

    location: Tuple[float, ...] = field(default_factory=tuple)

    metadata: Dict[str, Any] = field(default_factory=dict)





class GeometrySearch:

    """

    Spatial proximity search.



    Mathematical Foundation:

        Euclidean distance:

            d(p, q) = √(Σ (p_i - q_i)²)



        Similarity:

            sim(p, q) = 1 / (1 + d(p, q))



        Bounding box check (for range queries):

            |p_i - q_i| ≤ r_i  for each dimension

    """



    def __init__(self, metric: str = "euclidean") -> None:

        self.metric = metric

        self.points: Dict[Any, np.ndarray] = {}

        self.metadata: Dict[Any, Dict[str, Any]] = {}



    def add(

        self,

        item_id: Any,

        coordinates: np.ndarray,

        metadata: Optional[Dict[str, Any]] = None,

    ) -> None:

        """Add a spatial point."""

        c = np.asarray(coordinates, dtype=np.float64)

        if c.ndim != 1:

            raise ValueError("coordinates must be 1-D.")

        self.points[item_id] = c

        if metadata is not None:

            self.metadata[item_id] = metadata



    def knn(

        self,

        query_coordinates: np.ndarray,

        k: int = 10,

    ) -> List[GeometryResult]:

        """k-Nearest Neighbors search."""

        if not self.points:

            raise EmptyIndexError("Geometry index is empty.")

        q = np.asarray(query_coordinates, dtype=np.float64)

        if q.ndim != 1:

            raise ValueError("query must be 1-D.")

        distances: List[Tuple[Any, float]] = []

        for item_id, p in self.points.items():

            if p.shape[0] != q.shape[0]:

                continue

            d = self._distance(q, p)

            distances.append((item_id, d))

        distances.sort(key=lambda x: x[1])

        top = distances[:k]

        results: List[GeometryResult] = []

        for i, (iid, d) in enumerate(top, start=1):

            p = self.points[iid]

            results.append(

                GeometryResult(

                    item_id=iid,

                    distance=float(d),

                    similarity=float(1.0 / (1.0 + d)),

                    rank=i,

                    location=tuple(p.tolist()),

                    metadata=self.metadata.get(iid, {}),

                )

            )

        return results



    def radius(

        self,

        query_coordinates: np.ndarray,

        radius: float,

    ) -> List[GeometryResult]:

        """Find all points within `radius` of query."""

        if not self.points:

            raise EmptyIndexError("Geometry index is empty.")

        q = np.asarray(query_coordinates, dtype=np.float64)

        if q.ndim != 1:

            raise ValueError("query must be 1-D.")

        results: List[GeometryResult] = []

        for item_id, p in self.points.items():

            if p.shape[0] != q.shape[0]:

                continue

            d = self._distance(q, p)

            if d <= radius:

                results.append(

                    GeometryResult(

                        item_id=item_id,

                        distance=float(d),

                        similarity=float(1.0 / (1.0 + d)),

                        rank=0,

                        location=tuple(p.tolist()),

                        metadata=self.metadata.get(item_id, {}),

                    )

                )

        results.sort(key=lambda r: r.distance)

        for i, r in enumerate(results, start=1):

            r.rank = i

        return results



    def bbox(

        self,

        bbox: Tuple[float, ...],

    ) -> List[GeometryResult]:

        """Find all points inside an axis-aligned bounding box."""

        if len(bbox) % 2 != 0 or len(bbox) < 4:

            raise ValueError("bbox must have even length ≥ 4.")

        if not self.points:

            raise EmptyIndexError("Geometry index is empty.")

        ndim = len(bbox) // 2

        mins = np.array(bbox[:ndim])

        maxs = np.array(bbox[ndim:])

        results: List[GeometryResult] = []

        for item_id, p in self.points.items():

            if p.shape[0] != ndim:

                continue

            if np.all(p >= mins) and np.all(p <= maxs):

                results.append(

                    GeometryResult(

                        item_id=item_id,

                        distance=0.0,

                        similarity=1.0,

                        rank=0,

                        location=tuple(p.tolist()),

                        metadata=self.metadata.get(item_id, {}),

                    )

                )

        for i, r in enumerate(results, start=1):

            r.rank = i

        return results



    def _distance(self, u: np.ndarray, v: np.ndarray) -> float:

        if self.metric == "euclidean":

            return float(np.linalg.norm(u - v))

        if self.metric == "manhattan":

            return float(np.abs(u - v).sum())

        if self.metric == "chebyshev":

            return float(np.abs(u - v).max())

        return float(np.linalg.norm(u - v))
