# 02 - Release Capability Matrix
All features are verified against empirical acceptance test suites:
- **Account Authentication**: READY (Short-lived JWT & session binding)
- **License Activation**: READY (Ed25519 challenge-response proof-of-possession)
- **Device Binding**: READY (Hardware fingerprint + public key; max 1 device)
- **Document Upload**: READY (MIME allowlisted; max 25MB)
- **Document Parsing**: READY (Structured PyMuPDF extraction with failure boundary)
- **Document Intelligence**: READY (Grounded reasoning; no LLM training)
- **Context Optimization**: READY (Hierarchical chunking + hybrid BM25/Vector)
- **Retrieval**: READY (Strict tenant-isolated search)
- **Comparison**: LIMITED (Evaluator-owned documents only)
- **Export**: READY (Sanitized JSON/CSV exports)
- **Usage Reporting**: READY (Two-phase quota reservation + reconciliation)
- **License Revocation**: READY (Synchronous session invalidation < 5s)
