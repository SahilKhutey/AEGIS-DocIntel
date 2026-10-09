# AEGIS-DocIntel

**Adaptive Mathematical Document Intelligence Operating System**

[![CI Status](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/test.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions)
[![Coverage: 76%+](https://img.shields.io/badge/Coverage-76%25%2B-brightgreen)](status.md)
[![Status: Alpha / Experimental](https://img.shields.io/badge/Status-Alpha%20%2F%20Experimental-orange)](status.md)
[![License: Apache 2.0 (docprep)](https://img.shields.io/badge/License-Apache--2.0-blue)](docprep.md)

AEGIS-DocIntel is an experimental document-structuring research platform designed to transform complex, multi-page documents (PDFs, multi-column articles, financial tables, unstructured scans) into structured mathematical representations prior to Large Language Model (LLM) ingestion.

---

## Start Here: `aegis-docprep`

If you are looking for validated, low-risk tools to use in your pipeline today, start with [`aegis-docprep`](docprep.md).

Extracted directly from the platform during Phase 14, `aegis-docprep` provides three decoupled, independently-tested primitives with minimal dependencies (**NumPy only**):

1. **PII Redaction Engine**: Zero-third-party-dependency deterministic compliance engine scrubbing Email, Phone, SSN, Credit Cards, and API keys with structured verification.
2. **Submodular Context Packer**: Greedy submodular knapsack solver optimizing information coverage under hard LLM token budgets.
3. **Spatial Reading-Order Extractor**: Directed topological sort over 2D bounding boxes resolving multi-column and layout ordering without neural overhead.

```bash
# Minimal installation (NumPy only)
pip install aegis-docprep
```

```python
from aegis_docprep import RedactionEngine, SubmodularContextPacker, GraphReadingOrder

# 1. PII Redaction
redactor = RedactionEngine()
clean_text = redactor.redact("Contact jane.doe@corp.internal for access.")

# 2. Reading Order Extraction
sorter = GraphReadingOrder()
ordered_blocks = sorter.sort_blocks(raw_blocks)

# 3. Context Packing
packer = SubmodularContextPacker(token_limit=1024)
packed_context = packer.pack(documents=ordered_blocks)
```

See the [aegis-docprep Guide](docprep.md) for LangChain and LlamaIndex integration recipes.

---

## The Full Platform (AMDI-OS)

The full platform represents a 16-mathematical-domain operating system built around the formal 10-tuple Master State:

$$\mathcal{D} = (P, S, G, R, F, M, T, X, H, E)$$

The platform integrates reading-order graphs, spectral embeddings, elastic token chunking, and dual-layer caching.

> **Important Status Notice:** The full platform is currently classified as **Alpha / Experimental**. While the mathematical formalisms and core engines are implemented and verified across 944+ unit tests, peripheral modules (LayoutLM semantic encoders, distributed persistence, and persistent homology) are either mock-backed or active research targets. See [Status & 16-Phase Journey](status.md) for the exact layer-by-layer audit.

---

## Key Verified Results (Phase 9 Real Benchmark)

In Phase 9, synthetic benchmark claims were permanently replaced with measurements from a real 62-document corpus (`production/benchmark-dataset-real/`):

| Metric | Real Verified Value | Status |
|---|---|---|
| **Unit Test Suite** | 944 passed, 0 failed | Verified across Python 3.10–3.12 |
| **Test Coverage** | 76.5%+ core package | Verified via pytest-cov |
| **Context Compression** | 35.8% token savings | Submodular knapsack optimization |
| **PII Redaction Precision** | 100% on standard identifiers | SSN, CC, Email, Phone, Keys |
| **Table Extraction** | Fixed compound API bug | PDFPlumber bbox coordinate conversion |
| **Observability** | 9 Prometheus metrics wired | Full scraping endpoint at `/metrics` |

---

## Documentation Navigation

- [**Status & 16-Phase Journey**](status.md): Complete audit of what was broken, what was fixed, and the layer-by-layer roadmap.
- [**aegis-docprep Package**](docprep.md): The decoupled standalone package ready for production pipelines.
- [**Architecture & Master State**](architecture.md): Formal mathematical specification of $\mathcal{D}$ and the engine hierarchy.
- [**Installation & Cold-Start**](installation.md): Tiered requirements (`core`, `dev`, `ml`, `infra`) and clean cold-start execution.
- [**API Reference**](api.md): Verified FastAPI endpoints and SDK alignment.
- [**Compliance Gap Analysis**](compliance.md): Audit against GDPR, HIPAA, and SOC 2 requirements.
- [**Security Policy & Audit**](security.md): Internal vulnerability findings and reporting guidelines.
- [**Pilot Case Studies**](pilot_cases.md): Real feedback and performance metrics from pilot deployments.
