"""
Tests for MasterState schema migrations.
"""
from __future__ import annotations

from src.core.schema_migrations import MIGRATIONS, migrate


def test_schema_migrate_noop_on_current_version():
    data = {"doc_id": "test_1", "schema_version": "1.0.0"}
    migrated = migrate(data)
    assert migrated["schema_version"] == "1.0.0"
    assert migrated["doc_id"] == "test_1"


def test_schema_migrate_sequential_transitions():
    def _mig_1_to_2(d: dict) -> dict:
        out = dict(d)
        out["schema_version"] = "1.1.0"
        out["migrated_flag"] = True
        return out

    def _mig_2_to_3(d: dict) -> dict:
        out = dict(d)
        out["schema_version"] = "2.0.0"
        out["migrated_v2"] = True
        return out

    MIGRATIONS["1.0.0"] = _mig_1_to_2
    MIGRATIONS["1.1.0"] = _mig_2_to_3
    try:
        data = {"doc_id": "test_upgrade", "schema_version": "1.0.0"}
        result = migrate(data)
        assert result["schema_version"] == "2.0.0"
        assert result["migrated_flag"] is True
        assert result["migrated_v2"] is True
    finally:
        MIGRATIONS.clear()
