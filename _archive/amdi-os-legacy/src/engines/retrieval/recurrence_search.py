"""

Recurrence Search

=================



Near-duplicate detection via:

- LSH (Locality-Sensitive Hashing)

- MinHash for Jaccard similarity

- Hamming distance for binary fingerprints

- SimHash for cosine similarity

"""



from __future__ import annotations



import hashlib

import random

from collections import defaultdict

from dataclasses import dataclass, field

from typing import Any, Dict, List, Optional, Set, Tuple



import numpy as np



from .exceptions import EmptyIndexError





@dataclass

class RecurrenceResult:

    """A single recurrence search result."""



    item_id: Any

    similarity: float

    rank: int

    matched_buckets: List[int] = field(default_factory=list)

    metadata: Dict[str, Any] = field(default_factory=dict)





class MinHasher:

    """MinHash signature generator."""



    def __init__(self, num_hashes: int = 128, seed: int = 42) -> None:

        self.num_hashes = num_hashes

        self.rng = random.Random(seed)

        # generate hash functions: h(x) = (a*x + b) % p

        self.p = (1 << 61) - 1  # Mersenne prime

        self.coeffs: List[Tuple[int, int]] = [

            (self.rng.randint(1, self.p - 1), self.rng.randint(0, self.p - 1))

            for _ in range(num_hashes)

        ]



    def signature(self, items: Set[int]) -> np.ndarray:

        """Compute MinHash signature for a set of items."""

        sig = np.full(self.num_hashes, np.iinfo(np.int64).max, dtype=np.int64)

        for x in items:

            for i, (a, b) in enumerate(self.coeffs):

                h = (a * x + b) % self.p

                if h < sig[i]:

                    sig[i] = h

        return sig



    def estimate_jaccard(self, sig1: np.ndarray, sig2: np.ndarray) -> float:

        """Estimate Jaccard similarity from two signatures."""

        if sig1.shape != sig2.shape:

            raise ValueError("Signature shape mismatch.")

        return float(np.mean(sig1 == sig2))





class RecurrenceSearch:

    """

    LSH-based near-duplicate search.



    Mathematical Foundation:

        MinHash:

            Pr[h_min(A) = h_min(B)] = J(A, B)



        LSH banding:

            Two items match in a band of size b with probability

            ≈ 1 - (1 - J^r)^b where r = number of rows per band

    """



    def __init__(

        self,

        num_hashes: int = 128,

        bands: int = 32,

        rows_per_band: int = 4,

        seed: int = 42,

    ) -> None:

        if num_hashes != bands * rows_per_band:

            raise ValueError(

                f"num_hashes ({num_hashes}) must equal bands × rows_per_band "

                f"({bands} × {rows_per_band} = {bands * rows_per_band})."

            )

        self.num_hashes = num_hashes

        self.bands = bands

        self.rows_per_band = rows_per_band

        self.hasher = MinHasher(num_hashes=num_hashes, seed=seed)

        self.buckets: List[Dict[int, Set[Any]]] = [

            defaultdict(set) for _ in range(bands)

        ]

        self.signatures: Dict[Any, np.ndarray] = {}

        self.metadata: Dict[Any, Dict[str, Any]] = {}



    def add(

        self,

        item_id: Any,

        items: Set[int],

        metadata: Optional[Dict[str, Any]] = None,

    ) -> None:

        """Add an item (set of integers) to the index."""

        sig = self.hasher.signature(items)

        self.signatures[item_id] = sig

        for band_idx in range(self.bands):

            start = band_idx * self.rows_per_band

            end = start + self.rows_per_band

            band_hash = int(hashlib.md5(sig[start:end].tobytes()).hexdigest(), 16)

            self.buckets[band_idx][band_hash].add(item_id)

        if metadata is not None:

            self.metadata[item_id] = metadata



    def query(

        self,

        items: Set[int],

        top_k: int = 10,

        min_similarity: float = 0.0,

    ) -> List[RecurrenceResult]:

        """Find near-duplicates of `items`."""

        if not self.signatures:

            raise EmptyIndexError("Recurrence index is empty.")

        sig = self.hasher.signature(items)

        # collect candidates from buckets

        candidates: Dict[Any, Set[int]] = defaultdict(set)

        for band_idx in range(self.bands):

            start = band_idx * self.rows_per_band

            end = start + self.rows_per_band

            band_hash = int(hashlib.md5(sig[start:end].tobytes()).hexdigest(), 16)

            for cand_id in self.buckets[band_idx].get(band_hash, []):

                candidates[cand_id].add(band_idx)

        # score candidates

        results: List[RecurrenceResult] = []

        for cand_id, matched_bands in candidates.items():

            sim = self.hasher.estimate_jaccard(sig, self.signatures[cand_id])

            if sim < min_similarity:

                continue

            results.append(

                RecurrenceResult(

                    item_id=cand_id,

                    similarity=float(sim),

                    rank=0,

                    matched_buckets=sorted(matched_bands),

                    metadata=self.metadata.get(cand_id, {}),

                )

            )

        results.sort(key=lambda r: r.similarity, reverse=True)

        for i, r in enumerate(results[:top_k], start=1):

            r.rank = i

        return results[:top_k]



    def exact_jaccard(self, items1: Set[int], items2: Set[int]) -> float:

        """Compute exact Jaccard similarity."""

        if not items1 and not items2:

            return 1.0

        union = items1 | items2

        if not union:

            return 1.0

        return len(items1 & items2) / len(union)
