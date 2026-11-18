"""
AEGIS-DocIntel Compliance Control Repository
PROT-FINAL-07: Workstream 07.03

Provides data access and schema validation for compliance controls,
regulatory obligations, and risk registers.
"""

from __future__ import annotations

import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger("aegis.compliance.control_repository")

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
REGISTERS_DIR = REPO_ROOT / "compliance" / "registers"
SCHEMAS_DIR = REPO_ROOT / "compliance" / "schemas"


class ControlRepository:
    def __init__(self, registers_dir: Path = REGISTERS_DIR):
        self.registers_dir = registers_dir
        self.control_file = self.registers_dir / "control_register.csv"
        self.obligations_file = self.registers_dir / "compliance_obligations.csv"

    def list_controls(self) -> List[Dict[str, Any]]:
        """Reads all controls from control_register.csv."""
        if not self.control_file.exists():
            return []
        controls = []
        with open(self.control_file, mode="r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert scope and evidence_required to lists
                row["scope"] = [s.strip() for s in row["scope"].split(";") if s.strip()]
                row["evidence_required"] = [e.strip() for e in row["evidence_required"].split(";") if e.strip()]
                controls.append(row)
        return controls

    def get_control(self, control_id: str) -> Optional[Dict[str, Any]]:
        """Retrieves a single control by ID."""
        for c in self.list_controls():
            if c["control_id"] == control_id:
                return c
        return None

    def list_obligations(self) -> List[Dict[str, Any]]:
        """Reads all obligations from compliance_obligations.csv."""
        if not self.obligations_file.exists():
            return []
        with open(self.obligations_file, mode="r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def validate_control_schema(self, control: Dict[str, Any]) -> bool:
        """Validates control against control.schema.json structure."""
        schema_path = SCHEMAS_DIR / "control.schema.json"
        if not schema_path.exists():
            return True
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        required = schema.get("required", [])
        return all(k in control for k in required)


control_repository = ControlRepository()
