"""
tests.reliability.backups.test_backup_restoration_suite
=======================================================
Tests for WP-07.06 Disaster Recovery & Backup Restoration Security Gate (BACKUP-001 through BACKUP-014).
"""

import hashlib
import sqlite3
import pytest
from aegis.reliability.backup import DisasterRecoveryDrill, BackupRestorationBenchmarkRunner


@pytest.fixture
def dr_drill(tmp_path):
    drill = DisasterRecoveryDrill(tmp_path / "dr_env")
    drill.setup_source_environment()
    return drill


def test_backup_001_online_backup_integrity_check(dr_drill):
    ok, msg = dr_drill.execute_online_backup()
    assert ok
    assert dr_drill.backup_db_path.exists()

    # Direct PRAGMA check on backup file
    conn = sqlite3.connect(str(dr_drill.backup_db_path))
    res = conn.execute("PRAGMA integrity_check").fetchone()
    conn.close()
    assert res[0] == "ok"


def test_backup_002_clean_environment_restore(dr_drill):
    dr_drill.execute_online_backup()
    ok, rto, msg = dr_drill.restore_into_clean_environment(dr_drill.backup_db_path)
    assert ok
    assert rto <= 900.0  # RTO target <= 15 minutes

    conn = sqlite3.connect(str(dr_drill.restored_db_path))
    count = conn.execute("SELECT count(*) FROM documents").fetchone()[0]
    conn.close()
    assert count == 2


def test_backup_003_encrypted_backup_key_recovery(dr_drill):
    dr_drill.execute_online_backup()
    enc_path, expected_hash = dr_drill.simulate_encrypted_backup(secret_key="TestKey12345!")
    dec_bytes = dr_drill.decrypt_backup(enc_path, secret_key="TestKey12345!")
    actual_hash = hashlib.sha256(dec_bytes).hexdigest()
    assert actual_hash == expected_hash


def test_backup_004_corrupted_backup_rejected(dr_drill):
    corrupt_file = dr_drill.work_dir / "bad.db"
    corrupt_file.write_bytes(b"Corrupted database bytes")
    ok, _, msg = dr_drill.restore_into_clean_environment(corrupt_file)
    assert not ok
    assert "integrity check" in msg.lower() or "failure" in msg.lower()


def test_backup_005_benchmark_runner_full_suite():
    runner = BackupRestorationBenchmarkRunner()
    report = runner.run_suite()
    assert report["execution_status"] == "COMPLETED"
    assert report["metrics"]["passed_scenarios"] == 14
    assert report["metrics"]["rto_target_met"] is True
    assert report["metrics"]["database_integrity_verified"] is True
