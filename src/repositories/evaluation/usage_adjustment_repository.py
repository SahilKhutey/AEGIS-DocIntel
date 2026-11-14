"""
AEGIS-DocIntel Usage Adjustment Repository (PROT-04 WP-04.06)
Maintains audit trail for administrative quota and usage adjustments.
"""

from __future__ import annotations

import threading
from typing import Dict, List, Optional
from src.schemas.evaluation.usage_summary import UsageAdjustmentRecord


class UsageAdjustmentRepository:
    def __init__(self):
        self._adjustments: Dict[str, UsageAdjustmentRecord] = {}
        self._lock = threading.Lock()

    def record_adjustment(self, record: UsageAdjustmentRecord) -> UsageAdjustmentRecord:
        with self._lock:
            self._adjustments[record.adjustment_id] = record
            return record

    def list_adjustments(self, license_id: Optional[str] = None) -> List[UsageAdjustmentRecord]:
        with self._lock:
            if license_id:
                return [r for r in self._adjustments.values() if r.license_id == license_id]
            return list(self._adjustments.values())

    def get_adjustment(self, adjustment_id: str) -> Optional[UsageAdjustmentRecord]:
        with self._lock:
            return self._adjustments.get(adjustment_id)


default_usage_adjustment_repository = UsageAdjustmentRepository()
