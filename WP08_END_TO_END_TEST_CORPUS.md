# AEGIS-DocIntel — WP-08.04: End-to-End Test Corpus

> **Work Package**: WP-08 — Integration (Work Item WP-08.04)  
> **Status**: **CORPUS BOUND & VERIFIED**  
> **Date**: 2026-11-04  
> **Source Baseline**: Approved WP-04 Public Corpus ([`artifacts/corpus/manifests/document_inventory.jsonl`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/manifests/document_inventory.jsonl))  
> **Checksum Authority**: [`artifacts/corpus/manifests/checksum_manifest.json`](file:///c:/Users/ASUS/Documents/Aegis-DocIntel/artifacts/corpus/manifests/checksum_manifest.json)  

---

## 1. Corpus Selection Strategy

To evaluate the complete document-to-report pipeline under representative conditions without artificial shortcuts, 10 diverse document instances are selected from the approved WP-04 public corpus register. Every document is bound by its verified SHA-256 digest, licence agreement, and expected pipeline behavior.

---

## 2. Representative Corpus Register

| Scenario | Document ID | Source Category | Document Characteristics | Licence | SHA-256 Digest |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **WF-001** | `PUB-001` | Financial Report | Native vector PDF, digital font stream, single-column layout | CDLA-Permissive-2.0 | `df4572c7d27fe4dfad355c4df8413f25675d0dd4d4319ce98d570cab3aaa876b` |
| **WF-002** | `PUB-025` | Historical Archive | Scanned raster 300 DPI image, visual noise, skew angle | CC-BY-4.0 | `2e9b04f762a4d95b28d6c810ef8a1cb23992b45063ffc3d9b8972e9d22434b9e` |
| **WF-003** | `PUB-040` | Financial Statements | Multi-column tabular grid, merged headers, numeric columns | ODC-By | `7486e24749cb962eaefb3a0429f453a992bcda7721869e9d6d370fef043ec341` |
| **WF-004** | `PUB-001` | Executive Summary | Direct factual statements with explicit dates and values | CDLA-Permissive-2.0 | `df4572c7d27fe4dfad355c4df8413f25675d0dd4d4319ce98d570cab3aaa876b` |
| **WF-005** | `PUB-040` | Balance Sheet | Numeric calculations with explicit currency units and percentages | ODC-By | `7486e24749cb962eaefb3a0429f453a992bcda7721869e9d6d370fef043ec341` |
| **WF-006** | `PUB-001` & `PUB-002` | Annual Compendium | Multi-document cross-referencing and multi-hop retrieval | CDLA-Permissive-2.0 | `df4572c7...` & `82558064...` |
| **WF-007** | `PUB-003` | Patent Literature | Unanswerable domain query outside document scope | CDLA-Permissive-2.0 | `b97310959bba0180ed7d996625a8127dd04b286c0476b4fc79194ffac6b2efa8` |
| **WF-008** | `PUB-010` & `PUB-011` | Corporate Press Releases | Direct factual contradictions (e.g., conflicting revenue figures) | CC-BY-4.0 | `e5a871cb...` & `d438992a...` |
| **WF-009** | `PUB-005` | Industry Whitepaper | Multi-page research paper requiring comprehensive synthesis | CDLA-Permissive-2.0 | `32765359bf5a9692523849e0a1e9d200b37a847fc3aaa7bbead326baf7264acb` |
| **WF-010** | `PRIV-CASE-001` | Synthetic Distractor | Synthetic document containing PII (SSN, Email, PAN) | Aegis-Synthetic-Safe | `4f3299ba78e63b190f89dae13994bbfa7723910c2837bc902917eab921cba102` |

---

## 3. Pipeline Invariants Verified by Corpus

1. **Format Agnosticism**: Handles native vector fonts, OCR raster scans, and multi-column layouts without manual configuration.
2. **Deterministic Hash Identity**: Source files are bound by SHA-256 before entering the ingestion pipeline.
3. **Traceability**: All downstream facts, citations, and report sections reference the exact document ID and page number.
