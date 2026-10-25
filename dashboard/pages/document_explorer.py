"""
Document Explorer
==================

Browse, search, and inspect processed documents.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DocumentSummary:
    """Summary view of a document."""

    document_id: str
    name: str
    file_type: str
    size_bytes: int
    page_count: int
    uploaded_at: str
    processed: bool
    engine_reports: Dict[str, bool] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "document_id": self.document_id,
            "name": self.name,
            "file_type": self.file_type,
            "size_bytes": self.size_bytes,
            "page_count": self.page_count,
            "uploaded_at": self.uploaded_at,
            "processed": self.processed,
            "engine_reports": self.engine_reports,
            "tags": self.tags,
            "metadata": self.metadata,
        }


class DocumentExplorer:
    """Document explorer backend API."""

    def __init__(self) -> None:
        self.documents: Dict[str, DocumentSummary] = {}

    def add_document(
        self,
        document_id: str,
        name: str,
        file_type: str,
        size_bytes: int,
        page_count: int = 0,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> DocumentSummary:
        from datetime import datetime, timezone
        summary = DocumentSummary(
            document_id=document_id,
            name=name,
            file_type=file_type,
            size_bytes=size_bytes,
            page_count=page_count,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
            processed=False,
            tags=tags or [],
            metadata=metadata or {},
        )
        self.documents[document_id] = summary
        return summary

    def mark_processed(
        self,
        document_id: str,
        engine_reports: Optional[Dict[str, bool]] = None,
    ) -> DocumentSummary:
        if document_id not in self.documents:
            raise ValueError(f"Document {document_id} not found")
        doc = self.documents[document_id]
        doc.processed = True
        doc.engine_reports = engine_reports or doc.engine_reports
        return doc

    def list_documents(
        self,
        tag: Optional[str] = None,
        file_type: Optional[str] = None,
        processed_only: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> List[DocumentSummary]:
        items = list(self.documents.values())
        if tag:
            items = [d for d in items if tag in d.tags]
        if file_type:
            items = [d for d in items if d.file_type == file_type]
        if processed_only:
            items = [d for d in items if d.processed]
        items.sort(key=lambda d: d.uploaded_at, reverse=True)
        return items[offset : offset + limit]

    def search(
        self,
        query: str,
        limit: int = 20,
    ) -> List[DocumentSummary]:
        q = query.lower()
        results = []
        for d in self.documents.values():
            if q in d.name.lower():
                results.append(d)
                continue
            if any(q in t.lower() for t in d.tags):
                results.append(d)
                continue
            if any(q in str(v).lower() for v in d.metadata.values()):
                results.append(d)
        return results[:limit]

    def get_stats(self) -> Dict[str, Any]:
        total = len(self.documents)
        processed = sum(1 for d in self.documents.values() if d.processed)
        by_type: Dict[str, int] = {}
        total_size = 0
        total_pages = 0
        for d in self.documents.values():
            by_type[d.file_type] = by_type.get(d.file_type, 0) + 1
            total_size += d.size_bytes
            total_pages += d.page_count
        return {
            "total_documents": total,
            "processed": processed,
            "unprocessed": total - processed,
            "by_type": by_type,
            "total_size_bytes": total_size,
            "total_pages": total_pages,
        }
