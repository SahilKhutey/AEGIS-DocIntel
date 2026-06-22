"""
Tenant Admin
==============

Admin endpoints for tenant management.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from .tenant_billing import TenantBilling, UsageMetric
from .tenant_manager import Tenant, TenantManager, TenantPlan, TenantStatus

router = APIRouter(prefix="/v1/admin/tenants", tags=["Tenant Admin"])

# Global fallback instances if not mounted on app.state
_global_manager = TenantManager()
_global_billing = TenantBilling()


def get_tenant_manager(request: Request) -> TenantManager:
    """Dependency to retrieve TenantManager from app state or fallback."""
    if hasattr(request.app, "state") and hasattr(request.app.state, "tenant_manager"):
        return request.app.state.tenant_manager
    return _global_manager


def get_tenant_billing(request: Request) -> TenantBilling:
    """Dependency to retrieve TenantBilling from app state or fallback."""
    if hasattr(request.app, "state") and hasattr(request.app.state, "tenant_billing"):
        return request.app.state.tenant_billing
    return _global_billing


# --- Pydantic Schemas ---

class TenantCreate(BaseModel):
    name: str
    plan: str = "free"
    billing_email: str = ""
    contact_name: str = ""
    region: str = "us-east-1"
    config: Dict[str, Any] = Field(default_factory=dict)


class TenantUpdate(BaseModel):
    name: Optional[str] = None
    billing_email: Optional[str] = None
    contact_name: Optional[str] = None
    region: Optional[str] = None
    config: Optional[Dict[str, Any]] = None


class PlanUpgrade(BaseModel):
    plan: str


class SuspendReason(BaseModel):
    reason: str = ""


class UsageRecordCreate(BaseModel):
    metric: str
    quantity: float = 1.0
    metadata: Dict[str, Any] = Field(default_factory=dict)


# --- Endpoints ---

@router.post("", response_model=Dict[str, Any], status_code=201)
async def create_tenant(
    payload: TenantCreate,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Create a new tenant."""
    try:
        plan_enum = TenantPlan(payload.plan.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")

    try:
        tenant = manager.create_tenant(
            name=payload.name,
            plan=plan_enum,
            billing_email=payload.billing_email,
            contact_name=payload.contact_name,
            region=payload.region,
            config=payload.config,
        )
        return tenant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[Dict[str, Any]])
async def list_tenants(
    status: Optional[str] = None,
    plan: Optional[str] = None,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """List all tenants, optionally filtered."""
    status_enum = None
    if status:
        try:
            status_enum = TenantStatus(status.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status filter: {status}")

    plan_enum = None
    if plan:
        try:
            plan_enum = TenantPlan(plan.lower())
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid plan filter: {plan}")

    tenants = manager.list_tenants(status=status_enum, plan=plan_enum)
    return [t.to_dict() for t in tenants]


@router.get("/{tenant_id}", response_model=Dict[str, Any])
async def get_tenant(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Get a tenant by ID."""
    tenant = manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return tenant.to_dict()


@router.patch("/{tenant_id}", response_model=Dict[str, Any])
async def update_tenant(
    tenant_id: str,
    payload: TenantUpdate,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Update a tenant's fields."""
    updates = {k: v for k, v in payload.model_dump().items() if v is not None}
    try:
        tenant = manager.update_tenant(tenant_id, **updates)
        return tenant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.delete("/{tenant_id}", response_model=Dict[str, bool])
async def delete_tenant(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Delete a tenant."""
    success = manager.delete_tenant(tenant_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")
    return {"deleted": success}


@router.post("/{tenant_id}/upgrade", response_model=Dict[str, Any])
async def upgrade_tenant_plan(
    tenant_id: str,
    payload: PlanUpgrade,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Upgrade or downgrade tenant plan."""
    try:
        plan_enum = TenantPlan(payload.plan.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid plan: {payload.plan}")

    try:
        tenant = manager.upgrade_plan(tenant_id, plan_enum)
        return tenant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{tenant_id}/suspend", response_model=Dict[str, Any])
async def suspend_tenant(
    tenant_id: str,
    payload: SuspendReason,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Suspend a tenant."""
    try:
        tenant = manager.suspend_tenant(tenant_id, reason=payload.reason)
        return tenant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{tenant_id}/reactivate", response_model=Dict[str, Any])
async def reactivate_tenant(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Reactivate a suspended tenant."""
    try:
        tenant = manager.reactivate_tenant(tenant_id)
        return tenant.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{tenant_id}/rotate-api-key", response_model=Dict[str, Any])
async def rotate_tenant_api_key(
    tenant_id: str,
    manager: TenantManager = Depends(get_tenant_manager),
):
    """Rotate the tenant API key."""
    try:
        tenant = manager.rotate_api_key(tenant_id)
        # Expose the API key in the response only during rotation/creation
        result = tenant.to_dict()
        result["api_key"] = tenant.api_key
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# --- Billing Endpoints ---

@router.post("/{tenant_id}/usage", response_model=Dict[str, Any])
async def record_tenant_usage(
    tenant_id: str,
    payload: UsageRecordCreate,
    manager: TenantManager = Depends(get_tenant_manager),
    billing: TenantBilling = Depends(get_tenant_billing),
):
    """Record usage of a specific metric for a tenant."""
    tenant = manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")

    try:
        metric_enum = UsageMetric(payload.metric.lower())
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid metric: {payload.metric}")

    record = billing.record(
        tenant_id=tenant_id,
        metric=metric_enum,
        quantity=payload.quantity,
        metadata=payload.metadata,
    )
    return {
        "tenant_id": record.tenant_id,
        "metric": record.metric.value,
        "quantity": record.quantity,
        "unit_cost": record.unit_cost,
        "cost": record.cost,
        "timestamp": record.timestamp,
    }


@router.get("/{tenant_id}/usage", response_model=Dict[str, Any])
async def get_tenant_usage(
    tenant_id: str,
    period_start: Optional[float] = None,
    period_end: Optional[float] = None,
    manager: TenantManager = Depends(get_tenant_manager),
    billing: TenantBilling = Depends(get_tenant_billing),
):
    """Get usage summary for a billing period."""
    tenant = manager.get_tenant(tenant_id)
    if not tenant:
        raise HTTPException(status_code=404, detail=f"Tenant {tenant_id} not found")

    summary = billing.get_usage(tenant_id, period_start=period_start, period_end=period_end)
    current_period = billing.get_current_period_usage(tenant_id)
    return {
        "tenant_id": tenant_id,
        "period_summary": summary,
        "current_period_aggregates": current_period,
    }


@router.post("/{tenant_id}/invoices", response_model=Dict[str, Any])
async def generate_tenant_invoice(
    tenant_id: str,
    period_start: Optional[float] = None,
    period_end: Optional[float] = None,
    manager: TenantManager = Depends(get_tenant_manager),
    billing: TenantBilling = Depends(get_tenant_billing),
):
    """Generate invoice for a tenant."""
    try:
        invoice = billing.generate_invoice(
            tenant_id=tenant_id,
            tenant_manager=manager,
            period_start=period_start,
            period_end=period_end,
        )
        return invoice.to_dict()
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("/{tenant_id}/invoices", response_model=List[Dict[str, Any]])
async def list_tenant_invoices(
    tenant_id: str,
    status: Optional[str] = None,
    billing: TenantBilling = Depends(get_tenant_billing),
):
    """List all invoices generated for a tenant."""
    invoices = billing.get_invoices(tenant_id=tenant_id, status=status)
    return [i.to_dict() for i in invoices]
