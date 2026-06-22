import os
import sys
from pathlib import Path
import pytest
import asyncio

# Configure Python path to find backend packages
root_dir = Path(__file__).parent.parent
sys.path.insert(0, str(root_dir))

from backend.src.graphql import (
    DataLoader,
    GraphQLEngine,
    get_playground_html,
)
from backend.src.multitenancy import TenantManager, TenantBilling
from backend.src.analytics import AnalyticsEngine


@pytest.mark.asyncio
async def test_dataloader_batching():
    call_count = 0

    async def mock_batch_loader(keys):
        nonlocal call_count
        call_count += 1
        # Simply square each key
        return [k * k for k in keys]

    loader = DataLoader(mock_batch_loader)

    # Trigger loads concurrently
    res1_task = loader.load(2)
    res2_task = loader.load(3)
    res3_task = loader.load(2)  # Should hit cache

    res1, res2, res3 = await asyncio.gather(res1_task, res2_task, res3_task)

    assert res1 == 4
    assert res2 == 9
    assert res3 == 4

    # The batch loader should be called exactly once
    assert call_count == 1


@pytest.mark.asyncio
async def test_graphql_engine_query_and_mutation():
    manager = TenantManager()
    billing = TenantBilling()
    analytics = AnalyticsEngine()
    engine = GraphQLEngine(manager, billing, analytics)

    # 1. Create a tenant using GraphQL Mutation
    mutation = """
        mutation CreateNewTenant {
            createTenant(name: "GraphQL Corp", plan: "Starter", email: "info@gql.com") {
                id
                name
                plan
                status
            }
        }
    """
    mut_result = await engine.execute(mutation)
    assert "errors" not in mut_result
    tenant_data = mut_result["data"]["createTenant"]
    tenant_id = tenant_data["id"]
    assert tenant_data["name"] == "GraphQL Corp"
    assert tenant_data["plan"] == "starter"

    # Verify tenant is in manager
    tenant = manager.get_tenant(tenant_id)
    assert tenant is not None

    # 2. Query Tenant details using variables
    query = """
        query GetTenantDetails($tid: ID!) {
            tenant(id: $tid) {
                id
                name
                plan
                status
            }
        }
    """
    query_result = await engine.execute(query, variables={"tid": tenant_id})
    assert "errors" not in query_result
    assert query_result["data"]["tenant"]["id"] == tenant_id
    assert query_result["data"]["tenant"]["name"] == "GraphQL Corp"


@pytest.mark.asyncio
async def test_graphql_dataloader_nplus1_prevention():
    manager = TenantManager()
    billing = TenantBilling()
    analytics = AnalyticsEngine()
    engine = GraphQLEngine(manager, billing, analytics)

    # Query documents and nested authors (which triggers DataLoader)
    query = """
        query GetDocumentsWithAuthors {
            documents(tenant_id: "any") {
                id
                title
                author {
                    id
                    name
                    role
                }
            }
        }
    """

    engine.author_batch_calls = 0  # reset stats
    result = await engine.execute(query)
    
    assert "errors" not in result
    docs = result["data"]["documents"]
    assert len(docs) == 3
    
    # Check that authors are resolved correctly
    assert docs[0]["author"]["name"] == "Alice Vance"
    assert docs[1]["author"]["name"] == "Bob Vance"
    assert docs[2]["author"]["name"] == "Alice Vance"

    # Crucial assertion: N+1 prevention check
    # Instead of making 3 calls (one per doc), it should batch them in exactly 1 call!
    assert engine.author_batch_calls == 1


@pytest.mark.asyncio
async def test_graphql_persisted_queries():
    manager = TenantManager()
    billing = TenantBilling()
    analytics = AnalyticsEngine()
    engine = GraphQLEngine(manager, billing, analytics)

    # Create a tenant
    tenant = manager.create_tenant(name="Persisted Inc", billing_email="info@p.com")

    # Send query using hash register key
    result = await engine.execute("sha256_get_tenant_profile", variables={"id": tenant.tenant_id})
    assert "errors" not in result
    assert result["data"]["tenant"]["name"] == "Persisted Inc"

    # Send unregistered query hash
    bad_result = await engine.execute("sha256_unregistered_hash_key")
    assert bad_result["data"] is None
    assert bad_result["errors"][0]["message"] == "PersistedQueryNotFound"


@pytest.mark.asyncio
async def test_graphql_mutation_and_analytics_query():
    manager = TenantManager()
    billing = TenantBilling()
    analytics = AnalyticsEngine()
    engine = GraphQLEngine(manager, billing, analytics)

    # Register tenant
    tenant = manager.create_tenant("Analytics Ltd")

    # Log document processing usage
    usage_mutation = """
        mutation LogDocs {
            recordUsage(tenant_id: "$tid", metric: "DOCUMENTS_PROCESSED", quantity: 12.0)
        }
    """.replace("$tid", tenant.tenant_id)
    
    mut_res = await engine.execute(usage_mutation)
    assert mut_res["data"]["recordUsage"] is True

    # Add mock user click activity
    analytics.behavior_manager.log_query("q1", "u1", "quantum physics")
    analytics.behavior_manager.log_click("q1", "doc1", 1)

    # Add cost log
    analytics.cost_optimizer.log_query_execution("hi", "gpt-4", 10, 20, 0.5)

    # Query analytics
    analytics_query = """
        query GetAnalytics($tid: ID!) {
            analytics(tenant_id: $tid) {
                total_documents
                click_through_rate
                mean_reciprocal_rank
                monthly_savings_usd
            }
        }
    """

    res = await engine.execute(analytics_query, variables={"tid": tenant.tenant_id})
    assert "errors" not in res
    report = res["data"]["analytics"]
    assert report["total_documents"] == 12
    assert report["click_through_rate"] == 1.0
    assert report["mean_reciprocal_rank"] == 1.0
    assert report["monthly_savings_usd"] > 0.0


@pytest.mark.asyncio
async def test_graphql_subscriptions():
    manager = TenantManager()
    billing = TenantBilling()
    analytics = AnalyticsEngine()
    engine = GraphQLEngine(manager, billing, analytics)

    sub_query = """
        subscription OnDocsProcessed($tid: ID!) {
            onEventTriggered(tenant_id: $tid) {
                id
                topic
                timestamp
            }
        }
    """
    res = await engine.execute(sub_query, variables={"tid": "tenant_123"})
    assert "errors" not in res
    
    # Subscription yields an async generator
    async_gen = res["data"]["onEventTriggered"]
    events = []
    async for event in async_gen:
        events.append(event)

    assert len(events) == 3
    assert events[0]["id"] == "evt_sub_0"
    assert events[0]["topic"] == "document.processed"


def test_graphql_playground_rendering():
    response = get_playground_html(graphql_endpoint="/my-graphql-url")
    assert response.status_code == 200
    # HTML must contain loading element and url configuration
    assert b"AMDI-OS GraphQL Playground" in response.body
    assert b"/my-graphql-url" in response.body
    assert b"graphiql" in response.body
