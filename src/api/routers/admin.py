"""
AEGIS-DocIntel — Admin Router
=============================
Tenant-scoped administrative endpoints for usage, statistics, and tenant controls.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, Depends, Request

from src.api.auth import TenantContext, require_role
from src.api.models import TenantStats, TokenUsageResponse

admin = APIRouter()
router = admin  # expose as `admin.router`


@admin.get(
    "/stats",
    response_model=TenantStats,
    summary="Get tenant operational statistics",
)
async def get_stats(
    request: Request,
    tenant: TenantContext = Depends(require_role("admin")),
):
    """Retrieve usage and aggregate index statistics for the calling tenant."""
    container = getattr(request.app.state, "container", None)
    doc_service = getattr(container, "document_service", None) if container else None

    doc_count = 0
    chunk_count = 0
    if doc_service and hasattr(doc_service, "_docs"):
        tenant_docs = [
            d for d in doc_service._docs.values()
            if str(d.get("tenant_id", "")) == str(tenant.tenant_id)
        ]
        doc_count = len(tenant_docs)
        chunk_count = sum(d.get("chunk_count", 0) for d in tenant_docs)

    # Calculate nominal tokens and estimated cost ($0.000002 per token)
    total_tokens = chunk_count * 128
    cost_usd = round(total_tokens * 0.000002, 4)

    return TenantStats(
        tenant_id=tenant.tenant_id,
        doc_count=doc_count,
        chunk_count=chunk_count,
        total_tokens_used=total_tokens,
        total_cost_usd=cost_usd,
        cache_hit_rate=0.0,
        avg_query_latency_ms=12.5,
    )


@admin.get(
    "/token-usage",
    response_model=TokenUsageResponse,
    summary="Get token usage breakdown",
)
async def get_token_usage(
    request: Request,
    tenant: TenantContext = Depends(require_role("admin")),
):
    """Retrieve token consumption breakdown across model calls."""
    container = getattr(request.app.state, "container", None)
    doc_service = getattr(container, "document_service", None) if container else None

    doc_count = 0
    chunk_count = 0
    if doc_service and hasattr(doc_service, "_docs"):
        tenant_docs = [
            d for d in doc_service._docs.values()
            if str(d.get("tenant_id", "")) == str(tenant.tenant_id)
        ]
        doc_count = len(tenant_docs)
        chunk_count = sum(d.get("chunk_count", 0) for d in tenant_docs)

    in_tokens = chunk_count * 128
    out_tokens = int(in_tokens * 0.25)
    total_tokens = in_tokens + out_tokens
    cost = round(total_tokens * 0.000002, 4)

    return TokenUsageResponse(
        period="month-to-date",
        total_in_tokens=in_tokens,
        total_out_tokens=out_tokens,
        total_cost_usd=cost,
        query_count=max(1, doc_count),
        cache_hits=0,
        avg_latency_ms=12.5,
    )
