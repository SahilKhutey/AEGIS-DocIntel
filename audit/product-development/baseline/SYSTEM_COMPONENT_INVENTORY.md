# AEGIS-DocIntel System Component Inventory

**Inventory Version:** 1.0.0  
**Phase Reference:** PROT-FINAL-10 (Work Package PD-01)  
**Date:** 2026-11-19  
**Status:** COMPLETE  

---

## 1. System Architecture Overview

AEGIS-DocIntel is structured into three primary operational tiers:
1. **Frontend Presentation & Interaction Tier (`web/`):** Next.js 15 App Router web client providing document inspection, query composition, evidence visualization, and management interfaces.
2. **Evaluation Gateway & Licensing Boundary (`services/evaluation_gateway/`):** Fail-closed API gateway managing Ed25519 licensing, device activation, and tenant quota metering.
3. **Core Document Intelligence Engine (`src/`):** FastAPI application orchestrating document intake, layout extraction, Kahn DAG reading order, submodular context packing, hybrid retrieval, and grounded question answering.

---

## 2. Component Inventory Matrix

| Component / Subsystem | Primary Path / Module | Key Files / Classes | Responsibility | Status |
| :--- | :--- | :--- | :--- | :--- |
| **API Entrypoint** | `src/main.py` | `create_app()`, `lifespan()` | Application startup, dependency container wiring, middleware, router mounting (74 endpoints) | WORKING |
| **Gateway Service** | `services/evaluation_gateway/app.py` | `app`, `verify_license()`, `quota_manager` | Public perimeter gateway, Ed25519 license validation, session management (92 endpoints) | WORKING |
| **Document Ingestion API** | `src/api/routers/documents.py` | `upload_document()`, `get_document()` | File intake, mime-type validation, size limits, idempotency verification | WORKING |
| **Document Persistence** | `src/services/container.py` | `RealDocumentService` | SQLite document persistence, raw byte storage, SHA-256 integrity, restart recovery | WORKING |
| **PDF Extraction Engine** | `src/ingestion/pdf_loader.py` | `PDFLoader`, `fitz` | PyMuPDF text and coordinate extraction with OCR fallback | WORKING |
| **DOCX Extraction Engine** | `src/ingestion/docx_loader.py` | `DOCXLoader` | Structured extraction for Microsoft Word documents | WORKING |
| **Text & Office Loaders** | `src/ingestion/` | `text_loader.py`, `pptx_loader.py`, `xlsx_loader.py` | Ingestion loaders for plain text, presentations, spreadsheets | WORKING |
| **OCR Fallback Engine** | `src/ingestion/ocr_engine.py` | `OCREngine` | Tesseract OCR rendering and optical character recognition | PARTIAL |
| **Ingestion Security** | `src/ingestion/secure_parser.py` | `SecureParser`, `anomaly_gate.py` | Defense against zip bombs, XML entity attacks, malformed byte payloads | WORKING |
| **Reading Order Engine** | `src/engines/graph_reading_order.py`| `is_reading_forward_successor()`, Kahn DAG | Deterministic topological sort with $(y_{min}, x_{min}, \text{node\_id})$ tie-breaking | WORKING |
| **Layout Normalization** | `src/normalization/layout.py` | `LayoutNormalizer` | Bounding box spatial normalization, line and paragraph grouping | WORKING |
| **Background Job Engine** | `src/operations/job_service.py` | `JobService`, `JobRepository` | Durable background job queuing, lease locking, exponential backoff retries | WORKING |
| **Retrieval Engine** | `src/engines/retrieval/` | `AMDIRetriever`, `hybrid_retrieval.py` | Hybrid dense + sparse vector search, BM25 term weighting, tenant filtering | WORKING |
| **Context Optimizer** | `aegis-docprep/aegis_docprep/` | `SubmodularKnapsackPacker` | Provable $(1 - 1/e)/2$ submodular knapsack context packing under token budget | WORKING |
| **LLM Inference Engine** | `src/engines/llm/llm_interface.py` | `LLMInterface`, `MockProvider` | Multi-provider LLM abstraction (`litellm`), deterministic mock for tests | WORKING |
| **Citation Verifier** | `src/engines/coordinate/` | `CoordinateEngine`, `CitationVerifier` | Bounding-box coordinate citation verification, grounding scoring | WORKING |
| **Document Comparison** | `src/api/routers/intelligence.py` | `compare_documents()` | Cross-document semantic diffing and structured conflict extraction | WORKING |
| **Human Review Workflow** | `src/api/routers/reviews.py` | `ReviewService`, `ReviewRepository` | Human-in-the-loop review, claim approval, discrepancy override | WORKING |
| **Web Frontend App** | `web/src/app/` | Next.js App Router Pages (17 routes) | Document workbench, search, comparison, and review UI | WORKING |
| **Frontend API Client** | `web/src/lib/api-client.ts` | `apiRequest()` | Zod-validated, type-safe HTTP client with session header injection | WORKING |
| **Reverse Proxy Gateway** | `infrastructure/gateway/` | `Caddyfile`, Dockerfile | Edge reverse proxy, automatic TLS, rate limiting, security headers | WORKING |
| **Container Infrastructure**| `deploy/`, `infrastructure/` | Dockerfiles, Compose files | Staging, production, and demo multi-container orchestration | WORKING |

---

## 3. Storage and Database Inventory

| Storage Resource | Technology | Location / Mount | Schema / Table | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Documents DB** | SQLite 3 | `data/documents.db` | `documents` | Durable document metadata, status, sha256, byte blobs |
| **Jobs DB** | SQLite 3 | `data/jobs.db` | `jobs`, `job_events` | Durable background tasks, retry state, leases, transition logs |
| **License Key Store** | File / Registry | `services/evaluation_gateway/keys/` | Ed25519 Keys | Public/private key pairs for offline token signature and verification |
| **Audit Ledger** | JSON / Append-only | `audit/` | Audit logs, manifests | Monotonic compliance, security, and verification records |
