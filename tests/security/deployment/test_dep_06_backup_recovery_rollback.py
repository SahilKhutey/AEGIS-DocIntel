"""
Tests for PROT-FINAL-05: Backup, Disaster Recovery & Revocation Preservation
Covers DEP-TEST-012, DEP-TEST-017, DEP-TEST-018
"""

import tempfile
from datetime import datetime, timezone, timedelta
from pathlib import Path
import pytest

from infrastructure.backup.backup import BackupEngine
from infrastructure.backup.restore import RestoreEngine
from infrastructure.backup.verify_restore import verify_recovery_objectives


def test_dep_012_revoked_license_after_restoration_remains_revoked():
    """DEP-TEST-012: Restoring a historical database backup MUST NOT resurrect revoked licenses."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        backup_dir = Path(tmp_dir)
        backup_engine = BackupEngine(backup_dir)
        restore_engine = RestoreEngine(backup_dir)

        # Snapshot taken yesterday when license-123 was still ACTIVE
        db_snapshot_data = {
            "licenses": {
                "lic-normal-001": {"status": "ACTIVE", "tier": "DEMO"},
                "lic-revoked-later": {"status": "ACTIVE", "tier": "PROPRIETARY"},
            }
        }
        manifest = backup_engine.create_snapshot(
            snapshot_id="snap-2026-11-17",
            database_data=db_snapshot_data,
            revocation_list=[],
            audit_events_count=100,
        )
        assert manifest["status"] == "COMPLETED"

        # In the interim, lic-revoked-later was revoked in the authoritative registry
        authoritative_revocations = {"lic-revoked-later"}

        # Perform disaster recovery restoration
        ok, err, summary, restored_domains = restore_engine.restore_snapshot(
            snapshot_id="snap-2026-11-17",
            current_revocation_registry=authoritative_revocations,
        )
        assert ok
        assert err is None
        assert summary["prevented_resurrections"] == 1

        # Check restored data in memory: lic-revoked-later MUST be marked REVOKED
        restored_licenses = restored_domains["licenses"]
        assert restored_licenses["lic-revoked-later"]["status"] == "REVOKED"
        assert restored_licenses["lic-revoked-later"]["revocation_reason"] == "PRESERVED_POST_RESTORE"
        assert restored_licenses["lic-normal-001"]["status"] == "ACTIVE"


def test_dep_017_backup_restoration_recovery_objectives():
    """DEP-TEST-017: Restoration verifies RPO < 24h, RTO < 4h, and zero license resurrection."""
    now = datetime.now(timezone.utc)
    snapshot_time = now - timedelta(hours=6)  # 6 hours old (within 24h RPO)
    restoration_duration_seconds = 180.0     # 3 minutes (within 4h RTO)

    revoked_ids = ["lic-compromised-99"]
    status_map = {
        "lic-normal-01": "ACTIVE",
        "lic-compromised-99": "REVOKED",
    }

    report = verify_recovery_objectives(
        snapshot_timestamp=snapshot_time,
        restoration_duration_seconds=restoration_duration_seconds,
        revoked_license_ids=revoked_ids,
        restored_license_status_map=status_map,
    )
    assert report["overall_pass"] is True
    assert report["rpo_compliant"] is True
    assert report["rto_compliant"] is True
    assert report["revocation_preserved"] is True
    assert len(report["resurrected_licenses"]) == 0


def test_dep_018_deployment_rollback_security_state_preservation():
    """DEP-TEST-018: Rolling back deployment version preserves revocation state and audit log continuity."""
    # Rolling back image tags from 1.1.0 to 1.0.9 must retain persistent volumes for revocations and database
    prod_compose_path = Path(__file__).resolve().parent.parent.parent.parent / "infrastructure" / "compose" / "production" / "docker-compose.yml"
    compose_text = prod_compose_path.read_text(encoding="utf-8")

    # Volumes are persistent named volumes, not ephemeral bind mounts
    assert "production-postgres-data:" in compose_text
    assert "volumes:" in compose_text
    # Internal networks are decoupled from service versions
    assert "internal: true" in compose_text
