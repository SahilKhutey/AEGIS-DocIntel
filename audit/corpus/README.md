# AEGIS-DocIntel — Public Document Benchmark Corpus v1.0

**Classification:** Release Verification Benchmark Specification  
**Status:** Canonical MVP Audit Manifest (250 Documents)  
**Date:** November 2026  

---

## 1. Overview & Strategy

The AEGIS-DocIntel Public Document Benchmark Corpus v1.0 establishes an authentic, reproducible, and legally compliant 250-document evaluation corpus for rigorous verification of document processing fidelity, layout reconstruction, table parsing, retrieval grounding, fact extraction, conflict detection, and adversarial resilience.

### Corpus Composition (250 Records)

| Category / Source | Target Records | Primary Capabilities Tested | Licensing |
| :--- | :---: | :--- | :--- |
| **DocLayNet** | 40 | Bounding boxes, layout classes, reading order, headers/footers | CDLA-Permissive-1.0 |
| **PubLayNet & PubTabNet** | 30 | Scientific multi-column layouts, table cell F1, HTML structure | CDLA-Permissive-1.0 |
| **FUNSD & DocVQA** | 30 | Noisy scanned form OCR, key-value extraction, grounded Q&A | Academic & Challenge |
| **World Bank Documents** | 50 | Long-form reports, policy tables, metadata, citations | Creative Commons CC-BY 4.0 |
| **SEC EDGAR Filings** | 35 | GAAP financial tables, balance sheets, entity comparisons | US Public Domain |
| **India OGD Reports** | 35 | Government reports, bilingual terms, budget tables | GODL-India |
| **arXiv Technical Papers** | 20 | Multi-column papers, LaTeX math formulas, citation graphs | arXiv Open Access |
| **AEGIS Adversarial Fixtures** | 10 | Encrypted, corrupt, empty, rotated, PII, and conflict cases | MIT / Apache-2.0 |
| **TOTAL** | **250** | **Complete MVP Document Intelligence Lifecycle** | **Fully Audited** |

---

## 2. Directory Layout

```
audit/public-corpus-v1/
├── README.md                           # This document
├── manifest.csv                        # 250-record canonical document manifest
├── source-register.csv                 # Registry of all 10 sources, APIs, and portals
├── licence-register.csv                # Licensing compliance, redistribution & usage
├── checksums.sha256                    # SHA-256 cryptographic hashes
├── ground-truth/                       # Labelled annotations (layout, tables, QA, conflicts)
│   ├── layout_ground_truth_sample.json
│   └── table_ground_truth_sample.json
└── expected-results/                   # Quality gates and failure handling standards
    └── quality-gates-expected.json
```

---

## 3. Mandatory Quality Gates

AEGIS-DocIntel must strictly satisfy the following automated quality thresholds across the corpus:

1. **Reading Order Fidelity:** Kendall's tau $\ge 0.80$ (Target: 1.0)
2. **Table Extraction Accuracy:** Cell F1 $\ge 0.90$ (Target: 1.0)
3. **Context Budget Packing:** Token budget violation rate $= 0.0\%$ (Target: 0.0%)
4. **Submodular Knapsack Approximation:** Approximation ratio $\ge 0.316$ (Target: 0.8571)
5. **Privacy & Redaction:** Precision $\ge 0.85$, Recall $\ge 0.85$, Secret Leakage $= 0.0\%$
6. **Retrieval Grounding:** MRR $\ge 0.70$, Recall@5 $\ge 0.80$, Safe Abstention $= 100.0\%$
7. **Document Intelligence:** Fact Extraction F1 $\ge 0.85$, Conflict Recall $\ge 0.90$
8. **Adversarial Resilience:** Controlled exceptions for encrypted, corrupt, and oversized files.

---

## 4. Execution Command

To execute the automated benchmark against the available corpus fixtures:

```bash
python scripts/run_public_corpus_benchmark.py
```
