"""
aegis.intelligence.questions.partition
======================================
Deterministic, document-scope grouped partitioner for golden questions
allocating development (60%), validation (20%), and holdout (20%) partitions with zero leakage.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Dict, List, Set

from aegis.intelligence.models import GoldenQuestion


class QuestionPartitioner:
    """Partitions golden questions into dev, val, and holdout without document leakage."""

    def __init__(self, seed: int = 20261103):
        self.seed = seed

    def _hash_doc_scope(self, doc_scope: List[str]) -> float:
        """Deterministic hash ratio [0.0, 1.0) based on document scope."""
        key = f"{self.seed}:" + ":".join(sorted(doc_scope))
        h = int(hashlib.sha256(key.encode("utf-8")).hexdigest(), 16)
        return (h % 1000000) / 1000000.0

    def partition(
        self,
        questions: List[GoldenQuestion],
        dev_ratio: float = 0.60,
        val_ratio: float = 0.20,
    ) -> Dict[str, List[GoldenQuestion]]:
        """Split questions into dev, val, holdout."""
        dev_set: List[GoldenQuestion] = []
        val_set: List[GoldenQuestion] = []
        holdout_set: List[GoldenQuestion] = []

        dev_docs: Set[str] = set()
        val_docs: Set[str] = set()
        holdout_docs: Set[str] = set()

        for q in questions:
            # Check existing document assignment
            q_docs = set(q.document_scope)
            if q_docs.intersection(dev_docs):
                dev_set.append(q)
                dev_docs.update(q_docs)
                continue
            if q_docs.intersection(val_docs):
                val_set.append(q)
                val_docs.update(q_docs)
                continue
            if q_docs.intersection(holdout_docs):
                holdout_set.append(q)
                holdout_docs.update(q_docs)
                continue

            # New document group: assign based on hash ratio
            ratio = self._hash_doc_scope(q.document_scope)
            if ratio < dev_ratio:
                dev_set.append(q)
                dev_docs.update(q_docs)
            elif ratio < (dev_ratio + val_ratio):
                val_set.append(q)
                val_docs.update(q_docs)
            else:
                holdout_set.append(q)
                holdout_docs.update(q_docs)

        return {
            "development": dev_set,
            "validation": val_set,
            "holdout": holdout_set,
        }
