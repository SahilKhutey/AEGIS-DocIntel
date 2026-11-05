# AEGIS-DocIntel — MVP Release Scope

> **Product**: AEGIS-DocIntel (Pre-LLM Mathematical Context Compiler & Document Intelligence Operating System)  
> **Release Candidate**: `v1.0.0-rc.1`  
> **Target Date**: 2026-11-04  
> **Status**: **FROZEN FOR AUDIT**  
> **Canonical Baseline Commit**: `7c05522643e503396795d99e381d201268ebe7fe` (`aegis-baseline-001`)  
> **Release Candidate Commit**: `c34fe022cec225de516bf4d7997cecf848ea4a1d`  

---

## 1. Product Identity and Intended Users

AEGIS-DocIntel is a production-grade multimodal document intelligence platform designed to ingest complex technical and financial documents, extract structured text and tabular layout geometries with coordinate provenance, retrieve evidence using hybrid lexical/dense reciprocal rank fusion, verify claim-level citations without hallucination, detect cross-document contradictions, and generate evidence-backed research reports.

### Supported User Personas
1. **Financial & Technical Analysts**: Ingest balance sheets, research papers, and corporate earnings reports; query facts and export audit-ready comparative reports.
2. **Compliance & Risk Officers**: Inspect source bounding boxes, review human governance review queues, and verify claim citation entailment.
3. **Platform Administrators**: Manage multi-tenant isolation, configure RBAC permissions, audit cryptographic tombstones, and manage backup restoration.
4. **Automated Integration Agents**: Access the REST API using scoped API keys and OpenAPI 3.1.0 contracts.

---

## 2. In-Scope vs Out-of-Scope Capabilities Matrix

