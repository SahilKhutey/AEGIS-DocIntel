"""
Tenant Manager
================

CRUD operations for tenants.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional


class TenantStatus(Enum):
    """Tenant lifecycle status."""

    ACTIVE = "active"
    SUSPENDED = "suspended"
    TRIAL = "trial"
    CANCELLED = "cancelled"
    PENDING = "pending"


class TenantPlan(Enum):
    """Subscription plans."""

    FREE = "free"
    STARTER = "starter"
    PROFESSIONAL = "professional"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"


@dataclass
class Tenant:
    """A tenant (organization)."""

    tenant_id: str
    name: str
    plan: TenantPlan
    status: TenantStatus
    created_at: float
    api_key: str = ""
    config: Dict[str, Any] = field(default_factory=dict)
    quotas: Dict[str, int] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    billing_email: str = ""
    contact_name: str = ""
    region: str = "us-east-1"
    trial_ends_at: Optional[float] = None

    # Default quotas per plan
    DEFAULT_QUOTAS = {
        TenantPlan.FREE: {
            "documents_per_month": 100,
            "queries_per_month": 1000,
            "storage_gb": 1,
            "users": 3,
            "agents": 1,
        },
        TenantPlan.STARTER: {
            "documents_per_month": 1000,
            "queries_per_month": 10_000,
            "storage_gb": 10,
            "users": 10,
            "agents": 3,
        },
        TenantPlan.PROFESSIONAL: {
            "documents_per_month": 10_000,
            "queries_per_month": 100_000,
            "storage_gb": 100,
            "users": 50,
            "agents": 6,
        },
        TenantPlan.ENTERPRISE: {
            "documents_per_month": 1_000_000,
            "queries_per_month": 10_000_000,
            "storage_gb": 10_000,
            "users": 1000,
            "agents": 6,
        },
    }

    def to_dict(self) -> dict:
        return {
            "tenant_id": self.tenant_id,
            "name": self.name,
            "plan": self.plan.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "billing_email": self.billing_email,
            "contact_name": self.contact_name,
            "region": self.region,
            "quotas": self.quotas,
            "config": self.config,
        }


class TenantManager:
    """
    Manages tenants and their lifecycle.
    """

    def __init__(self) -> None:
        self.tenants: Dict[str, Tenant] = {}
        self._by_api_key: Dict[str, str] = {}  # api_key → tenant_id
        self._by_name: Dict[str, str] = {}    # name → tenant_id

    def create_tenant(
        self,
        name: str,
        plan: TenantPlan = TenantPlan.FREE,
        billing_email: str = "",
        contact_name: str = "",
        region: str = "us-east-1",
        config: Optional[Dict[str, Any]] = None,
    ) -> Tenant:
        """Create a new tenant."""
        if name in self._by_name:
            raise ValueError(f"Tenant name '{name}' already exists")
        tenant_id = f"tenant_{uuid.uuid4().hex[:16]}"
        api_key = f"amdi_{uuid.uuid4().hex}"
        quotas = dict(Tenant.DEFAULT_QUOTAS.get(plan, {}))
        # set trial end for free plans
        now = time.time()
        trial_ends_at = now + 14 * 86400 if plan == TenantPlan.FREE else None
        tenant = Tenant(
            tenant_id=tenant_id,
            name=name,
            plan=plan,
            status=TenantStatus.PENDING if plan == TenantPlan.CUSTOM else TenantStatus.TRIAL,
            created_at=now,
            api_key=api_key,
            quotas=quotas,
            config=config or {},
            billing_email=billing_email,
            contact_name=contact_name,
            region=region,
            trial_ends_at=trial_ends_at,
        )
        self.tenants[tenant_id] = tenant
        self._by_api_key[api_key] = tenant_id
        self._by_name[name] = tenant_id
        return tenant

    def get_tenant(self, tenant_id: str) -> Optional[Tenant]:
        return self.tenants.get(tenant_id)

    def get_tenant_by_api_key(self, api_key: str) -> Optional[Tenant]:
        tenant_id = self._by_api_key.get(api_key)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None

    def get_tenant_by_name(self, name: str) -> Optional[Tenant]:
        tenant_id = self._by_name.get(name)
        if tenant_id:
            return self.tenants.get(tenant_id)
        return None

    def update_tenant(
        self,
        tenant_id: str,
        **updates,
    ) -> Tenant:
        """Update tenant fields."""
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        for key, value in updates.items():
            if hasattr(tenant, key):
                setattr(tenant, key, value)
        return tenant

    def upgrade_plan(self, tenant_id: str, new_plan: TenantPlan) -> Tenant:
        """Upgrade/downgrade tenant plan."""
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.plan = new_plan
        tenant.quotas = dict(Tenant.DEFAULT_QUOTAS.get(new_plan, {}))
        return tenant

    def suspend_tenant(self, tenant_id: str, reason: str = "") -> Tenant:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = TenantStatus.SUSPENDED
        tenant.metadata["suspend_reason"] = reason
        tenant.metadata["suspended_at"] = time.time()
        return tenant

    def reactivate_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = TenantStatus.ACTIVE
        return tenant

    def cancel_tenant(self, tenant_id: str) -> Tenant:
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        tenant.status = TenantStatus.CANCELLED
        tenant.metadata["cancelled_at"] = time.time()
        return tenant

    def rotate_api_key(self, tenant_id: str) -> Tenant:
        """Rotate tenant API key (invalidates old key)."""
        tenant = self.tenants.get(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        # remove old key mapping
        if tenant.api_key in self._by_api_key:
            del self._by_api_key[tenant.api_key]
        # generate new key
        tenant.api_key = f"amdi_{uuid.uuid4().hex}"
        self._by_api_key[tenant.api_key] = tenant_id
        return tenant

    def list_tenants(
        self,
        status: Optional[TenantStatus] = None,
        plan: Optional[TenantPlan] = None,
    ) -> List[Tenant]:
        """List tenants, optionally filtered."""
        tenants = list(self.tenants.values())
        if status:
            tenants = [t for t in tenants if t.status == status]
        if plan:
            tenants = [t for t in tenants if t.plan == plan]
        return tenants

    def delete_tenant(self, tenant_id: str) -> bool:
        if tenant_id in self.tenants:
            tenant = self.tenants[tenant_id]
            if tenant.api_key in self._by_api_key:
                del self._by_api_key[tenant.api_key]
            if tenant.name in self._by_name:
                del self._by_name[tenant.name]
            del self.tenants[tenant_id]
            return True
        return False
