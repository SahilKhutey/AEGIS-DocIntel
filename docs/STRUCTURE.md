# Canonical Repository Structure

This is the **single source of truth** for how AEGIS-DocIntel is organized.

```
AEGIS-DocIntel/
├── pyproject.toml                      ONE source of truth for deps + tooling
├── README.md                           SINGLE README (no variants)
├── LICENSE
├── CHANGELOG.md
├── SECURITY.md
├── CONTRIBUTING.md
├── Dockerfile                          API image (Stage 1 of any deploy)
├── docker/
│   ├── api.Dockerfile
│   └── worker.Dockerfile
├── docker-compose.yml                  Local dev stack
│
├── src/amdi/                           CANONICAL PACKAGE — pip install -e .
│   ├── __init__.py
│   ├── __main__.py                     `python -m amdi`
│   ├── version.py
│   ├── config.py                       pydantic-settings, env prefix AMDI_*
│   ├── legacy_bridge.py                BC shims (deprecation window only)
│   │
│   ├── api/                            FastAPI surface
│   │   ├── app.py                      create_app() factory
│   │   ├── deps.py                     DI helpers
│   │   └── routers/
│   │       ├── health.py
│   │       ├── documents.py
│   │       ├── jobs.py
│   │       ├── query.py
│   │       └── advanced.py
│   │
│   ├── core/                           Domain objects
│   │   ├── document_object.py
│   │   ├── master_state.py
│   │   └── orchestrator.py
│   │
│   ├── engines/                        12 mathematical engines
│   │   ├── geometry.py
│   │   ├── frequency.py
│   │   ├── recurrence.py
│   │   ├── matrix.py
│   │   ├── template.py
│   │   ├── semantic.py
│   │   ├── graph.py
│   │   ├── topology.py
│   │   ├── spectral.py
│   │   ├── tensor.py
│   │   ├── info_physics.py
│   │   └── retrieval.py                (engine façade; see retrieval/)
│   │
│   ├── retrieval/                      Hybrid 7-method retrieval subsystem
│   │   ├── hybrid.py
│   │   ├── schemas.py
│   │   ├── fusion.py
│   │   ├── reranker.py
│   │   ├── deduplication.py
│   │   ├── telemetry.py
│   │   ├── index_store.py
│   │   ├── backends/{inmemory,filesystem,faiss_store}.py
│   │   └── methods/{base,bm25,dense,frequency,geometry,graph,matrix,template}.py
│   │
│   ├── ingestion/                      PDF, DOCX, XLSX, PPTX, Image, Audio
│   │   ├── pdf.py
│   │   ├── docx.py
│   │   ├── xlsx.py
│   │   ├── pptx.py
│   │   ├── html.py
│   │   ├── text.py
│   │   ├── image.py
│   │   ├── audio.py
│   │   ├── ocr.py
│   │   └── preprocessor.py
│   │
│   ├── jobs/                           Async ingestion pipeline (Sprint 1)
│   │   ├── schemas.py
│   │   ├── ledger.py
│   │   ├── worker.py
│   │   ├── tasks.py
│   │   ├── progress.py
│   │   ├── shutdown.py
│   │   └── cli.py
│   │
│   ├── compliance/                     PII, anomaly, redaction
│   │   ├── pii.py
│   │   ├── redaction.py
│   │   ├── anomaly.py
│   │   └── injection_filter.py
│   │
│   ├── entity/                         Cross-doc entity resolution
│   │   └── resolver.py
│   │
│   ├── versioning/                     APTED tree-edit distance diff
│   │   └── diff.py
│   │
│   ├── export/                         LLMTokenOptimizedExporter + others
│   │   ├── llm_optimized.py
│   │   ├── markdown.py
│   │   ├── json.py
│   │   └── yaml.py
│   │
│   ├── query/                          Sub-query DAG preprocessor
│   │   └── decomposition.py
│   │
│   ├── math_concepts/                  MasterUnifiedMathEngine (16 domains)
│   │   ├── topology.py
│   │   ├── spectral.py
│   │   ├── physics.py
│   │   ├── information_theory.py
│   │   ├── graph_theory.py
│   │   ├── optimization.py
│   │   ├── tensor.py
│   │   ├── probability.py
│   │   ├── statistics.py
│   │   ├── harmonic_analysis.py
│   │   ├── computational_geometry.py
│   │   ├── control_theory.py
│   │   ├── decision_theory.py
│   │   ├── dynamical_systems.py
│   │   ├── linear_algebra.py
│   │   └── numerical_analysis.py
│   │
│   ├── connectors/                     AI agent SDKs (chat backends)
│   │   ├── base.py
│   │   ├── chatgpt.py
│   │   ├── gemini.py
│   │   ├── claude.py
│   │   ├── deepseek.py
│   │   ├── qwen.py
│   │   └── local.py                    llama.cpp / ollama
│   │
│   ├── services/                       Lazy, async DI container
│   │   └── container.py
│   │
│   └── ael/                            Adaptive Export Layer / token budget
│       └── budget.py
│
├── tests/
│   ├── conftest.py
│   ├── test_smoke.py
│   ├── migration/                      enforces the new layout
│   ├── retrieval/                      per-method + fusion + e2e
│   ├── jobs/                           arq + SSE tests
│   ├── benchmarks/                     (separate suite under benchmarks/)
│   └── api/                            FastAPI end-to-end
│
├── benchmarks/                         Run separately; not gated by unit tests
│   ├── golden/                         questions + corpus
│   ├── pipelines/
│   ├── metrics/
│   ├── runners/
│   └── docs/Benchmarks.md              auto-published
│
├── ui/                                 Frontend (Streamlit or React, per decision)
│
└── ops/                                Deployment helpers
    ├── prometheus.yml
    ├── redis.conf
    ├── grafana/
    └── helm/                           # reserved
```

## Why this layout

- **`src/amdi/`** so `pip install -e .` produces real, importable, type-checked wheels.
- **Flat domains** (no `core.domain.subdomain.subsub` crates — overkill here).
- **No `backend/` prefix.** The README's old `backend/src/...` import path never
  worked because `backend` is not a Python package.
- **`retrieval/` is a subsystem,** not an engine. Engines live flat in `engines/`.
- **`benchmarks/` lives outside the install target** so it never bloats the wheel.
- **`legacy_bridge.py`** is the single, well-named BC shim. Anything else that
  needed to be kept from the legacy layout is a *symptom* of incomplete migration.
