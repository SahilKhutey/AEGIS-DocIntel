# AMDI-OS Systems

## 1. System Overview

AMDI-OS is composed of 6 primary subsystems:

| Subsystem | Purpose | Components |
|-----------|---------|------------|
| **Ingestion** | Load documents | PDF, DOCX, PPTX, XLSX, OCR |
| **Intelligence** | Extract representations | 12 engines + Fusion |
| **Memory** | Store & retrieve | L0-L5 hierarchy |
| **Retrieval** | Search & rank | 7 hybrid methods |
| **Context** | Build AI-ready context | Rank/Compress/Summarize/Assemble |
| **Verification** | Validate outputs | Citation/Fact/Confidence/Hallucination |

## 2. Subsystem Specifications

### 2.1 Ingestion Subsystem

**Purpose**: Load and normalize documents from various formats.

**Components**:

- `PDFLoader` — PyMuPDF + pdfplumber
- `DOCXLoader` — python-docx
- `PPTXLoader` — python-pptx
- `XLSXLoader` — openpyxl
- `OCRLoader` — Tesseract / PaddleOCR / DocTR
- `LayoutDetector` — Detect reading order, tables, figures
- `MetadataExtractor` — Author, date, title, DOI
- `LanguageDetector` — langdetect / fasttext

**Interfaces**:

- Input: file path, bytes
- Output: `Document` object

**Requirements**:

- Supports scanned PDFs via OCR
- Handles corrupted files gracefully
- Extracts metadata from multiple sources

### 2.2 Intelligence Subsystem (12 Engines)

#### Wave 1 (Foundational)

**Geometry Engine**: Spatial coordinates

- Input: Document with bounding boxes
- Output: Coordinate system + element positions
- Algorithm: Coordinate normalization, alignment detection

**Matrix Engine**: Tabular representations

- Input: Tables (lists of lists)
- Output: Matrix + statistics (mean, median, growth)
- Algorithm: SVD, correlation analysis

**Template Engine**: Fingerprint matching

- Input: Document structure
- Output: Template fingerprint
- Algorithm: Hamming/Jaccard/cosine similarity

#### Wave 2 (Statistical)

**Frequency Engine**: TF-IDF / BM25

- Algorithm: BM25 scoring
- Output: Term-document matrix

**Recurrence Engine**: LSH / MinHash

- Algorithm: MinHash signature + LSH banding
- Output: Near-duplicate detection

**Semantic Engine**: Embeddings

- Algorithm: sentence-transformers, OpenAI embeddings
- Output: 384/768/1536-dim vectors

**Graph Engine**: Graph operations

- Algorithm: PageRank, BFS, shortest paths
- Output: Ranked nodes + communities

#### Wave 4 (Advanced)

**Topology Engine**: Persistent homology

- Algorithm: Betti numbers, Vietoris-Rips filtration
- Output: Topological features

**Spectral Engine**: Eigenvalue analysis

- Algorithm: Laplacian decomposition, spectral clustering
- Output: Eigenvectors + clusters

**Tensor Engine**: Multi-mode decomposition

- Algorithm: Tucker HOOI, CP ALS, TT-SVD
- Output: Compressed tensor + components

**Information Physics Engine**: Physical metaphor

- Algorithm: Energy, gravity, fields, entropy
- Output: Information physics metrics

**Retrieval Engine**: Hybrid retrieval

- Algorithm: 7-method hybrid + RRF fusion
- Output: Ranked documents

### 2.3 Fusion Subsystem

**Purpose**: Combine engine outputs into unified scores.

**Components**:

- `DynamicWeightLearner` — Adaptive weights
- `Ranker` — Multi-method ranking (Weighted Sum / RRF / Borda / Condorcet)
- `ConfidenceScorer` — Composite confidence
- `FusionScorer` — Unified scoring
- `WeightOptimizer` — Gradient / bandit / coord descent

**Algorithms**:

- Softmax temperature scaling
- Cohen's weighted sum
- Reciprocal Rank Fusion (RRF)

### 2.4 Memory Subsystem

**Purpose**: Six-level hierarchical storage.

**Levels**:

- L0 Raw: original content (highest volume, slowest)
- L1 Templates: fingerprints (medium)
- L2 Structures: graphs/topology (medium)
- L3 Tables: matrix data (medium)
- L4 Semantic: embeddings (fast, costly)
- L5 Summaries: compressed (fastest, smallest)

**Operations**: Store, Cache (LRU/LFU/ARC), Promote (up), Evict (down), Retrieve

**Promotion rule**: `score = α·freq + β·imp + γ·recency`

### 2.5 Retrieval Subsystem

**Purpose**: 7-method hybrid retrieval.

**Methods**:

1. Semantic (cosine / dot / euclidean)

2. Matrix (column/row cosine, SVD)

3. Geometry (k-NN, radius, bbox)

4. Graph (PageRank, BFS, shortest path)

5. Template (Hamming, Jaccard, cosine)

6. Frequency (TF-IDF, BM25)

7. Recurrence (LSH + MinHash)

**Fusion**: Reciprocal Rank Fusion (RRF)

### 2.6 Context Subsystem

**Purpose**: Build optimized AI-agent-ready context.

**Pipeline**: Rank → Compress → Summarize → Assemble

**Components**:

- `ContextRanker` — Weighted + MMR diversity
- `ContextCompressor` — Truncate/Extractive/Abstractive/Hybrid
- `ContextSummarizer` — Lead/Middle/Tail/Extractive/TF-IDF
- `ContextAssembler` — Section assembly → UEO
- `TokenCounter` — Budget management

