"""Handles MasterState schema version migrations as the schema evolves."""

from __future__ import annotations

from typing import Any, Callable, Dict

# Registry of schema migration functions mapping source_version -> migration_fn
MIGRATIONS: Dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    # "1.0.0": migrate_1_0_0_to_1_1_0,
}


def migrate(state_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Apply sequential migrations to state_dict until the latest schema version is reached.
    """
    version = state_dict.get("schema_version", "1.0.0")
    while version in MIGRATIONS:
        state_dict = MIGRATIONS[version](state_dict)
        version = state_dict.get("schema_version", version)
    return state_dict
