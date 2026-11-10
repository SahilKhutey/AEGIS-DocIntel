# AEGIS-DocIntel

**Adaptive Mathematical Document Intelligence Operating System**

[![CI Status](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions)
[![Coverage: 76%+](https://img.shields.io/badge/Coverage-76%25%2B-brightgreen)](STATUS.md)
[![Status: Alpha / Experimental](https://img.shields.io/badge/Status-Alpha%20%2F%20Experimental-orange)](STATUS.md)
[![License: Apache 2.0 (docprep)](https://img.shields.io/badge/License-Apache--2.0-blue)](aegis-docprep/LICENSE)

AEGIS-DocIntel is a dual-tier document intelligence platform combining mathematically rigorous pre-LLM document structuring primitives with an enterprise-grade grounded intelligence and sovereign governance workbench:

1. **`aegis-docprep`**: Decoupled, zero-GPU Python primitives (PII redaction, reading-order recovery, and submodular context packing) ready for immediate integration.
2. **Enterprise Workbench (`web/`)**: Next.js 16 (App Router) and React 19 interface featuring grounded natural-language Q&A, citation previews, human-in-the-loop review queues, conflict resolution matrices, and cycle-safe DAG observability.
3. **Core Operating System (AMDI-OS)**: 16-mathematical-domain document compiler modeling documents into the formal 10-tuple Master State $\mathcal{D} = (P, S, G, R, F, M, T, X, H, E)$ with FastAPI REST endpoints and resilient background worker orchestration.

---

## 1. Start Here: `aegis-docprep`

Three real, independently-tested document-processing primitives extracted from this platform for minimal-overhead pipeline integration (see [real benchmark results](production/performance-report/pdf_pipeline_benchmark.json) from Phase 9 testing, not marketing copy):

```bash
# Not yet published to PyPI — install from source:
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
pip install ./AEGIS-DocIntel/aegis-docprep
```

- **Zero Heavy Dependencies**: Minimal runtime (`numpy>=1.26.0` only). Zero deep learning or GPU requirements.
- **Deterministic PII Redaction**: Regex and tokenization detection for US SSNs, Luhn-validated credit cards, international E.164 and local phone numbers, email addresses, API tokens, and Title-Case names. Treat as a first-pass filter with human review, not a compliance guarantee — see [limitations](aegis-docprep/README.md#limitations-verified).
- **Submodular Context Packing**: Greedy knapsack optimization with provable $(1 - 1/e)/2 \approx 0.316$ information coverage guarantee under strict LLM token ceilings.
- **Spatial Reading-Order Recovery**: Directed topological DAG sorting over 2D bounding boxes resolving multi-column layout interleaving without heavy neural visual models.
- **Framework Integrations**: Ready-to-use LangChain Document Transformers and LlamaIndex Node Postprocessors.

See the [aegis-docprep package documentation](aegis-docprep/README.md) and [docs/docprep.md](docs/docprep.md) for quickstart guides.

---

## 2. Enterprise UI/UX Workbench (`web/`)

The AEGIS-DocIntel Workbench is built on Next.js 16.4.3, React 19, TypeScript 5, and Tailwind CSS. It connects authorized users to document intelligence, evidence verification, and sovereign oversight:

```
                  ┌─────────────────────────────────────────────────────────┐
                  │          AEGIS-DocIntel Application Shell               │
                  │   Global Search (Ctrl+K) · Workspace / Tenant Selector  │
                  └────────────┬───────────────────────────────┬────────────┘
                               │                               │
             ┌─────────────────┴───────────────┐ ┌─────────────┴───────────────┐
             │       Core & Intelligence       │ │    Governance & Advanced     │
             ├─────────────────────────────────┤ ├─────────────────────────────┤
             │ • Document Library & Inspector  │ │ • Review Queue & SLA Badges │
             │ • Processing Monitor & Queues   │ │ • Fact Verification Matrix  │
             │ • Ask AEGIS Grounded Q&A        │ │ • Sovereign Decision Dialog │
             │ • Exact Citation Highlighting   │ │ • Cycle-Safe Pipeline DAG   │
             │ • Side-by-Side Diff Workbench   │ │ • Telemetry Latency Gauges  │
             └─────────────────────────────────┘ └─────────────────────────────┘
```

### Core Workbench Capabilities

- **Ask AEGIS Grounded Q&A**: Natural-language question answering strictly bound to verbatim document chunks with click-to-preview page citations and spatial bounding boxes.
- **Sovereign Governance Layer**: Human oversight layer allowing verified reviewers to confirm, dispute, or override model-derived facts with cryptographic signatures and immutable audit logging.
- **Document Comparison Workbench**: Side-by-side diffing identifying semantic deviations, conflicting claims, and tabular changes across document versions.
- **Mathematical Observability**: Formatted KaTeX equation rendering, embedding vector similarity matrices, and live pipeline stage latency telemetry.
- **WCAG 2.2 Level AA Accessibility**: 100% compliant contrast ratios (>=4.5:1 text, >=3:1 UI), keyboard navigation focus traps, and screen reader landmarks.

```bash
# Launch the web workbench locally:
cd web
npm install
npm run dev        # Runs on http://localhost:3000
npm run test       # Vitest unit & component test suite (46 suites, 220 tests)
npm run test:e2e   # Playwright browser regression test suite (87 tests)
```

See the full [UI/UX Architecture Dossier](docs/ui-ux/README.md) for specifications across WP-UI-01 through WP-UI-08.

---

## 3. The Full Platform (AMDI-OS)

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

## 4. External Validation

**No external pilots have been completed yet.** Earlier revisions of this README described pilot case studies with specific metrics; they could not be corroborated (the repository has no pilot issues) and were removed — see [STATUS.md](STATUS.md). Pilot results will be published here only when each one links to a public GitHub issue.

Want to try it and tell us what breaks? Start with [`aegis-docprep`](aegis-docprep/README.md), then open an issue using the *pilot feedback* template. Invitation draft: [docs/pilot/recruitment_announcement.md](docs/pilot/recruitment_announcement.md).

---

## 5. Benchmark Results (Real Corpus, Reproducible)

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

### P2 AI Quality & Evaluation Framework

AEGIS-DocIntel includes a versioned evaluation framework in [`evaluation/`](evaluation/README.md) testing document extraction fidelity, context packing invariants, PII redaction precision/recall, and retrieval grounding:

| Domain | Key Metric | Gate | Baseline Result |
|---|---|---|---|
| **Extraction Fidelity** | Reading Order Kendall's $\tau$ | $\ge 0.80$ | $1.00$ |
| **Table Reconstruction** | Table Cell Grid F1 | $\ge 0.90$ | $1.00$ |
| **Context Packing** | Token Budget Violation Rate | $0.0\%$ | $0.0\%$ |
| **Submodular Bound** | Min Approximation Ratio vs Optimal | $\ge 0.316$ | $0.857$ |
| **PII Redaction** | Precision / Recall on Labeled Corpus | $\ge 0.85$ | $1.00 / 1.00$ |
| **Secret Protection** | Downstream Raw Secret Leakage | $0.0\%$ | $0.0\%$ |
| **Retrieval Accuracy** | MRR / Recall@5 | $\ge 0.70 / \ge 0.80$ | $1.00 / 1.00$ |
| **Hallucination Defense** | Abstention on Unanswerable Queries | $100.0\%$ | $100.0\%$ |

Run the unified evaluation suite locally:
```bash
python evaluation/scripts/run_all.py --fail-under-gates
```

---

## 6. Installation & Cold-Start

Follow the tiered installation structure to avoid downloading unnecessary dependencies:

### Tier 1: Minimal Primitives (`aegis-docprep`)

Requires only `numpy>=1.26.0`:

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
pip install ./aegis-docprep
```

### Tier 2: Full Platform Core (FastAPI REST Server & Worker Engine)

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

# Start backend REST API server on http://localhost:8000
python -m uvicorn src.main:app --port 8000
```

### Tier 3: Developer & Test Suite (Cold-Start Safe)

These exact commands are run on a fresh virtual environment by CI on every push ([`scripts/cold_start_check.sh`](scripts/cold_start_check.sh)), so this path cannot silently break:

```bash
pip install -r requirements-core.txt -r requirements-dev.txt
pytest tests/
```

Supported Python: **3.12** (canonical runtime, validated in CI PR gate) and **3.13** (experimental / compatibility sweep in scheduled maintenance). Dependencies are defined in `pyproject.toml`; `requirements-*.txt` files are synchronized from it (`python scripts/check_dependency_sync.py --write`).

### Tier 4: Background Job Worker Verification Drill

Verify the asynchronous background task queue, lease renewal heartbeats, and exponential retry policy:

```bash
python scripts/verify_jobs_run.py
```

### Tier 5: Modern Web Workbench (`web/`)

Run the Next.js 16 frontend workbench:

```bash
cd web
npm install
npm run dev        # Runs on http://localhost:3000
npm run test       # Runs Vitest unit & component test suite
npm run test:e2e   # Runs Playwright browser regression test suite
```

---

## 7. Documentation Architecture

Comprehensive documentation is available locally and via Material for MkDocs:

```bash
# Build and preview local documentation
pip install mkdocs mkdocs-material
mkdocs serve
```

### Primary Documentation Guides

- [**Enterprise UI/UX Workbench Dossier**](docs/ui-ux/README.md): Master index for WP-UI-01 through WP-UI-08.
- [**System Status & Roadmap**](docs/status.md): Layer-by-layer status, audit history, and active milestones.
- [**aegis-docprep Package Guide**](docs/docprep.md): Standalone library quickstart and framework recipes.
- [**Platform Architecture & Master State**](docs/Architecture.md): Formal mathematical specification of $\mathcal{D}$.
- [**Multi-Tenant Isolation Architecture**](docs/architecture/tenant-isolation.md): Cryptographic tenant separation and IDOR defenses.
- [**Data Governance & Lifecycle Policies**](docs/architecture/data-governance.md): Hard-deletion guarantees and retention policies.
- [**REST API Reference**](docs/api.md): Complete OpenAPI 3.1.0 endpoints and schema contracts.
- [**Enterprise Threat Model**](docs/security/threat-model.md): Threat vectors, boundary trust assumptions, and mitigation controls.
- [**Security Policy & Vulnerability Disclosure**](docs/security.md): Security practices and responsible disclosure process.
- [**Contributing Guidelines**](CONTRIBUTING.md): Engineering standards, code conventions, and pull request procedures.

---

## 8. License & Governance

- **`aegis-docprep`**: Licensed under the permissive **[Apache License 2.0](aegis-docprep/LICENSE)**.
- **Full AEGIS-DocIntel Platform**: Available under evaluation and research terms per **[LICENSE](LICENSE)**.
