"""
aegis.corpus.partition.splitter
===============================
Deterministic, leakage-resistant dataset splitter for AEGIS corpus.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from aegis.corpus.partition.grouping import DocumentGrouper, GroupableDocument


class PartitionSets(BaseModel):
    development: List[str] = Field(default_factory=list)
    validation: List[str] = Field(default_factory=list)
    holdout: List[str] = Field(default_factory=list)


class PartitionManifest(BaseModel):
    split_id: str
    split_version: str = "1.0.0"
    algorithm: str
    seed: int
    grouping_key: str
    partitions: PartitionSets
    leakage_check_status: str = "PENDING"
    approved_by: Optional[str] = None
    approved_at: Optional[str] = None

    def to_schema_dict(self) -> Dict[str, Any]:
        data = {
            "split_id": self.split_id,
            "split_version": self.split_version,
            "algorithm": self.algorithm,
            "seed": self.seed,
            "grouping_key": self.grouping_key,
            "partitions": {
                "development": self.partitions.development,
                "validation": self.partitions.validation,
                "holdout": self.partitions.holdout,
            },
            "leakage_check_status": self.leakage_check_status,
        }
        if self.approved_by:
            data["approved_by"] = self.approved_by
        if self.approved_at:
            data["approved_at"] = self.approved_at
        return data


class DeterministicSplitter:
    """Splits grouped documents into development, validation, and holdout partitions reproducibly."""

    def __init__(
        self,
        seed: int = 20261103,
        ratios: Optional[Dict[str, float]] = None,
        algorithm: str = "grouped_deterministic_hash"
    ):
        self.seed = seed
        self.ratios = ratios or {"development": 0.60, "validation": 0.20, "holdout": 0.20}
        self.algorithm = algorithm

        # Validate ratios sum to 1.0 within tolerance
        total = sum(self.ratios.values())
        if abs(total - 1.0) > 0.001:
            raise ValueError(f"Split ratios must sum to 1.0, got {total}")

    def split(
        self,
        documents: List[GroupableDocument],
        grouping_key: str = "family",
        split_id: Optional[str] = None
    ) -> PartitionManifest:
        """Partition documents deterministically without breaking grouping boundaries."""
        groups = DocumentGrouper.group_documents(documents, grouping_key=grouping_key)
        sorted_group_keys = sorted(groups.keys())

        # Seeded deterministic shuffle of groups
        rng = random.Random(self.seed)
        shuffled_keys = list(sorted_group_keys)
        rng.shuffle(shuffled_keys)

        total_groups = len(shuffled_keys)
        n_dev = int(round(total_groups * self.ratios.get("development", 0.60)))
        n_val = int(round(total_groups * self.ratios.get("validation", 0.20)))

        # Ensure that if total_groups >= 3, each partition gets at least 1 group
        if total_groups >= 3:
            n_dev = max(1, min(n_dev, total_groups - 2))
            n_val = max(1, min(n_val, total_groups - n_dev - 1))

        dev_keys = set(shuffled_keys[:n_dev])
        val_keys = set(shuffled_keys[n_dev : n_dev + n_val])
        holdout_keys = set(shuffled_keys[n_dev + n_val :])

        dev_docs: List[str] = []
        val_docs: List[str] = []
        holdout_docs: List[str] = []

        for k in sorted_group_keys:
            doc_ids = [d.document_id for d in groups[k]]
            if k in dev_keys:
                dev_docs.extend(doc_ids)
            elif k in val_keys:
                val_docs.extend(doc_ids)
            else:
                holdout_docs.extend(doc_ids)

        now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        s_id = split_id or f"SPLIT-{self.seed}-{grouping_key.upper()}"

        return PartitionManifest(
            split_id=s_id,
            split_version="1.0.0",
            algorithm=self.algorithm,
            seed=self.seed,
            grouping_key=grouping_key,
            partitions=PartitionSets(
                development=sorted(dev_docs),
                validation=sorted(val_docs),
                holdout=sorted(holdout_docs),
            ),
            leakage_check_status="PENDING",
            approved_by="AEGIS-Governance-Engine",
            approved_at=now,
        )
