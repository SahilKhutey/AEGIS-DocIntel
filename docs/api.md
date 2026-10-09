# REST API & SDK Reference

This document provides the authoritative API reference for AEGIS-DocIntel, reflecting the verified route paths established in Phase 13 and documented in `openapi.json`.

---

## Verified Route Map

All API routes are mounted directly under the `/v1/` prefix:

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | System health check and uptime probe |
| `GET` | `/metrics` | Prometheus metrics endpoint (Phase 12) |
| `POST` | `/v1/documents/upload` | Upload and process a new document (PDF, TXT, DOCX) |
| `GET` | `/v1/documents/{doc_id}` | Retrieve document metadata and Master State |
| `GET` | `/v1/documents/{doc_id}/status` | Check processing status of an ingested document |
| `GET` | `/v1/documents` | List all ingested documents with pagination |
| `DELETE` | `/v1/documents/{doc_id}` | Cascade deletion across memory, cache, and index |
| `POST` | `/v1/documents/{doc_id}/reindex` | Trigger reprocessing and vector re-indexing |
| `GET` | `/v1/documents/{doc_id}/chunks` | Retrieve elastic chunks ($E$) for a document |
| `POST` | `/v1/documents/batch` | Batch document ingestion endpoint |
| `GET` | `/v1/documents/{doc_id}/elements` | Retrieve extracted bounding boxes and elements ($P$) |
| `POST` | `/v1/query` | Submodular retrieval and search query |

---

## Endpoint Details

### 1. Document Upload
**`POST /v1/documents/upload`**

Uploads a document file for asynchronous ingestion.

**Request:** `multipart/form-data`
- `file`: Binary file upload
- `compliance_mode`: (Optional) `"standard"` | `"hipaa"` | `"gdpr"` (default: `"standard"`)

**Response:**
```json
{
  "doc_id": "doc_9f82a17b4c",
  "filename": "annual_report.pdf",
  "status": "processing",
  "pages": 14,
  "created_at": "2026-10-09T08:00:00Z"
}
```

### 2. Query & Submodular Retrieval
**`POST /v1/query`**

Queries the knowledge index, optimizing context packing via submodular knapsack selection.

**Request:** `application/json`
```json
{
  "query": "What were the total operating expenses for Q3?",
  "top_k": 5,
  "max_tokens": 1024,
  "redact_pii": true
}
```

**Response:**
```json
{
  "query": "What were the total operating expenses for Q3?",
  "chunks": [
    {
      "chunk_id": "chunk_01",
      "doc_id": "doc_9f82a17b4c",
      "text": "Operating expenses for Q3 totaled $4.2M, representing...",
      "score": 0.892,
      "pii_redacted": true
    }
  ],
  "total_tokens": 812,
  "compression_ratio": 0.358
}
```

### 3. Cascade Deletion
**`DELETE /v1/documents/{doc_id}`**

Executes cryptographic cascade deletion across disk, memory cache, and vector embeddings.

**Response:**
```json
{
  "doc_id": "doc_9f82a17b4c",
  "status": "purged",
  "cascade_summary": {
    "file_unlinked": true,
    "cache_evicted": true,
    "vectors_deleted": 42,
    "audit_event_logged": true
  }
}
```

---

## SDK Usage Examples (Aligned in Phase 13)

### Python SDK (`sdk/python/`)

```python
from aegis_sdk import AegisClient

client = AegisClient(base_url="http://localhost:8000", api_key="test_key")

# Upload a document
doc = client.documents.upload("contract.pdf")

# Check status
status = client.documents.get_status(doc["doc_id"])

# Query with submodular context packing
results = client.query.search(
    query="Termination clause terms",
    max_tokens=500
)
```

### TypeScript SDK (`sdk/typescript/`)

```typescript
import { AegisClient } from "@aegis/sdk";

const client = new AegisClient({
  baseUrl: "http://localhost:8000",
  apiKey: "test_key",
});

const doc = await client.documents.upload(fileBlob);
const results = await client.query.search({
  query: "Termination clause terms",
  maxTokens: 500,
});
```
