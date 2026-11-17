"""
AEGIS-DocIntel — Demo API Router
==================================
Endpoints for demo session discovery, guided tour status, and repeatable workspace reset.
"""
from __future__ import annotations

import os
from typing import Any, Dict, List, Optional
import structlog
from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field

from src.api.auth import TenantContext, get_current_tenant

router = APIRouter(tags=["Demo"])
log = structlog.get_logger("aegis.api.demo")


class DemoGuidedStep(BaseModel):
    step: int
    title: str
    description: str
    target_route: str


class DemoSessionResponse(BaseModel):
    demo_mode: bool
    tenant_id: str
    principal_id: str
    token: str
    roles: List[str]
    monthly_token_limit: int
    system_version: str = "1.2.0-launch"
    sample_documents: List[Dict[str, Any]] = Field(default_factory=list)
    guided_workflow: List[DemoGuidedStep] = Field(default_factory=list)


class DemoResetResponse(BaseModel):
    status: str
    tenant_id: str
    message: str
    documents_restored: int


@router.get(
    "/demo/session",
    response_model=DemoSessionResponse,
    summary="Get demo session metadata and guided tour configuration",
)
async def get_demo_session(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DemoSessionResponse:
    """Retrieve demo session context, active tenant bounds, and guided walkthrough steps."""
    demo_mode = os.environ.get("AEGIS_DEMO_MODE", "false").lower() in ("true", "1", "yes")
    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    is_demo = demo_mode or env == "demo"
    demo_token = os.environ.get("AEGIS_DEMO_TOKEN", "aegis-demo-token-sandbox")

    # Fetch pre-seeded documents for demo-tenant if container is initialized
    sample_docs: List[Dict[str, Any]] = []
    container = getattr(request.app.state, "container", None)
    if container and hasattr(container, "document_service") and container.document_service:
        try:
            docs_res = await container.document_service.list_documents(tenant_id=tenant.tenant_id)
            items = getattr(docs_res, "items", docs_res if isinstance(docs_res, list) else [])
            sample_docs = [
                {
                    "doc_id": d.get("doc_id") if isinstance(d, dict) else getattr(d, "doc_id", None),
                    "filename": d.get("filename") if isinstance(d, dict) else getattr(d, "filename", None),
                    "status": d.get("status") if isinstance(d, dict) else getattr(d, "status", None),
                    "page_count": d.get("page_count", 1) if isinstance(d, dict) else getattr(d, "page_count", 1),
                }
                for d in items
            ]
        except Exception as exc:
            log.warning("Could not list demo documents for session response", error=str(exc))

    guided_steps = [
        DemoGuidedStep(
            step=1,
            title="Explore Sample Documents",
            description="Examine extracted structures, tables, and bounding boxes for technical documents.",
            target_route="/documents",
        ),
        DemoGuidedStep(
            step=2,
            title="Ask AEGIS & Verify Citations",
            description="Ask questions grounded in document evidence with submodular context compression.",
            target_route="/ask",
        ),
        DemoGuidedStep(
            step=3,
            title="Cross-Document Contradiction Analysis",
            description="Compare v1.0 and v2.0 hardware specs to pinpoint exact conflicting engineering claims.",
            target_route="/compare",
        ),
        DemoGuidedStep(
            step=4,
            title="Mathematical Representations & Audit",
            description="Inspect spatial reading DAGs, topological manifold invariants, and SHA-256 audit logs.",
            target_route="/mathematics",
        ),
    ]

    return DemoSessionResponse(
        demo_mode=is_demo,
        tenant_id=tenant.tenant_id,
        principal_id=tenant.principal_id,
        token=demo_token if is_demo else "",
        roles=sorted(list(tenant.roles)),
        monthly_token_limit=tenant.monthly_token_limit,
        system_version="1.2.0-launch",
        sample_documents=sample_docs,
        guided_workflow=guided_steps,
    )


@router.post(
    "/demo/reset",
    response_model=DemoResetResponse,
    summary="Reset demo tenant workspace to initial seeded state",
)
async def reset_demo_workspace(
    request: Request,
    tenant: TenantContext = Depends(get_current_tenant),
) -> DemoResetResponse:
    """
    Restore demo tenant documents to the default pristine seed state.
    Allowed only in demo mode and strictly scoped to demo-tenant.
    """
    demo_mode = os.environ.get("AEGIS_DEMO_MODE", "false").lower() in ("true", "1", "yes")
    env = os.environ.get("AEGIS_ENVIRONMENT", "production").lower()
    if not (demo_mode or env == "demo"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Reset operation is only available when AEGIS_DEMO_MODE is enabled.",
        )

    if tenant.tenant_id != "demo-tenant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset operation is strictly restricted to 'demo-tenant'.",
        )

    container = getattr(request.app.state, "container", None)
    if not container:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Service container not initialized.",
        )

    try:
        # Import reset script logic
        from demo.scripts.reset_demo import execute_demo_reset
        count = await execute_demo_reset(container)
        return DemoResetResponse(
            status="success",
            tenant_id="demo-tenant",
            message="Demo workspace successfully restored to clean seed state.",
            documents_restored=count,
        )
    except Exception as exc:
        log.exception("Demo reset failed", error=str(exc))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Demo reset failed: {exc}",
        )
