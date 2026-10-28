"""
AEGIS-DocIntel — Service Container (Dependency Injection)
==========================================================
Bootstraps and wires all system components together.
Central access point for all services.
"""
from __future__ import annotations

import asyncio
import inspect
import logging
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import structlog

from src.config import Settings
from src.models.document_object import DocumentObject, DocumentFormat
from src.core.orchestrator import AMDIOrchestrator
from src.llm_service.llm_client import LLMService
from src.services.query_service import QueryService
from src.observability.audit_logger import audit_logger
from src.observability.metrics import (
    DOCUMENTS_INGESTED,
    CHUNKS_INDEXED,
    ACTIVE_DOCUMENTS,
)

log = structlog.get_logger("aegis.container")


from src.services.storage_errors import (
    DocumentStorageError,
    DocumentPersistenceError,
    DocumentNotFoundError,
    DocumentRecoveryError,
    DocumentCleanupPending,
)

ALLOWED_TRANSITIONS = {
    "processing": {"ready", "failed", "deleting"},
    "ready": {"deleting"},
    "failed": {"processing", "deleting"},
    "deleting": {"delete_failed"},
    "delete_failed": {"deleting"},
}


class RealDocumentService:
    """Document service that delegates to AMDIOrchestrator and persists state."""

    def __init__(self, orchestrator: AMDIOrchestrator, db_path: Optional[str] = None):
        self.orchestrator = orchestrator
        self._docs: dict = {}
        if db_path is None:
            self.db_path = os.environ.get("AEGIS_SQLITE_PATH", "data/documents.db")
        else:
            self.db_path = db_path
        self._init_db()
        self._load_docs()

    def _init_db(self):
        if not self.db_path or self.db_path == ":memory:":
            return
        try:
            p = Path(self.db_path)
            p.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.execute("PRAGMA user_version")
                version = cursor.fetchone()[0]

                conn.execute("""
                    CREATE TABLE IF NOT EXISTS documents (
                        doc_id TEXT PRIMARY KEY,
                        tenant_id TEXT NOT NULL,
                        filename TEXT NOT NULL,
                        status TEXT NOT NULL,
                        page_count INTEGER NOT NULL,
                        chunk_count INTEGER NOT NULL,
                        is_scanned BOOLEAN NOT NULL,
                        language TEXT NOT NULL,
                        created_at TEXT NOT NULL,
                        updated_at TEXT,
                        raw_bytes BLOB,
                        content_type TEXT,
                        byte_size INTEGER,
                        sha256 TEXT,
                        error_code TEXT
                    )
                """)
                conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_tenant_status ON documents(tenant_id, status)")
                conn.execute("CREATE INDEX IF NOT EXISTS idx_documents_created_at ON documents(created_at DESC)")

                cursor = conn.execute("PRAGMA table_info(documents)")
                existing_cols = {col[1] for col in cursor.fetchall()}
                for col_name, col_type in [
                    ("updated_at", "TEXT"),
                    ("raw_bytes", "BLOB"),
                    ("content_type", "TEXT"),
                    ("byte_size", "INTEGER"),
                    ("sha256", "TEXT"),
                    ("error_code", "TEXT"),
                ]:
                    if col_name not in existing_cols:
                        conn.execute(f"ALTER TABLE documents ADD COLUMN {col_name} {col_type}")

                if version < 2:
                    conn.execute("PRAGMA user_version = 2")
                conn.commit()
        except Exception as e:
            log.exception("Could not initialize SQLite document store", error=str(e))
            raise DocumentStorageError(f"Database initialization failed: {e}") from e

    def _load_docs(self):
        if not self.db_path or self.db_path == ":memory:":
            return
        try:
            if not Path(self.db_path).exists():
                return
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                # Reconcile stale processing or deleting documents interrupted by a previous restart
                conn.execute("""
                    UPDATE documents
                    SET status = 'failed', error_code = 'STALE_PROCESSING_INTERRUPTED'
                    WHERE status = 'processing'
                """)
                conn.execute("""
                    UPDATE documents
                    SET status = 'delete_failed', error_code = 'STALE_DELETION_INTERRUPTED'
                    WHERE status = 'deleting'
                """)
                conn.commit()

                cursor = conn.execute(
                    """
                    SELECT doc_id, tenant_id, filename, status, page_count, chunk_count,
                           is_scanned, language, created_at, updated_at, content_type, byte_size, sha256
                    FROM documents
                    """
                )
                for row in cursor.fetchall():
                    try:
                        created = datetime.fromisoformat(row[8]) if row[8] else datetime.now(timezone.utc)
                    except Exception:
                        created = datetime.now(timezone.utc)
                    doc_info = {
                        "doc_id": row[0],
                        "tenant_id": row[1],
                        "filename": row[2],
                        "status": row[3],
                        "page_count": row[4],
                        "chunk_count": row[5],
                        "is_scanned": bool(row[6]),
                        "language": row[7],
                        "created_at": created,
                        "updated_at": row[9] or str(created),
                        "content_type": row[10] or "application/octet-stream",
                        "byte_size": row[11] or 0,
                        "sha256": row[12] or "",
                    }
                    if doc_info["status"] == "ready":
                        self._docs[row[0]] = doc_info
        except Exception as e:
            log.exception("Could not load documents from SQLite", error=str(e))
            raise DocumentStorageError(f"Failed to load documents from database: {e}") from e

    def _persist_doc(self, doc_info: dict, raw_bytes: Optional[bytes] = None):
        """Persist or update document metadata and raw bytes in SQLite."""
        if not self.db_path or self.db_path == ":memory:":
            return
        try:
            created_str = (
                doc_info["created_at"].isoformat()
                if isinstance(doc_info["created_at"], datetime)
                else str(doc_info["created_at"])
            )
            updated_str = (
                doc_info.get("updated_at", created_str).isoformat()
                if isinstance(doc_info.get("updated_at"), datetime)
                else str(doc_info.get("updated_at") or created_str)
            )
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                conn.execute("""
                    INSERT INTO documents
                    (doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, updated_at, raw_bytes, content_type, byte_size, sha256, error_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(doc_id) DO UPDATE SET
                        status = excluded.status,
                        page_count = excluded.page_count,
                        chunk_count = excluded.chunk_count,
                        updated_at = excluded.updated_at,
                        error_code = excluded.error_code,
                        raw_bytes = COALESCE(excluded.raw_bytes, documents.raw_bytes)
                """, (
                    doc_info["doc_id"],
                    doc_info["tenant_id"],
                    doc_info["filename"],
                    doc_info["status"],
                    doc_info.get("page_count", 0),
                    doc_info.get("chunk_count", 0),
                    1 if doc_info.get("is_scanned") else 0,
                    doc_info.get("language", "en"),
                    created_str,
                    updated_str,
                    raw_bytes,
                    doc_info.get("content_type", "application/octet-stream"),
                    doc_info.get("byte_size", len(raw_bytes) if raw_bytes else 0),
                    doc_info.get("sha256", ""),
                    doc_info.get("error_code"),
                ))
                conn.commit()
        except Exception as e:
            log.warning("Could not persist document to SQLite", error=str(e))
            raise DocumentPersistenceError(f"Failed to persist document {doc_info.get('doc_id')}: {e}") from e

    def _load_raw_bytes(self, doc_id: str, tenant_id: Optional[str] = None) -> Optional[bytes]:
        if not tenant_id:
            raise ValueError("tenant_id is required to load raw document bytes")
        if not self.db_path or self.db_path == ":memory:":
            return None
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                cursor = conn.execute(
                    "SELECT raw_bytes, sha256 FROM documents WHERE doc_id = ? AND tenant_id = ? AND status = 'ready'",
                    (str(doc_id), str(tenant_id)),
                )
                row = cursor.fetchone()
                if row and row[0]:
                    raw_bytes, sha256_hash = row[0], row[1]
                    if sha256_hash:
                        import hashlib
                        if hashlib.sha256(raw_bytes).hexdigest() != sha256_hash:
                            raise DocumentRecoveryError(f"Checksum mismatch for document {doc_id}")
                    return raw_bytes
        except DocumentRecoveryError:
            raise
        except Exception as e:
            log.warning("Could not load raw_bytes from SQLite", error=str(e))
            raise DocumentStorageError(f"Database error loading raw bytes: {e}") from e
        return None

    async def hydrate_document(self, doc_id: str, tenant_id: str) -> bool:
        """Re-hydrates document into orchestrator if not present in memory."""
        doc = self._docs.get(str(doc_id))
        if not doc:
            if self.db_path and self.db_path != ":memory:":
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    cursor = conn.execute(
                        "SELECT doc_id, tenant_id, filename FROM documents WHERE doc_id = ? AND tenant_id = ? AND status = 'ready'",
                        (str(doc_id), str(tenant_id)),
                    )
                    row = cursor.fetchone()
                    if row:
                        doc = {"doc_id": row[0], "tenant_id": row[1], "filename": row[2]}
        if not doc or str(doc.get("tenant_id", "")) != str(tenant_id):
            return False
        if hasattr(self.orchestrator, "_doc_state") and str(doc_id) not in self.orchestrator._doc_state:
            raw_bytes = self._load_raw_bytes(str(doc_id), tenant_id=str(tenant_id))
            if raw_bytes:
                try:
                    from src.models.document_object import DocumentObject
                    doc_obj = DocumentObject(
                        doc_id=str(doc_id),
                        filename=doc["filename"],
                        raw_bytes=raw_bytes,
                        tenant_id=str(tenant_id),
                    )
                    await self.orchestrator.ingest(doc_obj)
                    return True
                except Exception as e:
                    log.warning("Failed to re-hydrate document into orchestrator", error=str(e))
        return False

    def _delete_persisted_doc(self, doc_id: str, tenant_id: Optional[str] = None) -> bool:
        if not self.db_path or self.db_path == ":memory:":
            return True
        try:
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                if tenant_id:
                    cursor = conn.execute(
                        "DELETE FROM documents WHERE doc_id = ? AND tenant_id = ?",
                        (str(doc_id), str(tenant_id)),
                    )
                else:
                    cursor = conn.execute(
                        "DELETE FROM documents WHERE doc_id = ?",
                        (str(doc_id),),
                    )
                conn.commit()
                return cursor.rowcount > 0
        except Exception as e:
            log.warning("Could not delete document from SQLite", error=str(e))
            raise DocumentStorageError(f"Database error deleting document: {e}") from e

    async def ingest(self, file_bytes: bytes, filename: str, content_type: str, tenant_id: str):
        import hashlib
        doc_id = str(uuid.uuid4())
        sha256_hash = hashlib.sha256(file_bytes).hexdigest()
        byte_size = len(file_bytes)
        now = datetime.now(timezone.utc)

        # 1. Pre-persist durable record in 'processing' state
        initial_info = {
            "doc_id": doc_id,
            "tenant_id": str(tenant_id),
            "filename": filename,
            "status": "processing",
            "page_count": 0,
            "chunk_count": 0,
            "is_scanned": False,
            "language": "en",
            "created_at": now,
            "updated_at": now.isoformat(),
            "content_type": content_type,
            "byte_size": byte_size,
            "sha256": sha256_hash,
            "error_code": None,
        }
        self._persist_doc(initial_info, raw_bytes=file_bytes)

        doc = DocumentObject(
            doc_id=doc_id,
            filename=filename,
            raw_bytes=file_bytes,
            tenant_id=str(tenant_id),
        )

        try:
            # 2. Ingest using orchestrator
            stats = await self.orchestrator.ingest(doc)
            page_count = stats.get("pages", 1)
            chunk_count = stats.get("elements", 0)

            # 3. Transition to 'ready' state
            ready_info = {
                **initial_info,
                "status": "ready",
                "page_count": page_count,
                "chunk_count": chunk_count,
                "updated_at": datetime.now(timezone.utc).isoformat(),
            }
            self._persist_doc(ready_info, raw_bytes=file_bytes)
            self._docs[doc_id] = ready_info

            audit_logger.log(
                action="doc.ingest",
                tenant_id=str(tenant_id),
                resource_id=doc_id,
                status="SUCCESS",
                detail={"filename": filename, "pages": page_count},
            )

            DOCUMENTS_INGESTED.labels(tenant_id=str(tenant_id), status="success").inc()
            CHUNKS_INDEXED.labels(tenant_id=str(tenant_id), block_type="mixed").inc(chunk_count)
            ACTIVE_DOCUMENTS.labels(tenant_id=str(tenant_id)).inc()

            class _DocResp:
                def __init__(self, d):
                    for k, v in d.items():
                        setattr(self, k, v)
            return _DocResp(ready_info)
        except Exception as exc:
            # Transition to 'failed' state in SQLite & cleanup memory
            failed_info = {
                **initial_info,
                "status": "failed",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "error_code": type(exc).__name__,
            }
            try:
                self._persist_doc(failed_info, raw_bytes=file_bytes)
            except Exception:
                pass
            self._docs.pop(doc_id, None)
            DOCUMENTS_INGESTED.labels(tenant_id=str(tenant_id), status="failed").inc()
            raise

    async def get(self, doc_id: str, tenant_id: str):
        doc = self._docs.get(str(doc_id))
        if not doc and self.db_path and self.db_path != ":memory:":
            try:
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    cursor = conn.execute(
                        """
                        SELECT doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, content_type, byte_size
                        FROM documents
                        WHERE doc_id = ? AND tenant_id = ? AND status = 'ready'
                        """,
                        (str(doc_id), str(tenant_id)),
                    )
                    row = cursor.fetchone()
                    if row:
                        doc = {
                            "doc_id": row[0],
                            "tenant_id": row[1],
                            "filename": row[2],
                            "status": row[3],
                            "page_count": row[4],
                            "chunk_count": row[5],
                            "is_scanned": bool(row[6]),
                            "language": row[7],
                            "created_at": row[8],
                            "content_type": row[9],
                            "byte_size": row[10],
                        }
            except Exception:
                pass

        if not doc or str(doc.get("tenant_id", "")) != str(tenant_id):
            return None
        class _DocResp:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        return _DocResp(doc)

    async def get_status(self, doc_id: str, tenant_id: str):
        doc = self._docs.get(str(doc_id))
        if not doc and self.db_path and self.db_path != ":memory:":
            try:
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    cursor = conn.execute(
                        "SELECT doc_id, tenant_id, status, chunk_count FROM documents WHERE doc_id = ? AND tenant_id = ?",
                        (str(doc_id), str(tenant_id)),
                    )
                    row = cursor.fetchone()
                    if row:
                        doc = {
                            "doc_id": row[0],
                            "tenant_id": row[1],
                            "status": row[2],
                            "chunk_count": row[3],
                        }
            except Exception:
                pass

        if not doc or str(doc.get("tenant_id", "")) != str(tenant_id):
            return None
        class _Status:
            def __init__(self, d):
                self.doc_id = d["doc_id"]
                self.status = d["status"]
                self.progress_percent = 100.0 if d["status"] == "ready" else 0.0
                self.stage = "complete" if d["status"] == "ready" else d["status"]
                self.error = None
                self.chunks_indexed = d.get("chunk_count", 0)
        return _Status(doc)

    async def list_documents(self, tenant_id: str, page: int = 1, page_size: int = 20, status: str | None = None):
        if page < 1:
            raise ValueError("page must be >= 1")
        if not 1 <= page_size <= 100:
            raise ValueError("page_size must be between 1 and 100")

        if self.db_path and self.db_path != ":memory:" and Path(self.db_path).exists():
            with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                if status is not None:
                    count_cur = conn.execute(
                        "SELECT COUNT(*) FROM documents WHERE tenant_id = ? AND LOWER(status) = LOWER(?)",
                        (str(tenant_id), str(status)),
                    )
                else:
                    count_cur = conn.execute(
                        "SELECT COUNT(*) FROM documents WHERE tenant_id = ? AND status != 'deleting'",
                        (str(tenant_id),),
                    )
                total = count_cur.fetchone()[0]

                offset = (page - 1) * page_size
                if status is not None:
                    cur = conn.execute(
                        """
                        SELECT doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, content_type, byte_size
                        FROM documents
                        WHERE tenant_id = ? AND LOWER(status) = LOWER(?)
                        ORDER BY created_at DESC, doc_id DESC
                        LIMIT ? OFFSET ?
                        """,
                        (str(tenant_id), str(status), page_size, offset),
                    )
                else:
                    cur = conn.execute(
                        """
                        SELECT doc_id, tenant_id, filename, status, page_count, chunk_count, is_scanned, language, created_at, content_type, byte_size
                        FROM documents
                        WHERE tenant_id = ? AND status != 'deleting'
                        ORDER BY created_at DESC, doc_id DESC
                        LIMIT ? OFFSET ?
                        """,
                        (str(tenant_id), page_size, offset),
                    )
                items = [
                    {
                        "doc_id": r[0],
                        "tenant_id": r[1],
                        "filename": r[2],
                        "status": r[3],
                        "page_count": r[4],
                        "chunk_count": r[5],
                        "is_scanned": bool(r[6]),
                        "language": r[7],
                        "created_at": r[8],
                        "content_type": r[9] or "application/octet-stream",
                        "byte_size": r[10] or 0,
                    }
                    for r in cur.fetchall()
                ]
        else:
            filtered = [
                v for v in self._docs.values()
                if str(v.get("tenant_id", "")) == str(tenant_id)
                and (status is None or str(v.get("status", "")).lower() == str(status).lower())
            ]
            filtered.sort(
                key=lambda doc: (str(doc.get("created_at", "")), str(doc.get("doc_id", ""))),
                reverse=True,
            )
            total = len(filtered)
            start = (page - 1) * page_size
            items = filtered[start : start + page_size]

        class _Doc:
            def __init__(self, d):
                for k, v in d.items():
                    setattr(self, k, v)
        class _List:
            def __init__(self, items, total, page, page_size):
                self.items = [_Doc(i) for i in items]
                self.total = total
                self.page = page
                self.page_size = page_size
        return _List(items, total, page, page_size)

    async def delete(self, doc_id: str, tenant_id: str) -> bool:
        if not tenant_id:
            raise ValueError("tenant_id is required for document deletion")
        # 1. Authorize tenant
        doc = self._docs.get(str(doc_id))
        if not doc and self.db_path and self.db_path != ":memory:":
            try:
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    cur = conn.execute(
                        "SELECT tenant_id FROM documents WHERE doc_id = ? AND tenant_id = ?",
                        (str(doc_id), str(tenant_id)),
                    )
                    row = cur.fetchone()
                    if row:
                        doc = {"tenant_id": row[0]}
            except Exception:
                pass

        if not doc or str(doc.get("tenant_id", "")) != str(tenant_id):
            return False

        # 2. Commit a deletion tombstone in SQLite
        if self.db_path and self.db_path != ":memory:":
            try:
                now_iso = datetime.now(timezone.utc).isoformat()
                with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                    row = conn.execute(
                        "SELECT status FROM documents WHERE doc_id = ? AND tenant_id = ?",
                        (str(doc_id), str(tenant_id)),
                    ).fetchone()
                    if row is not None:
                        if row[0] not in ('ready', 'failed', 'delete_failed'):
                            return False
                        conn.execute(
                            """
                            UPDATE documents
                            SET status = 'deleting', updated_at = ?
                            WHERE doc_id = ? AND tenant_id = ? AND status IN ('ready', 'failed', 'delete_failed')
                            """,
                            (now_iso, str(doc_id), str(tenant_id)),
                        )
                        conn.commit()
            except Exception as e:
                log.exception("Failed to mark document as deleting", error=str(e))
                raise DocumentStorageError(f"Database error during deletion tombstone: {e}") from e

        self._docs.pop(str(doc_id), None)

        # 3. Clean up derived stores
        cleanup_failed = False
        store_errors = []

        if hasattr(self.orchestrator, "vector_store") and self.orchestrator.vector_store:
            try:
                res = self.orchestrator.vector_store.delete(doc_id=str(doc_id))
                if inspect.isawaitable(res):
                    await res
            except Exception as e:
                cleanup_failed = True
                store_errors.append(f"vector_store: {e}")
                log.warning("Vector store deletion failed for %s: %s", doc_id, e)

        if hasattr(self.orchestrator, "semantic_cache") and self.orchestrator.semantic_cache:
            try:
                res = self.orchestrator.semantic_cache.invalidate(doc_id=str(doc_id))
                if inspect.isawaitable(res):
                    await res
            except Exception as e:
                cleanup_failed = True
                store_errors.append(f"semantic_cache: {e}")
                log.warning("Cache invalidation failed for %s: %s", doc_id, e)

        if hasattr(self.orchestrator, "delete_document"):
            try:
                res = self.orchestrator.delete_document(str(doc_id), tenant_id=str(tenant_id))
                if inspect.isawaitable(res):
                    res = await res
                if res is False:
                    cleanup_failed = True
                    store_errors.append("orchestrator: delete_document returned False")
            except Exception as e:
                cleanup_failed = True
                store_errors.append(f"orchestrator: {e}")
                log.warning("Orchestrator document deletion failed for %s: %s", doc_id, e)

        # 4. Handle store failure vs complete success
        if cleanup_failed:
            if self.db_path and self.db_path != ":memory:":
                try:
                    with sqlite3.connect(self.db_path, timeout=10.0) as conn:
                        conn.execute(
                            "UPDATE documents SET status = 'delete_failed', updated_at = ?, error_code = ? WHERE doc_id = ? AND tenant_id = ?",
                            (datetime.now(timezone.utc).isoformat(), "; ".join(store_errors), str(doc_id), str(tenant_id)),
                        )
                        conn.commit()
                except Exception:
                    pass
            audit_logger.log(
                action="doc.delete",
                tenant_id=str(tenant_id),
                resource_id=str(doc_id),
                status="PENDING",
                detail={"errors": store_errors},
            )
            return False

        # If all stores succeeded, finalize deletion from SQLite
        self._delete_persisted_doc(str(doc_id), tenant_id=str(tenant_id))
        audit_logger.log(
            action="doc.delete",
            tenant_id=str(tenant_id),
            resource_id=str(doc_id),
            status="SUCCESS",
        )
        ACTIVE_DOCUMENTS.labels(tenant_id=str(tenant_id)).dec()
        return True


    async def reindex(self, doc_id: str, tenant_id: str):
        return await self.get_status(doc_id, tenant_id)

    async def list_chunks(self, doc_id: str, tenant_id: str, page: int = 1, page_size: int = 50):
        # Tenant-isolation fix: this previously called
        # self.orchestrator.get_document_elements(str(doc_id)) with NO
        # tenant_id at all, completely bypassing the orchestrator's own
        # tenant check (see src/core/orchestrator.py) even though that
        # check exists and works correctly when actually invoked with a
        # tenant_id. This is the same class of bug as get()/get_status()/
        # delete() above, but more severe: a document-level PermissionError
        # is a deliberate, positive protection; a call site that simply
        # never passes the parameter needed to trigger it bypasses that
        # protection entirely rather than merely leaving it unenforced by
        # this method's own logic.
        class _ChunkList:
            def __init__(self, items, total):
                self.items = items
                self.total = total

        doc = self._docs.get(str(doc_id))
        if not doc or str(doc.get("tenant_id", "")) != str(tenant_id):
            return _ChunkList([], 0)

        await self.hydrate_document(str(doc_id), str(tenant_id))

        try:
            elements = self.orchestrator.get_document_elements(str(doc_id), tenant_id=str(tenant_id))
        except PermissionError:
            elements = []

        total = len(elements)
        start = (page - 1) * page_size
        end = start + page_size
        paged_elements = elements[start:end]

        class _Chunk:
            def __init__(self, e):
                self.chunk_id = e.element_id
                self.doc_id = e.doc_id
                self.page_start = e.page
                self.page_end = e.page
                self.section = e.section
                self.block_type = e.type.value if hasattr(e.type, "value") else str(e.type)
                self.text = e.content
                self.token_count = e.token_count if hasattr(e, "token_count") else max(1, len(e.content.split()))

        return _ChunkList([_Chunk(e) for e in paged_elements], total)

    async def batch_ingest(self, documents: list, tenant_id: str):
        class _Job:
            job_id = uuid.uuid4()
            doc_count = len(documents)
            status = "queued"
        return _Job()


