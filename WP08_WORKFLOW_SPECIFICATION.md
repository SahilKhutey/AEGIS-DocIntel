# AEGIS-DocIntel — WP-08.04: Workflow Specification

> **Work Package**: WP-08 — Integration (Work Item WP-08.04)  
> **Status**: **ACTIVE SPECIFICATION**  
> **Date**: 2026-11-04  
> **Corpus Reference**: [`WP08_END_TO_END_TEST_CORPUS.md`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/WP08_END_TO_END_TEST_CORPUS.md)  

---

## 1. Complete Document-to-Report Workflow Stages

Every integration workflow executes across 14 synchronized validation checkpoints:
1. **Upload & Ingestion**: Multipart document payload received; SHA-256 computed; state `pending`.
2. **Security & Format Validation**: Allowed MIME check, virus/malware scan, size check ($\le 200\text{ MB}$).
3. **OCR & Text Extraction**: Multi-page text extraction (CER/WER thresholds enforced).
4. **Layout Detection & Segmentation**: Bounding box coordinates generated for headings, paragraphs, and tables.
5. **Reading Order Reconstruction**: Topological sorting through reading-order DAG.
6. **Table Structure Reconstruction**: Rows, columns, and merged cell extraction.
7. **Coordinate Normalization**: Coordinates scaled to standard $[0.0, 1.0]$ bounding boxes.
8. **Provenance Grounding**: Every chunk bound to source file SHA-256, page number, and bbox coordinates.
9. **Dual Indexing**: Sparse BM25 lexical index and dense semantic vector embedding generation.
10. **Hybrid RRF Retrieval**: Candidate chunk retrieval using Reciprocal Rank Fusion ($k_0=60$).
11. **Grounded QA & Citation Validation**: Claim decomposition and 7-label citation support verification.
12. **Structured Fact & Conflict Extraction**: Entity-attribute triples extracted; contradictions preserved.
13. **Report Synthesis**: Multi-section research report rendered in Markdown, HTML, and JSON.
14. **Artifact Sealing & Audit**: Output digest recorded in workflow run manifest.

---

## 2. End-to-End Scenarios Matrix (`WF-001` through `WF-010`)

| Scenario ID | Name & Objective | Input Documents | Expected Pipeline Behavior | Intermediate Checkpoint Assertion |
| :--- | :--- | :--- | :--- | :--- |
| **WF-001** | Process native PDF | `PUB-001` | Extracts native text streams directly without loss | Text accuracy $\ge 98\%$, 0 OCR noise |
| **WF-002** | Process scanned PDF | `PUB-025` | Automatically triggers OCR rasterization | OCR character error rate $\le 3\%$, page coordinates preserved |
| **WF-003** | Extract table values | `PUB-040` | Parses rows, columns, and numeric headers | Table reconstruction F1 $\ge 95\%$, numeric precision exact |
| **WF-004** | Direct factual QA | `PUB-001` | Answers revenue query with exact quote and page | Citation precision $1.0$, claim support = `SUPPORTS` |
| **WF-005** | Numeric QA with units | `PUB-040` | Retrieves exact monetary values and currency units | Raw unit preservation verified (e.g., `$M`, `YoY %`) |
| **WF-006** | Multi-document QA | `PUB-001` & `PUB-002` | Retrieves cross-document chunks | Citations span both `PUB-001` and `PUB-002` |
| **WF-007** | Unanswerable query | `PUB-003` | Abstains with `INSUFFICIENT_EVIDENCE` notice | Zero hallucinations; abstention confidence $\ge 0.90$ |
| **WF-008** | Conflicting documents | `PUB-010` & `PUB-011` | Preserves both contradictory claims | 8-stage conflict comparator flags `DIRECT_CONTRADICTION` |
| **WF-009** | Research report synthesis | `PUB-005` | Generates multi-section evidence-backed report | Pre-render validation passes; 0 unverified claims |
| **WF-010** | Restricted data report | `PRIV-CASE-001` | Enforces PII redaction policy | Secrets masked (`[REDACTED:EMAIL]`); 0.0% output leakage |

---

## 3. Failure & Replay Semantics

When an intermediate checkpoint fails:
- The execution terminates immediately.
- The pipeline records the stage name, failure reason, and document hash into `WP08_INTEGRATION_FAILURE_REGISTRY.md`.
- Downstream stages are marked `SKIPPED`.
- Storage is purged to avoid orphaned intermediate artifacts.
