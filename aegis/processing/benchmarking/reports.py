"""
aegis.processing.benchmarking.reports
=====================================
Generates and writes versioned benchmark reports for WP-05 document processing capabilities.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional
import jsonschema

from aegis.processing.models import BenchmarkRecord

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
SCHEMA_FILE = REPO_ROOT / "schemas" / "processing" / "benchmark.schema.json"


class BenchmarkReportWriter:
    """Validates and exports benchmark results conforming to benchmark.schema.json."""

    @classmethod
    def write_report(
        cls,
        record: BenchmarkRecord,
        output_path: Path | str,
        validate: bool = True
    ) -> Path:
        p = Path(output_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        data = record.to_schema_dict()

        if validate and SCHEMA_FILE.exists():
            with open(SCHEMA_FILE, "r", encoding="utf-8") as sf:
                schema = json.load(sf)
            jsonschema.validate(data, schema)

        with open(p, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return p
