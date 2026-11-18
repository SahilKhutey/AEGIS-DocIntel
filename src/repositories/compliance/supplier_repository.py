"""
AEGIS-DocIntel Third-Party Supplier Repository
PROT-FINAL-07: Workstream 07.06

Data access for third-party infrastructure and LLM suppliers, tracking
processing locations, model training terms, and exit readiness (COMP-007, COMP-016).
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aegis.compliance.supplier_repository")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTERS_DIR = REPO_ROOT / "compliance" / "registers"


class SupplierRepository:
    def __init__(self, registers_dir: Path = REGISTERS_DIR):
        self.registers_dir = registers_dir
        self.suppliers_file = self.registers_dir / "third_party_supplier_register.csv"

    def list_suppliers(self) -> List[Dict[str, Any]]:
        """Reads all suppliers from third_party_supplier_register.csv."""
        if not self.suppliers_file.exists():
            return []
        with open(self.suppliers_file, mode="r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def get_supplier(self, supplier_id: str) -> Optional[Dict[str, Any]]:
        for sup in self.list_suppliers():
            if sup["supplier_id"] == supplier_id:
                return sup
        return None

    def get_llm_suppliers(self) -> List[Dict[str, Any]]:
        return [
            s for s in self.list_suppliers()
            if "LLM" in s.get("purpose", "") or "Inference" in s.get("purpose", "")
        ]


supplier_repository = SupplierRepository()
