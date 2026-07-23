"""
AEGIS-AMDI-OS — Annotation Models
====================================
Data models for document annotations.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class AnnotationType(str, Enum):
    """Types of annotations."""
    HIGHLIGHT = "highlight"
    NOTE = "note"
    CORRECTION = "correction"
    TAG = "tag"
    QUESTION = "question"
    VERIFICATION = "verification"
    RATING = "rating"
    MARKER = "marker"
    COMMENT = "comment"
    BOOKMARK = "bookmark"


class AnnotationStatus(str, Enum):
    """Status of an annotation."""
    DRAFT = "draft"
    ACTIVE = "active"
    RESOLVED = "resolved"
    ARCHIVED = "archived"
    DELETED = "deleted"


@dataclass
class AnnotationPosition:
    """Where in the document this annotation lives."""
    page: int
    bbox: Optional[tuple[float, float, float, float]] = None  # (x0, y0, x1, y1)
    char_start: Optional[int] = None  # Character offset (for text annotations)
    char_end: Optional[int] = None
    section: Optional[str] = None
    element_id: Optional[str] = None  # Reference to specific element

    def to_dict(self) -> dict:
        return {
            "page": self.page,
            "bbox": list(self.bbox) if self.bbox else None,
            "char_start": self.char_start,
            "char_end": self.char_end,
            "section": self.section,
            "element_id": self.element_id,
        }


@dataclass
class Annotation:
    """
    A single annotation on a document.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str = ""
    user_id: str = "default"
    type: AnnotationType = AnnotationType.NOTE
    status: AnnotationStatus = AnnotationStatus.ACTIVE
    position: AnnotationPosition = field(default_factory=lambda: AnnotationPosition(page=1))
    content: str = ""
    color: str = "#fbbf24"
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    parent_id: str | None = None
    replies: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "user_id": self.user_id,
            "type": self.type.value,
            "status": self.status.value,
            "position": self.position.to_dict(),
            "content": self.content,
            "color": self.color,
            "tags": self.tags,
            "metadata": self.metadata,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "parent_id": self.parent_id,
            "replies": self.replies,
        }


@dataclass
class AnnotationThread:
    """A thread of annotations (for discussion)."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: str = ""
    title: str = ""
    annotation_ids: list[str] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.now)
    resolved: bool = False

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "doc_id": self.doc_id,
            "title": self.title,
            "annotation_ids": self.annotation_ids,
            "created_at": self.created_at.isoformat(),
            "resolved": self.resolved,
        }


@dataclass
class AnnotationSet:
    """Collection of annotations for a document."""
    doc_id: str
    annotations: list[Annotation] = field(default_factory=list)
    threads: list[AnnotationThread] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "doc_id": self.doc_id,
            "annotations": [a.to_dict() for a in self.annotations],
            "threads": [t.to_dict() for t in self.threads],
        }
