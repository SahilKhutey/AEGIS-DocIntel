"""
aegis.corpus.partition.holdout
==============================
Access guard and sealing mechanisms protecting holdout evaluation items from
unintentional exposure, overfitting, or leakage during development cycles.
"""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional
from aegis.corpus.adapters.models import CanonicalEvaluationItem
from aegis.corpus.partition.splitter import PartitionManifest


class HoldoutAccessGuard:
    """Controls access to holdout ground-truth evaluation items."""

    def __init__(self, partition_manifest: Optional[PartitionManifest] = None):
        self.manifest = partition_manifest
        self.holdout_ids = set(partition_manifest.partitions.holdout) if partition_manifest else set()

    def filter_evaluation_items(
        self,
        items: List[CanonicalEvaluationItem],
        allow_holdout: bool = False
    ) -> List[CanonicalEvaluationItem]:
        """Filter or seal ground-truth in evaluation items belonging to holdout partition."""
        sanitized: List[CanonicalEvaluationItem] = []

        for item in items:
            is_holdout = item.document_id in self.holdout_ids
            if is_holdout and not allow_holdout:
                # Mask ground truth
                masked_item = copy.deepcopy(item)
                masked_item.ground_truth = {
                    "status": "SEALED",
                    "reason": "Holdout ground truth is sealed during development",
                }
                sanitized.append(masked_item)
            else:
                sanitized.append(item)

        return sanitized

    def verify_holdout_access_permission(self, caller: str, auth_token: Optional[str] = None) -> bool:
        """Verify whether an evaluation runner is authorized to unseal holdout."""
        # Simple policy: only explicit final benchmark runners with formal token
        if caller in ["audit_final_runner", "wp04_final_auditor"] and auth_token == "AEGIS-HOLDOUT-AUTH-2026":
            return True
        return False
