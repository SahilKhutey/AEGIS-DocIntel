"""
AEGIS-AMDI-OS — Annotation Storage
====================================
Persistent SQLite-based annotation storage.
"""
from __future__ import annotations

import json
import logging
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Iterator

from src.annotations.models import (
    Annotation, AnnotationPosition, AnnotationStatus, AnnotationThread, AnnotationType,
)

logger = logging.getLogger(__name__)


class AnnotationStore:
    """
    SQLite-backed annotation storage.

    Thread-safe with a lock.
    Schema is auto-created on first use.
    """

    SCHEMA = """
    CREATE TABLE IF NOT EXISTS annotations (
        id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        user_id TEXT NOT NULL,
        type TEXT NOT NULL,
        status TEXT NOT NULL,
        page INTEGER NOT NULL,
        bbox TEXT,
        char_start INTEGER,
        char_end INTEGER,
        section TEXT,
        element_id TEXT,
        content TEXT NOT NULL,
        color TEXT,
        tags TEXT,
        metadata TEXT,
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL,
        parent_id TEXT,
        replies TEXT
    );

    CREATE TABLE IF NOT EXISTS threads (
        id TEXT PRIMARY KEY,
        doc_id TEXT NOT NULL,
        title TEXT NOT NULL,
        annotation_ids TEXT,
        created_at TEXT NOT NULL,
        resolved INTEGER DEFAULT 0
    );

    CREATE INDEX IF NOT EXISTS idx_annotations_doc ON annotations(doc_id);
    CREATE INDEX IF NOT EXISTS idx_annotations_page ON annotations(doc_id, page);
    CREATE INDEX IF NOT EXISTS idx_annotations_type ON annotations(doc_id, type);
    CREATE INDEX IF NOT EXISTS idx_annotations_user ON annotations(doc_id, user_id);
    CREATE INDEX IF NOT EXISTS idx_threads_doc ON threads(doc_id);
    """

    def __init__(self, db_path: str = "data/annotations.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize database schema."""
        with self._connect() as conn:
            conn.executescript(self.SCHEMA)

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        """Thread-safe connection context."""
        with self._lock:
            conn = sqlite3.connect(str(self.db_path), timeout=30)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            finally:
                conn.close()

    # ============================================================
    # CREATE
    # ============================================================

    def create_annotation(self, annotation: Annotation) -> str:
        """Create a new annotation. Returns its ID."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO annotations
                (id, doc_id, user_id, type, status, page, bbox, char_start, char_end,
                 section, element_id, content, color, tags, metadata,
                 created_at, updated_at, parent_id, replies)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    annotation.id, annotation.doc_id, annotation.user_id,
                    annotation.type.value, annotation.status.value,
                    annotation.position.page,
                    json.dumps(annotation.position.bbox) if annotation.position.bbox else None,
                    annotation.position.char_start,
                    annotation.position.char_end,
                    annotation.position.section,
                    annotation.position.element_id,
                    annotation.content, annotation.color,
                    json.dumps(annotation.tags),
                    json.dumps(annotation.metadata),
                    annotation.created_at.isoformat(),
                    annotation.updated_at.isoformat(),
                    annotation.parent_id,
                    json.dumps(annotation.replies),
                ),
            )
        return annotation.id

    # ============================================================
    # READ
    # ============================================================

    def get_annotation(self, annotation_id: str) -> Annotation | None:
        """Get a single annotation by ID."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM annotations WHERE id = ?", (annotation_id,)
            ).fetchone()
        if not row:
            return None
        return self._row_to_annotation(row)

    def list_annotations(
        self,
        doc_id: str,
        page: int | None = None,
        type: AnnotationType | None = None,
        user_id: str | None = None,
        status: AnnotationStatus | None = None,
        tags: list[str] | None = None,
        limit: int = 1000,
    ) -> list[Annotation]:
        """List annotations with optional filters."""
        query = "SELECT * FROM annotations WHERE doc_id = ? AND status != 'deleted'"
        params: list = [doc_id]
        if page is not None:
            query += " AND page = ?"
            params.append(page)
        if type is not None:
            query += " AND type = ?"
            params.append(type.value)
        if user_id is not None:
            query += " AND user_id = ?"
            params.append(user_id)
        if status is not None:
            query += " AND status = ?"
            params.append(status.value)
        query += " ORDER BY page, created_at LIMIT ?"
        params.append(limit)
        with self._connect() as conn:
            rows = conn.execute(query, params).fetchall()
        return [self._row_to_annotation(row) for row in rows]

    def search_annotations(
        self, doc_id: str, query: str, limit: int = 100,
    ) -> list[Annotation]:
        """Full-text search in annotation content."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT * FROM annotations
                WHERE doc_id = ? AND status != 'deleted'
                AND content LIKE ?
                ORDER BY created_at DESC LIMIT ?""",
                (doc_id, f"%{query}%", limit),
            ).fetchall()
        return [self._row_to_annotation(row) for row in rows]

    # ============================================================
    # UPDATE
    # ============================================================

    def update_annotation(
        self,
        annotation_id: str,
        content: str | None = None,
        status: AnnotationStatus | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
        metadata: dict | None = None,
    ) -> bool:
        """Update an annotation. Returns True if successful."""
        updates = []
        params: list = []
        if content is not None:
            updates.append("content = ?")
            params.append(content)
        if status is not None:
            updates.append("status = ?")
            params.append(status.value)
        if color is not None:
            updates.append("color = ?")
            params.append(color)
        if tags is not None:
            updates.append("tags = ?")
            params.append(json.dumps(tags))
        if metadata is not None:
            updates.append("metadata = ?")
            params.append(json.dumps(metadata))
        if not updates:
            return False
        updates.append("updated_at = ?")
        params.append(datetime.now().isoformat())
        params.append(annotation_id)
        with self._connect() as conn:
            cursor = conn.execute(
                f"UPDATE annotations SET {', '.join(updates)} WHERE id = ?",
                params,
            )
            return cursor.rowcount > 0

    def add_reply(self, parent_id: str, reply_id: str) -> bool:
        """Add a reply annotation to a parent."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT replies FROM annotations WHERE id = ?", (parent_id,)
            ).fetchone()
            if not row:
                return False
            replies = json.loads(row["replies"] or "[]")
            if reply_id not in replies:
                replies.append(reply_id)
            conn.execute(
                "UPDATE annotations SET replies = ?, updated_at = ? WHERE id = ?",
                (json.dumps(replies), datetime.now().isoformat(), parent_id),
            )
        return True

    # ============================================================
    # DELETE
    # ============================================================

    def delete_annotation(self, annotation_id: str, soft: bool = True) -> bool:
        """Delete an annotation (soft delete by default)."""
        if soft:
            return self.update_annotation(
                annotation_id, status=AnnotationStatus.DELETED,
            )
        with self._connect() as conn:
            cursor = conn.execute(
                "DELETE FROM annotations WHERE id = ?", (annotation_id,)
            )
            return cursor.rowcount > 0

    # ============================================================
    # THREADS
    # ============================================================

    def create_thread(self, thread: AnnotationThread) -> str:
        """Create an annotation thread."""
        with self._connect() as conn:
            conn.execute(
                """INSERT INTO threads
                (id, doc_id, title, annotation_ids, created_at, resolved)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    thread.id, thread.doc_id, thread.title,
                    json.dumps(thread.annotation_ids),
                    thread.created_at.isoformat(),
                    int(thread.resolved),
                ),
            )
        return thread.id

    def list_threads(self, doc_id: str) -> list[AnnotationThread]:
        """List all threads for a document."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM threads WHERE doc_id = ? ORDER BY created_at DESC",
                (doc_id,),
            ).fetchall()
        return [
            AnnotationThread(
                id=row["id"],
                doc_id=row["doc_id"],
                title=row["title"],
                annotation_ids=json.loads(row["annotation_ids"] or "[]"),
                created_at=datetime.fromisoformat(row["created_at"]),
                resolved=bool(row["resolved"]),
            )
            for row in rows
        ]

    # ============================================================
    # STATISTICS
    # ============================================================

    def statistics(self, doc_id: str) -> dict:
        """Get annotation statistics for a document."""
        annotations = self.list_annotations(doc_id)
        if not annotations:
            return {"doc_id": doc_id, "n_total": 0}
        by_type: dict[str, int] = {}
        by_status: dict[str, int] = {}
        by_page: dict[int, int] = {}
        for a in annotations:
            by_type[a.type.value] = by_type.get(a.type.value, 0) + 1
            by_status[a.status.value] = by_status.get(a.status.value, 0) + 1
            by_page[a.position.page] = by_page.get(a.position.page, 0) + 1
        return {
            "doc_id": doc_id,
            "n_total": len(annotations),
            "by_type": by_type,
            "by_status": by_status,
            "by_page": by_page,
            "n_pages_annotated": len(by_page),
        }

    # ============================================================
    # HELPERS
    # ============================================================

    def _row_to_annotation(self, row: sqlite3.Row) -> Annotation:
        """Convert SQLite row to Annotation object."""
        bbox_data = json.loads(row["bbox"]) if row["bbox"] else None
        return Annotation(
            id=row["id"],
            doc_id=row["doc_id"],
            user_id=row["user_id"],
            type=AnnotationType(row["type"]),
            status=AnnotationStatus(row["status"]),
            position=AnnotationPosition(
                page=row["page"],
                bbox=tuple(bbox_data) if bbox_data else None,
                char_start=row["char_start"],
                char_end=row["char_end"],
                section=row["section"],
                element_id=row["element_id"],
            ),
            content=row["content"],
            color=row["color"] or "#fbbf24",
            tags=json.loads(row["tags"] or "[]"),
            metadata=json.loads(row["metadata"] or "{}"),
            created_at=datetime.fromisoformat(row["created_at"]),
            updated_at=datetime.fromisoformat(row["updated_at"]),
            parent_id=row["parent_id"],
            replies=json.loads(row["replies"] or "[]"),
        )

    def export_to_json(self, doc_id: str) -> str:
        """Export all annotations to JSON."""
        annotations = self.list_annotations(doc_id)
        threads = self.list_threads(doc_id)
        return json.dumps({
            "doc_id": doc_id,
            "annotations": [a.to_dict() for a in annotations],
            "threads": [t.to_dict() for t in threads],
        }, indent=2)

    def import_from_json(self, json_data: str) -> int:
        """Import annotations from JSON. Returns count imported."""
        data = json.loads(json_data)
        count = 0
        for ann_data in data.get("annotations", []):
            bbox_val = ann_data["position"].get("bbox")
            bbox_tuple = tuple(bbox_val) if bbox_val else None
            ann = Annotation(
                id=ann_data["id"],
                doc_id=ann_data["doc_id"],
                user_id=ann_data.get("user_id", "default"),
                type=AnnotationType(ann_data["type"]),
                status=AnnotationStatus(ann_data["status"]),
                position=AnnotationPosition(
                    page=ann_data["position"]["page"],
                    bbox=bbox_tuple,
                    char_start=ann_data["position"].get("char_start"),
                    char_end=ann_data["position"].get("char_end"),
                    section=ann_data["position"].get("section"),
                    element_id=ann_data["position"].get("element_id")
                ),
                content=ann_data["content"],
                color=ann_data.get("color", "#fbbf24"),
                tags=ann_data.get("tags", []),
                metadata=ann_data.get("metadata", {}),
                parent_id=ann_data.get("parent_id"),
                replies=ann_data.get("replies", []),
            )
            ann.created_at = datetime.fromisoformat(ann_data["created_at"])
            ann.updated_at = datetime.fromisoformat(ann_data["updated_at"])
            self.create_annotation(ann)
            count += 1
        return count
