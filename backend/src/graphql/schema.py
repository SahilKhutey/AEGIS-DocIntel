"""
AMDI-OS GraphQL API: Schema Definitions
=======================================

Defines GraphQL types, query/mutation/subscription entry points, 
and supports a Persisted Query registry for optimizing payload bandwidth.
"""

from typing import Dict, Any, Optional, List


# In-memory registry for Persisted Queries (SHA256 hash -> query string)
PERSISTED_QUERIES: Dict[str, str] = {
    "sha256_get_tenant_profile": """
        query GetTenantProfile($id: ID!) {
            tenant(id: $id) {
                id
                name
                plan
                status
                region
            }
        }
    """,
    "sha256_get_analytics": """
        query GetAnalyticsReport($tenant_id: ID!) {
            analytics(tenant_id: $tenant_id) {
                total_documents
                click_through_rate
                mean_reciprocal_rank
                monthly_savings_usd
            }
        }
    """
}


class GraphQLField:
    def __init__(self, name: str, type_name: str, arguments: Optional[Dict[str, str]] = None):
        self.name = name
        self.type_name = type_name
        self.arguments = arguments or {}


class GraphQLType:
    def __init__(self, name: str, fields: List[GraphQLField]):
        self.name = name
        self.fields = {f.name: f for f in fields}


# Type specifications
TENANT_TYPE = GraphQLType("Tenant", [
    GraphQLField("id", "ID"),
    GraphQLField("name", "String"),
    GraphQLField("plan", "String"),
    GraphQLField("status", "String"),
    GraphQLField("region", "String"),
    GraphQLField("billing_email", "String"),
    GraphQLField("contact_name", "String"),
])

DOCUMENT_TYPE = GraphQLType("Document", [
    GraphQLField("id", "ID"),
    GraphQLField("title", "String"),
    GraphQLField("author_id", "ID"),
    GraphQLField("author", "Author"),  # Resolved via DataLoader to prevent N+1 queries
])

AUTHOR_TYPE = GraphQLType("Author", [
    GraphQLField("id", "ID"),
    GraphQLField("name", "String"),
    GraphQLField("role", "String"),
])

ANALYTICS_REPORT_TYPE = GraphQLType("AnalyticsReport", [
    GraphQLField("total_documents", "Int"),
    GraphQLField("click_through_rate", "Float"),
    GraphQLField("mean_reciprocal_rank", "Float"),
    GraphQLField("monthly_savings_usd", "Float"),
])

QUERY_TYPE = GraphQLType("Query", [
    GraphQLField("tenant", "Tenant", {"id": "ID!"}),
    GraphQLField("documents", "[Document]", {"tenant_id": "ID!"}),
    GraphQLField("analytics", "AnalyticsReport", {"tenant_id": "ID!"}),
])

MUTATION_TYPE = GraphQLType("Mutation", [
    GraphQLField("createTenant", "Tenant", {"name": "String!", "plan": "String!", "email": "String!"}),
    GraphQLField("recordUsage", "Boolean", {"tenant_id": "ID!", "metric": "String!", "quantity": "Float!"}),
])

SUBSCRIPTION_TYPE = GraphQLType("Subscription", [
    GraphQLField("onEventTriggered", "Event", {"tenant_id": "ID!"}),
])
