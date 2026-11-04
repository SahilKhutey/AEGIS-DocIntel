# AEGIS-DocIntel — WP-08.02: API Contract Test Plan

> **Work Package**: WP-08 — Integration (Work Item WP-08.02)  
> **Status**: **ACTIVE PLAN**  
> **Date**: 2026-11-04  
> **Contract Source of Truth**: [`contracts/openapi.yaml`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/contracts/openapi.yaml) / [`openapi.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/openapi.json)  
> **Client Runtime Schemas**: [`web/src/lib/schemas.ts`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/web/src/lib/schemas.ts)  
> **Endpoint Inventory**: [`contracts/API_ENDPOINT_INVENTORY.csv`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/contracts/API_ENDPOINT_INVENTORY.csv) (76 Endpoints)  

---

## 1. Objective and Contract Principles

API contract testing verifies that the frontend client, backend FastAPI service, and asynchronous background workers agree on request formats, response payloads, status codes, and error envelopes.

### Core Contract Invariants
1. **Bidirectional Schema Conformance**: Every response returned by the backend must satisfy the frontend Zod schemas in `web/src/lib/schemas.ts`.
2. **Unified Error Model**: Error responses conform to `{ "error": { "code": string, "message": string, "request_id": string, "details": object } }`.
3. **Fail-Closed Anti-IDOR**: Cross-tenant requests return `HTTP 404 (Not Found)` to prevent IDOR enumeration.
4. **Idempotency Guarantee**: Ingestion and deletion requests accept `Idempotency-Key` headers; repeated submissions return identical cached responses without duplicate side effects.
5. **Safe Asynchronous Lifecycles**: Polling `/v1/documents/{doc_id}/status` transitions safely across `pending` -> `indexing` -> `ready` | `failed`.

---

## 2. API Contract Test Scenarios Matrix

| Scenario ID | Test Name | Target Endpoint | Input / Condition | Expected Status & Schema |
| :--- | :--- | :--- | :--- | :---: |
| **API-001** | Valid authentication request | `/v1/documents` | Valid Bearer JWT / API key | `200 OK` (Schema-valid list) |
| **API-002** | Invalid request payload | `/v1/answers` | Empty body `{}` | `422 Unprocessable Entity` |
| **API-003** | Upload valid document | `/v1/documents/upload` | Valid PDF file multipart | `202 Accepted` (`doc_id`, `status: pending`) |
| **API-004** | Upload unsupported file | `/v1/documents/upload` | Unsupported MIME (e.g., `image/bmp`) | `415 Unsupported Media Type` |
| **API-005** | Get processing status | `/v1/documents/{id}/status` | Valid UUID | `200 OK` (`IngestionStatusResponse`) |
| **API-006** | Search query | `/v1/queries` | Valid natural language query | `200 OK` (`QueryResponse` with items) |
| **API-007** | Answer query | `/v1/answers` | Valid question + doc IDs | `200 OK` (`AnswerResponse` with citations) |
| **API-008** | Citation resolution | `/v1/answers` | Answer containing citations | Citations contain valid doc ID and page |
| **API-009** | Generate report | `/v1/reports/generate` | Synthesize findings payload | `201 Created` (`ReportResponse`) |
| **API-010** | Unauthorized request | `/v1/documents` | Missing Authorization header | `401 Unauthorized` |
| **API-011** | Cross-tenant document request | `/v1/documents/{id}` | Token for Tenant A, document owned by Tenant B | `404 Not Found` (Anti-IDOR) |
| **API-012** | Missing document | `/v1/documents/{id}` | Non-existent UUID | `404 Not Found` |
| **API-013** | Backend missing required field | Test client parser | Simulated response missing required field | Client parser throws `ApiError` |
| **API-014** | Breaking schema change | Schema diff | Incompatible schema change (e.g., renamed field) | Compatibility analyzer flags break |
| **API-015** | Service timeout / error | Error handler | Simulated provider timeout | Controlled `504 Gateway Timeout` |

---

## 3. Evidence Artifacts
- [`artifacts/integration/api_contract/API_CONTRACT_TEST_REPORT.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/integration/api_contract/API_CONTRACT_TEST_REPORT.json)
- [`artifacts/integration/api_contract/API_COMPATIBILITY_REPORT.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/integration/api_contract/API_COMPATIBILITY_REPORT.json)
- [`artifacts/integration/api_contract/API_SCHEMA_VALIDATION_REPORT.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/integration/api_contract/API_SCHEMA_VALIDATION_REPORT.json)
