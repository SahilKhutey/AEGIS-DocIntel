"""
Tenant Router
================

Request routing by tenant (for multi-region / sharding).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .tenant_manager import Tenant, TenantManager


class RoutingStrategy(Enum):
    """Tenant routing strategies."""

    REGION = "region"
    LATENCY = "latency"
    LOAD = "load"
    COST = "cost"
    STICKY = "sticky"


@dataclass
class RoutingDecision:
    """A routing decision for a tenant."""

    tenant_id: str
    target_region: str
    target_endpoint: str
    strategy: RoutingStrategy
    reason: str


@dataclass
class RegionEndpoint:
    """A regional endpoint for routing."""

    region: str
    endpoint: str
    latency_ms: float = 0.0
    load: float = 0.0
    cost_factor: float = 1.0
    is_healthy: bool = True


class TenantRouter:
    """
    Routes tenant requests to appropriate backend endpoints.
    """

    def __init__(self, strategy: RoutingStrategy = RoutingStrategy.REGION) -> None:
        self.strategy = strategy
        self.endpoints: Dict[str, RegionEndpoint] = {}
        self._tenant_routing: Dict[str, str] = {}  # sticky routing cache

    def register_endpoint(self, endpoint: RegionEndpoint) -> None:
        self.endpoints[endpoint.region] = endpoint

    def route(self, tenant: Tenant) -> RoutingDecision:
        """Determine where to route a tenant's request."""
        if self.strategy == RoutingStrategy.STICKY:
            # check sticky cache
            if tenant.tenant_id in self._tenant_routing:
                region = self._tenant_routing[tenant.tenant_id]
                if region in self.endpoints and self.endpoints[region].is_healthy:
                    ep = self.endpoints[region]
                    return RoutingDecision(
                        tenant_id=tenant.tenant_id,
                        target_region=region,
                        target_endpoint=ep.endpoint,
                        strategy=self.strategy,
                        reason="sticky_cache",
                    )
        if self.strategy == RoutingStrategy.REGION:
            region = tenant.region
        elif self.strategy == RoutingStrategy.LATENCY:
            region = self._select_by_latency()
        elif self.strategy == RoutingStrategy.LOAD:
            region = self._select_by_load()
        elif self.strategy == RoutingStrategy.COST:
            region = self._select_by_cost()
        else:
            region = tenant.region
        # fall back to tenant region if not available
        if region not in self.endpoints:
            region = tenant.region
        if region not in self.endpoints and self.endpoints:
            region = next(iter(self.endpoints))
        ep = self.endpoints.get(region)
        if ep is None:
            raise RuntimeError("No endpoints registered")
        # cache for sticky routing
        if self.strategy == RoutingStrategy.STICKY:
            self._tenant_routing[tenant.tenant_id] = region
        return RoutingDecision(
            tenant_id=tenant.tenant_id,
            target_region=region,
            target_endpoint=ep.endpoint,
            strategy=self.strategy,
            reason=f"{self.strategy.value}_selection",
        )

    def _select_by_latency(self) -> str:
        candidates = [ep for ep in self.endpoints.values() if ep.is_healthy]
        if not candidates:
            return "us-east-1"
        return min(
            candidates,
            key=lambda ep: ep.latency_ms,
        ).region

    def _select_by_load(self) -> str:
        candidates = [ep for ep in self.endpoints.values() if ep.is_healthy]
        if not candidates:
            return "us-east-1"
        return min(candidates, key=lambda ep: ep.load).region

    def _select_by_cost(self) -> str:
        candidates = [ep for ep in self.endpoints.values() if ep.is_healthy]
        if not candidates:
            return "us-east-1"
        return min(candidates, key=lambda ep: ep.cost_factor).region

    def update_health(self, region: str, is_healthy: bool) -> None:
        if region in self.endpoints:
            self.endpoints[region].is_healthy = is_healthy

    def update_load(self, region: str, load: float) -> None:
        if region in self.endpoints:
            self.endpoints[region].load = load

    def update_latency(self, region: str, latency_ms: float) -> None:
        if region in self.endpoints:
            self.endpoints[region].latency_ms = latency_ms
