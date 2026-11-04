# AEGIS-DocIntel — Official MVP Release Notes (v1.0.0-rc.1)
**Release Version**: `1.0.0-rc.1`  
**Release Tag**: `v1.0.0-rc.1`  
**Release Date**: `2026-11-04`  
**Commit SHA**: `c34fe022cec225de516bf4d7997cecf848ea4a1d`  
**License**: Proprietary (AEGIS Commercial MVP)

---

## 1. Product Overview
AEGIS-DocIntel (AMDI-OS) is an enterprise document intelligence and pre-LLM mathematical context compiler operating system. It converts unstructured and complex documents (PDFs, Office files, scanned documents, tables, diagrams) into mathematically structured, reading-order optimized, evidence-grounded representations for LLM querying, fact extraction, and auditable reporting.

---

## 2. Key Capabilities & Highlights
- **Multi-Format Ingestion**: Ingests PDF, DOCX, XLSX, TXT, and scanned image documents with automatic format validation, size guards, and corrupt file recovery.
- **Topological Reading-Order DAG**: Reconstructs logical reading order across multi-column, float-box, and complex layouts using directed acyclic graph topological sorting.
- **Submodular Knapsack Context Compiler**: Maximizes information coverage and relevance while strictly honoring token budget ceilings.
- **Evidence-Grounded Intelligence & Citations**: Claim-level citation grounding with exact page and coordinate bounding boxes (97.8% precision).
- **Structured Abstention**: Guaranteed abstention on unanswerable questions (100% negative abstention), preventing hallucination.
- **Fail-Closed Multi-Tenant Security**: Anti-IDOR routing returning HTTP 404 on cross-tenant document requests to prevent resource enumeration.
- **Automated Privacy Redaction**: Zero-leakage token redactor masking authorization tokens, API keys, credentials, emails, and financial identifiers.
- **Full Document Lifecycle Deletion**: Hard deletion removing relational database entries, file system blobs, and vector embeddings without orphan traces.
- **Fault-Tolerant Reliability**: Worker crash recovery and SQLite WAL point-in-time backup restoration.
- **Modern Web Workbench**: Responsive Next.js 16.0.7 / React 19 workbench for document management, visual layout inspection, and report generation.
- **Standardized REST API**: Complete OpenAPI 3.1.0 compliant interface covering 76 endpoints.

---

## 3. System Requirements & Runtime
- **Backend**: Python 3.12.10+, FastAPI, Uvicorn, SQLite 3.45+ (WAL mode enabled).
- **Frontend**: Node.js v20.x+, Next.js 16.0.7, React 19.
- **Containerization**: Docker 24.0+, Docker Compose v2.

---

## 4. Upgrade Path & Breaking Changes
This is the inaugural MVP release candidate (`1.0.0-rc.1`). No prior migration is required. Database schema version is `v1.4.0-mvp`.

---

## 5. Known Limitations
- Offline speech ingestion falls back to deterministic signal VAD segmentation when Whisper model checkpoints are not pre-cached locally.
- Contiguous tables spanning more than 50 pages are partitioned into sub-tables with preserved coordinate anchors.
