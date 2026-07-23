"""
Upload Dashboard
=================

File ingestion page.
Backend contract for upload tracking, queueing, validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional


class UploadStatus(Enum):
    PENDING = "pending"
    UPLOADING = "uploading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class UploadItem:
    """A single upload record."""

    upload_id: str
    filename: str
    file_size: int
    file_type: str
    status: UploadStatus
    progress: float = 0.0
    uploaded_at: str = ""
    processed_at: Optional[str] = None
    error_message: Optional[str] = None
    document_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "upload_id": self.upload_id,
            "filename": self.filename,
            "file_size": self.file_size,
            "file_type": self.file_type,
            "status": self.status.value,
            "progress": round(self.progress, 4),
            "uploaded_at": self.uploaded_at,
            "processed_at": self.processed_at,
            "error_message": self.error_message,
            "document_id": self.document_id,
            "metadata": self.metadata,
        }


@dataclass
class UploadPageData:
    """Data for the upload dashboard."""

    active_uploads: List[UploadItem] = field(default_factory=list)
    recent_uploads: List[UploadItem] = field(default_factory=list)
    total_uploaded: int = 0
    total_size_bytes: int = 0
    success_rate: float = 1.0
    supported_formats: List[str] = field(default_factory=lambda: [
        "PDF", "DOCX", "PPTX", "XLSX", "PNG", "JPG", "TXT",
    ])
    max_file_size_mb: int = 100

    def to_dict(self) -> dict:
        return {
            "active_uploads": [u.to_dict() for u in self.active_uploads],
            "recent_uploads": [u.to_dict() for u in self.recent_uploads],
            "total_uploaded": self.total_uploaded,
            "total_size_bytes": self.total_size_bytes,
            "success_rate": round(self.success_rate, 4),
            "supported_formats": self.supported_formats,
            "max_file_size_mb": self.max_file_size_mb,
        }


class UploadDashboard:
    """Upload dashboard backend API."""

    def __init__(self) -> None:
        self.uploads: Dict[str, UploadItem] = {}

    def create_upload(
        self,
        filename: str,
        file_size: int,
        file_type: str,
    ) -> UploadItem:
        import uuid
        upload_id = str(uuid.uuid4())
        item = UploadItem(
            upload_id=upload_id,
            filename=filename,
            file_size=file_size,
            file_type=file_type,
            status=UploadStatus.PENDING,
            uploaded_at=datetime.now(timezone.utc).isoformat(),
        )
        self.uploads[upload_id] = item
        return item

    def update_progress(
        self,
        upload_id: str,
        progress: float,
        status: Optional[UploadStatus] = None,
    ) -> UploadItem:
        if upload_id not in self.uploads:
            raise ValueError(f"Upload {upload_id} not found")
        item = self.uploads[upload_id]
        item.progress = max(0.0, min(1.0, progress))
        if status:
            item.status = status
        return item

    def complete_upload(
        self,
        upload_id: str,
        document_id: str,
    ) -> UploadItem:
        if upload_id not in self.uploads:
            raise ValueError(f"Upload {upload_id} not found")
        item = self.uploads[upload_id]
        item.status = UploadStatus.COMPLETED
        item.progress = 1.0
        item.document_id = document_id
        item.processed_at = datetime.now(timezone.utc).isoformat()
        return item

    def fail_upload(
        self,
        upload_id: str,
        error: str,
    ) -> UploadItem:
        if upload_id not in self.uploads:
            raise ValueError(f"Upload {upload_id} not found")
        item = self.uploads[upload_id]
        item.status = UploadStatus.FAILED
        item.error_message = error
        item.processed_at = datetime.now(timezone.utc).isoformat()
        return item

    def list_uploads(self, limit: int = 50) -> List[UploadItem]:
        items = sorted(
            self.uploads.values(),
            key=lambda u: u.uploaded_at,
            reverse=True,
        )
        return items[:limit]

    def get_active_uploads(self) -> List[UploadItem]:
        return [
            u for u in self.uploads.values()
            if u.status in (
                UploadStatus.PENDING,
                UploadStatus.UPLOADING,
                UploadStatus.PROCESSING,
            )
        ]

    def get_page_data(self) -> UploadPageData:
        active = self.get_active_uploads()
        recent = self.list_uploads(20)
        completed = [u for u in self.uploads.values() if u.status == UploadStatus.COMPLETED]
        failed = [u for u in self.uploads.values() if u.status == UploadStatus.FAILED]
        total_attempts = len(completed) + len(failed)
        success_rate = (
            len(completed) / total_attempts if total_attempts > 0 else 1.0
        )
        total_size = sum(u.file_size for u in self.uploads.values())
        return UploadPageData(
            active_uploads=active,
            recent_uploads=recent,
            total_uploaded=len(self.uploads),
            total_size_bytes=total_size,
            success_rate=success_rate,
        )
