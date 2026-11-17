# AEGIS-DocIntel — Product Launch Demo Environment

This directory packages the **AEGIS Live Demo Edition**, enabling visitors and evaluators to experience AEGIS-DocIntel within minutes without complex setup, external API keys, or security risks to production systems.

---

## 1. Overview & Positioning

The AEGIS Demo Environment provides a hosted, browser-ready or locally containerized workspace seeded with synthetic technical documents. It allows users to test:
- **P0 End-to-End Ingestion:** Layout-aware parsing, bounding box extraction, and table reconstruction.
- **P0 Ask AEGIS (Evidence RAG):** Submodular knapsack context packing with 100% traceable page citations.
- **P0 Document Comparison:** Automated detection of cross-document engineering and specification contradictions.
- **P1 Mathematical Representations:** Topological manifold invariants and spatial DAG reading order.
- **P1 Governance & Audit:** Tamper-evident SHA-256 chained audit logs and PII redaction.

---

## 2. Directory Layout

```
demo/
├── README.md                      # This documentation
├── config/
│   ├── demo.env.example           # Environment variables for demo container
│   └── demo-policy.yaml           # Tenant budget, rate limits, and access policies
├── seed/
│   ├── documents/                 # Synthetic technical documents
│   │   ├── aegis_neural_hardware_spec_v1.txt
│   │   ├── aegis_neural_hardware_spec_v2.txt
│   │   └── aegis_enterprise_governance_whitepaper.txt
│   ├── expected-answers/          # Ground-truth QA benchmarks
│   │   ├── qa_01_hardware_throughput.json
│   │   ├── qa_02_memory_cache.json
│   │   ├── qa_03_audit_chaining.json
│   │   └── qa_04_unanswerable_cloud_backup.json
│   ├── expected-citations/        # Expected provenance & citation targets
│   │   ├── citations_v1_v2_comparison.json
│   │   └── citations_security_framework.json
│   └── manifest.json              # Machine-readable corpus index & test claims
├── scripts/
│   ├── seed_demo.py               # In-process or API seeding utility
│   ├── reset_demo.py              # Atomic workspace restore utility
│   └── verify_demo.py             # Pre-launch deployment verification harness
└── tests/
    ├── test_demo_isolation.py     # Tenant isolation & security boundary tests
    ├── test_demo_seed.py          # Seeding lifecycle and document parsing tests
    └── test_demo_reset.py         # Workspace reset and state recovery tests
```

---

## 3. The Synthetic Evaluation Corpus

To prove that AEGIS is an evidence-grounded intelligence compiler rather than a generic probabilistic chatbot, the seed corpus includes deliberate factual relationships:

| Document | Key Facts | Invariants vs Revisions |
| :--- | :--- | :--- |
| **Hardware Spec v1.0** | 450 TFLOPS FP16, 1.85 GHz, 220W TDP, 128 MB cache | Baseline specification |
| **Hardware Spec v2.0** | 620 TFLOPS FP16, 2.20 GHz, 285W TDP, 128 MB cache | **Contradicts v1.0** on clock, throughput, and TDP. **Preserves** 128 MB SRAM cache invariant. |
| **Security Whitepaper** | SHA-256 audit chaining, genesis hash, RBAC matrix, <500ms right-to-erasure | Contains security ground truth and tests **model abstention** (no cloud backup claims). |

### Deliberate Contradictions
When running **Document Comparison** on v1.0 and v2.0, AEGIS detects:
1. **Compute Throughput:** 450 TFLOPS (v1.0) vs 620 TFLOPS (v2.0)
2. **Clock Frequency:** 1.85 GHz (v1.0) vs 2.20 GHz (v2.0)
3. **Power Budget:** 220 Watts (v1.0) vs 285 Watts (v2.0)

---

## 4. Quickstart Commands

### A. Seed the Demo Workspace
```bash
# In-process seeding (standalone container)
python demo/scripts/seed_demo.py

# Or via running API
python demo/scripts/seed_demo.py --api-url http://127.0.0.1:8000 --token aegis-demo-token-sandbox
```

### B. Reset the Demo Workspace
```bash
python demo/scripts/reset_demo.py --api-url http://127.0.0.1:8000
```

### C. Run the Pre-Launch Verification Suite
```bash
python demo/scripts/verify_demo.py --api-url http://127.0.0.1:8000 --output-json verification_report.json
```

---

## 5. Security & Isolation Invariants

1. **Scoped Demo Identity:** All demo operations run within `tenant_id="demo-tenant"`.
2. **Restricted RBAC:** Demo callers hold `["viewer", "editor"]` roles only. Platform maintenance (`platform_admin`) and tenant administration (`tenant_admin`) endpoints return `403 Forbidden`.
3. **Fail-Closed Route Guard:** If `AEGIS_DEMO_MODE` is disabled, demo tokens and anonymous access are unconditionally rejected with `401 Unauthorized`.
4. **Isolated Database:** The demo deployment uses a separate SQLite path (`demo_documents.db`) and audit log (`demo_audit.log`).
