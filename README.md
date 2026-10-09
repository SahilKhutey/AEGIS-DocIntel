# AEGIS-DocIntel / AMDI-OS

**Pre-LLM Mathematical Context Compiler & Document Intelligence Toolkit**

[![CI](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/badge/coverage-80%25-green.svg)]()
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%20%7C%203.13-green.svg)]()
[![Status](https://img.shields.io/badge/Status-Alpha_/_Experimental-orange.svg)]()

---

> **Project status (updated October 2026):** This is an active research/engineering
> project with a substantial, independently-testable mathematical core (see
> `STATUS.md`). Prior versions of this README and the `production/` folder
> included fabricated security audit and benchmark documents; these have been
> moved to `_unverified_archive/` and should not be relied upon. See
> [STATUS.md](STATUS.md) for exactly what is and isn't currently verified.
>
> **Looking for a lightweight, focused library?** Check out [`aegis-docprep`](aegis-docprep/) (`pip install aegis-docprep`), our standalone, minimal-dependency package (only `numpy` required) extracting the three most verified primitives: PII redaction, submodular context packing, and spatial reading-order extraction. Integrates directly with LangChain and LlamaIndex.

---

## Executive Overview

**AEGIS-DocIntel** functions as a **Pre-LLM Structural & Mathematical Compiler**. 

Most Retrieval-Augmented Generation (RAG) and document AI systems feed raw or naively chunked text directly into LLM prompts. This causes:
1. **Layout corruption**: Multi-column text, headers, and tables get scrambled.
2. **Context redundancy**: Top-$k$ vector retrieval selects redundant chunks with overlapping information, wasting token budget.
3. **Data leakage**: Unchecked PII is transmitted to external model providers.
4. **Context window degradation**: Excessive prompt size inflates inference costs and triggers "Lost in the Middle" attention degradation.

AEGIS-DocIntel solves this by processing unstructured documents through mathematical and structural filters **before** context is dispatched to language models:

```
  Raw Document
 (PDF, DOCX, XLSX)
         │
         ▼
  ┌─────────────────────────────────────────────────────────────┐
  │              AEGIS Context Compilation Pipeline             │
  │                                                             │
  │  1. Spatial Layout DAG       ──► Reading order determinism   │
  │  2. Entity & PII Scrubber   ──► Zero-leakage sanitization   │
  │  3. Submodular Knapsack     ──► (1 - 1/e) optimal context   │
  └─────────────────────────────────────────────────────────────┘
         │
         ▼
  Token-Bounded, Non-Redundant, Provenance-Tagged Context
         │
         ▼
  Downstream LLM (OpenAI / Anthropic / Gemini / Local vLLM)
```

---

## Core Verified Capabilities

- **Submodular Knapsack Context Optimization (`src/engines/optimization/`)**:
  - Implements the modified density greedy algorithm with best single-item check.
  - Guarantees the classical $(1 - 1/e) \approx 0.632$ approximation bound under strict token capacity constraints $B$.
  - Maximizes unique concept coverage while minimizing token expenditure.
- **Spatial Reading-Order DAG (`src/engines/layout/`, `src/engines/hierarchy/`)**:
  - Extracts 2D bounding boxes and constructs an acyclic directed graph of text blocks.
  - Linearizes blocks via topological sorting (Kahn's algorithm) to prevent multi-column interleaving.
- **Deterministic PII Redaction & Sanitization (`src/compliance/`)**:
  - Policy-driven token masking (`<US_SSN_REDACTED>`, `<EMAIL_REDACTED>`) before API dispatch.
- **Probabilistic Entity Resolution (`src/entity/`)**:
  - Fellegi-Sunter record linkage and NetworkX equivalence graph clustering.
- **Structural Tree Diff Engine (`src/versioning/`)**:
  - APTED (All-Path Tree Edit Distance) implementation for hierarchical contract and document version comparisons.
- **Multimodal Document Parsers (`src/ingestion/`)**:
  - Extractors for PDF (PyMuPDF, pdfplumber), DOCX, XLSX, PPTX, images, and audio/speech.

---

## Master Mathematical Intelligence Domains

The framework structures document analysis across formal mathematical formulations in `src/math_concepts/`:

| Index | Domain | Primary Formulation / Implementation | Module Path |
| :-: | :--- | :--- | :--- |
| **1** | **Optimization** | Monotone submodular knapsack ($(1 - 1/e)$ bound), MCKP Dynamic Programming | `src/math_concepts/optimization.py` |
| **2** | **Graph Theory** | Spatial Reading Order DAG, PageRank power iteration, hypergraphs | `src/math_concepts/graph_theory.py` |
| **3** | **Spectral** | Graph Laplacian spectrum $L = D - A$, Fiedler vector bisection | `src/math_concepts/spectral.py` |
| **4** | **Topology** | Simplicial complexes, Betti numbers $H_0, H_1, H_2$ | `src/math_concepts/topology.py` |
| **5** | **Information Theory** | Shannon entropy, mutual information, Information Bottleneck | `src/math_concepts/information_theory.py` |
| **6** | **Linear Algebra** | Singular Value Decomposition ($A = U \Sigma V^T$), low-rank approximation | `src/math_concepts/linear_algebra.py` |
| **7** | **Statistics** | Covariance matrix $\Sigma$, Pearson correlation, distribution moments | `src/math_concepts/statistics.py` |
| **8** | **Probability** | Bayesian posterior updating $P(\theta \mid D) \propto P(D \mid \theta) P(\theta)$ | `src/math_concepts/probability.py` |

*(Experimental domains including physics analogies and dynamical systems are being benchmarked for empirical utility under Phase 6).*

---

## Installation

### Recommended: Standalone Lightweight Toolkit (`aegis-docprep`)
If you only need the validated pre-LLM primitives (PII redaction, submodular context packing, spatial reading order) without the 16-domain platform or infrastructure:
```bash
pip install aegis-docprep
```
*Single dependency:* `numpy>=1.26.0`. No heavy ML frameworks, no torch, no FastAPI required.

---

### Full Monorepo Platform Installation

#### Prerequisites
- Python 3.12 or 3.13 (verified in CI)

#### Option 1 — Core Platform (recommended to start)
Runs the API server, document ingestion pipeline, and core mathematical engines.
```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-core.txt
```

#### Option 2 — Development & Test Setup (Cold-Start Safe)
To run the full unit test suite (1,060+ tests), install development tooling (`pytest`, `hypothesis`, etc.):
```bash
pip install -r requirements-core.txt -r requirements-dev.txt
pytest tests/
```

#### Option 3 — Full Platform with Embeddings & Vector Search
Enables local dense vector search and semantic caching (pulls in `torch` via `sentence-transformers`):
```bash
pip install -r requirements-core.txt -r requirements-ml.txt
```

#### Option 4 — Exact Reproducible Pinned Build
```bash
pip install -r requirements-core.lock.txt
```

## Compatibility
Tested and verified on: Python 3.12, 3.13 (Linux, via CI; Windows local). macOS support is expected to work but is not yet covered by automated tests.

---

## Quickstart: Python Context Compilation

```python
from src.engines.optimization.optimization_engine import OptimizationEngine

# Initialize the optimization engine
engine = OptimizationEngine(alpha=0.5, beta=0.25, gamma=0.25)

# Example: Submodular Knapsack Context Packing
# Given candidate chunks with extracted concepts and token weights:
item_concepts = [
    {"revenue", "growth", "q4"},
    {"revenue", "guidance"},
    {"operating_expenses", "ebitda"},
    {"risk_factors", "debt"},
]
concept_weights = {
    "revenue": 2.0,
    "growth": 1.5,
    "q4": 1.0,
    "guidance": 1.8,
    "operating_expenses": 1.2,
    "ebitda": 1.5,
    "risk_factors": 1.0,
    "debt": 1.0,
}
token_weights = [150, 100, 200, 180]
token_budget = 300

# Pack optimal subset guaranteeing (1 - 1/e) information density
result = engine.solve_submodular_knapsack(
    item_concepts=item_concepts,
    concept_weights=concept_weights,
    item_weights=token_weights,
    capacity=token_budget,
)

print(f"Selected Chunks: {result.selected_indices}")
print(f"Covered Information Value: {result.total_value}")
print(f"Total Tokens Used: {result.total_tokens} / {token_budget}")
```

---

## REST API Overview

Start the FastAPI application:
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive OpenAPI documentation will be accessible at **`http://localhost:8000/docs`**.

Key endpoints:
* `POST /v1/documents/upload` — Ingest document into intermediate state representation.
* `POST /v1/query/` — Execute context-optimized hybrid RAG query.
* `POST /v1/advanced/compliance/pii-scan` — Scan and mask sensitive PII tokens.
* `POST /v1/advanced/entity/resolve` — Probabilistic entity clustering via Fellegi-Sunter.
* `POST /v1/advanced/versioning/diff` — Structural APTED tree edit distance comparison.
* `POST /v1/advanced/export/llm-optimized` — Export compact Markdown / minified JSON context.

---

## Project Structure

```text
AEGIS-DocIntel/
├── src/
│   ├── api/                   # FastAPI routes, schemas, and routers
│   ├── compliance/            # PII detection & policy redaction engine
│   ├── connectors/            # LLM provider connectors (OpenAI, Anthropic, Gemini, etc.)
│   ├── core/                  # DocumentObject, Master State D, orchestrator
│   ├── engines/               # Optimization, layout DAG, retrieval, and math engines
│   ├── entity/                # Cross-document entity resolution (Fellegi-Sunter)
│   ├── export/                # Token-optimized Markdown & JSON exporters
│   ├── ingestion/             # PDF, DOCX, XLSX, PPTX, image, and audio loaders
│   ├── math_concepts/         # MasterUnifiedMathEngine & mathematical domains
│   └── versioning/            # Structural diff engine (APTED tree-edit distance)
├── tests/                     # 1,060+ passing pytest unit test suite
├── docs/                      # Technical specifications, math formulations, and ROADMAP.md
├── _unverified_archive/       # Quarantined legacy mock audit/benchmark files (Phase 1)
├── STATUS.md                  # Verification and public credibility disclosure
└── requirements.txt           # Verified dependency manifest
```

---

## Roadmap & Governance

The repository is governed by the **[16-Phase Development & Remediation Roadmap](docs/ROADMAP.md)**:
- **Phase 1 (Complete):** Truth Audit & Public Credibility Reset.
- **Phase 2 (In Progress):** Build & Dependency Repair (`requirements-*.txt`, `pyproject.toml`).
- **Phase 3:** Continuous Integration & Automated Multi-OS Testing.
- **Phase 4:** Architectural Deduplication & Module Consolidation.
- **Phases 5–6:** Core Schema Unification & Test Suite Hardening.
- **Phases 7–9:** Real-World Corpus Ingestion & Public Benchmark Suite.
- **Phases 10–12:** Real Security Scans, Compliance Gap Analysis & Observability.
- **Phases 13–16:** API Stabilization, Focused Packaging (`pip install aegis-docintel`), Pilots & GTM.

---

## License & Authorship

**Sahil Khutey**  
For license terms, see [LICENSE](LICENSE).