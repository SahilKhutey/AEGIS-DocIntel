"""
AEGIS-AMDI-OS — Annotation Engine
====================================
Business logic for annotations.
"""
from __future__ import annotations

import logging
from typing import Optional

from src.annotations.models import (
    Annotation, AnnotationPosition, AnnotationStatus, AnnotationThread, AnnotationType,
)
from src.annotations.store import AnnotationStore

logger = logging.getLogger(__name__)


class AnnotationEngine:
    """
    High-level annotation operations.
    """

    def __init__(self, store: AnnotationStore | None = None):
        self.store = store or AnnotationStore()

    # ============================================================
    # HIGHLIGHTING
    # ============================================================

    def highlight(
        self,
        doc_id: str,
        page: int,
        bbox: tuple[float, float, float, float],
        text: str = "",
        color: str = "#fde047",
        user_id: str = "default",
        element_id: str | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Create a highlight annotation."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.HIGHLIGHT,
            position=AnnotationPosition(page=page, bbox=bbox, element_id=element_id),
            content=text,
            color=color,
            parent_id=parent_id,
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # NOTES
    # ============================================================

    def add_note(
        self,
        doc_id: str,
        page: int,
        content: str,
        bbox: tuple[float, float, float, float] | None = None,
        color: str = "#fbbf24",
        user_id: str = "default",
        element_id: str | None = None,
        tags: list[str] | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a note annotation."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.NOTE,
            position=AnnotationPosition(page=page, bbox=bbox, element_id=element_id),
            content=content,
            color=color,
            tags=tags or [],
            parent_id=parent_id,
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # CORRECTIONS
    # ============================================================

    def add_correction(
        self,
        doc_id: str,
        page: int,
        original_text: str,
        corrected_text: str,
        bbox: tuple[float, float, float, float] | None = None,
        user_id: str = "default",
        element_id: str | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Record a correction to the document text."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.CORRECTION,
            position=AnnotationPosition(page=page, bbox=bbox, element_id=element_id),
            content=corrected_text,
            color="#ef4444",
            metadata={"original_text": original_text, "type": "correction"},
            parent_id=parent_id,
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # QUESTIONS
    # ============================================================

    def ask_question(
        self,
        doc_id: str,
        page: int,
        question: str,
        bbox: tuple[float, float, float, float] | None = None,
        user_id: str = "default",
        element_id: str | None = None,
        parent_id: str | None = None,
    ) -> str:
        """Add a question about a specific element/page."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.QUESTION,
            position=AnnotationPosition(page=page, bbox=bbox, element_id=element_id),
            content=question,
            color="#a78bfa",
            metadata={"resolved": False},
            parent_id=parent_id,
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # TAGS
    # ============================================================

    def tag_element(
        self,
        doc_id: str,
        page: int,
        element_id: str,
        tags: list[str],
        user_id: str = "default",
    ) -> str:
        """Tag a specific element."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.TAG,
            position=AnnotationPosition(page=page, element_id=element_id),
            content=", ".join(tags),
            color="#10b981",
            tags=tags,
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # VERIFICATION
    # ============================================================

    def verify_claim(
        self,
        doc_id: str,
        page: int,
        claim: str,
        is_correct: bool,
        user_id: str = "default",
        element_id: str | None = None,
    ) -> str:
        """Mark a claim as verified correct or incorrect."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.VERIFICATION,
            position=AnnotationPosition(page=page, element_id=element_id),
            content=f"{'✓' if is_correct else '✗'} {claim}",
            color="#22c55e" if is_correct else "#ef4444",
            status=AnnotationStatus.RESOLVED if is_correct else AnnotationStatus.ACTIVE,
            metadata={"verified": is_correct},
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # RATINGS
    # ============================================================

    def rate_element(
        self,
        doc_id: str,
        page: int,
        element_id: str,
        rating: int,  # 1-5
        comment: str = "",
        user_id: str = "default",
    ) -> str:
        """Rate an element 1-5 stars."""
        if not 1 <= rating <= 5:
            raise ValueError("Rating must be 1-5")
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.RATING,
            position=AnnotationPosition(page=page, element_id=element_id),
            content=comment,
            color="#fbbf24",
            metadata={"rating": rating, "stars": "⭐" * rating},
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # BOOKMARKS
    # ============================================================

    def bookmark(
        self,
        doc_id: str,
        page: int,
        label: str,
        user_id: str = "default",
    ) -> str:
        """Bookmark a page."""
        annotation = Annotation(
            doc_id=doc_id,
            user_id=user_id,
            type=AnnotationType.BOOKMARK,
            position=AnnotationPosition(page=page),
            content=label,
            color="#f59e0b",
        )
        return self.store.create_annotation(annotation)

    # ============================================================
    # THREADS
    # ============================================================

    def start_thread(
        self,
        doc_id: str,
        title: str,
        first_annotation_id: str,
        user_id: str = "default",
    ) -> str:
        """Start a discussion thread."""
        thread = AnnotationThread(
            doc_id=doc_id,
            title=title,
            annotation_ids=[first_annotation_id],
        )
        return self.store.create_thread(thread)

    def reply_to_thread(
        self,
        thread_id: str,
        annotation_id: str,
    ) -> bool:
        """Add an annotation to a thread."""
        # Find thread
        with self.store._connect() as conn:
            row = conn.execute(
                "SELECT annotation_ids FROM threads WHERE id = ?", (thread_id,)
            ).fetchone()
            if not row:
                return False
            ann_ids = json.loads(row["annotation_ids"] or "[]")
            if annotation_id not in ann_ids:
                ann_ids.append(annotation_id)
            conn.execute(
                "UPDATE threads SET annotation_ids = ? WHERE id = ?",
                (json.dumps(ann_ids), thread_id)
            )
        # Also update parent replies relation if applicable
        ann = self.store.get_annotation(annotation_id)
        if ann and ann.parent_id:
            self.store.add_reply(ann.parent_id, annotation_id)
        return True

    # ============================================================
    # QUERIES
    # ============================================================

    def get_page_annotations(
        self, doc_id: str, page: int,
    ) -> list[Annotation]:
        """Get all annotations for a specific page."""
        return self.store.list_annotations(doc_id=doc_id, page=page)

    def get_user_annotations(
        self, doc_id: str, user_id: str,
    ) -> list[Annotation]:
        """Get all annotations by a specific user."""
        return self.store.list_annotations(doc_id=doc_id, user_id=user_id)

    def search(
        self, doc_id: str, query: str,
    ) -> list[Annotation]:
        """Search annotations by content."""
        return self.store.search_annotations(doc_id, query)

    def statistics(self, doc_id: str) -> dict:
        """Get statistics."""
        return self.store.statistics(doc_id)

    # ============================================================
    # OPERATIONS
    # ============================================================

    def update(
        self,
        annotation_id: str,
        content: str | None = None,
        status: AnnotationStatus | None = None,
        color: str | None = None,
        tags: list[str] | None = None,
    ) -> bool:
        return self.store.update_annotation(
            annotation_id, content, status, color, tags,
        )

    def resolve(self, annotation_id: str) -> bool:
        """Mark an annotation as resolved."""
        return self.store.update_annotation(
            annotation_id, status=AnnotationStatus.RESOLVED,
        )

    def delete(self, annotation_id: str, soft: bool = True) -> bool:
        return self.store.delete_annotation(annotation_id, soft=soft)

    def export(self, doc_id: str) -> str:
        return self.store.export_to_json(doc_id)

    def import_annotations(self, doc_id: str, json_data: str) -> int:
        return self.store.import_from_json(json_data)
import json # import json for reply_to_thread serialization
