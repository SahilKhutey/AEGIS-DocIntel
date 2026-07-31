<div align="center">

# AEGIS-DocIntel / AMDI-OS
**Adaptive Mathematical Document Intelligence Operating System**

[![License: Proprietary](https://img.shields.io/badge/License-Proprietary-blue.svg)](./LICENSE)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)](#installation)
[![CI](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml/badge.svg)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml)
[![Tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/SahilKhutey/AEGIS-DocIntel/master/.github/test-count.json)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/SahilKhutey/AEGIS-DocIntel?label=coverage)](https://codecov.io/gh/SahilKhutey/AEGIS-DocIntel)
[![Code style: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/SahilKhutey/AEGIS-DocIntel/master/.github/ruff-status.json)](https://github.com/SahilKhutey/AEGIS-DocIntel/actions/workflows/ci.yml)

*A compiler that converts human documents, tables, images, and audio into mathematical objects before any AI model sees them.*

</div>

---

## What this is

A **pre-LLM document intelligence operating system**. Instead of feeding a 200-page
PDF (≈130k tokens) straight to a model, AEGIS-DocIntel converts it into a
synchronized set of mathematical representations — topology, spectra, tensors,
graphs, layout, frequency — and exports a token-optimized context window.

**What is verified at this commit:**
- 12 mathematical engines import and pass unit tests (FFT-based layout analysis,
  graph Laplacian, eigendecomposition, BM25, spatial DAG reading order).
- FastAPI service runs (`uvicorn amdi.api.app:create_app --factory`).
- Modular layout under `src/amdi/`, installable via `pip install -e .`.

**What is a research target, not a measured result:**
- 50–80% token reduction
- >95% information retention
- >95% citation accuracy

Numbers in the papers are projected, not measured. The badge above reflects
the *actual* `pytest --collect-only` count from CI.

## Multi-language SDKs

AEGIS-DocIntel is contract-first. The full API surface is defined in
[`proto/amdi.proto`](./proto/amdi.proto) and generated into four first-class
SDKs:

| Language    | Path                            | Install                        |
| ----------- | ------------------------------- | ------------------------------ |
| Python      | [`sdks/python`](./sdks/python) | `pip install amdi-sdk`        |
| TypeScript  | [`sdks/typescript`](./sdks/typescript) | `npm install @amdi/sdk` |
| Java        | [`sdks/java`](./sdks/java)     | `io.amdi:amdi-sdk:0.2.0`       |
| C++         | [`sdks/cpp`](./sdks/cpp)       | CMake: `add_subdirectory(sdks/cpp)` |

```python
# Python — sync
from amdi_sdk import AmdiClient
client = AmdiClient("localhost:50051", api_key="...")
print(client.health().serving_state)

# Python — async
from amdi_sdk.aio import AsyncAmdiClient
async with AsyncAmdiClient("localhost:50051") as c:
    print((await c.health()).serving_state)
```

---

## Architecture in one picture


```
 INGEST (PDF/DOCX/XLSX/PPTX/IMG/AUD)
   │
   ▼
 NORMALIZATION  ──▶  preprocessing, layout decomposition
   │
   ▼
 12 ENGINES (parallel)  ──▶  semantic, geometry, frequency, matrix,
 │                            template, recurrence, graph, topology,
 │                            spectral, tensor, info-physics, retrieval
   ▼
 FUSION  ──▶  weighted scoring + monotone submodular knapsack
   │
   ▼
 MEMORY (L0–L5 hierarchical cache)
   │
   ▼
 HYBRID RETRIEVAL (7 methods, RRF fusion + reranker)
   │
   ▼
 LLM-OPTIMIZED EXPORTER  ──▶  compact .md or minified .json
   │
   ▼
 AI AGENT CONNECTORS  (ChatGPT / Gemini / Claude / DeepSeek / Qwen / local)
```

Formal guarantees (see [`docs/Mathematics.md`](./docs/Mathematics.md)):
- **Thm 6.1** Spatial DAG Acyclicity · **Thm 6.2** Kahn Topological Determinism
- **Thm 9.1** ½-Knapsack Bound · **Monotone Submodular (1 − 1/e)** Approximation

---

## Installation

### Requirements
- Python **3.12+**
- Optional: Tesseract OCR binary for scanned PDFs
- Optional: CUDA for GPU-accelerated embedding/reranker

### Install from source (recommended for development)

```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
python -m venv .venv
source .venv/bin/activate           # Windows: .venv\Scripts\activate
pip install -e ".[dev,benchmarks]"
```

### Verify your environment

```bash
python -m amdi doctor
python -m amdi info
```

### Run the test suite

```bash
pytest                                  # full suite
pytest -m "not slow"                    # fast subset
pytest --cov=amdi --cov-report=term-missing
```

### Start the API server

```bash
python -m amdi serve                    # default 0.0.0.0:8000
# OR
uvicorn amdi.api.app:create_app --factory --reload
```

Interactive OpenAPI docs at: <http://localhost:8000/docs>

---

## REST API surface (current)

| Method | Route | Function |
| --- | --- | --- |
| `GET` | `/healthz` | Liveness probe |
| `GET` | `/readyz` | Readiness probe |
| `POST` | `/v1/documents/upload` | Multimodal document ingestion |
| `POST` | `/v1/query/` | Hybrid 7-method RAG query |
| `POST` | `/v1/advanced/compliance/pii-scan` | PII detect & redact |
| `POST` | `/v1/advanced/entity/resolve` | Cross-doc entity resolution |
| `POST` | `/v1/advanced/versioning/diff` | APTED structural diff |
| `POST` | `/v1/advanced/ingestion/anomaly-check` | IsolationForest outlier gate |
| `POST` | `/v1/advanced/matrix/normalize-quantity` | Locale-aware normalization |
| `POST` | `/v1/advanced/query/decompose` | Sub-query DAG decomposition |
| `POST` | `/v1/advanced/math/unified-evaluation` | Eval state across 16 MIOS domains |
| `POST` | `/v1/advanced/ingestion/parse-speech` | STT + diarization |
| `POST` | `/v1/advanced/ingestion/parse-image-layout` | Layout decomposition + sharpness |
| `POST` | `/v1/advanced/export/llm-optimized` | Compact md / minified json |

---

## Project layout

```
.
├── pyproject.toml               # one source of truth for build + deps + tooling
├── src/amdi/
│   ├── __init__.py              # lazy re-exports (DocumentObject, MasterStateSpace, AMDIOrchestrator)
│   ├── __main__.py              # python -m amdi  (serve / info / doctor / version)
│   ├── config.py                # pydantic-settings, env prefix AMDI_*
│   ├── version.py               # hatch_vcs single source
│   ├── api/
│   │   ├── app.py               # FastAPI factory
│   │   └── routers/             # health, documents, query, advanced
│   ├── core/                    # DocumentObject, MasterStateSpace D, AMDIOrchestrator
│   ├── engines/                 # 12 mathematical engines
│   ├── retrieval/               # hybrid 7-method retrieval
│   ├── ingestion/               # PDF / DOCX / XLSX / PPTX / Image / Audio
│   ├── compliance/              # PII / anomaly
│   ├── entity/                  # Fellegi-Sunter + NetworkX clustering
│   ├── export/                  # llm-optimized exporter
│   ├── versioning/              # APTED tree-edit diff
│   ├── query/                   # sub-query DAG preprocessor
│   ├── connectors/              # AI agent SDKs
│   └── services/container.py    # DI container (async-safe, lazy)
├── tests/                       # pytest; coverage gate ≥70%
├── docs/                        # Architecture.md, Mathematics.md, Benchmarks.md, …
├── ui/src/pages/                # 13 dashboard surfaces
└── .github/workflows/ci.yml     # lint + typecheck + test + build
```

---

## Configuration

Settings load from environment variables prefixed `AMDI_` (or a `.env` file):

```bash
export AMDI_API_PORT=8000
export AMDI_STORAGE_BACKEND=filesystem        # or s3 / memory
export AMDI_EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
export AMDI_ENABLE_RERANKER=1
export AMDI_DEFAULT_TOKEN_BUDGET=8000
export AMDI_JWT_SECRET="$(python -c 'import secrets;print(secrets.token_urlsafe(64))')"
```

See [`src/amdi/config.py`](./src/amdi/config.py) for the full surface.

---

## Status — what is real, what is not

| Claim | Status |
| --- | --- |
| Mathematical engines implemented | ✅ verified by unit tests in CI |
| Spatial DAG acyclicity (Thm 6.1/6.2) | ✅ verified by graph tests |
| Knapsack bound (Thm 9.1) | ✅ verified by optimization tests |
| FastAPI service runs | ✅ verified by `test_app_factory_builds` |
| 50–80% token reduction | 🎯 research target — not yet benchmarked |
| >95% information retention | 🎯 research target |
| >95% citation accuracy | 🎯 research target |
| RAGAS / DeepEval eval harness | 🔜 see `benchmarks/` (Sprint 4) |
| Async ingestion (Celery/arq) | 🔜 see roadmap |
| Streaming `/v1/query/` (SSE) | 🔜 see roadmap |

---

## Roadmap

1. **Sprint 1** *(this PR)*: pyproject + consolidated README + CI + smoke tests
2. **Sprint 2**: tear out prototype scaffolding; publish CHANGELOG, SECURITY, CONTRIBUTING
3. **Sprint 3**: async ingestion (arq + Redis), persistent vector store (Qdrant)
4. **Sprint 4**: RAGAS/DeepEval harness; p50/p95 latency benchmarks; PII/jailbreak corpus
5. **Sprint 5**: 4-language SDK skeletons from one `.proto`

---

## License & authorship

**Proprietary — All rights reserved.** See [`LICENSE`](./LICENSE).

**Author:** Sahil Khutey · with AI Research Collaborator, *Gensouls Lab*
**Series:** *July 2026 Monograph Series & System Specifications.*