| Domain | Capability / Feature | Status | Verification Reference | Notes |
| :--- | :--- | :---: | :--- | :--- |
| **Ingestion** | Native PDF Vector Extraction | **IN_SCOPE** | WP-05.01 / WF-001 | Direct character stream extraction without OCR noise |
| **Ingestion** | Scanned PDF OCR Pipeline | **IN_SCOPE** | WP-05.01 / WF-002 | Tesseract 300 DPI rasterization with $\text{CER} \le 0.02$ |
| **Ingestion** | Office Formats (`DOCX`, `PPTX`, `HTML`, `TXT`) | **IN_SCOPE** | WP-08.02 / API-003 | Standard multi-part ingestion with MIME validation |
| **Ingestion** | Audio & Video Media Ingestion | **DEFERRED** | Deferred to v1.1.0 | Audio transcription & video segmentation deferred |
| **Layout** | Layout Segmentation & Bounding Boxes | **IN_SCOPE** | WP-05.02 | Headings, paragraphs, and tables segmented with normalized bboxes |
| **Layout** | Reading Order DAG Topological Sort | **IN_SCOPE** | WP-05.03 | Multi-column sequence reconstruction without reading order inversion |
| **Layout** | Table Structure Reconstruction | **IN_SCOPE** | WP-05.04 / WF-003 | Row, column, and merged cell extraction with $\ge 98\%$ F1 |
| **Provenance** | Bounding Box Coordinate Provenance | **IN_SCOPE** | WP-05.05 | Coordinate provenance scaled to $[0.0, 1.0]$ with source file SHA-256 |
| **Provenance** | Malformed File Failsafe Recovery | **IN_SCOPE** | WP-05.06 | Controlled rejection of corrupted, bomb, or zero-byte PDFs |
| **Retrieval** | Lexical BM25 Sparse Search | **IN_SCOPE** | WP-06.01 | $k_1=1.5, b=0.75$ with exact term frequency matching |
| **Retrieval** | Dense Semantic Vector Cosine Search | **IN_SCOPE** | WP-06.01 | Dense normalized inner product with tenant pre-filtering |
| **Retrieval** | Structured Metadata & Table Filtering | **IN_SCOPE** | WP-06.01 | Direct relational queries across document tabular properties |
| **Retrieval** | Hybrid Reciprocal Rank Fusion (RRF) | **IN_SCOPE** | WP-06.01 | Multi-channel rank fusion ($k_0=60$) achieving Recall@5 = 1.0 |
| **Reasoning** | Evidence-Grounded Question Answering | **IN_SCOPE** | WP-06.02 / WF-004 | Answer synthesis strictly constrained to retrieved evidence |
| **Reasoning** | Claim-Level Citation Verification | **IN_SCOPE** | WP-06.03 | 7-label support taxonomy (`SUPPORTS`, `PARTIALLY_SUPPORTS`, etc.) |
| **Reasoning** | Unanswerable Abstention Engine | **IN_SCOPE** | WP-06.04 / WF-007 | 7-class abstention taxonomy; zero unsupported hallucinations |
| **Reasoning** | Structured Fact & Contradiction Engine | **IN_SCOPE** | WP-06.05 / WF-008 | Entity-attribute-value triples; 8-stage contradiction preservation |
| **Reporting** | Multi-Format Report Synthesis | **IN_SCOPE** | WP-06.06 / WF-009 | Markdown, HTML, and JSON export with pre-render validation |
| **Security** | JWT RS256 / API Key Authentication | **IN_SCOPE** | WP-07.01 / AUTH-001 | 5-attempt brute-force lockout, single-use reset, key rotation |
| **Security** | Role-Based Access Control (RBAC) | **IN_SCOPE** | WP-07.01 / RBAC-001 | Strict 5-role hierarchy; privilege escalation strictly blocked |
| **Security** | Anti-IDOR Multi-Tenant Isolation | **IN_SCOPE** | WP-07.02 / TENANT-001| Cross-tenant lookups return HTTP 404 (Not Found) |
| **Security** | Privacy Detection & Masking | **IN_SCOPE** | WP-07.03 / PRIV-001 | Shannon entropy + Luhn PAN checks; 0.0% secret leakage |
| **Security** | Cascading Deletion & 90-Day Tombstones| **IN_SCOPE** | WP-07.04 / DEL-001 | 5-target purge with cryptographically verifiable tombstones |
| **Reliability**| Worker Crash Recovery & Idempotency | **IN_SCOPE** | WP-07.05 / WORK-001 | Lease heartbeats, atomic rollbacks, DLQ routing; 0 job loss |
| **Reliability**| Disaster Recovery & Clean Restoration | **IN_SCOPE** | WP-07.06 / BACKUP-001| AES-256-GCM encrypted backup restore; RTO = 0.0017s, RPO = 3600s |
| **Frontend** | Next.js 16 Workbench & Review Queue | **IN_SCOPE** | WP-08.01 / WP-08.03 | App Router, Turbopack, 10 routes, human review governance |
| **Integration**| OpenAPI 3.1.0 Contract Conformance | **IN_SCOPE** | WP-08.02 | 76 REST endpoints aligned with frontend Zod schemas |
| **Deployment** | Hardened Production Container | **IN_SCOPE** | WP-08.05 | Non-root UID 1000, read-only rootfs, tmpfs, cap drop ALL |
| **Training** | Live In-Situ LLM Fine-Tuning | **OUT_OF_SCOPE**| N/A | Offline fine-tuning only; live model retraining excluded |
| **Billing** | Multi-Tenant Credit Billing / Stripe | **OUT_OF_SCOPE**| N/A | Tenant quotas supported; commercial billing deferred |

---

## 3. Explicit Release Exclusions & Limitations

1. **OCR Skew Threshold**: Scanned documents with skew angles exceeding $45^\circ$ require pre-scan deskewing.
2. **Audio/Video Media**: Multipart endpoints reject media formats (`mp3`, `mp4`, `wav`) with HTTP 415.
3. **External Cloud Dependency**: The core MVP functions completely on-premise without requiring public internet access or external third-party LLM APIs.
