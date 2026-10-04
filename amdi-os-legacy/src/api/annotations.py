"""Annotation API routes."""
from __future__ import annotations

from typing import Optional, List, Dict, Any

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, Field

from src.annotations.engine import AnnotationEngine
from src.annotations.models import (
    Annotation, AnnotationPosition, AnnotationStatus, AnnotationType,
)
from src.annotations.ai_assist import AIAnnotationAssistant

router = APIRouter(prefix="/annotations", tags=["annotations"])
engine = AnnotationEngine()
ai_assistant = AIAnnotationAssistant(engine)


# ============================================================
# SCHEMAS
# ============================================================

class PositionSchema(BaseModel):
    page: int
    bbox: Optional[List[float]] = None
    char_start: Optional[int] = None
    char_end: Optional[int] = None
    section: Optional[str] = None
    element_id: Optional[str] = None


class AnnotationCreate(BaseModel):
    doc_id: str
    type: AnnotationType = AnnotationType.NOTE
    position: PositionSchema
    content: str
    color: str = "#fbbf24"
    tags: List[str] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    user_id: str = "default"


class AnnotationUpdate(BaseModel):
    content: Optional[str] = None
    status: Optional[AnnotationStatus] = None
    color: Optional[str] = None
    tags: Optional[List[str]] = None
    metadata: Optional[dict] = None


class HighlightCreate(BaseModel):
    doc_id: str
    page: int
    bbox: List[float]  # [x0, y0, x1, y1]
    text: str = ""
    color: str = "#fde047"
    element_id: Optional[str] = None
    user_id: str = "default"


class NoteCreate(BaseModel):
    doc_id: str
    page: int
    content: str
    bbox: Optional[List[float]] = None
    color: str = "#fbbf24"
    element_id: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    user_id: str = "default"


class CorrectionCreate(BaseModel):
    doc_id: str
    page: int
    original_text: str
    corrected_text: str
    bbox: Optional[List[float]] = None
    user_id: str = "default"


class VerificationCreate(BaseModel):
    doc_id: str
    page: int
    claim: str
    is_correct: bool
    element_id: Optional[str] = None
    user_id: str = "default"


class AutoAnnotateRequest(BaseModel):
    doc_id: str
    enable_insights: bool = False


class ImportRequest(BaseModel):
    json_data: str


# ============================================================
# ENDPOINTS
# ============================================================

@router.post("/")
async def create_generic_annotation(data: AnnotationCreate):
    """Create a generic annotation."""
    bbox_tuple = tuple(data.position.bbox) if data.position.bbox else None
    annotation = Annotation(
        doc_id=data.doc_id,
        user_id=data.user_id,
        type=data.type,
        position=AnnotationPosition(
            page=data.position.page,
            bbox=bbox_tuple,
            char_start=data.position.char_start,
            char_end=data.position.char_end,
            section=data.position.section,
            element_id=data.position.element_id
        ),
        content=data.content,
        color=data.color,
        tags=data.tags,
        metadata=data.metadata,
    )
    aid = engine.store.create_annotation(annotation)
    return {"id": aid, "status": "created"}


@router.post("/highlight")
async def create_highlight(data: HighlightCreate):
    """Create a highlight annotation."""
    bbox = tuple(data.bbox)
    if len(bbox) != 4:
        raise HTTPException(400, "bbox must be exactly 4 coordinates [x0, y0, x1, y1]")
    aid = engine.highlight(
        doc_id=data.doc_id,
        page=data.page,
        bbox=bbox,
        text=data.text,
        color=data.color,
        element_id=data.element_id,
        user_id=data.user_id,
    )
    return {"id": aid, "status": "created"}


@router.post("/note")
async def create_note(data: NoteCreate):
    """Create a note annotation."""
    bbox = tuple(data.bbox) if data.bbox else None
    if bbox and len(bbox) != 4:
        raise HTTPException(400, "bbox must be exactly 4 coordinates [x0, y0, x1, y1]")
    aid = engine.add_note(
        doc_id=data.doc_id,
        page=data.page,
        content=data.content,
        bbox=bbox,
        color=data.color,
        element_id=data.element_id,
        tags=data.tags,
        user_id=data.user_id,
    )
    return {"id": aid, "status": "created"}


@router.post("/correction")
async def create_correction(data: CorrectionCreate):
    """Create a correction annotation."""
    bbox = tuple(data.bbox) if data.bbox else None
    if bbox and len(bbox) != 4:
        raise HTTPException(400, "bbox must be exactly 4 coordinates [x0, y0, x1, y1]")
    aid = engine.add_correction(
        doc_id=data.doc_id,
        page=data.page,
        original_text=data.original_text,
        corrected_text=data.corrected_text,
        bbox=bbox,
        user_id=data.user_id,
    )
    return {"id": aid, "status": "created"}


