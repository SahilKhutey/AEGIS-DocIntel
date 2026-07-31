"""Persistence to disk using numpy memmaps + a sidecar SQLite metadata DB."""

from __future__ import annotations

import asyncio
import json
import sqlite3
from pathlib import Path
from typing import Sequence

import numpy as np

from amdi.retrieval.index_store import CorpusUnit, IndexStore


class FilesystemIndexStore(IndexStore):
    def __init__(self, root: Path) -> None:
        self._root = Path(root)
        (self._root / "emb").mkdir(parents=True, exist_ok=True)
        self._db = self._root / "meta.sqlite"
        self._lock = asyncio.Lock()
        self._init_schema()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA synchronous=NORMAL")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as c:
            c.executescript(
                """
                CREATE TABLE IF NOT EXISTS units (
                    unit_id TEXT PRIMARY KEY,
                    document_id TEXT NOT NULL,
                    page INTEGER,
                    bbox TEXT,
                    section TEXT,
                    text TEXT NOT NULL,
                    emb_offset INTEGER,
                    emb_dim INTEGER
                );
                CREATE INDEX IF NOT EXISTS idx_units_doc ON units(document_id);
                """
            )

    async def add_units(self, units: Sequence[CorpusUnit]) -> None:
        grouped: dict[str, list[CorpusUnit]] = {}
        for u in units:
            grouped.setdefault(u.document_id, []).append(u)

        with self._connect() as c:
            for doc_id, group in grouped.items():
                embs = [u.embedding for u in group if u.embedding is not None]
                if embs:
                    arr = np.asarray(embs, dtype=np.float32)
                    path = self._root / "emb" / f"{doc_id}.npy"
                    if path.exists():
                        existing = np.load(path)
                        arr = np.vstack([existing, arr])
                    np.save(path, arr)
                else:
                    path = None

                for u in group:
                    emb_offset, emb_dim = None, None
                    if u.embedding is not None:
                        emb_dim = len(u.embedding)
                    bbox_json = json.dumps(u.bbox) if u.bbox else None
                    c.execute(
                        """INSERT OR REPLACE INTO units
                           (unit_id, document_id, page, bbox, section, text,
                            emb_offset, emb_dim)
                           VALUES (?,?,?,?,?,?,?,?)""",
                        (u.unit_id, u.document_id, u.page, bbox_json,
                         u.section, u.text, emb_offset, emb_dim),
                    )

    async def all_units(self) -> Sequence[CorpusUnit]:
        with self._connect() as c:
            rows = c.execute("SELECT unit_id, document_id, page, bbox, section, text, emb_offset, emb_dim FROM units").fetchall()
        return [self._row_to_unit(r) for r in rows]

    async def get_unit(self, unit_id: str) -> CorpusUnit | None:
        with self._connect() as c:
            r = c.execute("SELECT unit_id, document_id, page, bbox, section, text, emb_offset, emb_dim FROM units WHERE unit_id=?", (unit_id,)).fetchone()
        return self._row_to_unit(r) if r else None

    async def commit(self) -> None:
        with self._connect() as c:
            c.execute("PRAGMA wal_checkpoint(TRUNCATE)")

    async def size(self) -> int:
        with self._connect() as c:
            row = c.execute("SELECT COUNT(*) FROM units").fetchone()
            return row[0] if row else 0

    def _row_to_unit(self, row: tuple) -> CorpusUnit:
        (unit_id, document_id, page, bbox_json, section, text,
         emb_offset, emb_dim) = row
        bbox = tuple(json.loads(bbox_json)) if bbox_json else None
        return CorpusUnit(
            unit_id=unit_id, document_id=document_id,
            page=page, bbox=bbox, section=section, text=text,
        )

    async def load_embeddings(self, doc_id: str) -> np.ndarray | None:
        path = self._root / "emb" / f"{doc_id}.npy"
        if not path.exists():
            return None
        return np.load(path)


__all__ = ["FilesystemIndexStore"]
