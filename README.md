# AEGIS-DocIntel / AMDI-OS

**Adaptive Mathematical Document Intelligence Operating System**

[![License](https://img.shields.io/badge/License-Proprietary-blue.svg)]()
[![Python 3.12+](https://img.shields.io/badge/Python-3.12+-green.svg)]()
[![Tests](https://img.shields.io/badge/Tests-860%2B_Passing-brightgreen.svg)]()
[![Status](https://img.shields.io/badge/Status-Production_Ready-success.svg)]()

---

## Executive Overview

**AEGIS-DocIntel / AMDI-OS** is a production-grade **Pre-LLM Document Intelligence Operating System** that converts unstructured documents (PDF, DOCX, XLSX, PPTX, Images, Speech/Audio) into multi-dimensional, synchronized mathematical representations before exporting token-optimized context to downstream AI agents (ChatGPT, Gemini, Claude, DeepSeek, Qwen, local models).

Built on the **10-tuple Master State Space $D = (P, S, G, R, F, M, T, X, H, E)$**, AEGIS-DocIntel enforces formal mathematical guarantees (**Theorem 6.1 Spatial DAG Acyclicity**, **Theorem 6.2 Kahn Topological Determinism**, **Theorem 9.1 $\frac{1}{2}$-Knapsack Bound**, and **Monotone Submodular Knapsack $(1 - 1/e)$ Approximation Bound**).

> *"A compiler that converts human documents, tables, images, and audio into mathematical objects before any AI model sees them."*

---

## Architectural Highlights

- **16 MIOS Mathematical Domains**: Topology, Spectral, Physics, Information Theory, Graph Theory, Optimization, Tensor, Probability, Statistics, Harmonic Analysis, Computational Geometry, Control Theory, Decision Theory, Dynamical Systems, Linear Algebra, Numerical Analysis.
- **Multimodal Ingestion Engine**:
  - **Documents**: PDF (native & scanned OCR), DOCX, XLSX, PPTX, HTML, Markdown, Plain Text.
  - **Speech & Audio**: WAV, MP3, FLAC, OGG, M4A with Speech-to-Text (STT) transcription, timestamped segments, and speaker diarization.
  - **Visual Layout Decomposition**: Bounding box region detection (Heading, Paragraph, Table, Figure, Caption, Header, Footer), image sharpness variance scoring $\sigma^2(\Delta I)$, and 128-D visual feature embedding.
- **Pre-LLM Security & Compliance Suite**:
  - **PII Redaction**: Regex & NER detection with policy-driven masking (`<US_SSN_REDACTED>`).
  - **Entity Resolution**: Fellegi-Sunter probabilistic matching & NetworkX equivalence clustering.
  - **Structural Version Diff Engine**: APTED tree-edit distance versioning and diff querying.
  - **Ingestion Anomaly Gate**: IsolationForest outlier detection & prompt-injection adversarial filter.
  - **Unit Normalizer**: Locale-aware quantity parsing & point-in-time currency conversion.
  - **Query Decomposition Pre-Processor**: Sub-query dependency DAG parser and executor.
- **LLM Token-Optimized Exporter (`LLMTokenOptimizedExporter`)**:
  - **Compact Markdown (.md)**: Minimal padding, dense pipe tables, inline citations `[Doc:pX]`, and contextual prefixing.
  - **Ultra-Dense Minified JSON (.json)**: Abbreviated keys (`sys`, `ctx`, `sum`, `cits`, `meta`), zero whitespace, and token budget capping.
- **13 UI Software Dashboard Pages**: Full backend API contracts & page data models.

---

## Master 16 Mathematical Intelligence Domains

| Domain Index | Mathematical Domain | Core Formulations & Algorithms | Engine Implementation |
| :-: | :--- | :--- | :--- |
| **1** | **Topology** | Simplicial complexes, Vietoris-Rips filtration, Betti numbers $H_0, H_1, H_2$ | `src/math_concepts/topology.py` |
| **2** | **Spectral** | Graph Laplacian spectrum $L = D - A$, Cheeger inequality expansion | `src/math_concepts/spectral.py` |
| **3** | **Physics** | Ising model spin Hamiltonian $H(s) = -\frac{1}{2} s^T J s - h^T s$, simulated annealing | `src/math_concepts/physics.py` |
| **4** | **Information Theory** | Shannon entropy $H(X) = -\sum p(x) \log p(x)$, mutual information, IB value function | `src/math_concepts/information_theory.py` |
| **5** | **Graph Theory** | Spatial Reading Order DAG (Thm 6.1/6.2), PageRank power iteration, Hypergraph spectral clustering | `src/math_concepts/graph_theory.py` |
| **6** | **Optimization** | Monotone submodular knapsack coverage ($(1 - 1/e)$ bound), Modified density greedy knapsack | `src/math_concepts/optimization.py` |
| **7** | **Tensor** | Multimodal CP / Tucker tensor decomposition, higher-order SVD | `src/math_concepts/tensor.py` |
| **8** | **Probability** | Bayesian posterior updating $P(\theta \mid D) \propto P(D \mid \theta) P(\theta)$ | `src/math_concepts/probability.py` |
| **9** | **Statistics** | Covariance matrix $\Sigma$, Pearson correlation $R$, statistical moments | `src/math_concepts/statistics.py` |
| **10** | **Harmonic Analysis** | Fast Fourier Transform (FFT), spectral density decomposition | `src/math_concepts/harmonic_analysis.py` |
| **11** | **Computational Geometry** | Bounding box Graham scan convex hull, Voronoi proximity diagram | `src/math_concepts/computational_geometry.py` |
| **12** | **Control Theory** | Proportional-Integral-Derivative (PID) error stability feedback loop | `src/math_concepts/control_theory.py` |
| **13** | **Decision Theory** | Expected utility hypothesis, Minimax regret decision matrix | `src/math_concepts/decision_theory.py` |
| **14** | **Dynamical Systems** | Phase space trajectory, largest Lyapunov exponent estimation | `src/math_concepts/dynamical_systems.py` |
| **15** | **Linear Algebra** | Singular Value Decomposition ($A = U \Sigma V^T$), low-rank approximation | `src/math_concepts/linear_algebra.py` |
| **16** | **Numerical Analysis** | Matrix condition number $\kappa(A) = \|A\| \|A^{-1}\|$, floating-point error bounds | `src/math_concepts/numerical_analysis.py` |

---

## 13 UI Software Dashboard Pages Suite

| Page Index | UI Dashboard Module | Primary System Functionality | File Path |
| :-: | :--- | :--- | :--- |
| **1** | **Upload Dashboard** | File ingestion progress tracking, file type validation & error reporting | `ui/src/pages/upload_dashboard.py` |
| **2** | **Document Explorer** | Interactive document browsing, layout tree navigation & metadata filtering | `ui/src/pages/document_explorer.py` |
| **3** | **Geometry Dashboard** | Spatial bounding box coordinates $[x, y, w, h]$ & spatial reading order DAG | `ui/src/pages/geometry_dashboard.py` |
| **4** | **Matrix Dashboard** | Multi-table structure extraction, financial statistical metrics & unit normalization | `ui/src/pages/matrix_dashboard.py` |
| **5** | **Graph Dashboard** | Node degree, closeness, betweenness centrality, PageRank & hypergraph clustering | `ui/src/pages/graph_dashboard.py` |
| **6** | **Memory Dashboard** | L0–L5 multi-tier hierarchical memory cache monitoring | `ui/src/pages/memory_dashboard.py` |
| **7** | **Retrieval Dashboard** | Hybrid 7-method vector + BM25 + visual ColPali search interface | `ui/src/pages/retrieval_dashboard.py` |
| **8** | **Analytics Dashboard** | Cross-document entity resolution & analytical insights | `ui/src/pages/analytics_dashboard.py` |
| **9** | **Performance Dashboard** | Sub-second engine latency, memory allocation & throughput metrics | `ui/src/pages/performance_dashboard.py` |
| **10** | **Agent Dashboard** | AI connector management (ChatGPT, Gemini, Claude, DeepSeek, Qwen) | `ui/src/pages/agent_dashboard.py` |
| **11** | **Settings Dashboard** | System-wide configuration, storage backends & environment flags | `ui/src/pages/settings_dashboard.py` |
| **12** | **Math & Advanced Dashboard** | PII redaction, entity canonicalization, version diff, anomaly gate & 16 MIOS domains | `ui/src/pages/math_advanced_dashboard.py` |
| **13** | **Speech & Image Dashboard** | Audio STT transcription, speaker diarization, SNR & visual image layout parsing | `ui/src/pages/speech_image_dashboard.py` |

---

## Installation & Verification

### Prerequisites
- Python 3.12+
- Dependencies listed in `requirements.txt` / `requirements.lock.txt`

### 1. Clone & Environment Setup
```bash
git clone https://github.com/SahilKhutey/AEGIS-DocIntel.git
cd AEGIS-DocIntel
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Run Test Suite
To run all **860+ passing unit test items**:
```bash
python -m pytest tests/
```

### 3. Start REST API Server
```bash
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload
```
Access interactive OpenAPI documentation at **http://localhost:8000/docs**.

---

## REST API Endpoints Overview

| HTTP Method | Route | Description |
| :--- | :--- | :--- |
| `POST` | `/v1/documents/upload` | Upload & ingest document (PDF, DOCX, XLSX, PPTX, Image, Audio) |
| `POST` | `/v1/query/` | Execute hybrid RAG query over ingested context |
| `POST` | `/v1/advanced/compliance/pii-scan` | Scan & redact PII with policy rules |
| `POST` | `/v1/advanced/entity/resolve` | Resolve cross-document entity mentions into canonical clusters |
| `POST` | `/v1/advanced/versioning/diff` | Compute structural tree-edit distance between document versions |
| `POST` | `/v1/advanced/ingestion/anomaly-check` | Scan document for IsolationForest outliers & prompt injection |
| `POST` | `/v1/advanced/matrix/normalize-quantity` | Parse locale quantities & normalize currencies |
| `POST` | `/v1/advanced/query/decompose` | Decompose complex query into sub-query dependency DAG |
| `POST` | `/v1/advanced/math/unified-evaluation` | Evaluate document state $D$ across all 16 mathematical domains |
| `POST` | `/v1/advanced/ingestion/parse-speech` | Transcribe speech audio with speaker diarization & SNR scoring |
| `POST` | `/v1/advanced/ingestion/parse-image-layout` | Decompose document image layout & compute sharpness score |
| `POST` | `/v1/advanced/export/llm-optimized` | Export token-optimized Markdown or minified JSON context |

---

## Repository Structure

```text
AEGIS-DocIntel/
├── src/
│   ├── ael/                   # Adaptive Export Layer & token budget allocator
│   ├── api/                   # FastAPI routes, auth, schemas, and routers
│   ├── compliance/            # PII detection & policy redaction engine
│   ├── connectors/            # AI agent connectors (LangChain, LlamaIndex, Claude, etc.)
│   ├── core/                  # DocumentObject, Master State D, AMDIOrchestrator
│   ├── engines/               # 12 core mathematical & spatial reading order engines
│   ├── entity/                # Cross-document entity resolution (Fellegi-Sunter)
│   ├── export/                # Exporters (Markdown, JSON, YAML, LLMTokenOptimizedExporter)
│   ├── ingestion/             # PDF, DOCX, XLSX, PPTX, Image, SpeechLoader, OCREngine
│   ├── math_concepts/         # MasterUnifiedMathEngine & 16 mathematical domains
│   ├── query/                 # Query decomposition DAG pre-processor
│   ├── services/              # ServiceContainer dependency injection
│   └── versioning/            # Structural diff engine (APTED tree-edit distance)
├── ui/
│   └── src/pages/             # 13 UI Dashboard software pages
├── tests/                     # 860+ passing pytest test items
├── Aegis Doc/                 # 11 Foundational Publications & Monographs
└── requirements.txt           # Dependency requirements
```

---

## License & Authorship

**Sahil Khutey** (with AI Research Collaborator, Gensouls Lab)  
*July 2026 Monograph Series & System Specifications.*  
Proprietary — All rights reserved.