class ServiceContainer:
    """
    Dependency injection container.
    Connects API gateway endpoints to real AMDI-OS orchestrator.
    """

    def __init__(self, settings: Settings):
        self.settings = settings
        self._started = False

        # Services (initialized in startup())
        self.embedding_model = None
        self.rag_engine = None
        self.memory_engine = None
        self.llm_service: LLMService | None = None
        self.query_service: QueryService | None = None
        self.document_service = None

        # Pre-LLM, Compliance, Versioning, Entity & Math Services
        self.compliance_service = None
        self.entity_service = None
        self.versioning_service = None
        self.anomaly_service = None
        self.normalizer_service = None
        self.decomposer_service = None
        self.math_engine = None
        self.intelligence_service = None

    async def startup(self):
        """Initialize all services."""
        log.info("Initializing service container")

        # Config mapping for AMDIOrchestrator
        amdi_config = {
            "embedding_dim": self.settings.embeddings.dimension,
            "embedding_provider": getattr(self.settings.embeddings, "provider", "auto"),
            "embedding_model": self.settings.embeddings.text_model,
            "redis_url": self.settings.redis.url,
            "llm_provider": self.settings.llm.provider,
            "llm_model": self.settings.llm.model,
            "openai_api_key": self.settings.llm.api_key or os.environ.get("OPENAI_API_KEY", ""),
            "max_context_tokens": self.settings.llm.max_input_tokens,
        }

        # ── Embedding Model ──────────────────────────────────────────────
        try:
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(
                self.settings.embeddings.text_model,
                device=self.settings.embeddings.device,
            )
            log.info("Embedding model loaded", model=self.settings.embeddings.text_model)
        except Exception as e:
            log.warning("SentenceTransformer unavailable, fallback in orchestrator", error=str(e))
            self.embedding_model = None

        # ── LLM Service ─────────────────────────────────────────
        self.llm_service = LLMService()

        # ── Real AMDIOrchestrator ───────────────────────────────
        self.rag_engine = AMDIOrchestrator(config=amdi_config)
        if self.embedding_model is None and hasattr(self.rag_engine, "_embedding") and self.rag_engine._embedding:
            self.embedding_model = self.rag_engine._embedding

        # ── Memory Engine (Redis-backed Cache) ─────────────────
        self.memory_engine = await self._init_memory()
        if self.rag_engine and self.memory_engine:
            self.rag_engine.semantic_cache = self.memory_engine

        # ── Document Service ─────────────────────────────────────
        self.document_service = RealDocumentService(self.rag_engine)

        # ── Query Service ────────────────────────────────────────
        self.query_service = QueryService(
            rag_engine=self.rag_engine,
            memory_engine=self.memory_engine,
            llm_service=self.llm_service,
            embedding_model=self.embedding_model,
            document_service=self.document_service,
        )

        # ── Advanced Submodules Wire-Up ─────────────────────────
        from src.compliance.redaction_engine import RedactionPolicy
        from src.entity.canonicalizer import cluster_into_canonical_entities
        from src.versioning.diff_engine import compute_structural_diff
        from src.ingestion.anomaly_gate import run_ingestion_gate
        from src.engines.matrix.unit_normalizer import parse_quantity
        from src.query.decomposer import build_query_dag
        from src.math_concepts.master_math_engine import MasterUnifiedMathEngine

        self.compliance_service = RedactionPolicy
        self.entity_service = cluster_into_canonical_entities
        self.versioning_service = compute_structural_diff
        self.anomaly_service = run_ingestion_gate
        self.normalizer_service = parse_quantity
        self.decomposer_service = build_query_dag
        self.math_engine = MasterUnifiedMathEngine()

        from src.engines.intelligence.service import DocumentIntelligenceService
        self.intelligence_service = DocumentIntelligenceService()

        self._started = True
        log.info("Service container ready")

    async def shutdown(self):
        """Graceful shutdown of all services."""
        log.info("Shutting down service container")
        self._started = False
        if self.rag_engine:
            try:
                await self.rag_engine.close()
            except Exception as e:
                log.warning("Error closing RAG engine during shutdown", error=str(e))
        if hasattr(self, "_redis") and self._redis:
            try:
                await self._redis.close()
            except Exception as e:
                log.warning("Error closing Redis during shutdown", error=str(e))

    async def verify_readiness(self) -> tuple[bool, dict[str, str]]:
        """Verify whether critical services and persistent database are ready to serve traffic."""
        details: dict[str, str] = {}
        if not getattr(self, "_started", False):
            details["container"] = "not_started"
            return False, details
        details["container"] = "ok"

        # Database readiness check
        if self.document_service is not None:
            db_path = getattr(self.document_service, "db_path", None)
            if db_path and db_path != ":memory:":
                try:
                    with sqlite3.connect(db_path, timeout=3.0) as conn:
                        cursor = conn.cursor()
                        cursor.execute("SELECT 1 FROM documents LIMIT 1")
                    details["database"] = "ok"
                except Exception as db_err:
                    details["database"] = f"unhealthy: {db_err}"
                    return False, details
            else:
                details["database"] = "ok"
        else:
            details["database"] = "missing_service"
            return False, details

        details["memory"] = "ok" if getattr(self, "memory", None) is not None else "degraded"
        details["rag_engine"] = "ok" if self.rag_engine is not None else "missing"
        return True, details

    async def health_check(self) -> dict[str, str]:
        """Check health of all dependent services."""
        checks = {
            "api": "ok",
            "embedding_model": "ok" if self.embedding_model else "unavailable",
            "llm_service": "ok" if self.llm_service else "unavailable",
        }

        # Check Redis
        try:
            if hasattr(self, "_redis") and self._redis:
                await self._redis.ping()
                checks["redis"] = "ok"
        except Exception:
            checks["redis"] = "unavailable"

        checks["milvus"] = "ok" if self.rag_engine and self.rag_engine._vector_store else "mock"
        checks["elasticsearch"] = "ok" if self.rag_engine and self.rag_engine._frequency else "mock"

        return checks

    async def _init_memory(self):
        """Initialize memory engine (Redis-backed)."""
        try:
            import redis.asyncio as redis_async
            self._redis = redis_async.from_url(
                self.settings.redis.url,
                decode_responses=False,
                socket_timeout=1.0,
                socket_connect_timeout=1.0,
            )
            await self._redis.ping()
            log.info("Redis connected", url=self.settings.redis.url)

            from src.memory_engine.semantic_cache import SemanticCache
            return SemanticCache(redis_client=self._redis)
        except Exception as e:
            log.warning("Redis unavailable, memory cache disabled", error=str(e))
            return None
