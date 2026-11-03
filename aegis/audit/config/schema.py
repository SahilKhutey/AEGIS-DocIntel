"""
aegis/audit/config/schema.py
============================
JSON Schema definition and defaults for AEGIS audit configuration contracts.
"""

from __future__ import annotations

CONFIG_SCHEMA = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "AEGIS Audit Configuration Contract",
    "type": "object",
    "required": ["version", "audit"],
    "additionalProperties": False,
    "properties": {
        "version": {
            "type": "string",
            "enum": ["1.0", "1.0.0"]
        },
        "audit": {
            "type": "object",
            "required": [
                "name", "enabled", "execution", "suites", "evidence"
            ],
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string", "minLength": 1},
                "enabled": {"type": "boolean"},
                "execution": {
                    "type": "object",
                    "required": ["timeout_seconds"],
                    "additionalProperties": True,
                    "properties": {
                        "mode": {"type": "string", "enum": ["sequential", "parallel"]},
                        "fail_fast": {"type": "boolean"},
                        "strict": {"type": "boolean"},
                        "timeout_seconds": {"type": "number", "minimum": 1},
                        "suite_timeout_seconds": {"type": "number", "minimum": 1},
                        "retries": {"type": "integer", "minimum": 0, "maximum": 5},
                        "max_parallel_suites": {"type": "integer", "minimum": 1}
                    }
                },
                "suites": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["id"],
                        "additionalProperties": True,
                        "properties": {
                            "id": {"type": "string", "minLength": 1},
                            "enabled": {"type": "boolean"},
                            "required": {"type": "boolean"},
                            "timeout_seconds": {"type": "number", "minimum": 1},
                            "dependencies": {
                                "type": "array",
                                "items": {"type": "string"}
                            }
                        }
                    }
                },
                "evidence": {
                    "type": "object",
                    "required": ["enabled"],
                    "additionalProperties": True,
                    "properties": {
                        "enabled": {"type": "boolean"},
                        "format": {"type": "string", "enum": ["json"]},
                        "validate": {"type": "boolean"},
                        "retain_artifacts": {"type": "boolean"},
                        "output_dir": {"type": "string"}
                    }
                },
                "traceability": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "capture_commit": {"type": "boolean"},
                        "capture_branch": {"type": "boolean"},
                        "capture_environment": {"type": "boolean"},
                        "capture_configuration_hash": {"type": "boolean"}
                    }
                },
                "reporting": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "generate_json": {"type": "boolean"},
                        "generate_markdown": {"type": "boolean"},
                        "include_findings": {"type": "boolean"}
                    }
                },
                "security": {
                    "type": "object",
                    "additionalProperties": True,
                    "properties": {
                        "redact_secrets": {"type": "boolean"},
                        "include_environment_values": {"type": "boolean"}
                    }
                }
            }
        }
    }
}
