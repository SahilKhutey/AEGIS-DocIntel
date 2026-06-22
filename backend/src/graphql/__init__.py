"""
AMDI-OS GraphQL API
===================

Self-contained, high-performance GraphQL schema definitions, query engines,
DataLoader batch loading, persisted queries, and GraphiQL playground.
"""

from .dataloader import (
    DataLoader,
)
from .schema import (
    PERSISTED_QUERIES,
    GraphQLType,
    GraphQLField,
)
from .resolvers import (
    FieldNode,
    GraphQLParser,
    GraphQLEngine,
)
from .playground import (
    get_playground_html,
)

__all__ = [
    "DataLoader",
    "PERSISTED_QUERIES",
    "GraphQLType",
    "GraphQLField",
    "FieldNode",
    "GraphQLParser",
    "GraphQLEngine",
    "get_playground_html",
]
