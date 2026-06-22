"""

Template Search

===============



Fingerprint-based template matching using:

- Hamming distance (binary fingerprints)

- Jaccard similarity (set fingerprints)

- Cosine similarity (numerical fingerprints)

- Exact template lookup

"""



from __future__ import annotations



from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Set, Tuple, Union



import numpy as np



from .exceptions import EmptyIndexError





@dataclass

class TemplateResult:

    """A single template search result."""



    template_id: Any

    similarity: float

    distance: float

    rank: int

    metadata: Dict[str, Any] = field(default_factory=dict)





class TemplateSearch:

    """

    Template / fingerprint matching.



    Mathematical Foundation:

        Hamming distance: count differing bits

        Jaccard: |A ∩ B| / |A ∪ B|

        Cosine: (A · B) / (||A|| ||B||)

    """



    def __init__(self, fingerprint_type: str = "binary") -> None:

        if fingerprint_type not in {"binary", "set", "numerical"}:

            raise ValueError(f"Unknown fingerprint type: {fingerprint_type}")

        self.fingerprint_type = fingerprint_type

        self.fingerprints: Dict[Any, Union[np.ndarray, Set, List[float]]] = {}

        self.metadata: Dict[Any, Dict[str, Any]] = {}



    def add(

        self,

        template_id: Any,

        fingerprint: Union[np.ndarray, Set, List[float]],

        metadata: Optional[Dict[str, Any]] = None,

    ) -> None:

        """Add a template fingerprint."""

        if self.fingerprint_type == "binary":

            fp = np.asarray(fingerprint, dtype=np.int8)

        elif self.fingerprint_type == "set":

            fp = set(fingerprint) if not isinstance(fingerprint, set) else fingerprint

        else:

            fp = np.asarray(fingerprint, dtype=np.float64)

        self.fingerprints[template_id] = fp

        if metadata is not None:

            self.metadata[template_id] = metadata



    def search(

        self,

        query_fingerprint: Union[np.ndarray, Set, List[float]],

        top_k: int = 10,

        max_distance: Optional[float] = None,

    ) -> List[TemplateResult]:

        """Find templates most similar to query fingerprint."""

        if not self.fingerprints:

            raise EmptyIndexError("Template index is empty.")

        scored: List[Tuple[Any, float, float]] = []

        for tid, fp in self.fingerprints.items():

            sim, dist = self._compare(query_fingerprint, fp)

            if max_distance is not None and dist > max_distance:

                continue

            scored.append((tid, sim, dist))

        scored.sort(key=lambda x: x[1], reverse=True)

        top = scored[:top_k]

        results: List[TemplateResult] = []

        for rank, (tid, sim, dist) in enumerate(top, start=1):

            results.append(

                TemplateResult(

                    template_id=tid,

                    similarity=float(sim),

                    distance=float(dist),

                    rank=rank,

                    metadata=self.metadata.get(tid, {}),

                )

            )

        return results



    def _compare(

        self,

        q: Union[np.ndarray, Set, List],

        fp: Union[np.ndarray, Set],

    ) -> Tuple[float, float]:

        if self.fingerprint_type == "binary":

            q_arr = np.asarray(q, dtype=np.int8)

            fp_arr = np.asarray(fp, dtype=np.int8)

            n = min(q_arr.shape[0], fp_arr.shape[0])

            hamming = float(np.sum(q_arr[:n] != fp_arr[:n]))

            sim = 1.0 - hamming / max(n, 1)

            return sim, hamming

        if self.fingerprint_type == "set":

            q_set = set(q) if not isinstance(q, set) else q

            fp_set = fp if isinstance(fp, set) else set(fp)

            union = q_set | fp_set

            inter = q_set & fp_set

            jaccard = len(inter) / max(len(union), 1)

            return jaccard, 1.0 - jaccard

        # numerical

        q_arr = np.asarray(q, dtype=np.float64)

        fp_arr = np.asarray(fp, dtype=np.float64)

        n = min(q_arr.shape[0], fp_arr.shape[0])

        nu = np.linalg.norm(q_arr[:n])

        nv = np.linalg.norm(fp_arr[:n])

        if nu < 1e-12 or nv < 1e-12:

            return 0.0, float(np.linalg.norm(q_arr[:n] - fp_arr[:n]))

        cos = float(np.dot(q_arr[:n], fp_arr[:n]) / (nu * nv))

        eucl = float(np.linalg.norm(q_arr[:n] - fp_arr[:n]))

        return cos, eucl
