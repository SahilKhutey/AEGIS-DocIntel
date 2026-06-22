import os
import sys
import time
from pathlib import Path
import asyncio
from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.multitenancy import (
    TenantManager,
    Tenant,
    TenantStatus,
    TenantPlan,
    TenantContext,
    set_current_tenant,
    get_current_tenant,
    TenantRouter,
    TenantBilling,
    UsageRecord,
    Invoice,
)
from backend.src.multitenancy.tenant_router import RoutingStrategy, RegionEndpoint
from backend.src.multitenancy.tenant_billing import UsageMetric
from backend.src.multitenancy.tenant_admin import router as admin_router


def test_tenant_manager():
    manager = TenantManager()

    # 1. Create Tenant
    tenant = manager.create_tenant(
        name="Acme Corp",
        plan=TenantPlan.STARTER,
        billing_email="billing@acme.com",
        contact_name="Alice Smith",
        region="us-west-2",
        config={"db_name": "acme_db"}
    )
    assert tenant.tenant_id.startswith("tenant_")
    assert tenant.name == "Acme Corp"
    assert tenant.plan == TenantPlan.STARTER
    assert tenant.status == TenantStatus.TRIAL
    assert tenant.api_key.startswith("amdi_")
    assert tenant.config == {"db_name": "acme_db"}
    assert tenant.billing_email == "billing@acme.com"
    assert tenant.contact_name == "Alice Smith"
    assert tenant.region == "us-west-2"

    # Try creating with duplicate name
    with pytest.raises(ValueError):
        manager.create_tenant(name="Acme Corp")

    # 2. Get Tenant
    assert manager.get_tenant(tenant.tenant_id) == tenant
    assert manager.get_tenant_by_api_key(tenant.api_key) == tenant
    assert manager.get_tenant_by_name("Acme Corp") == tenant

    # 3. Update Tenant
    updated = manager.update_tenant(tenant.tenant_id, contact_name="Bob Jones")
    assert updated.contact_name == "Bob Jones"

    # 4. Plan Upgrade
    upgraded = manager.upgrade_plan(tenant.tenant_id, TenantPlan.PROFESSIONAL)
    assert upgraded.plan == TenantPlan.PROFESSIONAL
    assert upgraded.quotas["documents_per_month"] == 10_000

    # 5. Suspend & Reactivate
    suspended = manager.suspend_tenant(tenant.tenant_id, reason="Non-payment")
    assert suspended.status == TenantStatus.SUSPENDED
    assert suspended.metadata["suspend_reason"] == "Non-payment"

    reactivated = manager.reactivate_tenant(tenant.tenant_id)
    assert reactivated.status == TenantStatus.ACTIVE

    # 6. Rotate API key
    old_key = tenant.api_key
    rotated = manager.rotate_api_key(tenant.tenant_id)
    assert rotated.api_key != old_key
    assert manager.get_tenant_by_api_key(old_key) is None
    assert manager.get_tenant_by_api_key(rotated.api_key) == tenant

    # 7. List and Delete
    assert len(manager.list_tenants()) == 1
    assert manager.delete_tenant(tenant.tenant_id) is True
    assert len(manager.list_tenants()) == 0


def test_tenant_context_thread_safety():
    # Helper for running in thread
    def run_in_thread(tenant_id, delay):
        with set_current_tenant(tenant_id):
            time.sleep(delay)
            # Verify context holds correct isolated value inside thread
            return get_current_tenant()

    with ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(run_in_thread, "tenant_a", 0.1)
        f2 = executor.submit(run_in_thread, "tenant_b", 0.05)
        
        assert f1.result() == "tenant_a"
        assert f2.result() == "tenant_b"

    # Verify context restored outside threads
    assert get_current_tenant() is None


@pytest.mark.asyncio
async def test_tenant_context_async_safety():
    # Helper for async tasks
    async def run_async_task(tenant_id, delay):
        async with set_current_tenant(tenant_id):
            await asyncio.sleep(delay)
            # Verify context is isolated in async coroutines
            return get_current_tenant()

    res1, res2 = await asyncio.gather(
        run_async_task("tenant_a", 0.1),
        run_async_task("tenant_b", 0.05)
    )
    assert res1 == "tenant_a"
    assert res2 == "tenant_b"


def test_tenant_router():
    manager = TenantManager()
    tenant = manager.create_tenant("Acme Corp", region="us-east-1")

    # Latency selection strategy
    router = TenantRouter(strategy=RoutingStrategy.LATENCY)
    router.register_endpoint(RegionEndpoint(region="us-east-1", endpoint="ep-east", latency_ms=100.0))
    router.register_endpoint(RegionEndpoint(region="us-west-2", endpoint="ep-west", latency_ms=20.0))

    decision = router.route(tenant)
    assert decision.target_region == "us-west-2"  # Lowest latency
    assert decision.target_endpoint == "ep-west"

    # Load selection strategy
    router.strategy = RoutingStrategy.LOAD
    router.update_load("us-east-1", 0.1)
    router.update_load("us-west-2", 0.9)
    decision = router.route(tenant)
    assert decision.target_region == "us-east-1"  # Lowest load

    # Cost selection strategy
    router.strategy = RoutingStrategy.COST
    router.endpoints["us-east-1"].cost_factor = 2.0
    router.endpoints["us-west-2"].cost_factor = 0.5
    decision = router.route(tenant)
    assert decision.target_region == "us-west-2"  # Lowest cost

    # Sticky strategy
    router.strategy = RoutingStrategy.STICKY
    decision1 = router.route(tenant)
    # Target should be us-east-1 (which is tenant's default region since cache is empty)
    assert decision1.target_region == "us-east-1"
    # Artificially alter latency and loads
    router.endpoints["us-east-1"].is_healthy = True
    # The sticky routing caching should still route to us-east-1
    decision2 = router.route(tenant)
    assert decision2.target_region == "us-east-1"


