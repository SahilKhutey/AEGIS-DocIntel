# AMDI-OS GraphQL API Module

A self-contained GraphQL engine supporting schema validation, AST parsing, DataLoader batch loading, and GraphiQL playground serving.

---

## N+1 Query Prevention

When querying lists of objects with nested fields (e.g. `documents` listing their `author`), standard resolvers run one query to list all documents, then one query *per document* to fetch its author (N+1 queries).

The `DataLoader` batches keys requested in a single tick of the event loop and executes a single batch loading call:

```python
# Instead of: N author database queries
author = db.get_author(author_id)

# DataLoader does: 1 batched query for all author IDs
author = await author_loader.load(author_id)
```

---

## FastAPI Routing Integration

To mount this GraphQL module onto a FastAPI application:

```python
from fastapi import FastAPI, Request
from backend.src.graphql import GraphQLEngine, get_playground_html

app = FastAPI()
# Initialize your engine with multitenancy and billing singletons
engine = GraphQLEngine(tenant_manager, tenant_billing, analytics_engine)

@app.get("/graphql")
async def graphql_playground():
    return get_playground_html(graphql_endpoint="/graphql")

@app.post("/graphql")
async def graphql_post(request: Request):
    body = await request.json()
    query = body.get("query")
    variables = body.get("variables", {})
    operation_name = body.get("operationName")
    
    result = await engine.execute(
        query=query, 
        variables=variables, 
        operation_name=operation_name
    )
    return result
```
