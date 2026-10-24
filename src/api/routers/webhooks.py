"""AEGIS-DocIntel — Webhook Router"""
from __future__ import annotations

import os
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.api.auth import TenantContext, get_current_tenant
from src.core.security_context import ROLE_TENANT_ADMIN, ROLE_PLATFORM_ADMIN, LEGACY_ADMIN
from src.core.webhook_security import is_safe_webhook_url
from backend.src.webhooks.webhook_manager import WebhookManager

router = APIRouter()
_manager = WebhookManager()


class WebhookCreate(BaseModel):
    url: str
    secret_token: str
    topic_pattern: str = "document.*"


def _check_webhook_admin(tenant: TenantContext) -> None:
    """Enforce that only tenant administrators can manage webhook endpoints."""
    if not tenant.has_role(ROLE_TENANT_ADMIN, ROLE_PLATFORM_ADMIN, LEGACY_ADMIN):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Forbidden: Webhook configuration requires tenant_admin role.",
        )


@router.post("/subscriptions", status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: WebhookCreate,
    tenant: TenantContext = Depends(get_current_tenant),
):
    _check_webhook_admin(tenant)

    # Validate destination URL against SSRF and private address vulnerabilities
    allow_private = os.getenv("AEGIS_ALLOW_PRIVATE_WEBHOOKS", "false").lower() in ("true", "1")
    is_safe, reason = is_safe_webhook_url(body.url, allow_private_for_tests=allow_private)
    if not is_safe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Insecure webhook destination: {reason}",
        )

    sub = _manager.create_subscription(
        tenant_id=tenant.tenant_id,
        url=body.url,
        secret_token=body.secret_token,
        topic_pattern=body.topic_pattern,
    )
    return {
        "subscription_id": sub.subscription_id,
        "tenant_id": sub.tenant_id,
        "url": sub.url,
        "topic_pattern": sub.topic_pattern,
        "is_active": sub.is_active,
    }


@router.get("/subscriptions")
async def list_subscriptions(
    tenant: TenantContext = Depends(get_current_tenant),
):
    _check_webhook_admin(tenant)
    subs = _manager.list_subscriptions(tenant.tenant_id)
    return [
        {
            "subscription_id": s.subscription_id,
            "tenant_id": s.tenant_id,
            "url": s.url,
            "topic_pattern": s.topic_pattern,
            "is_active": s.is_active,
        }
        for s in subs
    ]


@router.delete("/subscriptions/{subscription_id}")
async def delete_subscription(
    subscription_id: str,
    tenant: TenantContext = Depends(get_current_tenant),
):
    _check_webhook_admin(tenant)
    sub = _manager.get_subscription(subscription_id)
    if not sub or str(sub.tenant_id) != str(tenant.tenant_id):
        raise HTTPException(status_code=404, detail="Subscription not found")
    _manager.delete_subscription(subscription_id)
    return {"deleted": True, "subscription_id": subscription_id}


@router.post("/ingest-complete")
async def ingest_complete_webhook():
    return {"received": True}
