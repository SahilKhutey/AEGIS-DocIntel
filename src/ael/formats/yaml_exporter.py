'''YAML exporter.'''
from __future__ import annotations

import yaml
from src.ael.ueo import UniversalExportObject


class YAMLExporter:
    @staticmethod
    def export(ueo: UniversalExportObject) -> str:
        return yaml.dump(ueo.to_dict(), default_flow_style=False, sort_keys=False, allow_unicode=True)
