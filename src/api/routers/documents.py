"""
AEGIS-DocIntel — Documents API Router
======================================
Endpoints for document upload, status, listing, and deletion.
"""
from __future__ import annotations

import hashlib
import uuid
from typing import Annotated, Optional

import structlog
from fastapi import (
    APIRouter, BackgroundTasks, Depends, File, Form,
    HTTPException, Query, Request, UploadFile, status
)

from src.api.auth import TenantContext, get_current_tenant
from src.api.models import (
    BatchUploadRequest, BatchUploadResponse,
    ChunkListResponse, DocumentListResponse,
    DocumentResponse, DocumentStatus, IngestionStatusResponse,
)

router = APIRouter()
log = structlog.get_logger("aegis.api.documents")

ALLOWED_MIMETYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    "text/html",
    "text/plain",
}
MAX_UPLOAD_BYTES = 200 * 1024 * 1024  # 200 MB


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Upload a document for indexing",
)
async def upload_document(
    request: Request,
    file: UploadFile = File(..., description="PDF, DOCX, PPTX, or HTML file"),
    tenant: TenantContext = Depends(get_current_tenant),
):
    """
    Upload a document for ingestion and indexing.
    Returns immediately with doc_id and status=pending.
    Use GET /documents/{doc_id} to poll indexing status.
    """
    # Validate content type
    if file.content_type not in ALLOWED_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail=f"Unsupported file type: {file.content_type}. Allowed: {ALLOWED_MIMETYPES}",
        )

    # Read file bytes
    file_bytes = await file.read()
    if len(file_bytes) > MAX_UPLOAD_BYTES:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size {len(file_bytes) / 1024 / 1024:.1f}MB exceeds limit of 200MB",
        )
    if len(file_bytes) == 0:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Empty file")

    container = request.app.state.container
    doc_service = container.document_service

    try:
        doc = await doc_service.ingest(
            file_bytes=file_bytes,
            filename=file.filename or "upload.pdf",
            content_type=file.content_type,
            tenant_id=tenant.tenant_id,
        )
        log.info("Document queued", doc_id=str(doc.doc_id), filename=file.filename, tenant=tenant.tenant_id)
        return doc
    except Exception as e:
        log.error("Upload failed", error=str(e), tenant=tenant.tenant_id)
        raise HTTPException(status_code=500, detail=f"Upload failed: {e}")


@router.get(
    "/{doc_id}",
    response_model=DocumentResponse,
    summary="Get document status",
)
async def get_document(
    doc_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Get document metadata and indexing status."""
    container = request.app.state.container
    doc = await container.document_service.get(doc_id=str(doc_id), tenant_id=tenant.tenant_id)
    if not doc:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return doc


@router.get(
    "/{doc_id}/status",
    response_model=IngestionStatusResponse,
    summary="Get detailed indexing progress",
)
async def get_indexing_status(
    doc_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Get detailed indexing pipeline progress."""
    container = request.app.state.container
    status_info = await container.document_service.get_status(
        doc_id=str(doc_id), tenant_id=tenant.tenant_id
    )
    if not status_info:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return status_info


@router.get(
    "",
    response_model=DocumentListResponse,
    summary="List all documents",
)
async def list_documents(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: Optional[DocumentStatus] = Query(default=None, alias="status"),
):
    """List all documents for the tenant with optional status filter."""
    container = request.app.state.container
    result = await container.document_service.list_documents(
        tenant_id=tenant.tenant_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )
    return result


@router.delete(
    "/{doc_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    doc_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Delete a document and all its associated chunks, vectors, and cache entries."""
    container = request.app.state.container
    deleted = await container.document_service.delete(
        doc_id=str(doc_id), tenant_id=tenant.tenant_id
    )
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")


@router.post(
    "/{doc_id}/reindex",
    response_model=IngestionStatusResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger document re-indexing",
)
async def reindex_document(
    doc_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Force re-indexing of a document. Invalidates all caches."""
    container = request.app.state.container
    result = await container.document_service.reindex(
        doc_id=str(doc_id), tenant_id=tenant.tenant_id
    )
    if not result:
        raise HTTPException(status_code=404, detail=f"Document {doc_id} not found")
    return result


@router.get(
    "/{doc_id}/chunks",
    response_model=ChunkListResponse,
    summary="List document chunks",
)
async def list_chunks(
    doc_id: uuid.UUID,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=200),
):
    """List all chunks for a document (for debugging and inspection)."""
    container = request.app.state.container
    result = await container.document_service.list_chunks(
        doc_id=str(doc_id), tenant_id=tenant.tenant_id, page=page, page_size=page_size
    )
    return result


@router.post(
    "/batch",
    response_model=BatchUploadResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Batch upload from S3 manifest",
)
async def batch_upload(
    body: BatchUploadRequest,
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
):
    """Queue a batch of S3 documents for indexing."""
    container = request.app.state.container
    job = await container.document_service.batch_ingest(
        documents=body.documents, tenant_id=tenant.tenant_id
    )
    return job
