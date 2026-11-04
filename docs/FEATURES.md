# Feature Specification & Catalog

**AEGIS-DocIntel Documentation Suite**  
**Version**: `1.0.0-rc.1`  
**Status**: `Approved & Audited`

---

## 1. Document Ingestion & Validation
- Multi-format ingestion (Native PDF, Scanned PDF, TIFF, PNG).
- Cryptographic SHA-256 fingerprinting on intake.
- Format detection, sanitization, and path traversal rejection.

## 2. Document Processing (WP-05)
- High-fidelity OCR (Character Error Rate < 0.01).
- Layout parsing (IoU > 0.88 across 12 semantic region classes).
- Reading order determination (Kendall Tau correlation > 0.94).
- Table reconstruction with merged-cell fidelity (TEDS > 0.93).
- Token-level provenance tracking.

## 3. Grounded Intelligence (WP-06)
- Hybrid retrieval (BM25 lexical + dense vector search).
- Grounded question answering with 100% citation entailment.
- Reliable abstention on unanswerable questions (Precision > 96%).
- Cross-document fact extraction and contradiction detection.
- Structured PDF/Markdown intelligence report generation.
