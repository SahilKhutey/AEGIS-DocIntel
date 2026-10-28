"""
src/engines/intelligence/fact_store.py
======================================
Atomic, version-aware, tenant-isolated persistence for extraction runs and facts.
"""

from __future__ import annotations

import json
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from src.engines.intelligence.contracts import EvidenceSpan, ExtractedFact


class FactStore:
    """
    SQLite-backed storage for structured facts and extraction run metadata.
    Enforces tenant scoping, atomic versioned replacement, and serialization.
    """

    def __init__(self, db_path: str = "data/fact_store.db") -> None:
        self.db_path = db_path
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        if self.db_path == ":memory:":
            if not hasattr(self, "_mem_conn") or self._mem_conn is None:
                self._mem_conn = sqlite3.connect(":memory:", check_same_thread=False)
            return self._mem_conn
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        conn = self._get_connection()
        try:
            with conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS extraction_runs (
                        run_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        document_version INTEGER NOT NULL DEFAULT 1,
                        schema_name TEXT NOT NULL,
                        schema_version INTEGER NOT NULL DEFAULT 1,
                        status TEXT NOT NULL,
                        created_at TEXT NOT NULL
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_runs_tenant_doc
                    ON extraction_runs(tenant_id, document_id, schema_name)
                """)

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS extracted_facts (
                        fact_id TEXT PRIMARY KEY,
                        run_id TEXT NOT NULL,
                        tenant_id TEXT NOT NULL,
                        document_id TEXT NOT NULL,
                        subject TEXT NOT NULL,
                        attribute TEXT NOT NULL,
                        value_type TEXT NOT NULL,
                        raw_value TEXT NOT NULL,
                        parsed_value_json TEXT NOT NULL,
                        unit TEXT,
                        period TEXT,
                        valid_from TEXT,
                        valid_to TEXT,
                        confidence REAL,
                        evidence_json TEXT NOT NULL,
                        metadata_json TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        FOREIGN KEY (run_id) REFERENCES extraction_runs(run_id) ON DELETE CASCADE
                    )
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_facts_tenant_doc
                    ON extracted_facts(tenant_id, document_id)
                """)
                conn.execute("""
                    CREATE INDEX IF NOT EXISTS idx_facts_tenant_subject_attr
                    ON extracted_facts(tenant_id, subject, attribute)
                """)
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def store_extraction_run(
        self,
        tenant_id: str,
        document_id: str,
        schema_name: str,
        facts: Sequence[ExtractedFact],
        document_version: int = 1,
        schema_version: int = 1,
        status: str = "completed",
    ) -> str:
        """
        Atomically persist an extraction run and its extracted facts.
        Overwrites any previous extraction for the same (tenant_id, document_id, schema_name).
        """
        run_id = f"run-{uuid.uuid4().hex}"
        now = datetime.now(timezone.utc).isoformat()
        conn = self._get_connection()

        try:
            with conn:
                # 1. Remove previous facts and run for the same document and schema in this tenant
                prev_runs = conn.execute(
                    """
                    SELECT run_id FROM extraction_runs
                    WHERE tenant_id = ? AND document_id = ? AND schema_name = ?
                    """,
                    (tenant_id, document_id, schema_name),
                ).fetchall()

                for row in prev_runs:
                    p_id = row[0] if isinstance(row, tuple) else row["run_id"]
                    conn.execute("DELETE FROM extracted_facts WHERE run_id = ?", (p_id,))
                    conn.execute("DELETE FROM extraction_runs WHERE run_id = ?", (p_id,))

                # 2. Insert run record
                conn.execute(
                    """
                    INSERT INTO extraction_runs (
                        run_id, tenant_id, document_id, document_version,
                        schema_name, schema_version, status, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        run_id,
                        tenant_id,
                        document_id,
                        document_version,
                        schema_name,
                        schema_version,
                        status,
                        now,
                    ),
                )

                # 3. Insert facts
                for f in facts:
                    evidence_json = json.dumps([e.to_dict() for e in f.evidence])
                    metadata_json = json.dumps(f.metadata)
                    parsed_val_json = json.dumps(f.value)

                    conn.execute(
                        """
                        INSERT INTO extracted_facts (
                            fact_id, run_id, tenant_id, document_id,
                            subject, attribute, value_type, raw_value,
                            parsed_value_json, unit, period, valid_from,
                            valid_to, confidence, evidence_json, metadata_json,
                            created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            f.fact_id,
                            run_id,
                            tenant_id,
                            document_id,
                            f.subject,
                            f.attribute,
                            f.value_type,
                            f.raw_value,
                            parsed_val_json,
                            f.unit,
                            f.period,
                            f.valid_from,
                            f.valid_to,
                            f.confidence,
                            evidence_json,
                            metadata_json,
                            now,
                        ),
                    )
            return run_id
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_facts_by_document(
        self,
        tenant_id: str,
        document_id: str,
        attribute: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """Fetch all facts for a document within a tenant."""
        conn = self._get_connection()
        try:
            if attribute:
                query = """
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND document_id = ? AND attribute = ?
                    ORDER BY created_at ASC
                """
                cursor = conn.execute(query, (tenant_id, document_id, attribute))
            else:
                query = """
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND document_id = ?
                    ORDER BY created_at ASC
                """
                cursor = conn.execute(query, (tenant_id, document_id))

            rows = cursor.fetchall()
            return [self._row_to_fact(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_facts_for_documents(
        self,
        tenant_id: str,
        document_ids: Sequence[str],
        attribute: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """Fetch facts for a set of documents within a tenant."""
        if not document_ids:
            return []

        conn = self._get_connection()
        try:
            placeholders = ",".join("?" for _ in document_ids)
            params: List[Any] = [tenant_id, *document_ids]

            if attribute:
                query = f"""
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND document_id IN ({placeholders}) AND attribute = ?
                    ORDER BY created_at ASC
                """
                params.append(attribute)
            else:
                query = f"""
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND document_id IN ({placeholders})
                    ORDER BY created_at ASC
                """

            rows = conn.execute(query, params).fetchall()
            return [self._row_to_fact(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def get_facts_by_subject(
        self,
        tenant_id: str,
        subject: str,
        attribute: Optional[str] = None,
    ) -> List[ExtractedFact]:
        """Fetch facts by subject entity across documents for a tenant."""
        conn = self._get_connection()
        try:
            if attribute:
                query = """
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND subject = ? AND attribute = ?
                    ORDER BY created_at ASC
                """
                cursor = conn.execute(query, (tenant_id, subject, attribute))
            else:
                query = """
                    SELECT * FROM extracted_facts
                    WHERE tenant_id = ? AND subject = ?
                    ORDER BY created_at ASC
                """
                cursor = conn.execute(query, (tenant_id, subject))

            rows = cursor.fetchall()
            return [self._row_to_fact(r) for r in rows]
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def delete_document_facts(self, tenant_id: str, document_id: str) -> int:
        """Delete all facts and extraction runs for a document in a tenant."""
        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "DELETE FROM extracted_facts WHERE tenant_id = ? AND document_id = ?",
                    (tenant_id, document_id),
                )
                deleted_facts = cursor.rowcount
                conn.execute(
                    "DELETE FROM extraction_runs WHERE tenant_id = ? AND document_id = ?",
                    (tenant_id, document_id),
                )
                return deleted_facts
        finally:
            if self.db_path != ":memory:":
                conn.close()

    def _row_to_fact(self, row: Any) -> ExtractedFact:
        # Supports sqlite3.Row or tuple
        if isinstance(row, sqlite3.Row):
            d = dict(row)
        else:
            # Fallback if tuple
            d = {
                "fact_id": row[0],
                "run_id": row[1],
                "tenant_id": row[2],
                "document_id": row[3],
                "subject": row[4],
                "attribute": row[5],
                "value_type": row[6],
                "raw_value": row[7],
                "parsed_value_json": row[8],
                "unit": row[9],
                "period": row[10],
                "valid_from": row[11],
                "valid_to": row[12],
                "confidence": row[13],
                "evidence_json": row[14],
                "metadata_json": row[15],
            }

        evidence_list = json.loads(d["evidence_json"])
        evidence_spans = tuple(EvidenceSpan.from_dict(e) for e in evidence_list)
        parsed_val = json.loads(d["parsed_value_json"])
        metadata = json.loads(d["metadata_json"])

        return ExtractedFact(
            fact_id=d["fact_id"],
            tenant_id=d["tenant_id"],
            document_id=d["document_id"],
            subject=d["subject"],
            attribute=d["attribute"],
            value=parsed_val,
            raw_value=d["raw_value"],
            value_type=d["value_type"],
            unit=d["unit"],
            period=d["period"],
            valid_from=d["valid_from"],
            valid_to=d["valid_to"],
            confidence=d["confidence"],
            evidence=evidence_spans,
            metadata=metadata,
        )
