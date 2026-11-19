# AEGIS-DocIntel — Evaluation Release Known Limitations

**Workstream:** `launch/product-hunt/release`  
**Phase:** `PROT-FINAL-09`  
**Scope:** Transparent disclosure of v0.1.0 evaluation boundaries  

---

## 1. Intentional Architectural & Quota Boundaries

| Limitation | Operational Scope | Evaluator Impact | Rationale & Workaround |
| :--- | :--- | :--- | :--- |
| **Document Volume Limit** | 5 active documents per evaluator | Evaluators can store up to 5 uploaded documents simultaneously. | Deleting a document frees up a quota slot immediately. |
| **File Size Ceiling** | 10 MB per file | Uploads $> 10\text{ MB}$ rejected with HTTP 413. | Protects parser worker scratchpad memory during evaluation. |
| **Daily Query Quota** | 20 queries / comparisons per 24 hours | Evaluators can submit up to 20 queries daily. | Resets automatically every 24 hours at 00:00 UTC. |
| **Hardware Binding** | 1 active device per license | Attempting to activate on a 2nd machine revokes the 1st session. | Prevents illicit license redistribution. |
| **Supported File Formats**| PDF, PNG, JPEG | DOCX, XLSX, TXT, EPUB not accepted in v0.1.0. | Parser optimized specifically for visual layout documents. |
| **Cloud Inference Dependency**| Requires active internet connection | Offline inference not available in evaluation client. | Protects proprietary weights and mathematical engines. |
