'''JSON exporter — universal machine-readable format.'''
from __future__ import annotations

import json
from src.ael.ueo import UniversalExportObject


class JSONExporter:
    @staticmethod
    def export(ueo: UniversalExportObject) -> str:
        return json.dumps(ueo.to_dict(), indent=2, default=str, ensure_ascii=False)

    @staticmethod
    def export_compact(ueo: UniversalExportObject) -> str:
        return json.dumps(ueo.to_dict(), separators=(',', ':'), default=str)
