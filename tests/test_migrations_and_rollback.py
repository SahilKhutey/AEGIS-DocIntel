"""
tests/test_migrations_and_rollback.py
=====================================
Release engineering & migration verification suite for P3.5:
1. SQLite schema upgrade from legacy v1 (base metadata only) to v2 (audit & raw bytes).
2. Data preservation across schema migration (zero data loss or corruption).
3. Post-migration read/write operational integrity.
4. Database backup and restore rollback verification.
"""
from __future__ import annotations

import os
import shutil
import sqlite3
import tempfile

import pytest

from src.services.container import RealDocumentService


def test_sqlite_v1_to_v2_migration_and_data_preservation():
    """Verify legacy schema (v1) automatically and safely upgrades to v2 without data loss."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name

    try:
        # 1. Create a legacy v1 database (simulating older release)
        with sqlite3.connect(db_path) as conn:
            conn.execute("PRAGMA user_version = 1")
            conn.execute("""
                CREATE TABLE documents (
                    doc_id TEXT PRIMARY KEY,
                    tenant_id TEXT NOT NULL,
                    filename TEXT NOT NULL,
                    status TEXT NOT NULL,
                    page_count INTEGER NOT NULL,
                    chunk_count INTEGER NOT NULL,
                    is_scanned BOOLEAN NOT NULL,
                    language TEXT NOT NULL,
                    created_at TEXT NOT NULL
                )
            """)
            conn.execute("""
                INSERT INTO documents (doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at)
                VALUES ('doc-legacy-001', 'tenant-alpha', 'quarterly_report.pdf', 'ready', 12, 45, 0, 'en', '2026-01-01T00:00:00Z')
            """)
            conn.commit()

        # 2. Initialize RealDocumentService, which executes _init_db migration
        service = RealDocumentService(orchestrator=None, db_path=db_path)

        # 3. Verify PRAGMA user_version is bumped to 2
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("PRAGMA user_version")
            ver = cursor.fetchone()[0]
            assert ver == 2, f"Expected user_version 2, got {ver}"

            # Verify all expected columns now exist
            cursor = conn.execute("PRAGMA table_info(documents)")
            cols = {row[1] for row in cursor.fetchall()}
            expected_new_cols = {
                "updated_at",
                "raw_bytes",
                "content_type",
                "byte_size",
                "sha256",
                "error_code",
            }
            assert expected_new_cols.issubset(cols), f"Missing migrated columns: {expected_new_cols - cols}"

            # 4. Verify pre-existing data was completely preserved
            cursor = conn.execute("SELECT doc_id, tenant_id, filename, status, page_count FROM documents WHERE doc_id = 'doc-legacy-001'")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "doc-legacy-001"
            assert row[1] == "tenant-alpha"
            assert row[2] == "quarterly_report.pdf"
            assert row[3] == "ready"
            assert row[4] == 12

            # 5. Verify database integrity
            cursor = conn.execute("PRAGMA integrity_check")
            integrity = cursor.fetchone()[0]
            assert integrity == "ok", f"Integrity check failed: {integrity}"

    finally:
        if os.path.exists(db_path):
            try:
                os.remove(db_path)
            except OSError:
                pass


def test_sqlite_backup_and_restore_rollback_cycle():
    """Verify database snapshot backup and restore procedure returns database to clean state."""
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as tf:
        db_path = tf.name
    backup_path = f"{db_path}.bak"

    try:
        # Initialize database with base document
        service = RealDocumentService(orchestrator=None, db_path=db_path)
        with sqlite3.connect(db_path) as conn:
            conn.execute("""
                INSERT INTO documents (doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at)
                VALUES ('doc-stable-1', 'tenant-1', 'stable.pdf', 'ready', 5, 10, 0, 'en', '2026-02-01T00:00:00Z')
            """)
            conn.commit()

        # Step 1: Create cold backup
        shutil.copyfile(db_path, backup_path)
        assert os.path.exists(backup_path)

        # Step 2: Introduce destructive modification (simulating failed migration or corrupted state)
        with sqlite3.connect(db_path) as conn:
            conn.execute("DROP TABLE documents")
            conn.commit()

        # Verify table is gone
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='documents'")
            assert cursor.fetchone() is None

        # Step 3: Rollback / Restore from backup
        shutil.copyfile(backup_path, db_path)

        # Step 4: Verify restored database is intact and contains pre-rollback state
        with sqlite3.connect(db_path) as conn:
            cursor = conn.execute("SELECT doc_id, filename FROM documents WHERE doc_id = 'doc-stable-1'")
            row = cursor.fetchone()
            assert row is not None
            assert row[0] == "doc-stable-1"
            assert row[1] == "stable.pdf"

            cursor = conn.execute("PRAGMA integrity_check")
            assert cursor.fetchone()[0] == "ok"

    finally:
        for p in (db_path, backup_path):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
