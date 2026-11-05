"""
aegis.corpus.registry.acquisition_registry
==========================================
Enforces acquisition approval decisions, rights gates, and usage limitations.
"""

from __future__ import annotations

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml

from aegis.corpus.models import AcquisitionDecision, ReviewStatus
from .source_registry import SourceRegistry


class AcquisitionRegistry:
    """Acquisition decision gate verifying legal approval prior to ingestion."""

    def __init__(
        self,
        config_path: Path | str | None = None,
        source_registry: Optional[SourceRegistry] = None,
    ) -> None:
        self.decisions: Dict[str, AcquisitionDecision] = {}
        self.source_registry = source_registry
        if config_path:
            self.load(config_path)

    def load(self, config_path: Path | str) -> None:
        path = Path(config_path)
        if not path.exists():
            raise FileNotFoundError(f"Acquisition decisions config not found at: {path}")

        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        dec_list = raw.get("decisions", [])
        self.decisions.clear()
        for item in dec_list:
            record = AcquisitionDecision(**item)
            self.decisions[record.decision_id] = record

    def get_by_source(self, source_id: str) -> Optional[AcquisitionDecision]:
        for d in self.decisions.values():
            if d.source_id == source_id:
                return d
        return None

    def is_acquisition_permitted(self, source_id: str, intended_use: str = "evaluate") -> Tuple[bool, str]:
        """
        Determines whether a source can be acquired and used for intended_use.
        PENDING or REJECTED sources cannot pass.
        """
        decision = self.get_by_source(source_id)
        if not decision:
            return False, f"Source '{source_id}' has no recorded acquisition decision"

        if decision.status == ReviewStatus.REJECTED:
            return False, f"Source '{source_id}' was REJECTED during legal review: {decision.justification}"

        if decision.status == ReviewStatus.PENDING:
            return False, f"Source '{source_id}' is PENDING legal review; acquisition blocked"

        if intended_use in decision.prohibited_uses:
            return False, f"Activity '{intended_use}' is explicitly PROHIBITED for source '{source_id}'"

        if intended_use not in decision.permitted_uses and "all" not in decision.permitted_uses:
            return False, f"Activity '{intended_use}' is not in permitted_uses for source '{source_id}'"

        return True, "APPROVED"

    def list_all(self) -> List[AcquisitionDecision]:
        return list(self.decisions.values())
