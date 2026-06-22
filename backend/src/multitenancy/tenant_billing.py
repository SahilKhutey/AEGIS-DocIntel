"""
Tenant Billing
================

Usage tracking and invoice generation.
"""

from __future__ import annotations

import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .tenant_manager import Tenant, TenantPlan, TenantManager


class UsageMetric(Enum):
    """Trackable usage metrics."""

    DOCUMENTS_PROCESSED = "documents_processed"
    QUERIES = "queries"
    TOKENS_INPUT = "tokens_input"
    TOKENS_OUTPUT = "tokens_output"
    STORAGE_GB_HOURS = "storage_gb_hours"
    AGENT_CALLS = "agent_calls"
    ENGINE_CALLS = "engine_calls"


@dataclass
class UsageRecord:
    """A single usage record."""

    tenant_id: str
    metric: UsageMetric
    quantity: float
    unit_cost: float
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def cost(self) -> float:
        return self.quantity * self.unit_cost


@dataclass
class Invoice:
    """A monthly invoice."""

    invoice_id: str
    tenant_id: str
    period_start: float
    period_end: float
    line_items: List[Dict[str, Any]] = field(default_factory=list)
    subtotal: float = 0.0
    tax: float = 0.0
    total: float = 0.0
    status: str = "pending"
    created_at: float = field(default_factory=time.time)
    paid_at: Optional[float] = None

    def to_dict(self) -> dict:
        return {
            "invoice_id": self.invoice_id,
            "tenant_id": self.tenant_id,
            "period_start": self.period_start,
            "period_end": self.period_end,
            "line_items": self.line_items,
            "subtotal": round(self.subtotal, 2),
            "tax": round(self.tax, 2),
            "total": round(self.total, 2),
            "status": self.status,
            "created_at": self.created_at,
            "paid_at": self.paid_at,
        }


class TenantBilling:
    """
    Track tenant usage and generate invoices.
    """

    UNIT_COSTS = {
        UsageMetric.DOCUMENTS_PROCESSED: 0.01,
        UsageMetric.QUERIES: 0.001,
        UsageMetric.TOKENS_INPUT: 0.000_005,
        UsageMetric.TOKENS_OUTPUT: 0.000_015,
        UsageMetric.STORAGE_GB_HOURS: 0.001,
        UsageMetric.AGENT_CALLS: 0.005,
        UsageMetric.ENGINE_CALLS: 0.0001,
    }

    TAX_RATE = 0.08  # 8% tax

    def __init__(self) -> None:
        self.usage_records: List[UsageRecord] = []
        self.invoices: List[Invoice] = []
        # current period usage by tenant
        self._current_period_start = self._period_start(time.time())
        self._period_usage: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(float)
        )

    def record(
        self,
        tenant_id: str,
        metric: UsageMetric,
        quantity: float = 1.0,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> UsageRecord:
        """Record usage for a tenant."""
        unit_cost = self.UNIT_COSTS.get(metric, 0.0)
        record = UsageRecord(
            tenant_id=tenant_id,
            metric=metric,
            quantity=quantity,
            unit_cost=unit_cost,
            timestamp=time.time(),
            metadata=metadata or {},
        )
        self.usage_records.append(record)
        self._period_usage[tenant_id][metric.value] += quantity
        return record

    def get_usage(
        self,
        tenant_id: str,
        period_start: Optional[float] = None,
        period_end: Optional[float] = None,
    ) -> Dict[str, float]:
        """Get usage summary for a tenant in a period."""
        period_start = period_start or self._current_period_start
        period_end = period_end or time.time()
        usage: Dict[str, float] = defaultdict(float)
        for record in self.usage_records:
            if record.tenant_id != tenant_id:
                continue
            if not (period_start <= record.timestamp <= period_end):
                continue
            usage[record.metric.value] += record.quantity
        return dict(usage)

    def get_current_period_usage(self, tenant_id: str) -> Dict[str, float]:
        """Get current billing period usage."""
        usage = self._period_usage.get(tenant_id, {})
        return dict(usage)

    def generate_invoice(
        self,
        tenant_id: str,
        tenant_manager: TenantManager,
        period_start: Optional[float] = None,
        period_end: Optional[float] = None,
        tax_rate: Optional[float] = None,
    ) -> Invoice:
        """Generate invoice for a billing period."""
        tenant = tenant_manager.get_tenant(tenant_id)
        if tenant is None:
            raise ValueError(f"Tenant {tenant_id} not found")
        period_start = period_start or self._current_period_start
        period_end = period_end or time.time()
        usage = self.get_usage(tenant_id, period_start, period_end)
        # build line items
        line_items: List[Dict[str, Any]] = []
        subtotal = 0.0
        for metric_name, quantity in usage.items():
            unit_cost = self.UNIT_COSTS.get(UsageMetric(metric_name), 0.0)
            cost = quantity * unit_cost
            line_items.append({
                "metric": metric_name,
                "quantity": quantity,
                "unit_cost": unit_cost,
                "total": round(cost, 4),
            })
            subtotal += cost
        # add base subscription
        base_prices = {
            TenantPlan.FREE: 0.0,
            TenantPlan.STARTER: 49.0,
            TenantPlan.PROFESSIONAL: 199.0,
            TenantPlan.ENTERPRISE: 999.0,
            TenantPlan.CUSTOM: 0.0,
        }
        base_price = base_prices.get(tenant.plan, 0.0)
        if base_price > 0:
            line_items.insert(0, {
                "metric": "base_subscription",
                "plan": tenant.plan.value,
                "total": base_price,
            })
            subtotal += base_price
        tax = subtotal * (tax_rate or self.TAX_RATE)
        total = subtotal + tax
        invoice = Invoice(
            invoice_id=f"inv_{uuid.uuid4().hex[:16]}",
            tenant_id=tenant_id,
            period_start=period_start,
            period_end=period_end,
            line_items=line_items,
            subtotal=round(subtotal, 2),
            tax=round(tax, 2),
            total=round(total, 2),
        )
        self.invoices.append(invoice)
        return invoice

    def get_invoices(
        self,
        tenant_id: Optional[str] = None,
        status: Optional[str] = None,
    ) -> List[Invoice]:
        """Get invoices, optionally filtered."""
        invoices = self.invoices
        if tenant_id:
            invoices = [i for i in invoices if i.tenant_id == tenant_id]
        if status:
            invoices = [i for i in invoices if i.status == status]
        return invoices

    def mark_paid(self, invoice_id: str) -> Invoice:
        for inv in self.invoices:
            if inv.invoice_id == invoice_id:
                inv.status = "paid"
                inv.paid_at = time.time()
                return inv
        raise ValueError(f"Invoice {invoice_id} not found")

    def _period_start(self, now: float) -> float:
        """Get start of current billing period (1st of month UTC)."""
        import datetime as dt
        # Use timezone-aware UTC datetime to prevent deprecation warning
        d = dt.datetime.fromtimestamp(now, dt.timezone.utc)
        return int(dt.datetime(d.year, d.month, 1, tzinfo=dt.timezone.utc).timestamp())
