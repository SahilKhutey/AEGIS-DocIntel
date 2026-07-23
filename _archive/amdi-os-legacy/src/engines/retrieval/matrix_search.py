"""

Matrix Search

=============



Searches over tabular / matrix representations.

Strategies:

- Column match: find columns most similar to query

- Row match: find rows with matching values

- Cell match: find cells with target value

- SVD-based semantic search over columns

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Tuple



import numpy as np



from .exceptions import EmptyIndexError





@dataclass

class MatrixResult:

    """A single matrix search result."""



    item_id: Any

    score: float

    rank: int

    location: Tuple[int, ...] = field(default_factory=tuple)

    metadata: Dict[str, Any] = field(default_factory=dict)





class MatrixSearch:

    """

    Matrix-based tabular search.



    Mathematical Foundation:

        Column similarity: cosine(col_i, query)

        Row similarity:   cosine(row_i, query)

        Cell search:      exact match | fuzzy match

        SVD semantic:     U_k · Σ_k · V_k^T reconstruction

    """



    def __init__(self) -> None:

        self.tables: Dict[Any, np.ndarray] = {}

        self.row_metadata: Dict[Any, Dict[int, Dict[str, Any]]] = {}

        self.col_metadata: Dict[Any, Dict[int, Dict[str, Any]]] = {}

        self._svd_cache: Dict[Any, Tuple[np.ndarray, np.ndarray, np.ndarray]] = {}



    def add(

        self,

        table_id: Any,

        matrix: np.ndarray,

        row_metadata: Optional[Dict[int, Dict[str, Any]]] = None,

        col_metadata: Optional[Dict[int, Dict[str, Any]]] = None,

    ) -> None:

        """Add a table to the index."""

        M = np.asarray(matrix, dtype=np.float64)

        if M.ndim != 2:

            raise ValueError("matrix must be 2-D.")

        self.tables[table_id] = M

        if row_metadata:

            self.row_metadata[table_id] = row_metadata

        if col_metadata:

            self.col_metadata[table_id] = col_metadata



    def search_column(

        self,

        query: np.ndarray,

        top_k: int = 10,

    ) -> List[MatrixResult]:

        """

        Find columns most similar to query vector.

        """

        if not self.tables:

            raise EmptyIndexError("No tables indexed.")

        q = np.asarray(query, dtype=np.float64)

        results: List[MatrixResult] = []

        for tid, M in self.tables.items():

            if M.shape[1] != q.shape[0]:

                continue

            for j in range(M.shape[1]):

                col = M[:, j]

                score = self._cosine(q, col)

                results.append(

                    MatrixResult(

                        item_id=f"{tid}::col_{j}",

                        score=score,

                        rank=0,

                        location=(j,),

                        metadata={"table_id": tid, "col": j, "type": "column"},

                    )

                )

        results.sort(key=lambda r: r.score, reverse=True)

        return self._rerank(results, top_k)



    def search_row(

        self,

        query: np.ndarray,

        top_k: int = 10,

    ) -> List[MatrixResult]:

        """Find rows most similar to query vector."""

        if not self.tables:

            raise EmptyIndexError("No tables indexed.")

        q = np.asarray(query, dtype=np.float64)

        results: List[MatrixResult] = []

        for tid, M in self.tables.items():

            if M.shape[1] != q.shape[0]:

                continue

            for i in range(M.shape[0]):

                row = M[i, :]

                score = self._cosine(q, row)

                results.append(

                    MatrixResult(

                        item_id=f"{tid}::row_{i}",

                        score=score,

                        rank=0,

                        location=(i,),

                        metadata={"table_id": tid, "row": i, "type": "row"},

                    )

                )

        results.sort(key=lambda r: r.score, reverse=True)

        return self._rerank(results, top_k)



    def search_value(

        self,

        value: float,

        tolerance: float = 0.01,

        top_k: int = 10,

    ) -> List[MatrixResult]:

        """Find cells matching a target value."""

        if not self.tables:

            raise EmptyIndexError("No tables indexed.")

        results: List[MatrixResult] = []

        for tid, M in self.tables.items():

            mask = np.abs(M - value) <= tolerance

            coords = np.argwhere(mask)

            for c in coords:

                i, j = int(c[0]), int(c[1])

                score = 1.0 / (1.0 + abs(float(M[i, j]) - value))

                results.append(

                    MatrixResult(

                        item_id=f"{tid}::cell_{i}_{j}",

                        score=float(score),

                        rank=0,

                        location=(i, j),

                        metadata={"table_id": tid, "row": i, "col": j, "value": float(M[i, j])},

                    )

                )

        results.sort(key=lambda r: r.score, reverse=True)

        return self._rerank(results, top_k)



    def search_semantic_svd(

        self,

        query: np.ndarray,

        top_k: int = 10,

        n_components: int = 10,

    ) -> List[MatrixResult]:

        """Search using truncated SVD for semantic column/row matching."""

        if not self.tables:

            raise EmptyIndexError("No tables indexed.")

        q = np.asarray(query, dtype=np.float64)

        results: List[MatrixResult] = []

        for tid, M in self.tables.items():

            k = min(n_components, min(M.shape))

            try:

                U, S, Vt = np.linalg.svd(M, full_matrices=False)

            except np.linalg.LinAlgError:

                continue

            Uk = U[:, :k]

            Sk = S[:k]

            Vtk = Vt[:k, :]

            # project query onto column space

            try:

                proj = Vtk.T @ np.linalg.pinv(np.diag(Sk)) @ Uk.T @ q[: M.shape[0]]

            except Exception:

                continue

            # compare projected query to each column

            for j in range(M.shape[1]):

                col = M[:, j]

                if col.shape[0] != proj.shape[0]:

                    score = self._cosine(proj[: col.shape[0]], col)

                else:

                    score = self._cosine(proj, col)

                results.append(

                    MatrixResult(

                        item_id=f"{tid}::svd_col_{j}",

                        score=float(score),

                        rank=0,

                        location=(j,),

                        metadata={"table_id": tid, "col": j, "type": "svd_column"},

                    )

                )

        results.sort(key=lambda r: r.score, reverse=True)

        return self._rerank(results, top_k)



    @staticmethod

    def _cosine(u: np.ndarray, v: np.ndarray) -> float:

        nu = np.linalg.norm(u)

        nv = np.linalg.norm(v)

        if nu < 1e-12 or nv < 1e-12:

            return 0.0

        return float(np.dot(u, v) / (nu * nv))



    @staticmethod

    def _rerank(results: List[MatrixResult], top_k: int) -> List[MatrixResult]:

        for i, r in enumerate(results[:top_k], start=1):

            r.rank = i

        return results[:top_k]
