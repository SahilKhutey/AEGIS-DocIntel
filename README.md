# AEGIS-DocIntel

**Status: Alpha / Experimental** — [![CI Status](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions) [![Coverage: 76%+](https://img.shields.io/badge/Coverage-76%25%2B-brightgreen)](STATUS.md) [![Status](https://img.shields.io/badge/Status-Alpha%20%2F%20Experimental-orange)](STATUS.md) [![License: Apache 2.0 (docprep)](https://img.shields.io/badge/License-Apache--2.0-blue)](aegis-docprep/LICENSE)

An experimental document-structuring research platform for pre-LLM context compilation, with one component validated and decoupled for immediate production usage:

---

## Start Here: `aegis-docprep`

Three real, independently-tested document-processing primitives — PII redaction, submodular context packing, and spatial reading-order extraction — extracted from this platform because they are the pieces with the strongest real-world validation (see [real benchmark results](production/performance-report/pdf_pipeline_benchmark.json) from Phase 9 testing, not marketing copy):

```bash
pip install aegis-docprep
```

- **Dependencies**: Minimal (`numpy>=1.26.0` only). Zero deep learning or GPU dependencies required.
- **PII Redaction**: Zero-overhead deterministic redaction for SSNs, credit cards, emails, phone numbers, and API tokens with cryptographic verification reports.
- **Submodular Context Packing**: Greedy knapsack approximation with provable $(1 - 1/e)$ information coverage guarantees under strict LLM token ceilings.
- **Spatial Reading-Order Recovery**: Directed topological DAG sorting over 2D bounding boxes resolving multi-column layout interleaving without heavy neural visual models.
- **Framework Integrations**: Ready-to-use LangChain Document Transformers and LlamaIndex Node Postprocessors.

See the [aegis-docprep package documentation](aegis-docprep/README.md) and [docs/docprep.md](docs/docprep.md) for quickstart guides.

---

## The Full Platform (AMDI-OS)

A 16-mathematical-domain research system for pre-LLM document structuring. Real, substantial mathematical implementations exist for most core domains (see [the honest layer-by-layer status](STATUS.md#layer-by-layer-implementation-status), sourced from the project's own internal Extended Monograph's Appendix E). Several domains remain research targets rather than production features — see [STATUS.md](STATUS.md) for exactly which is which.

The platform centers on the formal 10-tuple Master State:

$$\mathcal{D} = (P, S, G, R, F, M, T, X, H, E)$$

implemented as a strictly-typed immutable schema in [`src/models/master_state.py`](src/models/master_state.py).

```
  Raw Document (PDF, DOCX, Scans)
               │
               ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              AEGIS Master State Extraction Pipeline         │
  │                                                             │
  │  1. Spatial Bounding Boxes (P)  ──► PyMuPDF extraction      │
  │  2. Reading-Order DAG (G)       ──► Topological sort        │
  │  3. Table Matrices (T)          ──► PDFPlumber bbox mapping │
  │  4. PII Redaction Layer (R)     ──► Deterministic masks     │
  │  5. Submodular Chunks (E)       ──► Knapsack budget solver  │
  └─────────────────────────────────────────────────────────────┘
               │
               ▼
  Master State D = (P, S, G, R, F, M, T, X, H, E)
               │
               ▼
  Token-Bounded, Non-Redundant Context Injection for LLMs
```

---

## What Pilots Have Found (Phase 15 External Evaluations)

During Phase 15, structured evaluations were conducted with external developers across real document corpora:

1. **FinTech Support Chat Sanitization (Alex M., Senior Backend Engineer)**:
   - Evaluated `aegis-docprep` PII redaction and context packing on 45 customer support transcripts.
   - **Accuracy**: 100% masking of valid SSNs (14/14) and credit cards (8/8) with Luhn validation.
   - **Token Compression**: Reduced total prompt tokens from 18,450 to 10,920 (**40.8% net reduction**).
2. **Legal SEC Form 10-K Exhibits (Sarah T., Solutions Architect)**:
   - Evaluated spatial reading-order recovery on 18 pages of 2-column legal filings.
   - **Topological Sorting**: Corrected multi-column text interleaving across 17 of 18 pages.
3. **Avionics Technical Manuals (Marcus K., AI Systems Engineer)**:
   - Evaluated submodular knapsack context packing under a hard 1,500 token budget.
   - **Information Diversity**: Replaced redundant overview chunks with distinct electrical specification tables and emergency procedures, cutting prompt latency by 28%.

Read the full case studies, metrics, and reported edge cases in [`docs/pilot/case_studies.md`](docs/pilot/case_studies.md).

---

## Verified Benchmark Results (Phase 9 Real Corpus)

In Phase 9, synthetic benchmark documents were retired and quarantined into `_unverified_archive/`. All reported numbers are measured against the authentic 62-document test corpus in [`production/benchmark-dataset-real/`](production/benchmark-dataset-real/):

| Metric | Measured Result | Verification Artifact |
|---|---|---|
| **Unit Test Pass Count** | 944 passed, 0 failed | `tests/` test run |
| **Code Coverage** | 76.5%+ core package | `pytest --cov=src` gate |
| **Ingestion Throughput** | 71–119ms per 14-page PDF | `production/benchmark-dataset-real/timing_results.csv` |
| **Table Extraction** | 220 tables across 29 docs | `tests/test_table_extraction_regression.py` |
| **Memory Consumption** | 0.14 MB peak per document | `tracemalloc` memory audit |
| **Observability** | 9 Prometheus metrics wired | Endpoint `/metrics` & Grafana dashboards |

---

## Roadmap

Per the project's own internal Appendix E status matrix (Phase 5 finding):

- **Hardened Today**: Reading-order graph, elastic chunker, knapsack solvers, spectral embedder, tabular compiler, PII redaction, submodular context packing — these are real, tested, and what `aegis-docprep` packages.
- **Real but Partially Mock**: Semantic (LayoutLM-class) encoding — works when `sentence-transformers` is installed, falls back to clearly-flagged deterministic feature vectors otherwise (`MasterState.semantic_status = 'mock_fallback'`).
- **Research Targets, Not Yet Production Features**: Persistent-homology-based hierarchy (topology's $H$ layer), full distributed production multi-cluster topology, end-to-end benchmark evaluation at scale. These are documented as targets because they are active research areas — not because we claim they already work in production.

---

## Installation & Cold-Start

Follow the tiered installation structure to avoid downloading unnecessary dependencies:

### 1. Minimal Primitives (`aegis-docprep`)
```bash
pip install aegis-docprep
```

### 2. Full Platform Core (Web API, Graph Engines, Math)
```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
python -m venv venv
# Linux / macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install core runtime
pip install -r requirements-core.txt
```

### 3. Developer & Test Suite (Cold-Start Safe)
To run the full 944+ unit test suite without collection errors:
```bash
pip install -r requirements-core.txt -r requirements-dev.txt
pytest tests/
```

### 4. Deep Learning Optional Extras
```bash
pip install -r requirements-ml.txt
```

---

## Documentation

Full documentation is available via Material for MkDocs:

```bash
# Build and preview local documentation
pip install mkdocs mkdocs-material
mkdocs serve
```

Browse the documentation sections:
- [Status & 16-Phase Journey](docs/status.md)
- [aegis-docprep Guide](docs/docprep.md)
- [Architecture & Master State](docs/architecture.md)
- [Installation Guide](docs/installation.md)
- [REST API Reference](docs/api.md)
- [Compliance Gap Analysis](docs/compliance.md)
- [Security Policy & Audit](docs/security.md)
- [Support Policy](docs/support.md)
- [Contributing Guidelines](CONTRIBUTING.md)

---

## License & Governance

- **`aegis-docprep`**: Licensed under the permissive **[Apache License 2.0](aegis-docprep/LICENSE)**.
- **Full AEGIS-DocIntel Platform**: Available under evaluation and research terms per **[LICENSE](LICENSE)**.