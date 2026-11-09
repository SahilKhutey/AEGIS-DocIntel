# 06 — Developer Platform and API Explorer

## 1. Functional Scope
The Developer Platform (`/developer`, `/developer/api`) provides interactive documentation, live request schemas, and multi-language client snippet generators.

## 2. OpenAPI Schema Explorer
Driven by `contracts/openapi.yaml` and `/openapi.json`:
- Grouped by functional modules:
  - Admin & Observability
  - Pipeline Execution
  - Webhooks
  - Advanced Mathematics
- Endpoint cards display HTTP method (`GET`, `POST`, `DELETE`), endpoint URI, parameter table (in, type, required, description), and verified sample responses.

## 3. Client Snippet Generation
Developers can toggle between code generation targets:
- **cURL**: Direct command line execution with auth header.
- **Python (Requests)**: Standard corporate automation pattern.
- **TypeScript (Fetch)**: Modern async browser and Node.js pattern.