def test_tenant_billing():
    manager = TenantManager()
    tenant = manager.create_tenant("Acme Corp", plan=TenantPlan.STARTER)
    billing = TenantBilling()

    # Record usage records
    billing.record(tenant.tenant_id, metric=UsageMetric.DOCUMENTS_PROCESSED, quantity=5)
    billing.record(tenant.tenant_id, metric=UsageMetric.QUERIES, quantity=200)

    # Fetch period usage
    usage = billing.get_usage(tenant.tenant_id)
    assert usage["documents_processed"] == 5.0
    assert usage["queries"] == 200.0

    # Current billing period aggregates
    current_agg = billing.get_current_period_usage(tenant.tenant_id)
    assert current_agg["documents_processed"] == 5.0

    # Invoice generation
    invoice = billing.generate_invoice(tenant.tenant_id, manager)
    # Expected starter plan cost is $49.0
    # Expected doc processing cost is 5 * 0.01 = $0.05
    # Expected queries cost is 200 * 0.001 = $0.20
    # Subtotal = 49.0 + 0.05 + 0.20 = 49.25
    # Tax (8%) = 49.25 * 0.08 = 3.94
    # Total = 49.25 + 3.94 = 53.19
    assert invoice.subtotal == 49.25
    assert invoice.tax == 3.94
    assert invoice.total == 53.19
    assert invoice.status == "pending"

    # Mark paid
    paid = billing.mark_paid(invoice.invoice_id)
    assert paid.status == "paid"
    assert paid.paid_at is not None


def test_tenant_admin_router():
    # Setup test FastAPI application
    app = FastAPI()
    app.include_router(admin_router)

    # Attach instances to app state
    manager = TenantManager()
    billing = TenantBilling()
    app.state.tenant_manager = manager
    app.state.tenant_billing = billing

    client = TestClient(app)

    # 1. POST /tenants
    resp1 = client.post(
        "/v1/admin/tenants",
        json={"name": "Test Org", "plan": "starter", "contact_name": "John Doe"}
    )
    assert resp1.status_code == 201
    tenant_data = resp1.json()
    assert tenant_data["name"] == "Test Org"
    assert tenant_data["plan"] == "starter"
    tenant_id = tenant_data["tenant_id"]

    # 2. GET /tenants
    resp2 = client.get("/v1/admin/tenants")
    assert resp2.status_code == 200
    assert len(resp2.json()) == 1

    # 3. GET /tenants/{tenant_id}
    resp3 = client.get(f"/v1/admin/tenants/{tenant_id}")
    assert resp3.status_code == 200
    assert resp3.json()["name"] == "Test Org"

    # 4. PATCH /tenants/{tenant_id}
    resp4 = client.patch(
        f"/v1/admin/tenants/{tenant_id}",
        json={"contact_name": "Jane Doe"}
    )
    assert resp4.status_code == 200
    assert manager.get_tenant(tenant_id).contact_name == "Jane Doe"

    # 5. POST /tenants/{tenant_id}/upgrade
    resp5 = client.post(
        f"/v1/admin/tenants/{tenant_id}/upgrade",
        json={"plan": "professional"}
    )
    assert resp5.status_code == 200
    assert resp5.json()["plan"] == "professional"

    # 6. POST /tenants/{tenant_id}/suspend
    resp6 = client.post(
        f"/v1/admin/tenants/{tenant_id}/suspend",
        json={"reason": "audit"}
    )
    assert resp6.status_code == 200
    assert resp6.json()["status"] == "suspended"

    # 7. POST /tenants/{tenant_id}/reactivate
    resp7 = client.post(f"/v1/admin/tenants/{tenant_id}/reactivate")
    assert resp7.status_code == 200
    assert resp7.json()["status"] == "active"

    # 8. POST /tenants/{tenant_id}/rotate-api-key
    resp8 = client.post(f"/v1/admin/tenants/{tenant_id}/rotate-api-key")
    assert resp8.status_code == 200
    assert "api_key" in resp8.json()

    # 9. POST /tenants/{tenant_id}/usage
    resp9 = client.post(
        f"/v1/admin/tenants/{tenant_id}/usage",
        json={"metric": "queries", "quantity": 500}
    )
    assert resp9.status_code == 200
    assert resp9.json()["quantity"] == 500.0

    # 10. GET /tenants/{tenant_id}/usage
    resp10 = client.get(f"/v1/admin/tenants/{tenant_id}/usage")
    assert resp10.status_code == 200
    assert resp10.json()["period_summary"]["queries"] == 500.0

    # 11. POST /tenants/{tenant_id}/invoices
    resp11 = client.post(f"/v1/admin/tenants/{tenant_id}/invoices")
    assert resp11.status_code == 200
    # profesional plan is $199.0, queries cost is 500 * 0.001 = $0.50
    # subtotal = 199.50, tax = 15.96, total = 215.46
    assert resp11.json()["total"] == 215.46

    # 12. GET /tenants/{tenant_id}/invoices
    resp12 = client.get(f"/v1/admin/tenants/{tenant_id}/invoices")
    assert resp12.status_code == 200
    assert len(resp12.json()) == 1

    # 13. DELETE /tenants/{tenant_id}
    resp13 = client.delete(f"/v1/admin/tenants/{tenant_id}")
    assert resp13.status_code == 200
    assert resp13.json()["deleted"] is True
