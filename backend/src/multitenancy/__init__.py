"""
AMDI-OS Multi-Tenancy Support
================================

Per-tenant isolation, configuration, billing, and admin.

Features:
    - Tenant CRUD
    - Per-request tenant context
    - Usage tracking
    - Quota enforcement
    - Billing integration

Author : AMDI-OS Development Team
Version: 1.3.0
"""

from .tenant_manager import TenantManager, Tenant, TenantStatus, TenantPlan
from .tenant_context import TenantContext, set_current_tenant, get_current_tenant
from .tenant_router import TenantRouter
from .tenant_billing import TenantBilling, UsageRecord, Invoice

__all__ = [
    "TenantManager",
    "Tenant",
    "TenantStatus",
    "TenantPlan",
    "TenantContext",
    "set_current_tenant",
    "get_current_tenant",
    "TenantRouter",
    "TenantBilling",
    "UsageRecord",
    "Invoice",
]

__version__ = "1.3.0"
