"""
aegis.corpus.partition
======================
Deterministic partitioning, group-aware splitting, leakage detection, and holdout protection.
"""

from aegis.corpus.partition.grouping import DocumentGrouper, GroupableDocument
from aegis.corpus.partition.holdout import HoldoutAccessGuard
from aegis.corpus.partition.leakage import LeakageDetector, LeakageReport
from aegis.corpus.partition.splitter import DeterministicSplitter, PartitionManifest, PartitionSets

__all__ = [
    "GroupableDocument",
    "DocumentGrouper",
    "DeterministicSplitter",
    "PartitionManifest",
    "PartitionSets",
    "LeakageDetector",
    "LeakageReport",
    "HoldoutAccessGuard",
]
