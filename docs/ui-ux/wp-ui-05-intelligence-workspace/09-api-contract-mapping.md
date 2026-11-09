# 09 — API Contract Mapping & Backend Integration

## 1. Overview
The Intelligence Workspace connects the Next.js frontend with AEGIS-DocIntel's FastAPI backend endpoints. All requests enforce Bearer authentication, tenant boundaries, and workspace permissions.

## 2. API Endpoint Matrix

| UI Capability | Operation ID | HTTP | Endpoint | Status | Backend Schemas | Required Permission |
|---|---|---|---|---|---|---|
| **Ask AEGIS** | `create_answer_v1_answers_post` | `POST` | `/v1/answers` or `/api/v1/ask` | `VERIFIED` | `AnswerRequest` -> `AnswerResponse` | `intelligence.query` |
| **RAG Query** | `query_documents_v1_query_post` | `POST` | `/v1/query` | `VERIFIED` | `QueryRequest` -> `QueryResponse` | `intelligence.query` |
| **Passage Chunks** | `list_chunks_v1_documents__doc_id__chunks_get` | `GET` | `/v1/documents/{doc_id}/chunks` | `VERIFIED` | None -> `DocumentChunkList` | `evidence.read` |
| **Extracted Facts** | `get_document_facts_v1_documents__document_id__facts_get` | `GET` | `/v1/documents/{document_id}/facts` | `VERIFIED` | Query param `attribute` -> `ExtractedFact[]` | `intelligence.query` |
| **Fact Comparison** | `compare_documents_v1_intelligence_compare_post` | `POST` | `/v1/intelligence/compare` | `VERIFIED` | `CompareDocumentsRequest` -> `DocumentComparison` | `documents.compare` |
| **Conflict Detection**| `get_conflicts_v1_intelligence_conflicts_get` | `GET` | `/v1/intelligence/conflicts` | `VERIFIED` | None -> `Conflict[]` | `governance.read` |
| **Standalone Retrieval**| `retrieve_v1_retrieve_post` | `POST` | `/v1/retrieve` | `PARTIAL / GAP` | Fallback to scoped document chunk query | `intelligence.query` |
| **Knowledge Graph**| `get_graph_v1_intelligence_graph_post` | `POST` | `/v1/intelligence/graph` | `PARTIAL / GAP` | Fallback to mapping `/v1/documents/{id}/facts` | `intelligence.query` |

## 3. Resilience & Graceful Fallbacks
- Where dedicated graph or retrieval endpoints are still pending full backend rollout, the frontend client falls back deterministically to documented base endpoints (`/v1/documents/{doc_id}/chunks` and `/v1/documents/{doc_id}/facts`), transforming the structured facts into nodes and relationships.
- Network and timeout errors are caught and surfaced via `ErrorState` components allowing user retries without reloading the page.
