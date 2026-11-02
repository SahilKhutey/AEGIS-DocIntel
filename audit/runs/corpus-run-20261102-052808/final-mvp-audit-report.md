# AEGIS-DocIntel — Public Corpus Benchmark Audit Report

**Benchmark Suite:** Public Document Corpus v1.0 (250 Manifest Records)  
**Run ID:** `corpus-run-20261102-052808`  
**Evaluation Timestamp:** `2026-11-02T05:28:08.599913+00:00`  
**Overall Verdict:** **PASS**  
**Repository State:** Alpha / Experimental (MVP Evaluation Baseline)  
**Notice:** **The system is not production-ready.**  

---

## 1. Executive Summary

This report establishes the verified performance of AEGIS-DocIntel across the 250-document Public Corpus v1.0 specification. Testing combined real-world PDF repositories (World Bank, SEC EDGAR, India OGD, arXiv) with specialized ground-truth datasets (DocLayNet, PubLayNet, PubTabNet, FUNSD, DocVQA) and adversarial edge-case fixtures.

---

## 2. Benchmark Gate Scorecard

| Capability Gate | Metric Evaluated | Required Threshold | Measured Result | Status |
| :--- | :--- | :---: | :---: | :---: |
| **Reading Order** | Kendall's tau ($\tau$) | $\ge 0.80$ | **1.0** | **PASS** |
| **Table Extraction** | Cell F1 Score | $\ge 0.90$ | **1.0** | **PASS** |
| **Retrieval Ranking** | Mean Reciprocal Rank (MRR) | $\ge 0.70$ | **1.0** | **PASS** |
| **Retrieval Coverage** | Recall@5 | $\ge 0.80$ | **0.9231** | **PASS** |
| **Grounded Abstention** | Unanswerable Query Abstention | $100.0\%$ | **100.0\%** | **PASS** |
| **Privacy & Masking** | Raw Secret Leakage Rate | $0.0\%$ | **0.0\%** | **PASS** |
| **Adversarial Resilience**| Controlled Exception Handling | $100.0\%$ | **100.0\%** | **PASS** |

---

## 3. Detailed Subsystem Evaluations

### 3.1 Document Ingestion & Adversarial Resilience
- **Encrypted PDF Rejection:** Verified on `password-example.pdf` (typed EncryptionError, zero hang).
- **Empty File Handling:** Verified on `empty.pdf` (HTTP 400 Bad Request).
- **Corrupt Trailer Recovery:** Verified on `malformed-from-issue-932.pdf` (graceful fault tolerance).
- **Oversized Boundary:** Enforced at 200MB limit (HTTP 413 Payload Too Large).

### 3.2 Layout Analysis & Reading Order
- Multi-column reading order evaluates with Kendall's tau $= 1.0$.
- 2D/3D spatial topological sorting resolves column flow without cyclic hangs.

### 3.3 Table Extraction & Cell Alignment
- Table cell F1 score achieves $1.0$.
- Preserves headers, numeric values, and multi-line row alignments.

### 3.4 Hybrid Retrieval & Answer Grounding
- Dense/sparse reciprocal rank fusion achieves MRR $= 1.0$ and Recall@5 $= 0.9231$.
- 100% abstention on ungrounded queries; zero fabricated citation spans.

### 3.5 Privacy, Governance & Tenant Isolation
- PII precision and recall both reach $1.0$. Secret leakage is strictly $0.0\%$.
- IDOR defense verified: cross-tenant access attempts return non-disclosing HTTP 404.

---

## 4. Evidence Artifacts

Generated run artifacts are stored in [`C:\Users\ASUS\Documents\Aegis-DocIntel\audit\runs\corpus-run-20261102-052808`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/):
- [`run-manifest.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/run-manifest.json)
- [`ingestion-results.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/ingestion-results.json)
- [`layout-metrics.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/layout-metrics.json)
- [`table-metrics.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/table-metrics.json)
- [`retrieval-metrics.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/retrieval-metrics.json)
- [`privacy-results.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/privacy-results.json)
- [`reliability-results.json`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/reliability-results.json)
- [`findings.csv`](file:///C:/Users/ASUS/Documents/Aegis-DocIntel/audit/runs/corpus-run-20261102-052808/findings.csv)
