"""
aegis/audit/config/loader.py
============================
Secure YAML/JSON loader for audit configuration files.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict
import yaml

from aegis.audit.runner.exceptions import ConfigurationError


class AuditConfigLoader:
    """Loads and parses audit configuration files safely."""

    @classmethod
    def load(cls, config_path: str | Path) -> Dict[str, Any]:
        path = Path(config_path).resolve()
        if not path.is_file():
            raise ConfigurationError(f"Audit configuration file not found: {path}")

        try:
            content = path.read_text(encoding="utf-8")
            if path.suffix.lower() == ".json":
                data = json.loads(content)
            else:
                data = yaml.safe_load(content)
        except Exception as e:
            raise ConfigurationError(f"Failed to parse configuration file '{path.name}': {e}")

        if not isinstance(data, dict):
            raise ConfigurationError(
                f"Audit configuration root must be an object/dict, got {type(data).__name__}"
            )

        return data
