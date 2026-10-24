# AEGIS-DocIntel

**Status: Alpha / Experimental** — [![CI Status](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions) [![Coverage: 76%+](https://img.shields.io/badge/Coverage-76%25%2B-brightgreen)](STATUS.md) [![Status](https://img.shields.io/badge/Status-Alpha%20%2F%20Experimental-orange)](STATUS.md) [![License: Apache 2.0 (docprep)](https://img.shields.io/badge/License-Apache--2.0-blue)](aegis-docprep/LICENSE)

An experimental document-structuring research platform for pre-LLM context compilation, with one component validated and decoupled for immediate production usage:

---

## Start Here: `aegis-docprep`

Three real, independently-tested document-processing primitives — PII redaction, submodular context packing, and spatial reading-order extraction — extracted from this platform because they are the pieces with the strongest real-world validation (see [real benchmark results](production/performance-report/pdf_pipeline_benchmark.json) from Phase 9 testing, not marketing copy):

```bash
# Not yet published to PyPI — install from source:
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
pip install ./AEGIS-DocIntel/aegis-docprep
```

- **Dependencies**: Minimal (`numpy>=1.26.0` only). Zero deep learning or GPU dependencies required.
- **PII Detection & Redaction**: Regex and tokenization-based detection of US SSNs, Luhn-validated credit-card numbers, phone numbers (US, international E.164, local 7-digit), email addresses, API keys/tokens, and Title-Case person names. Treat it as a first-pass filter with human review, not a compliance guarantee — see [limitations](aegis-docprep/README.md#limitations-verified).
- **Submodular Context Packing**: Greedy knapsack optimization with provable $(1 - 1/e)/2 \approx 0.316$ information coverage guarantee under strict LLM token ceilings.
- **Spatial Reading-Order Recovery**: Directed topological DAG sorting over 2D bounding boxes resolving multi-column layout interleaving without heavy neural visual models.
- **Framework Integrations**: Ready-to-use LangChain Document Transformers and LlamaIndex Node Postprocessors.

See the [aegis-docprep package documentation](aegis-docprep/README.md) and [docs/docprep.md](docs/docprep.md) for quickstart guides.

---

## The Full Platform (AMDI-OS)

A 16-mathematical-domain research system for pre-LLM document structuring. Real, substantial mathematical implementations exist for most core domains (see [the honest layer-by-layer status](STATUS.md#layer-by-layer-implementation-status), sourced from the project's own internal Extended Monograph's Appendix E). Several domains remain research targets rather than production features — see [STATUS.md](STATUS.md) for exactly which is which.

The platform centers on the formal 10-tuple Master State:

$$\mathcal{D} = (P, S, G, R, F, M, T, X, H, E)$$

implemented as a strictly-typed immutable schema in [`src/core/master_state.py`](src/core/master_state.py).

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

## External Validation

**No external pilots have been completed yet.** Earlier revisions of this README described pilot case studies with specific metrics; they could not be corroborated (the repository has no pilot issues) and were removed — see [STATUS.md](STATUS.md). Pilot results will be published here only when each one links to a public GitHub issue.

Want to try it and tell us what breaks? Start with [`aegis-docprep`](aegis-docprep/README.md), then open an issue using the *pilot feedback* template. Invitation draft: [docs/pilot/recruitment_announcement.md](docs/pilot/recruitment_announcement.md).

---

## Benchmark Results (real corpus, reproducible)

Corpus: 62 real-world PDFs ([provenance](production/benchmark-dataset-real/PROVENANCE.md)). Reproduce with `python scripts/run_benchmark.py`; raw per-document results are in [`production/performance-report/`](production/performance-report/).

| Metric | Result | Notes |
|---|---|---|
| Pipeline success | 61 / 62 (98.4%) | the single failure is a deliberately password-protected PDF, rejected with a typed `EncryptedPDFError` |
| Tables detected | 220 across 29 documents | deterministic; independently re-run and matched exactly |
| Latency (reference machine) | mean 1.22 s · median 0.24 s · p95 4.3 s · max 23.6 s | absolute values vary by hardware |
| Cost vs naive text extraction | ≈ 68× slower (1.22 s vs 0.018 s mean) | table extraction currently re-parses the PDF once per page — known issue, tracked |
| Test coverage | ≥ 75%, enforced by the CI gate | [`ci.yml`](.github/workflows/ci.yml) |
| Observability | 9 Prometheus metrics wired to real call sites | [`src/observability/metrics.py`](src/observability/metrics.py) |
| Test suite | see the CI badge above | counts are deliberately not hard-coded in prose |

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

Only needs `numpy`. Not yet on PyPI, so install from a clone of this repo:

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
pip install ./aegis-docprep
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

These exact commands are run on a fresh virtual environment by CI on every push ([`scripts/cold_start_check.sh`](scripts/cold_start_check.sh)), so this path cannot silently break:

```bash
pip install -r requirements-core.txt -r requirements-dev.txt
pytest tests/
```

Supported Python: **3.12 and 3.13** (the versions CI tests). Dependencies are defined once in `pyproject.toml`; the `requirements-*.txt` files are generated from it (`python scripts/check_dependency_sync.py --write`).

OCR tests additionally use `pytesseract`; real OCR needs the `tesseract` system binary.

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
- [Architecture & Master State](docs/Architecture.md)
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