### 2.7 Verification Subsystem

**Purpose**: Final validation before user delivery.

**Components**:

- `CitationVerifier` — Citation matching
- `FactVerifier` — Fact claim verification
- `ConfidenceScorer` — Composite confidence (Grade A-F)
- `HallucinationDetector` — 5-signal detection
- `ConsistencyChecker` — Internal consistency
- `SourceVerifier` — Source reliability

**Detection signals**:

1. Uncited claims

2. Internal contradictions

3. Specificity paradox

4. Entity confusion

5. Numerical inconsistencies

## 3. Interfaces

### 3.1 Internal Interfaces

```python

class EngineInterface:

    def process(self, document: Document) -> EngineOutput: ...

class MemoryInterface:

    def store(self, level: MemoryLevel, data: Any) -> str: ...

    def retrieve(self, level: MemoryLevel, item_id: str) -> Any: ...

class RetrievalInterface:

    def search(self, query: Query) -> RetrievalResult: ...

class ContextInterface:

    def build(self, candidates: List[Candidate]) -> UEO: ...

class VerificationInterface:

    def verify(self, response: str, sources: Dict) -> VerificationReport: ...

### 3.2 External Interfaces

REST API: HTTPS/JSON

gRPC: Internal microservices

WebSocket: Real-time dashboards

Prometheus: Metrics scrape endpoint

## 4. Requirements Matrix

Requirement	Component	Status

Support PDF/DOCX/PPTX/XLSX	Ingestion	✓

Handle scanned PDFs (OCR)	Ingestion	✓

12 mathematical engines	Intelligence	✓

7 retrieval methods	Retrieval	✓

6 memory levels (L0-L5)	Memory	✓

Token reduction 20-70%	Context	✓

Latency reduction 30-60%	Optimization	✓

Accuracy > 95%	Verification	✓

Hallucination < 5%	Verification	✓

6 AI agent connectors	Connectors	✓

4 export formats	Export	✓

11 dashboard pages	Dashboards	✓

Tamper-evident audit log	Security	✓

RBAC + ABAC	Security	✓

JWT + API keys + MFA	Security	✓

Docker + K8s deployment	Deployment	✓

Prometheus + Grafana monitoring	Monitoring	✓

CI/CD pipeline	CI/CD	✓

## 5. Operational Procedures

### 5.1 Startup

# 1. Start dependencies

docker compose up -d postgres redis qdrant neo4j

# 2. Run migrations

python -m backend.src.database.migrate

# 3. Start API server

uvicorn backend.src.api.main:app --host 0.0.0.0 --port 8000

# 4. Start workers

celery -A backend.src.workers worker --loglevel=info

# 5. Start frontend

npm start

### 5.2 Document Processing

# 1. Upload

doc = await api.upload_document("path/to/file.pdf")

# 2. Process

report = await api.process_document(doc.id)

# 3. Index

await api.index_document(doc.id)

# 4. Available for retrieval

### 5.3 Query Handling

# 1. User query

query = "What is quantum entanglement?"

# 2. Embed

embedding = await semantic.embed(query)

# 3. Retrieve

results = await retrieval.search(embedding, top_k=10)

# 4. Build context

context = await context_builder.build(results, budget=4000)

# 5. Send to agent

response = await claude.send_ueo(context.ueo)

# 6. Verify

verification = await verifier.verify(response, sources)

# 7. Return

return {

    "answer": response.text,

    "citations": response.citations,

    "confidence": verification.confidence,

}

### 5.4 Maintenance

# Daily: GC + compaction

python -m backend.scripts.daily_maintenance

# Weekly: Index optimization

python -m backend.scripts.optimize_indexes

# Monthly: Model refresh

python -m backend.scripts.refresh_models

## 6. Lifecycle Management

### 6.1 Document Lifecycle

Upload → Process → Index → Active → (Promote/Evict) → Archive → Delete

### 6.2 Model Lifecycle

Training → Validation → Staging → Canary (10%) → Production (100%) → Monitor → Retrain

### 6.3 Data Lifecycle

Hot (L4-L5, cache) → Warm (L2-L3, disk) → Cold (L0-L1, S3 archive) → Delete (after 90d)

### 6.4 Deployment Lifecycle

Dev → Test → Staging → Canary (5%) → Canary (15%) → Canary (30%) → Full (100%)

## 7. Performance Characteristics

Component	Latency (p50)	Latency (p95)	Throughput

Document upload (10 pages)	2s	5s	30 docs/min

Document processing (12 engines)	30s	90s	4 docs/min

Retrieval (7 methods, top-10)	200ms	800ms	5 queries/sec

Context building	100ms	400ms	10 builds/sec

AI agent call (Claude)	2s	5s	0.5 calls/sec

Verification	50ms	200ms	20 verifies/sec

End-to-end (no LLM)	400ms	1.5s	2 queries/sec

End-to-end (with LLM)	2.5s	6s	0.4 queries/sec

## 8. Capacity Planning

Storage (per 1000 documents)

Level	Size per Doc	1000 Docs

L0 Raw	500 KB	500 MB

L1 Templates	5 KB	5 MB

L2 Structures	50 KB	50 MB

L3 Tables	100 KB	100 MB

L4 Semantic	40 KB (768-dim × 10 chunks)	40 MB

L5 Summaries	5 KB	5 MB

Total	~700 KB	~700 MB

Compute

Component	CPU/docs	Memory/docs

Geometry	0.05s	50 MB

Semantic	0.5s	200 MB

Topology	0.2s	100 MB

Total pipeline	30s	4 GB peak

---