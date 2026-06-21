# AEGIS-AMDI-OS
## Adaptive Mathematical Document Intelligence Operating System

> **A pre-LLM intelligence layer** that converts PDFs, DOCX, XLSX, PPTX and images into 7 synchronized mathematical representations and adaptively routes queries to the most efficient layer.

---

## Mathematical Foundation

```
D = {S, G, R, F, M, T, X}

R_final = α·S + β·G + γ·R + δ·F + ε·M + ζ·T + η·X,   ΣW = 1
```

| Layer | Symbol | Engine | Method |
|-------|--------|--------|--------|
| Semantic | S | SemanticEngine | Dense embeddings + NER + keyphrases |
| Geometry | G | GeometryEngine | Spatial index E_i=(x,y,w,h,p) |
| Recurrence | R | RecurrenceEngine | MinHash + LSH deduplication |
| Frequency | F | FrequencyEngine | TF-IDF + Shannon entropy |
| Matrix | M | MatrixEngine | NumPy algebraic tables |
| Template | T | TemplateEngine | Cosine-cluster fingerprints |
| Graph | X | GraphEngine | NetworkX PageRank + BFS |

---

## Quick Start

### 1. Install
```bash
pip install -e ".[dev]"
```

### 2. Run API Server
```bash
make run
# → http://localhost:8000
# → http://localhost:8000/docs
```

### 3. Run Dashboard
```bash
cd dashboard && npm install && npm run dev
# → http://localhost:5173
```

### 4. Docker (Full Stack)
```bash
make docker-up
# API:       http://localhost:8000
# Dashboard: http://localhost:5173
# Grafana:   http://localhost:3000  (admin/admin)
# Qdrant:    http://localhost:6333
```

---

## API Reference

### Ingest Document
```bash
curl -X POST http://localhost:8000/ingest \
  -F "file=@report.pdf"
```
**Response:**
```json
{
  "doc_id": "550e8400-...",
  "filename": "report.pdf",
  "pages": 24,
  "elements": 312,
  "tables": 8,
  "templates": 3,
  "ingestion_ms": 187.4,
  "compression_pct": 73.2
}
```

### Query
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"question": "What is the total revenue?", "doc_id": "550e8400-..."}'
```
**Response:**
```json
{
  "answer": "Total revenue for 2024 was $5,247,000 [1]",
  "citations": [{"num": 1, "page": 3, "type": "table"}],
  "confidence": 0.95,
  "confidence_label": "HIGH",
  "query_type": "aggregation",
  "weights_used": {"semantic": 0.15, "matrix": 0.65, ...},
  "table_direct": ["SUM(Revenue) = 5247000.00  [Table p.3]"],
  "grounded": true,
  "latency_ms": 42.1,
  "tokens_used": 847,
  "model": "gpt-4o"
}
```

### Streaming Query
```bash
curl http://localhost:8000/query/stream?question=Summarize+this+document
```

---

## Performance Targets

| Metric | Baseline (Token-only) | AMDI Target |
|--------|-----------------------|-------------|
| Token Usage | 100% (8000 tok) | 10–30% (500–2000 tok) |
| Query Latency | 100% | 30–60% |
| Table Accuracy | ~65% | >95% |
| Template Detection | ~40% | >95% |
| Large Doc (100+ pg) | Degrades | Consistent |
| Cross-References | Poor | Excellent |

---

## Configuration

Copy `.env.example` to `.env` and configure:

```bash
# LLM Provider (mock | openai | anthropic | google | vllm | litellm)
AMDI_LLM_PROVIDER=openai
AMDI_LLM_MODEL=gpt-4o
AMDI_OPENAI_API_KEY=sk-...

# Storage
AMDI_REDIS_URL=redis://localhost:6379/0
AMDI_QDRANT_URL=http://localhost:6333

# Context budget
AMDI_TARGET_CONTEXT_TOKENS=1500
AMDI_MAX_CONTEXT_TOKENS=4096
```

---

## Architecture

```
INPUT (PDF/DOCX/XLSX/PPTX/Images)
        │
        ▼
LAYER 2: Normalization
  Parser → OCR → Layout Detector
        │
        ▼
MULTI-REPRESENTATION ENGINE (parallel)
  ┌────────┬────────┬────────┬────────┐
  S        G        R        F        
  Semantic Geometry Recurrn  Freq     
  ┌────────┬────────┬────────┐
  M        T        X        
  Matrix   Template Graph    
        │
        ▼
LAYER 10: Adaptive Fusion
  QueryClassifier → route(q) → FusionWeights
  W = argmax_{W} {query_type}
  R = α·S + β·G + γ·R + δ·F + ε·M + ζ·T + η·X
  MMR deduplication
        │
        ▼
LAYER 11: Hierarchical Memory
  L5-Summary (Hot) → L4-Chunk → L3-Table
  L2-Structure → L1-Template → L0-Raw (Cold)
        │
        ▼
LAYER 12: Context Builder
  Token-budget greedy assembly (500–2000 tokens)
        │
        ▼
LLM INTERFACE (GPT-4o / Claude / Gemini / DeepSeek / Local)
        │
        ▼
RESPONSE with citations + confidence
```

---

## License

Apache 2.0 — AEGIS Research
