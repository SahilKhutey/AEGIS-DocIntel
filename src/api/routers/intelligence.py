"""
src/api/routers/intelligence.py
===============================
AEGIS-DocIntel — Document Intelligence, Structured Extraction & Reasoning API.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant
from src.engines.intelligence.contracts import (
    ExtractionSchema,
)
from src.engines.intelligence.service import DocumentIntelligenceService

router = APIRouter()
log = structlog.get_logger("aegis.api.intelligence")

_default_service: Optional[DocumentIntelligenceService] = None


def get_intelligence_service(request: Request) -> DocumentIntelligenceService:
    global _default_service
    container = getattr(request.app.state, "container", None)
    if container is not None and hasattr(container, "intelligence_service") and container.intelligence_service is not None:
        return container.intelligence_service
    svc = getattr(request.app.state, "intelligence_service", None)
    if svc is not None:
        return svc
    if _default_service is None:
        _default_service = DocumentIntelligenceService()
    return _default_service


# ─────────────────────────────────────────────────────────────────
# Request & Response Schemas
# ─────────────────────────────────────────────────────────────────

class PassagePayload(BaseModel):
    chunk_id: Optional[str] = None
    text: str
    page_number: Optional[int] = None


class ExtractFactsRequest(BaseModel):
    schema_name: str = Field(default="contract_terms", description="Target extraction schema name")
    subject: Optional[str] = Field(default=None, description="Optional entity subject override")
    custom_schema: Optional[Dict[str, Any]] = Field(default=None, description="Custom ExtractionSchema definition")
    passages: Optional[List[PassagePayload]] = Field(default=None, description="Direct passages to extract facts from")


class EvidenceSpanModel(BaseModel):
    document_id: str
    tenant_id: str
    chunk_id: str
    page_number: Optional[int] = None
    start_offset: Optional[int] = None
    end_offset: Optional[int] = None
    quoted_text: str = ""


class FactModel(BaseModel):
    fact_id: str
    tenant_id: str
    document_id: str
    subject: str
    attribute: str
    value: Any
    raw_value: str
    value_type: str
    unit: Optional[str] = None
    period: Optional[str] = None
    valid_from: Optional[str] = None
    valid_to: Optional[str] = None
    evidence: List[EvidenceSpanModel] = Field(default_factory=list)
    confidence: Optional[float] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ExtractionResultResponse(BaseModel):
    status: str
    document_id: str
    tenant_id: str
    facts: List[FactModel] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)
    schema_name: Optional[str] = None
    schema_version: Optional[int] = None


class CompareDocumentsRequest(BaseModel):
    left_document_id: str
    right_document_id: str
    attributes: Optional[List[str]] = Field(default=None, description="Specific attributes to compare")


class PairComparisonModel(BaseModel):
    subject: str
    attribute: str
    status: str
    left_doc_id: str
    left_fact: FactModel
    right_doc_id: str
    right_fact: FactModel
    difference_summary: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class DocumentComparisonResponse(BaseModel):
    tenant_id: str
    left_doc_id: str
    right_doc_id: str
    comparisons: List[PairComparisonModel] = Field(default_factory=list)
    summary: Dict[str, int] = Field(default_factory=dict)


class ConflictReportModel(BaseModel):
    tenant_id: str
    subject: str
    attribute: str
    conflict_type: str
    description: str
    participating_facts: List[FactModel] = Field(default_factory=list)
    conflicting_document_ids: List[str] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
# Route Handlers
# ─────────────────────────────────────────────────────────────────

@router.post(
    "/documents/{document_id}/extract-facts",
    response_model=ExtractionResultResponse,
    summary="Extract structured facts from document passages",
    tags=["Intelligence"],
)
async def extract_facts(
    document_id: str,
    payload: ExtractFactsRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> ExtractionResultResponse:
    """
    Extract structured, typed facts from document passages or from indexed elements.
    Guarantees exact evidence span grounding and provenance persistence.
    """
    svc = get_intelligence_service(request)
    custom_schema_obj = (
        ExtractionSchema.from_dict(payload.custom_schema)
        if payload.custom_schema
        else None
    )

    if payload.passages:
        passages_data = [p.dict() for p in payload.passages]
        res = svc.extract_and_persist(
            tenant_id=tenant.tenant_id,
            document_id=document_id,
            passages=passages_data,
            schema_name=payload.schema_name,
            custom_schema=custom_schema_obj,
            subject=payload.subject,
        )
    else:
        orchestrator = getattr(request.app.state, "orchestrator", None)
        container = getattr(request.app.state, "container", None)
        if orchestrator is None and container is not None:
            orchestrator = getattr(container, "rag_engine", None)

        res = svc.extract_from_orchestrator(
            tenant_id=tenant.tenant_id,
            document_id=document_id,
            orchestrator=orchestrator,
            schema_name=payload.schema_name,
            custom_schema=custom_schema_obj,
            subject=payload.subject,
        )

    return ExtractionResultResponse(**res.to_dict())


@router.get(
    "/documents/{document_id}/facts",
    response_model=List[FactModel],
    summary="Retrieve extracted structured facts for a document",
    tags=["Intelligence"],
)
async def get_document_facts(
    document_id: str,
    request: Request,
    attribute: Optional[str] = Query(None, description="Optional attribute filter"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[FactModel]:
    """Retrieve persisted facts for an authorized document within the tenant boundary."""
    svc = get_intelligence_service(request)
    facts = svc.get_document_facts(
        tenant_id=tenant.tenant_id,
        document_id=document_id,
        attribute=attribute,
    )
    return [FactModel(**f.to_dict()) for f in facts]


@router.post(
    "/intelligence/compare",
    response_model=DocumentComparisonResponse,
    summary="Compare structured facts between two documents",
    tags=["Intelligence"],
)
async def compare_documents(
    payload: CompareDocumentsRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DocumentComparisonResponse:
    """
    Compare structured facts across two documents belonging to the authenticated tenant.
    Enforces tenant boundaries, unit compatibility, and temporal scope alignment.
    """
    svc = get_intelligence_service(request)
    try:
        res = svc.compare_documents(
            tenant_id=tenant.tenant_id,
            left_doc_id=payload.left_document_id,
            right_doc_id=payload.right_document_id,
            attributes=payload.attributes,
        )
        return DocumentComparisonResponse(**res.to_dict())
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(exc),
        )


@router.get(
    "/intelligence/conflicts",
    response_model=List[ConflictReportModel],
    summary="Detect conflicting facts across documents",
    tags=["Intelligence"],
)
async def get_conflicts(
    request: Request,
    document_ids: Optional[List[str]] = Query(None, description="Filter by document IDs"),
    subject: Optional[str] = Query(None, description="Filter by subject entity"),
    tenant: TenantContext = Depends(get_current_tenant),
) -> List[ConflictReportModel]:
    """
    Scan authorized documents for conflicting quantities, dates, and obligations.
    Preserves all conflicting sources without silently choosing one.
    """
    svc = get_intelligence_service(request)
    conflicts = svc.detect_conflicts(
        tenant_id=tenant.tenant_id,
        document_ids=document_ids,
        subject=subject,
    )
    return [ConflictReportModel(**c.to_dict()) for c in conflicts]