@router.post("/verify")
async def create_verification(data: VerificationCreate):
    """Create a verification annotation."""
    aid = engine.verify_claim(
        doc_id=data.doc_id,
        page=data.page,
        claim=data.claim,
        is_correct=data.is_correct,
        element_id=data.element_id,
        user_id=data.user_id,
    )
    return {"id": aid, "status": "created"}


@router.get("/{annotation_id}")
async def get_annotation(annotation_id: str):
    """Get an annotation by ID."""
    annotation = engine.store.get_annotation(annotation_id)
    if not annotation:
        raise HTTPException(404, "Annotation not found")
    return annotation.to_dict()


@router.get("/")
async def list_annotations(
    doc_id: str,
    page: Optional[int] = None,
    type: Optional[AnnotationType] = None,
    user_id: Optional[str] = None,
    status: Optional[AnnotationStatus] = None,
    limit: int = Query(1000, le=10000),
):
    """List annotations with filters."""
    annotations = engine.store.list_annotations(
        doc_id=doc_id,
        page=page, type=type,
        user_id=user_id, status=status,
        limit=limit,
    )
    return {
        "doc_id": doc_id,
        "count": len(annotations),
        "annotations": [a.to_dict() for a in annotations],
    }


@router.get("/search/")
async def search_annotations(doc_id: str, q: str):
    """Search annotations."""
    annotations = engine.search(doc_id, q)
    return {
        "doc_id": doc_id,
        "query": q,
        "count": len(annotations),
        "results": [a.to_dict() for a in annotations],
    }


@router.patch("/{annotation_id}")
async def update_annotation(annotation_id: str, data: AnnotationUpdate):
    """Update an annotation."""
    success = engine.update(
        annotation_id,
        content=data.content,
        status=data.status,
        color=data.color,
        tags=data.tags,
    )
    if not success:
        raise HTTPException(404, "Annotation not found or no updates")
    return {"id": annotation_id, "status": "updated"}


@router.post("/{annotation_id}/resolve")
async def resolve_annotation(annotation_id: str):
    """Mark annotation as resolved."""
    success = engine.resolve(annotation_id)
    if not success:
        raise HTTPException(404, "Annotation not found")
    return {"id": annotation_id, "status": "resolved"}


@router.delete("/{annotation_id}")
async def delete_annotation(annotation_id: str, soft: bool = True):
    """Delete an annotation."""
    success = engine.delete(annotation_id, soft=soft)
    if not success:
        raise HTTPException(404, "Annotation not found")
    return {"id": annotation_id, "status": "deleted"}


@router.get("/statistics/{doc_id}")
async def get_statistics(doc_id: str):
    """Get annotation statistics for a document."""
    stats = engine.statistics(doc_id)
    return stats


@router.post("/auto-annotate")
async def auto_annotate(req: AutoAnnotateRequest, request: Request):
    """Automatically generate AI annotations for document elements."""
    orchestrator = request.app.state.orchestrator
    if not orchestrator:
        raise HTTPException(503, "Orchestrator not initialized")
    
    elements = orchestrator.get_document_elements(req.doc_id)
    if not elements:
        raise HTTPException(404, f"No elements found for document {req.doc_id}")
    
    results = await ai_assistant.auto_annotate_all(
        doc_id=req.doc_id,
        elements=elements,
        enable_insights=req.enable_insights
    )
    
    # Return counts of created items
    return {
        "status": "ok",
        "doc_id": req.doc_id,
        "counts": {
            "tags": len(results["tags"]),
            "numerical_flags": len(results["numerical_flags"]),
            "questions": len(results["questions"]),
            "inconsistencies": len(results["inconsistencies"]),
            "insights": len(results["insights"]),
        }
    }


@router.get("/export/{doc_id}")
async def export_annotations(doc_id: str):
    """Export annotations to JSON string."""
    json_str = engine.export(doc_id)
    return {"doc_id": doc_id, "json_data": json_str}


@router.post("/import/{doc_id}")
async def import_annotations(doc_id: str, req: ImportRequest):
    """Import annotations from JSON string."""
    try:
        count = engine.import_annotations(doc_id, req.json_data)
        return {"status": "ok", "doc_id": doc_id, "imported_count": count}
    except Exception as e:
        raise HTTPException(400, f"Failed to import annotations: {e}")
